"""Turn lychee's JSON output into a tracking-issue body.

The weekly link check finds broken links but had nowhere to put them: the
workflow runs with `fail: false` and wrote only to a job summary nobody opens,
so confirmed 404s sat in the catalog for months. This script renders the
findings as markdown for a long-lived `broken-links` issue, and fingerprints
them so an unchanged set updates the issue body instead of posting a duplicate
comment every Monday.

Usage:
    python scripts/link_report.py --input lychee/out.json --run-url URL
    python scripts/link_report.py --input out.json --run-url URL --today 2026-08-01

Writes the issue body to stdout. Always exits 0 — this is a report, not a gate.
"""

import argparse
import datetime
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

FINGERPRINT_PREFIX = "broken-links-fingerprint:"

# lychee renamed this key; accept both so an upgrade doesn't silently blank the
# report. Order matters only for which one wins if a payload carries both.
ERROR_MAP_KEYS = ("error_map", "fail_map")


@dataclass(frozen=True)
class BrokenLink:
    """One broken URL and every file that references it."""

    url: str
    status: str
    sources: list[str]


def _coerce_status(raw: object) -> str:
    """Render lychee's status: a string in some versions, an object in others."""
    if isinstance(raw, str):
        return raw.strip() or "unknown"
    if isinstance(raw, Mapping):
        text = raw.get("text") or raw.get("message") or ""
        code = raw.get("code")
        if code and text:
            return f"{code} {text}"
        if code:
            return str(code)
        if text:
            return str(text)
    return "unknown"


def _entry_url(entry: object) -> str | None:
    if isinstance(entry, Mapping):
        url = entry.get("url") or entry.get("uri")
        return str(url) if url else None
    if isinstance(entry, str):
        return entry
    return None


def parse_lychee_json(payload: Mapping[str, object]) -> list[BrokenLink]:
    """Invert lychee's {source: [error, ...]} map into url -> sources.

    Returns [] when no recognised error map is present, so a schema change
    degrades to "no findings" rather than crashing the weekly job. A silent
    empty report is recoverable; a crashed workflow step is the failure mode
    this whole script exists to fix.
    """
    error_map: object = None
    for key in ERROR_MAP_KEYS:
        candidate = payload.get(key)
        if isinstance(candidate, Mapping):
            error_map = candidate
            break
    if not isinstance(error_map, Mapping):
        return []

    by_url: dict[str, dict[str, object]] = {}
    for source, entries in error_map.items():
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
            continue
        for entry in entries:
            url = _entry_url(entry)
            if not url:
                continue
            status = (
                _coerce_status(entry.get("status"))
                if isinstance(entry, Mapping)
                else "unknown"
            )
            record = by_url.setdefault(url, {"status": status, "sources": set()})
            sources = record["sources"]
            assert isinstance(sources, set)
            sources.add(str(source))

    links = [
        BrokenLink(
            url=url,
            status=str(record["status"]),
            sources=sorted(s for s in record["sources"]),  # type: ignore[union-attr]
        )
        for url, record in by_url.items()
    ]
    return sorted(links, key=lambda link: link.url)


def fingerprint(links: Sequence[BrokenLink]) -> str:
    """Stable hash over the URL set alone.

    Statuses are deliberately excluded: a host that flaps between 404, 429, and
    a timeout must not read as a changed finding, or the issue comments every
    week for the same rot.
    """
    digest = hashlib.sha256()
    for url in sorted({link.url for link in links}):
        digest.update(url.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()[:16]


def render_issue_body(
    links: Sequence[BrokenLink], run_url: str, checked_at: datetime.date
) -> str:
    """Markdown body for the tracking issue, ending with the fingerprint marker."""
    lines: list[str] = []
    if not links:
        lines.append(f"## No broken links as of {checked_at.isoformat()}")
        lines.append("")
        lines.append("Every catalog link resolved on the latest run.")
    else:
        lines.append(
            f"## Broken links — {len(links)} URL(s) as of {checked_at.isoformat()}"
        )
        lines.append("")
        lines.append("| URL | Status | Referenced in |")
        lines.append("| :--- | :--- | :--- |")
        for link in links:
            sources = ", ".join(f"`{s}`" for s in link.sources) or "—"
            lines.append(f"| {link.url} | {link.status} | {sources} |")
        lines.append("")
        lines.append(
            "Fix or replace each link, or add the domain to the `exclude` list in "
            "`lychee.toml` when it is a bot wall rather than real rot."
        )
    lines.append("")
    lines.append(f"[Full run log]({run_url})")
    lines.append("")
    lines.append(f"<!-- {FINGERPRINT_PREFIX} {fingerprint(links)} -->")
    return "\n".join(lines) + "\n"


def extract_fingerprint(body: str) -> str | None:
    """Read the fingerprint marker back out of an existing issue body."""
    marker = f"<!-- {FINGERPRINT_PREFIX} "
    start = body.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = body.find("-->", start)
    if end == -1:
        return None
    return body[start:end].strip() or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="lychee JSON output")
    parser.add_argument("--run-url", required=True, help="workflow run URL")
    parser.add_argument("--today", type=datetime.date.fromisoformat, default=None)
    args = parser.parse_args(argv)

    today = args.today or datetime.date.today()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # Never fail the weekly job over a malformed report.
        print(f"## Link report unavailable\n\nCould not read lychee output: {exc}\n")
        return 0

    links = parse_lychee_json(payload) if isinstance(payload, Mapping) else []
    print(render_issue_body(links, args.run_url, today), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
