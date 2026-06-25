"""Weekly RAG discovery engine.

Fetches trending RAG repositories from the GitHub Search API and checks
benchmarks.md for stale citations. Results are written to
.github/PROPOSED_UPDATES.md (gitignored) for the CI workflow to post as a
GitHub issue comment.
"""

import datetime
import logging
import os
import re
from pathlib import Path

import requests
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

# Matches github.com/{owner}/{repo} links; trailing delimiters end the repo group.
_REPO_URL_RE = re.compile(r"github\.com/([\w.\-]+)/([\w.\-]+?)(?:[/?#\s\)\]\"']|$)")

# Per-entry conventions (see CONTRIBUTING.md § Last Verified Date). A catalog
# entry is a top-level link bullet `- [Name](URL)` followed by an indented
# description sub-bullet; an optional `<!-- verified: YYYY-MM-DD -->` line in
# between records the last human review.
_ENTRY_ANCHOR_RE = re.compile(r"^- \[(?P<name>[^\]]+)\]\([^)]+\)\s*$")
_ENTRY_DESC_RE = re.compile(r"^\s+- \S")
_VERIFIED_RE = re.compile(r"<!--\s*verified:\s*(\d{4}-\d{2}-\d{2})\s*-->")

# Self-refs and well-known non-tool links to ignore when scanning README.
_SKIP_OWNERS = {"Yigtwxx", "sindresorhus", "github", "actions"}
_SKIP_REPOS = {"awesome", "awesome-list", ".github"}

# Repos repeatedly surfaced by topic:rag but out of scope for this infrastructure
# list. Seeded from documented "out-of-scope" triage verdicts (see the triage
# record in .github/PROPOSED_UPDATES.md / FAQ § Scope). Matched on lowercased
# owner/repo. Extend as new noise appears. Note: already-listed repos do NOT
# belong here — README dedup handles those automatically.
OUT_OF_SCOPE_REPOS = {
    # End-user apps / low-code platforms.
    "langgenius/dify",
    "open-webui/open-webui",
    "flowiseai/flowise",
    "mintplex-labs/anything-llm",
    "jeecgboot/jeecgboot",
    # Meta-lists, tutorials, educational guides (no production-infra focus).
    "shubhamsaboo/awesome-llm-apps",
    "dair-ai/prompt-engineering-guide",
    "datawhalechina/hello-agents",
    # Coding-assistant / session-memory plugins (not RAG infra).
    "safishamsi/graphify",
    "thedotmack/claude-mem",
}


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


