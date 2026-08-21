"""Weekly RAG discovery engine.

Fetches trending RAG repositories from the GitHub Search API and checks
benchmarks.md for stale citations. Results are written to
.github/PROPOSED_UPDATES.md (gitignored) for the CI workflow to post as a
GitHub issue comment.
"""

import calendar
import datetime
import logging
import os
import re
from pathlib import Path

import requests

# Entry grammar regexes shared with pr_entry_validator.py (see entry_patterns.py).
# Private aliases keep the module-internal names stable.
from entry_patterns import ENTRY_ANCHOR_RE as _ENTRY_ANCHOR_RE
from entry_patterns import ENTRY_DESC_RE as _ENTRY_DESC_RE
from entry_patterns import REPO_URL_RE as _REPO_URL_RE
from entry_patterns import VERIFIED_RE as _VERIFIED_RE
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Absolute base for links embedded in reports. The report is posted verbatim as a
# GitHub *issue comment*, where relative paths like ../CONTRIBUTING.md do not
# resolve — absolute blob URLs work both in the .github/ file and in the comment.
REPO_BLOB = "https://github.com/Yigtwxx/awesome-rag-production/blob/main"

# Markdown table separator cell, e.g. `:---`, `---`, `:---:`.
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")

# A benchmarks.md Date cell marked `(paper)` cites a fixed publication date and
# is exempt from the staleness check. See parse_row_date.
PAPER_CITATION_RE = re.compile(r"\(paper\)", re.IGNORECASE)

# Self-refs and well-known non-tool links to ignore when scanning README.
_SKIP_OWNERS = {"Yigtwxx", "sindresorhus", "github", "actions"}
_SKIP_REPOS = {"awesome", "awesome-list", ".github"}

# Repos repeatedly surfaced by topic:rag but out of scope for this infrastructure
# list. Seeded from documented "out-of-scope" triage verdicts (see the triage
# record in .github/DISCOVERY_TRIAGE.md / FAQ § Scope).
#
# Each entry maps the slug as written at triage time to the repository's GitHub
# id. The slug is for humans reading the diff; the id is what actually matches.
# A rejected project that moves org keeps its id but changes its slug, so
# slug-only matching silently re-admits it: graphify was rejected as
# safishamsi/graphify on 2026-08-01, moved to Graphify-Labs/graphify, and came
# back as the top candidate for three consecutive weekly reports. Its id
# (1200597263) never changed.
#
# Adding an entry: `gh api repos/<owner>/<name> --jq .id`. A None id still
# matches by slug, but loses rename protection and is warned about at run time;
# tests/test_discovery_engine.py enforces that every entry carries one.
# Already-listed repos do NOT belong here — README dedup handles those.
OUT_OF_SCOPE_REPOS: dict[str, int | None] = {
    # End-user apps / low-code platforms.
    "langgenius/dify": 626805178,
    "open-webui/open-webui": 701547123,
    "flowiseai/flowise": 621803253,
    "mintplex-labs/anything-llm": 649170660,
    "jeecgboot/jeecgboot": 159152904,
    "khoj-ai/khoj": 396569538,
    "cinnamon/kotaemon": 777111718,
    "labring/fastgpt": 605673387,
    "onyx-dot-app/onyx": 633262635,
    "simstudioai/sim": 912559512,
    "1panel-dev/maxkb": 691347156,
    "coze-dev/coze-studio": 1008726722,
    "tencent/weknora": 1024118326,
    "eosphoros-ai/db-gpt": 627480054,
    "arc53/docsgpt": 596516907,
    # General agent platforms / runtimes — agent infra, not RAG infra.
    "elizaos/eliza": 826170402,
    # Meta-lists, tutorials, educational guides (no production-infra focus).
    "shubhamsaboo/awesome-llm-apps": 793375104,
    "dair-ai/prompt-engineering-guide": 579082810,
    "datawhalechina/hello-agents": 1052050442,
    "datawhalechina/happy-llm": 806854629,
    "patchy631/ai-engineering-hub": 876064934,
    "hkuds/deeptutor": 1124219907,
    "bojieli/ai-agent-book": 1053118194,
    "nirdiamant/genai_agents": 854807707,
    "nirdiamant/agents-towards-production": 1003143578,
    "accumulatemore/cv": 476314415,
    "liyupi/ai-guide": 931950959,
    # Template / demo galleries.
    "pathwaycom/llm-app": 668195240,
    # Coding-assistant / session-memory plugins (not RAG infra).
    # Same repository under both slugs: rejected under the first, moved to the
    # second. Kept as a pair so the rename stays visible in the source.
    "safishamsi/graphify": 1200597263,
    "graphify-labs/graphify": 1200597263,
    "thedotmack/claude-mem": 1048065319,
    # General-purpose scrapers — ingestion-adjacent but not RAG infrastructure.
    "scrapegraphai/scrapegraph-ai": 749126547,
}

