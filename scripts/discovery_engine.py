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

# Self-refs and well-known non-tool links to ignore when scanning README.
_SKIP_OWNERS = {"Yigtwxx", "sindresorhus", "github", "actions"}
_SKIP_REPOS = {"awesome", "awesome-list", ".github"}

# Known end-user apps / low-code platforms repeatedly surfaced by topic:rag but
# out of scope for this infrastructure list (see FAQ § Scope). Matched on
# lowercased owner/repo. Extend as new noise appears.
OUT_OF_SCOPE_REPOS = {
    "langgenius/dify",
    "open-webui/open-webui",
    "flowiseai/flowise",
    "mintplex-labs/anything-llm",
    "shubhamsaboo/awesome-llm-apps",
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


if __name__ == "__main__":
    run_discovery()