def check_benchmark_freshness(repo_root: Path) -> None:
    """Parse benchmarks.md for rows with YYYY-MM-DD dates older than STALE_DAYS.

    Appends a warning section to PROPOSED_UPDATES.md when stale rows are found.
    Exits silently when benchmarks.md is absent or no stale rows exist.
    """
    STALE_DAYS = 365
    benchmarks_path = repo_root / "benchmarks.md"
    if not benchmarks_path.exists():
        return

    today = datetime.date.today()
    stale_threshold = today - datetime.timedelta(days=STALE_DAYS)
    stale_rows: list[tuple[int, int, str]] = []

    date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

    try:
        for line_no, line in enumerate(benchmarks_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|"):
                continue
            match = date_pattern.search(line)
            if not match:
                continue
            try:
                row_date = datetime.date.fromisoformat(match.group(1))
            except ValueError:
                continue
            if row_date < stale_threshold:
                days_old = (today - row_date).days
                stale_rows.append((line_no, days_old, line.strip()[:120]))
    except OSError as exc:
        log.warning("Benchmark freshness check skipped: %s", exc)
        return

    if not stale_rows:
        log.info("Freshness check: all benchmark rows are current.")
        return

    output_path = repo_root / ".github" / "PROPOSED_UPDATES.md"
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
    GitHub API for each repo's last push date, and appends a warning table to
    PROPOSED_UPDATES.md for any repo that hasn't been pushed to in the last
    STALE_TOOL_DAYS days (aligned with CONTRIBUTING's 6-month activity rule).

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

    session = _build_session()
    for owner, repo in sorted(seen):
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = session.get(api_url, headers=headers, timeout=15)
            if response.status_code == 404:
                # Repo deleted or renamed — flag it
                stale_tools.append((f"{owner}/{repo}", f"https://github.com/{owner}/{repo}", -1))
                log.warning("Listed repo not found (404): %s/%s", owner, repo)
                continue
            response.raise_for_status()
            data: dict = response.json()
        except requests.RequestException as exc:
            log.warning("Tool freshness: skipping %s/%s (%s)", owner, repo, exc)
            continue

        pushed_raw: str = (data.get("pushed_at") or "")[:10]
        if not pushed_raw:
            continue
        try:
            pushed_date = datetime.date.fromisoformat(pushed_raw)
        except ValueError:
            continue

        if pushed_date < stale_threshold:
            days_old = (today - pushed_date).days
            stale_tools.append((f"{owner}/{repo}", f"https://github.com/{owner}/{repo}", days_old))
            log.info("Stale listed tool: %s/%s (%d days since last push)", owner, repo, days_old)

    remaining = response.headers.get("X-RateLimit-Remaining", "?") if seen else "?"  # type: ignore[possibly-undefined]
    log.info("GitHub API rate limit remaining after tool audit: %s", remaining)

    if not stale_tools:
        log.info("Tool freshness check: all listed repos are current.")
        return

    output_path = repo_root / ".github" / "PROPOSED_UPDATES.md"
    try:
        with output_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n\n## Stale Listed Tools (>{STALE_TOOL_DAYS} days since last push)\n\n")
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

    Appends two things to PROPOSED_UPDATES.md when relevant:
    - a detailed table of entries whose marker is older than VERIFIED_STALE_DAYS;
    - a one-line coverage summary counting entries that lack a marker (kept as a
      count, not a list, because the convention is rolled out incrementally).

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

    if not stale_entries and not missing:
        log.info("Entry verification check: %d entries, all current.", total_entries)
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
            if stale_entries:
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
            "Entry verification: %d stale, %d missing (of %d entries) flagged.",
            len(stale_entries),
            missing,
            total_entries,
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
    PER_PAGE = 50       # fetch a wider pool so new candidates survive filtering
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
        log.warning("GITHUB_TOKEN not set — unauthenticated requests have low rate limits.")

    log.info("Starting discovery (stars >= %d, updated after %s)", MIN_STARS, cutoff_date)

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
    listed = {f"{owner}/{repo}".lower() for owner, repo in _listed_repo_slugs(REPO_ROOT)}
    skip = listed | OUT_OF_SCOPE_REPOS
    new_projects = [
        p for p in projects if (p.get("full_name") or "").lower() not in skip
    ]
    log.info(
        "Discovery: %d fetched, %d new after filtering (%d already-listed/out-of-scope removed)",
        len(projects), len(new_projects), len(projects) - len(new_projects),
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
                description: str = (project.get("description") or "No description provided.").replace("|", "-").replace("\n", " ")
                stars: int = project.get("stargazers_count", 0)
                pushed_at: str = (project.get("pushed_at") or "")[:10]

                if len(description) > 100:
                    description = description[:97] + "..."

                fh.write(f"| [{name}]({html_url}) | {stars} | {description} | {pushed_at} |\n")
                log.info("Candidate: %s (%d stars, pushed %s)", name, stars, pushed_at)

    log.info("Discovery complete — %d candidate(s) written to %s", len(candidates), output_path)
    check_benchmark_freshness(REPO_ROOT)
    check_listed_tool_freshness(REPO_ROOT)
    check_entry_verification_age(REPO_ROOT)


if __name__ == "__main__":
    run_discovery()
