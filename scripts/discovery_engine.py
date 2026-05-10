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
                f"[§ Gaps](../benchmarks.md#9-gaps--not-publicly-measured).\n\n"
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


def run_discovery() -> None:
    """Fetch trending RAG repositories from GitHub and write a discovery report.

    Filters:
    - topic:rag
    - Stars >= 100 (quality threshold)
    - Pushed within the last 90 days (freshness threshold)
    """
    MIN_STARS = 100
    DAYS_LIMIT = 90
    PER_PAGE = 15

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

    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# RAG Discovery — {datetime.date.today()}\n\n")
        fh.write(
            f"> **Filters:** Stars >= {MIN_STARS}, updated in the last {DAYS_LIMIT} days.\n\n"
        )
        fh.write("| Project | Stars | Description | Last Update |\n")
        fh.write("| :--- | :--- | :--- | :--- |\n")

        for project in projects:
            name: str = project.get("name", "unknown")
            html_url: str = project.get("html_url", "")
            description: str = (project.get("description") or "No description provided.").replace("|", "-").replace("\n", " ")
            stars: int = project.get("stargazers_count", 0)
            updated_at: str = (project.get("updated_at") or "")[:10]

            if len(description) > 100:
                description = description[:97] + "..."

            fh.write(f"| [{name}]({html_url}) | {stars} | {description} | {updated_at} |\n")
            log.info("Found: %s (%d stars, updated %s)", name, stars, updated_at)

    log.info("Discovery complete — %d projects written to %s", len(projects), output_path)
    check_benchmark_freshness(REPO_ROOT)


if __name__ == "__main__":
    run_discovery()