# Ids are what the filter actually matches on; the dict keys stay the readable
# record of why each repo is here.
OUT_OF_SCOPE_REPO_IDS = {
    repo_id for repo_id in OUT_OF_SCOPE_REPOS.values() if repo_id is not None
}


def is_out_of_scope(project: dict) -> bool:
    """Return True when a search result is on the out-of-scope denylist.

    Matches on the immutable repository id first so a rejected project that
    changes owner or name stays rejected, and falls back to the slug for
    entries whose id has not been filled in yet.
    """
    if project.get("id") in OUT_OF_SCOPE_REPO_IDS:
        return True
    return (project.get("full_name") or "").lower() in OUT_OF_SCOPE_REPOS


def filter_candidates(
    projects: list[dict], listed_slugs: set[str]
) -> tuple[list[dict], int, int]:
    """Drop already-listed and out-of-scope repos from search results.

    Returns the surviving projects plus how many were removed by each rule, so
    the caller can log the split instead of a single opaque total.
    """
    kept: list[dict] = []
    listed_hits = 0
    denied_hits = 0
    for project in projects:
        if (project.get("full_name") or "").lower() in listed_slugs:
            listed_hits += 1
            continue
        if is_out_of_scope(project):
            denied_hits += 1
            continue
        kept.append(project)
    return kept, listed_hits, denied_hits


def _build_session() -> requests.Session:
    """Return a requests Session with retry-and-backoff configured."""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _listed_repo_slugs(repo_root: Path) -> set[tuple[str, str]]:
    """Return the (owner, repo) pairs for every GitHub repo linked in README.md.

    Skips self-references and well-known non-tool links. Returns an empty set
    when README.md is absent or unreadable.
    """
    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        return set()
    try:
        readme_text = readme_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("Could not read README for repo-slug extraction: %s", exc)
        return set()

    slugs: set[tuple[str, str]] = set()
    for owner, repo in _REPO_URL_RE.findall(readme_text):
        # Strip trailing punctuation that the regex may have captured.
        repo = repo.rstrip(".,;:")
        if not owner or not repo:
            continue
        if owner in _SKIP_OWNERS or repo in _SKIP_REPOS:
            continue
        slugs.add((owner, repo))
    return slugs


def _row_cells(line: str) -> list[str]:
    """Split a markdown table row into trimmed cell texts."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _date_column_index(header: str) -> int | None:
    """Index of the header cell naming a date column, if any."""
    for index, cell in enumerate(_row_cells(header)):
        if "date" in cell.lower():
            return index
    return None


def parse_row_date(text: str) -> datetime.date | None:
    """Interpret a Date cell as the latest calendar day it could refer to.

    benchmarks.md dates are deliberately coarse — a leaderboard snapshot may be
    known only to the year (``2025``), a paper only to the month (``2022-12``),
    and some carry a suffix (``2024 (active doc)``). Partial dates resolve to
    the END of the period (``2024`` -> 2024-12-31) so a row is only ever flagged
    when even the most generous reading is stale.

    Returns None when the cell holds no date at all (e.g. "Ongoing"), which is
    how non-date columns and prose cells opt out. A cell marked ``(paper)`` also
    returns None: a peer-reviewed publication date is a fixed historical fact,
    not a freshness signal, so nagging about it every week is noise. Mark a row
    that way only when the citation is a published paper whose result does not
    expire — a vendor doc or leaderboard snapshot is not exempt.
    """
    if PAPER_CITATION_RE.search(text):
        return None
    match = re.search(r"\b(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?\b", text)
    if not match:
        return None
    year, month, day = match.group(1), match.group(2), match.group(3)
    try:
        if day:
            return datetime.date(int(year), int(month), int(day))
        if month:
            last_day = calendar.monthrange(int(year), int(month))[1]
            return datetime.date(int(year), int(month), last_day)
        return datetime.date(int(year), 12, 31)
    except (ValueError, calendar.IllegalMonthError):
        return None


def check_benchmark_freshness(
    repo_root: Path, today: datetime.date | None = None
) -> None:
    """Flag benchmarks.md rows whose cited source is older than STALE_DAYS.

    Reads the Date cell of each table rather than scanning whole lines: a naive
    line-wide date regex matches arXiv identifiers (``abs/2212.06121``) and
    other incidental digits, which is why the previous version silently matched
    nothing at all and reported "all rows current" every week.

    Each table's date column is located from its header row, so tables that use
    "Snapshot Date" or omit a date column entirely are handled without
    configuration. Appends a warning section to PROPOSED_UPDATES.md when stale
    rows are found; exits silently otherwise. ``today`` is injectable for
    deterministic tests.
    """
    STALE_DAYS = 365
    benchmarks_path = repo_root / "benchmarks.md"
    if not benchmarks_path.exists():
        return

    today = today or datetime.date.today()
    stale_threshold = today - datetime.timedelta(days=STALE_DAYS)
    stale_rows: list[tuple[int, int, str]] = []

    try:
        lines = benchmarks_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        log.warning("Benchmark freshness check skipped: %s", exc)
        return

    date_column: int | None = None
    for line_no, line in enumerate(lines, 1):
        if not line.startswith("|"):
            date_column = None  # table ended
            continue

        cells = _row_cells(line)
        if all(TABLE_SEPARATOR_RE.match(cell) for cell in cells if cell):
            continue  # `| :--- | :--- |` separator directly under the header

        # A row followed by a separator is the header: learn its date column.
        nxt = lines[line_no] if line_no < len(lines) else ""
        if nxt.strip().startswith("|") and all(
            TABLE_SEPARATOR_RE.match(cell) for cell in _row_cells(nxt) if cell
        ):
            date_column = _date_column_index(line)
            continue

        if date_column is None or date_column >= len(cells):
            continue
        row_date = parse_row_date(cells[date_column])
        if row_date is None:
            continue
        if row_date < stale_threshold:
            days_old = (today - row_date).days
            stale_rows.append((line_no, days_old, line.strip()[:120]))

    if not stale_rows:
        log.info("Freshness check: all benchmark rows are current.")
        return

    output_path = repo_root / ".github" / "PROPOSED_UPDATES.md"
    # Create the directory rather than assuming an earlier audit already did:
    # if discovery fails before this runs, the report would be lost silently.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n\n## Stale Benchmark Citations (>{STALE_DAYS} days old)\n\n")
            fh.write(
                f"> Detected {len(stale_rows)} row(s) in `benchmarks.md` with dates "
                f"older than {STALE_DAYS} days. Verify the cited source is still current "
                f"and update the Date field or move the row to "
                f"[§ Gaps]({REPO_BLOB}/benchmarks.md#9-gaps--not-publicly-measured).\n\n"
            )
            fh.write("| Line | Days Old | Row Preview |\n")
            fh.write("| :--- | :--- | :--- |\n")
            for line_no, days_old, preview in stale_rows:
                safe_preview = preview.replace("|", "\\|")
                fh.write(f"| {line_no} | {days_old} | `{safe_preview}` |\n")
        log.warning(
            "Freshness check: %d stale benchmark row(s) flagged in PROPOSED_UPDATES.md",
            len(stale_rows),
        )
    except OSError as exc:
        log.error("Could not write freshness report: %s", exc)


def check_listed_tool_freshness(repo_root: Path) -> None:
    """Audit GitHub repos already listed in README.md for staleness.

    Extracts all github.com/{owner}/{repo} URLs from README.md, queries the
    GitHub API for each repo, and appends warning tables to PROPOSED_UPDATES.md
    for repos that are archived upstream, or that have not been pushed to in the
    last STALE_TOOL_DAYS days (aligned with CONTRIBUTING's 6-month activity rule).

    Archived repos get their own table and are never folded into the push-age
    one. A project can archive right after shipping a release and so read as only
    mildly quiet — Vanna archived in 2026-02 and surfaced at 200 days, the
    mildest number in that week's report — which hides the strongest removal
    signal the Removal & Deprecation Policy recognises behind the weakest one.

    Skips the repo's own organisation link and the canonical awesome-list badge.
    Exits silently when README.md is absent or no stale tools are found.
    """
    STALE_TOOL_DAYS = 180  # 6 months — matches CONTRIBUTING Quality Standards

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    seen = _listed_repo_slugs(repo_root)
    if not seen:
        log.info("Tool freshness check: no external GitHub repos found in README.")
        return

    log.info("Tool freshness check: auditing %d listed repos …", len(seen))

    today = datetime.date.today()
    stale_threshold = today - datetime.timedelta(days=STALE_TOOL_DAYS)
    stale_tools: list[tuple[str, str, int]] = []  # (owner/repo, url, days_since_push)
    archived_tools: list[tuple[str, str, str]] = []  # (owner/repo, url, last_push)

    session = _build_session()
    # Sentinel: every request in the loop below may raise, leaving no response to
    # read the rate-limit header from. Without this the check raises NameError and
    # takes the whole weekly report down with it.
    response: requests.Response | None = None
    for owner, repo in sorted(seen):
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = session.get(api_url, headers=headers, timeout=15)
            if response.status_code == 404:
                # Repo deleted or renamed — flag it
                stale_tools.append(
                    (f"{owner}/{repo}", f"https://github.com/{owner}/{repo}", -1)
                )
                log.warning("Listed repo not found (404): %s/%s", owner, repo)
                continue
            response.raise_for_status()
            data: dict = response.json()
        except requests.RequestException as exc:
            log.warning("Tool freshness: skipping %s/%s (%s)", owner, repo, exc)
            continue

        pushed_raw: str = (data.get("pushed_at") or "")[:10]

        if data.get("archived"):
            archived_tools.append(
                (
                    f"{owner}/{repo}",
                    f"https://github.com/{owner}/{repo}",
                    pushed_raw or "unknown",
                )
            )
            log.warning("Archived listed tool: %s/%s", owner, repo)
            continue

        if not pushed_raw:
            continue
        try:
            pushed_date = datetime.date.fromisoformat(pushed_raw)
        except ValueError:
            continue

        if pushed_date < stale_threshold:
            days_old = (today - pushed_date).days
            stale_tools.append(
                (f"{owner}/{repo}", f"https://github.com/{owner}/{repo}", days_old)
            )
            log.info(
                "Stale listed tool: %s/%s (%d days since last push)",
                owner,
                repo,
                days_old,
            )

    remaining = (
        response.headers.get("X-RateLimit-Remaining", "?")
        if response is not None
        else "?"
    )
    log.info("GitHub API rate limit remaining after tool audit: %s", remaining)

    if not stale_tools and not archived_tools:
        log.info("Tool freshness check: all listed repos are current.")
        return

    output_path = repo_root / ".github" / "PROPOSED_UPDATES.md"
    # The two sibling audits already do this; this one did not, so its report was
    # lost whenever it ran before anything had created .github/.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if archived_tools:
            with output_path.open("a", encoding="utf-8") as fh:
                fh.write("\n\n## Archived Listed Tools\n\n")
                fh.write(
                    f"> Detected {len(archived_tools)} repo(s) in `README.md` that are "
                    f"archived on GitHub. Archival is an explicit end-of-life signal, so "
                    f"these need a decision regardless of how recently they were pushed "
                    f"to — see the [Removal & Deprecation Policy]"
                    f"({REPO_BLOB}/CONTRIBUTING.md#removal--deprecation-policy).\n\n"
                )
                fh.write("| Repo | Last Push | URL |\n")
                fh.write("| :--- | :--- | :--- |\n")
                for slug, url, last_push in archived_tools:
                    fh.write(f"| {slug} | {last_push} | {url} |\n")
            log.warning(
                "Tool freshness: %d archived repo(s) flagged in PROPOSED_UPDATES.md",
                len(archived_tools),
            )

        if not stale_tools:
            return

        with output_path.open("a", encoding="utf-8") as fh:
            fh.write(
                f"\n\n## Stale Listed Tools (>{STALE_TOOL_DAYS} days since last push)\n\n"
            )
            fh.write(
                f"> Detected {len(stale_tools)} repo(s) in `README.md` that have not been "
                f"pushed to in over {STALE_TOOL_DAYS} days. Verify each is still maintained "
                f"per [CONTRIBUTING Quality Standards]({REPO_BLOB}/CONTRIBUTING.md#quality-standards). "
                f"Consider adding a `(deprecated — use X)` note or opening a removal PR.\n\n"
            )
            fh.write("| Repo | Days Since Last Push | URL |\n")
            fh.write("| :--- | :--- | :--- |\n")
            for slug, url, days in stale_tools:
                days_str = str(days) if days >= 0 else "**404 — not found**"
                fh.write(f"| {slug} | {days_str} | {url} |\n")
        log.warning(
            "Tool freshness: %d stale/missing repo(s) flagged in PROPOSED_UPDATES.md",
            len(stale_tools),
        )
    except OSError as exc:
        log.error("Could not write tool freshness report: %s", exc)


def check_entry_verification_age(
    repo_root: Path, today: datetime.date | None = None
) -> None:
    """Audit per-entry `<!-- verified: YYYY-MM-DD -->` markers in README.md.

    This is the human-review counterpart to ``check_listed_tool_freshness``:
    ``pushed_at`` proves a repo is *active*, while a verified date proves a
    maintainer last confirmed the entry is still accurate and in scope. Each
    catalog entry (a top-level ``- [Name](URL)`` bullet with an indented
    description) may carry one verified marker on the line in between.

    Appends a report to PROPOSED_UPDATES.md **only when at least one marker is
    stale** — a table of entries older than VERIFIED_STALE_DAYS, plus a one-line
    coverage summary for context.

    Missing markers are never a finding on their own. The convention is
    forward-looking (CONTRIBUTING § 5): new and substantially edited entries must
    carry a marker, but the historical backlog is deliberately grandfathered.
    Reporting it weekly produced a number that never moved and drowned out the
    findings that do need action.

    Offline by design — reads only README.md. Malformed dates are skipped
    silently. ``today`` is injectable for deterministic tests.
    """
    VERIFIED_STALE_DAYS = 180  # 6 months — matches check_listed_tool_freshness

    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        return
    try:
        lines = readme_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        log.warning("Entry verification check skipped: %s", exc)
        return

    today = today or datetime.date.today()
    stale_threshold = today - datetime.timedelta(days=VERIFIED_STALE_DAYS)
    stale_entries: list[tuple[int, str, int]] = []  # (line_no, name, days_old)
    total_entries = 0
    missing = 0

    for index, line in enumerate(lines):
        anchor = _ENTRY_ANCHOR_RE.match(line)
        if not anchor:
            continue

        # Walk forward to the entry's description sub-bullet, capturing any
        # verified marker that appears in between. A bare link bullet with no
        # description is not a catalog entry and is not counted.
        found_date: str | None = None
        is_entry = False
        cursor = index + 1
        while cursor < len(lines):
            nxt = lines[cursor]
            if found_date is None:
                marker = _VERIFIED_RE.search(nxt)
                if marker:
                    found_date = marker.group(1)
                    cursor += 1
                    continue
            if _ENTRY_DESC_RE.match(nxt):
                is_entry = True
                break
            if _ENTRY_ANCHOR_RE.match(nxt) or nxt.strip() == "":
                break
            cursor += 1

        if not is_entry:
            continue

        total_entries += 1
        if found_date is None:
            missing += 1
            continue
        try:
            verified_date = datetime.date.fromisoformat(found_date)
        except ValueError:
            # Malformed date — skip silently rather than flag a false positive.
            continue
        if verified_date < stale_threshold:
            days_old = (today - verified_date).days
            stale_entries.append((index + 1, anchor.group("name"), days_old))

    if not stale_entries:
        log.info(
            "Entry verification: %d/%d entries carry a review date, none stale.",
            total_entries - missing,
            total_entries,
        )
        return

    output_path = repo_root / ".github" / "PROPOSED_UPDATES.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("a", encoding="utf-8") as fh:
            fh.write("\n\n## Entry Verification Audit\n\n")
            verified_count = total_entries - missing
            fh.write(
                f"> Per-entry `<!-- verified: YYYY-MM-DD -->` coverage: "
                f"{verified_count}/{total_entries} entries carry a review date "
                f"({missing} missing). See "
                f"[CONTRIBUTING § Last Verified Date]({REPO_BLOB}/CONTRIBUTING.md#5-last-verified-date-per-entry-review).\n\n"
            )
            fh.write(
                f"> {len(stale_entries)} entr(y/ies) reviewed more than "
                f"{VERIFIED_STALE_DAYS} days ago — re-verify the link, description, "
                f"and production relevance, then bump the date.\n\n"
            )
            fh.write("| Line | Entry | Days Since Review |\n")
            fh.write("| :--- | :--- | :--- |\n")
            for line_no, name, days_old in stale_entries:
                safe_name = name.replace("|", "\\|")
                fh.write(f"| {line_no} | {safe_name} | {days_old} |\n")
        log.warning(
            "Entry verification: %d stale entr(y/ies) flagged.", len(stale_entries)
        )
    except OSError as exc:
        log.error("Could not write entry verification report: %s", exc)


def run_discovery() -> None:
    """Fetch trending RAG repositories from GitHub and write a discovery report.

    Filters:
    - topic:rag
    - Stars >= 100 (quality threshold)
    - Pushed within the last 90 days (freshness threshold)
    """
    MIN_STARS = 100
    DAYS_LIMIT = 90
    PER_PAGE = 50  # fetch a wider pool so new candidates survive filtering
    DISPLAY_LIMIT = 15  # show at most this many new candidates

    github_token: str | None = os.getenv("GITHUB_TOKEN")

    cutoff_date = (
        datetime.datetime.now() - datetime.timedelta(days=DAYS_LIMIT)
    ).strftime("%Y-%m-%d")

    query = f"topic:rag stars:>={MIN_STARS} pushed:>={cutoff_date}"
    url = "https://api.github.com/search/repositories"
    params: dict[str, str | int] = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
    }

    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    else:
        log.warning(
            "GITHUB_TOKEN not set — unauthenticated requests have low rate limits."
        )

    log.info(
        "Starting discovery (stars >= %d, updated after %s)", MIN_STARS, cutoff_date
    )

    output_path = REPO_ROOT / ".github" / "PROPOSED_UPDATES.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session = _build_session()
    try:
        response = session.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data: dict = response.json()
    except requests.RequestException as exc:
        log.error("Discovery request failed: %s", exc)
        output_path.write_text(
            f"# RAG Discovery — {datetime.date.today()}\n\n> Discovery failed this run: {exc}\n",
            encoding="utf-8",
        )
        return

    remaining = response.headers.get("X-RateLimit-Remaining", "?")
    log.info("GitHub API rate limit remaining: %s", remaining)

    projects = data.get("items", [])

    # Drop repos already in the list or on the out-of-scope denylist so the feed
    # surfaces only genuinely new candidates worth triaging.
    listed = {
        f"{owner}/{repo}".lower() for owner, repo in _listed_repo_slugs(REPO_ROOT)
    }
    unresolved = [slug for slug, rid in OUT_OF_SCOPE_REPOS.items() if rid is None]
    if unresolved:
        log.warning(
            "Denylist entries without a repo id (slug-only, no rename protection): %s",
            ", ".join(sorted(unresolved)),
        )

    new_projects, listed_hits, denied_hits = filter_candidates(projects, listed)
    log.info(
        "Discovery: %d fetched, %d new after filtering (%d already listed, %d out of scope)",
        len(projects),
        len(new_projects),
        listed_hits,
        denied_hits,
    )
    candidates = new_projects[:DISPLAY_LIMIT]

    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# RAG Discovery — {datetime.date.today()}\n\n")
        fh.write(
            f"> **Filters:** Stars >= {MIN_STARS}, pushed in the last {DAYS_LIMIT} days, "
            f"excluding repos already listed and known out-of-scope apps.\n\n"
        )
        fh.write(
            "> **Triage note:** New candidate repos surfaced by automated discovery — "
            "already-listed repos and known end-user apps are pre-filtered out. Still "
            "verify each against\n"
            f"> [CONTRIBUTING Quality Standards]({REPO_BLOB}/CONTRIBUTING.md#quality-standards) "
            "and the Evidence Tier policy before adding.\n\n"
        )

        if not candidates:
            fh.write(
                "_No new candidates this week — all surfaced repos are already listed "
                "or out of scope._\n"
            )
            log.info("Discovery: no new candidates after filtering.")
        else:
            fh.write("| Project | Stars | Description | Last Push |\n")
            fh.write("| :--- | :--- | :--- | :--- |\n")

            for project in candidates:
                name: str = project.get("full_name") or project.get("name", "unknown")
                html_url: str = project.get("html_url", "")
                description: str = (
                    (project.get("description") or "No description provided.")
                    .replace("|", "-")
                    .replace("\n", " ")
                )
                stars: int = project.get("stargazers_count", 0)
                pushed_at: str = (project.get("pushed_at") or "")[:10]

                if len(description) > 100:
                    description = description[:97] + "..."

                fh.write(
                    f"| [{name}]({html_url}) | {stars} | {description} | {pushed_at} |\n"
                )
                log.info("Candidate: %s (%d stars, pushed %s)", name, stars, pushed_at)

    log.info(
        "Discovery complete — %d candidate(s) written to %s",
        len(candidates),
        output_path,
    )
    check_benchmark_freshness(REPO_ROOT)
    check_listed_tool_freshness(REPO_ROOT)
    check_entry_verification_age(REPO_ROOT)


if __name__ == "__main__":
    run_discovery()
