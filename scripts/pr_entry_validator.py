"""PR entry validator — CI gate for catalog content changes.

Validates changed markdown content files against the entry conventions in
CONTRIBUTING.md (two-line format, alphabetical order, duplicates, verified
markers, style bans, evidence tags) plus the PR-body policy. Each check runs
as a separate CI matrix job via ``--check``.

Stdlib-only by design: CI jobs and contributors need no pip install.

Usage:
    python scripts/pr_entry_validator.py --check CHECK_ID [FILES ...]
           [--repo-root PATH] [--base-ref REF] [--pr-body-file PATH]
           [--today YYYY-MM-DD]

Exit codes: 0 clean, 1 findings, 2 usage error.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from entry_patterns import ENTRY_ANCHOR_RE, VERIFIED_RE

CHECK_IDS = (
    "format",
    "alphabetical",
    "duplicates",
    "verified-markers",
    "style-bans",
    "evidence-tags",
    "pr-body",
)

# Root-level markdown files that are governance/meta, not catalog content.
NON_CONTENT = {
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "SECURITY.md",
}

# Escape hatches (HTML comments placed in the content itself).
NO_ALPHABETICAL_RE = re.compile(r"<!--\s*no-alphabetical\s*-->")
ALLOW_DUPLICATE_RE = re.compile(r"<!--\s*allow-duplicate\s*-->")

# A top-level external-link bullet with whatever trails the link. TOC and
# relative-path links are not entries. `rest` is empty for a strict anchor.
LINK_BULLET_RE = re.compile(r"^- \[[^\]]+\]\(https?://[^)]+\)(?P<rest>.*)$")

# Allowed trailing text on a link bullet: a dash-separated attribution or
# cross-reference (`- [Name](URL) - Author.`), the established hybrid style
# of blogs.md/datasets.md. Anything else after the link is malformed.
ATTRIBUTION_RE = re.compile(r"^\s+[-–—]\s+\S")

# Anything that looks like a verified marker attempt, for loud malformed-date
# failures (discovery_engine deliberately skips these silently).
VERIFIED_ATTEMPT_RE = re.compile(r"<!--\s*verified\b", re.IGNORECASE)

# Style bans (CONTRIBUTING.md § Formatting): no emoji, no bold inline labels
# in list items. Emoji ranges cover pictographs, dingbats, stars, and the
# variation selector; plain arrows/typography are allowed.
EMOJI_RE = re.compile("[\U0001f000-\U0001faff☀-➿⬀-⯿️]")
BOLD_LABEL_RE = re.compile(r"\*\*[^*\n]{1,40}:\*\*")

# Evidence tags (CONTRIBUTING.md § Evidence Tier). README escapes brackets
# (\[3P\]), topic files may not — accept both.
EVIDENCE_TAG_RE = re.compile(r"\\?\[(?:3P|V|A)\\?\]")
UNIT_CLAIM_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:%|ms\b|qps\b|rps\b|tok(?:ens)?/s|gb\b|mb\b)",
    re.IGNORECASE,
)
METRIC_WORD_RE = re.compile(
    r"\b(?:latency|recall|precision|throughput|cost reduction"
    r"|hallucination(?:\s+rate)?|accuracy|p9[59])\b[^.\n]{0,40}\d",
    re.IGNORECASE,
)

# PR-body policy: template checkbox / Engineering Context field shapes.
UNTICKED_BOX_RE = re.compile(r"^\s*- \[ \]", re.MULTILINE)
SOURCE_URL_FILLED_RE = re.compile(r"\*\*Source URL:\*\*\s*\S*https?://")
DATE_FILLED_RE = re.compile(r"\*\*Date[^*]*\*\*\s*`?\d{4}-\d{2}-\d{2}")
TAG_LINE_RE = re.compile(r"^.*\*\*Tag:\*\*.*$", re.MULTILINE)
# The untouched template legend lists all three tags with their glosses.
TAG_LEGEND_MARKERS = ("third-party", "vendor-stated", "anecdotal")


@dataclass(frozen=True)
class Entry:
    """One catalog entry: anchor bullet plus its marker/description lines."""

    file: Path
    line_no: int  # 1-indexed anchor line
    name: str
    url: str
    verified: str | None
    verified_line: int | None
    desc_line: int | None  # None = missing description


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    check: str
    message: str


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _fence_mask(lines: Sequence[str]) -> list[bool]:
    """True for lines inside (or delimiting) fenced code blocks."""
    mask: list[bool] = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        is_delim = stripped.startswith("```") or stripped.startswith("~~~")
        if is_delim:
            mask.append(True)
            in_fence = not in_fence
        else:
            mask.append(in_fence)
    return mask


def parse_entries(path: Path) -> list[Entry]:
    """Extract catalog entries, skipping fenced code blocks."""
    lines = _read_lines(path)
    fenced = _fence_mask(lines)
    entries: list[Entry] = []
    for i, line in enumerate(lines):
        if fenced[i]:
            continue
        anchor = ENTRY_ANCHOR_RE.match(line)
        if not anchor:
            continue
        # Catalog entries always link externally; `#anchor` TOC links and
        # relative-path links are not entries.
        if not anchor.group("url").startswith(("http://", "https://")):
            continue
        verified: str | None = None
        verified_line: int | None = None
        desc_line: int | None = None
        j = i + 1
        if j < len(lines):
            marker = VERIFIED_RE.search(lines[j])
            if marker:
                verified = marker.group(1)
                verified_line = j + 1
                j += 1
        if j < len(lines) and lines[j].lstrip().startswith("- "):
            if lines[j].startswith((" ", "\t")):
                desc_line = j + 1
        entries.append(
            Entry(
                file=path,
                line_no=i + 1,
                name=anchor.group("name"),
                url=anchor.group("url"),
                verified=verified,
                verified_line=verified_line,
                desc_line=desc_line,
            )
        )
    return entries


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _desc_block_end(lines: Sequence[str], desc_line: int) -> int:
    """0-based index of the last line of an entry's description block.

    The block spans the description bullet plus following indented lines —
    wrapped continuations and sibling sub-bullets (e.g. showcase's
    ``*Venue:*`` / ``*Why watch:*`` structure) — until a blank or
    unindented line.
    """
    last = desc_line - 1
    while (
        last + 1 < len(lines)
        and lines[last + 1].startswith("  ")
        and lines[last + 1].strip()
    ):
        last += 1
    return last


def _ends_with_terminal_punctuation(text: str) -> bool:
    stripped = text.rstrip().rstrip("\"'*)_`")
    return stripped.endswith((".", "?", "!"))


def check_format(files: Sequence[Path], repo_root: Path) -> list[Finding]:
    """Two-line entry format (CONTRIBUTING.md § Formatting)."""
    findings: list[Finding] = []
    for path in files:
        rel = _rel(path, repo_root)
        lines = _read_lines(path)
        fenced = _fence_mask(lines)
        for i, line in enumerate(lines):
            bullet = None if fenced[i] else LINK_BULLET_RE.match(line)
            if bullet is None or not bullet.group("rest").strip():
                continue  # not a link bullet, or a strict two-line anchor
            if not ATTRIBUTION_RE.match(bullet.group("rest")):
                # Junk after the link (emoji, labels, ...) also makes the
                # line invisible to the entry-based checks — reject it here.
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "format",
                        "malformed entry line: only a dash-separated "
                        "attribution may follow the link "
                        "(`- [Name](URL) - Author.`)",
                    )
                )
                continue
            # A trailing attribution is fine as long as the indented
            # description bullet follows; a true one-liner is not.
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if not (next_line.startswith("  ") and next_line.strip()):
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "format",
                        "one-line entry style; use the two-line format: "
                        "`- [Name](URL)` then an indented description bullet",
                    )
                )
        entries = parse_entries(path)
        # Contiguous runs of entries: a bare-link run where NO entry carries a
        # description is a reference list (e.g. "Further Reading"), not
        # catalog content — those are exempt from the description rule.
        runs: list[list[Entry]] = []
        prev_end = -2
        for entry in entries:
            end = entry.line_no - 1
            if entry.desc_line is not None:
                end = _desc_block_end(lines, entry.desc_line)
            elif entry.verified_line is not None:
                end = entry.verified_line - 1
            # Same run when at most one blank line separates entries.
            if entry.line_no - 1 - prev_end > 2 or not runs:
                runs.append([])
            runs[-1].append(entry)
            prev_end = end
        described_runs = {
            id(e)
            for run in runs
            if any(x.desc_line is not None for x in run)
            for e in run
        }
        for entry in entries:
            if entry.verified_line is not None:
                marker_raw = lines[entry.verified_line - 1]
                if not marker_raw.startswith("  <!--"):
                    findings.append(
                        Finding(
                            rel,
                            entry.verified_line,
                            "format",
                            "verified marker must be indented exactly 2 spaces "
                            "directly under the entry link",
                        )
                    )
            if entry.desc_line is None:
                if id(entry) in described_runs:
                    findings.append(
                        Finding(
                            rel,
                            entry.line_no,
                            "format",
                            f"entry '{entry.name}' is missing its indented "
                            "description bullet",
                        )
                    )
                continue
            desc_raw = lines[entry.desc_line - 1]
            if not desc_raw.startswith("  - ") or desc_raw.startswith("   "):
                findings.append(
                    Finding(
                        rel,
                        entry.desc_line,
                        "format",
                        "description bullet must be indented exactly 2 spaces",
                    )
                )
            # Descriptions may wrap or use structured sub-bullets; the
            # punctuation requirement applies to the block's last line.
            last = _desc_block_end(lines, entry.desc_line)
            if not _ends_with_terminal_punctuation(lines[last]):
                findings.append(
                    Finding(
                        rel,
                        last + 1,
                        "format",
                        "description must end with terminal punctuation "
                        "(usually a period)",
                    )
                )
    return findings


def check_alphabetical(files: Sequence[Path], repo_root: Path) -> list[Finding]:
    """Entries must be alphabetical within each section (contiguous runs)."""
    findings: list[Finding] = []
    for path in files:
        rel = _rel(path, repo_root)
        lines = _read_lines(path)
        fenced = _fence_mask(lines)
        section_exempt = False
        prev: tuple[str, int] | None = None  # (casefolded name, line_no)
        for i, line in enumerate(lines):
            if fenced[i]:
                continue
            if line.startswith("#"):
                section_exempt = False
                prev = None
                continue
            if NO_ALPHABETICAL_RE.search(line):
                section_exempt = True
                continue
            anchor = ENTRY_ANCHOR_RE.match(line)
            if anchor and not anchor.group("url").startswith(("http://", "https://")):
                anchor = None  # TOC / relative links are not catalog entries
            if anchor:
                name = anchor.group("name").casefold()
                if not section_exempt and prev and name < prev[0]:
                    findings.append(
                        Finding(
                            rel,
                            i + 1,
                            "alphabetical",
                            f"'{anchor.group('name')}' (line {i + 1}) sorts "
                            f"before the entry on line {prev[1]}; keep entries "
                            "alphabetical within the section",
                        )
                    )
                prev = (name, i + 1)
                continue
            # Entry sub-lines (indented) and blanks keep the run alive;
            # any other content (prose, tables, sub-headings) resets it.
            if line.strip() and not line.startswith((" ", "\t")):
                prev = None
    return findings


def _normalize_url(url: str) -> str:
    url = url.strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    url = url.split("#", 1)[0]
    return url.rstrip("/")


def check_duplicates(changed: Sequence[Path], repo_root: Path) -> list[Finding]:
    """Duplicate names/URLs repo-wide, blamed only on changed files."""
    changed_rel = {_rel(p, repo_root) for p in changed}
    all_files = sorted(
        p
        for p in repo_root.glob("*.md")
        if p.name not in NON_CONTENT and p.name.lower() != "readme.md"
    )
    readme = repo_root / "README.md"
    if readme.exists():
        all_files.insert(0, readme)

    by_url: dict[str, list[tuple[str, int, str]]] = {}
    by_name: dict[str, list[tuple[str, int, str]]] = {}
    for path in all_files:
        lines = _read_lines(path)
        rel = _rel(path, repo_root)
        for entry in parse_entries(path):
            # `<!-- allow-duplicate -->` on the line above the anchor exempts
            # this occurrence (legitimate README <-> topic-guide overlap).
            above = lines[entry.line_no - 2] if entry.line_no >= 2 else ""
            if ALLOW_DUPLICATE_RE.search(above):
                continue
            occ = (rel, entry.line_no, entry.name)
            by_url.setdefault(_normalize_url(entry.url), []).append(occ)
            by_name.setdefault(entry.name.casefold(), []).append(occ)

    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()
    for kind, index in (("URL", by_url), ("name", by_name)):
        for occurrences in index.values():
            if len(occurrences) < 2:
                continue
            for rel, line_no, name in occurrences:
                if rel not in changed_rel or (rel, line_no) in seen:
                    continue
                others = ", ".join(
                    f"{r}:{ln}" for r, ln, _ in occurrences if (r, ln) != (rel, line_no)
                )
                seen.add((rel, line_no))
                findings.append(
                    Finding(
                        rel,
                        line_no,
                        "duplicates",
                        f"'{name}' duplicates the same {kind} as {others} "
                        "(add `<!-- allow-duplicate -->` on the line above "
                        "if intentional)",
                    )
                )
    return findings


def check_verified_markers(
    files: Sequence[Path], repo_root: Path, today: datetime.date
) -> list[Finding]:
    """Strict `<!-- verified: YYYY-MM-DD -->` syntax and placement."""
    findings: list[Finding] = []
    for path in files:
        rel = _rel(path, repo_root)
        lines = _read_lines(path)
        fenced = _fence_mask(lines)
        anchor_lines = {e.line_no for e in parse_entries(path)}
        for i, line in enumerate(lines):
            if fenced[i] or not VERIFIED_ATTEMPT_RE.search(line):
                continue
            match = VERIFIED_RE.search(line)
            if not match:
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "verified-markers",
                        "malformed verified marker; expected "
                        "`<!-- verified: YYYY-MM-DD -->`",
                    )
                )
                continue
            try:
                stamp = datetime.date.fromisoformat(match.group(1))
            except ValueError:
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "verified-markers",
                        f"invalid date '{match.group(1)}' in verified marker",
                    )
                )
                continue
            if stamp > today:
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "verified-markers",
                        f"verified date {stamp} is in the future",
                    )
                )
            # Placement: the marker on 1-indexed line i+1 must directly
            # follow an entry anchor, i.e. line i must be an anchor line.
            if i not in anchor_lines:
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "verified-markers",
                        "verified marker must sit directly under an entry link line",
                    )
                )
    return findings


def _entry_blocks(path: Path, lines: Sequence[str]) -> list[list[int]]:
    """Per entry, the 0-based line indices of its block (anchor..desc end)."""
    blocks: list[list[int]] = []
    for entry in parse_entries(path):
        indices = [entry.line_no - 1]
        if entry.verified_line is not None:
            indices.append(entry.verified_line - 1)
        if entry.desc_line is not None:
            last = _desc_block_end(lines, entry.desc_line)
            indices.extend(range(entry.desc_line - 1, last + 1))
        blocks.append(sorted(set(indices)))
    return blocks


def _entry_block_indices(path: Path, lines: Sequence[str]) -> set[int]:
    """0-based line indices belonging to catalog entries (anchor..desc end)."""
    return {i for block in _entry_blocks(path, lines) for i in block}


def check_style_bans(files: Sequence[Path], repo_root: Path) -> list[Finding]:
    """No emoji, no bold inline labels in catalog entries (fences exempt).

    Both bans are scoped to entry blocks: structural doc lists (checklists,
    reference-architecture stack bullets) legitimately use both.
    """
    findings: list[Finding] = []
    for path in files:
        rel = _rel(path, repo_root)
        lines = _read_lines(path)
        fenced = _fence_mask(lines)
        entry_indices = _entry_block_indices(path, lines)
        for i, line in enumerate(lines):
            if fenced[i]:
                continue
            if i not in entry_indices and not LINK_BULLET_RE.match(line):
                continue
            if EMOJI_RE.search(line):
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "style-bans",
                        "emoji are not allowed in entries",
                    )
                )
            if BOLD_LABEL_RE.search(line):
                findings.append(
                    Finding(
                        rel,
                        i + 1,
                        "style-bans",
                        "bold inline labels (`**Label:**`) are not allowed in entries",
                    )
                )
    return findings


TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|?$")


def _line_has_claim(text: str) -> bool:
    # Ranking cutoffs (top-100, Recall@10, k=10) are not claims by themselves.
    text = re.sub(r"(?:top-|@|k=)\d+", "", text, flags=re.IGNORECASE)
    return bool(UNIT_CLAIM_RE.search(text) or METRIC_WORD_RE.search(text))


@dataclass(frozen=True)
class Claim:
    file: str
    line: int
    tagged: bool


def scoped_claims(
    files: Sequence[Path],
    added: Mapping[str, list[tuple[int, str]]],
    repo_root: Path,
) -> list[Claim]:
    """Numeric claims among added lines, scoped to where the policy applies.

    The Evidence Tier rule targets catalog entries and benchmark table data
    rows; guide prose (tuning advice, caveats discussing unverified figures)
    is out of scope. A claim counts as tagged when a [3P]/[V]/[A] tag appears
    anywhere in the same entry block or on the same table row.
    """
    by_rel = {_rel(p, repo_root): p for p in files}
    claims: list[Claim] = []
    for rel, line_items in added.items():
        path = by_rel.get(rel)
        if path is None or not path.exists():
            continue
        lines = _read_lines(path)
        fenced = _fence_mask(lines)
        block_text: dict[int, str] = {}
        for block in _entry_blocks(path, lines):
            text = "\n".join(lines[i] for i in block)
            for i in block:
                block_text[i] = text
        for line_no, text in line_items:
            i = line_no - 1
            if i >= len(lines) or fenced[i] or not _line_has_claim(text):
                continue
            if i in block_text:
                claims.append(
                    Claim(rel, line_no, bool(EVIDENCE_TAG_RE.search(block_text[i])))
                )
                continue
            stripped = lines[i].strip()
            if not stripped.startswith("|") or TABLE_SEP_RE.match(stripped):
                continue  # prose or separator row — out of scope
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if TABLE_SEP_RE.match(nxt):
                continue  # header row (column names like Recall@10)
            claims.append(Claim(rel, line_no, bool(EVIDENCE_TAG_RE.search(text))))
    return claims


def check_evidence_tags(
    files: Sequence[Path],
    added: Mapping[str, list[tuple[int, str]]],
    repo_root: Path,
) -> list[Finding]:
    """Added numeric claims in entries/tables must carry a [3P]/[V]/[A] tag."""
    return [
        Finding(
            c.file,
            c.line,
            "evidence-tags",
            "numeric claim without a [3P]/[V]/[A] evidence tag "
            "(CONTRIBUTING.md § Evidence Tier)",
        )
        for c in scoped_claims(files, added, repo_root)
        if not c.tagged
    ]


def check_pr_body(body: str, has_claims: bool) -> list[Finding]:
    """PR template checklist ticked; Engineering Context filled for claims."""
    findings: list[Finding] = []
    if not body.strip():
        findings.append(
            Finding(
                "PR body",
                1,
                "pr-body",
                "PR description is empty; fill in the pull request template",
            )
        )
        return findings
    unticked = len(UNTICKED_BOX_RE.findall(body))
    if unticked:
        findings.append(
            Finding(
                "PR body",
                1,
                "pr-body",
                f"{unticked} checklist item(s) not ticked; confirm each "
                "requirement (tick even if N/A)",
            )
        )
    if has_claims:
        problems: list[str] = []
        if not SOURCE_URL_FILLED_RE.search(body):
            problems.append("Source URL")
        if not DATE_FILLED_RE.search(body):
            problems.append("Date")
        tag_line = TAG_LINE_RE.search(body)
        tag_filled = bool(
            tag_line
            and EVIDENCE_TAG_RE.search(tag_line.group(0))
            and not all(m in tag_line.group(0) for m in TAG_LEGEND_MARKERS)
        )
        if not tag_filled:
            problems.append("Tag")
        if problems:
            findings.append(
                Finding(
                    "PR body",
                    1,
                    "pr-body",
                    "diff adds numeric claims but Engineering Context "
                    f"field(s) not filled: {', '.join(problems)} "
                    "(CONTRIBUTING.md § Evidence Tier)",
                )
            )
    return findings


def added_lines_from_git(
    base_ref: str, files: Sequence[Path], repo_root: Path
) -> dict[str, list[tuple[int, str]]]:
    """Parse `git diff -U0` into {relpath: [(new_line_no, text), ...]}."""
    rels = [_rel(p, repo_root) for p in files]
    cmd = [
        "git",
        "-C",
        str(repo_root),
        "diff",
        "-U0",
        f"{base_ref}...HEAD",
        "--",
        *rels,
    ]
    out = subprocess.run(
        cmd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    added: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    line_no = 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            line_no = int(match.group(1)) if match else 0
            continue
        if current is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            added.setdefault(current, []).append((line_no, raw[1:]))
            line_no += 1
    return added


def changed_files_from_git(base_ref: str, repo_root: Path) -> list[Path]:
    cmd = [
        "git",
        "-C",
        str(repo_root),
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        f"{base_ref}...HEAD",
    ]
    out = subprocess.run(
        cmd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    return [repo_root / name for name in out.splitlines() if name.strip()]


def filter_content_files(files: Iterable[Path], repo_root: Path) -> list[Path]:
    """Root-level catalog markdown only (governance/meta excluded)."""
    result: list[Path] = []
    for path in files:
        rel = _rel(path, repo_root)
        if "/" in rel or not rel.endswith(".md") or rel in NON_CONTENT:
            continue
        if (repo_root / rel).exists():
            result.append(repo_root / rel)
    return result


def _emit(findings: Sequence[Finding]) -> None:
    on_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    for f in sorted(findings, key=lambda x: (x.file, x.line)):
        print(f"{f.file}:{f.line}: [{f.check}] {f.message}")
        if on_actions and f.file != "PR body":
            print(f"::error file={f.file},line={f.line},title={f.check}::{f.message}")
        elif on_actions:
            print(f"::error title={f.check}::{f.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="changed markdown files")
    parser.add_argument("--check", required=True, choices=(*CHECK_IDS, "all"))
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--base-ref", default=None, help="git base ref for diff-scoped checks"
    )
    parser.add_argument("--pr-body-file", type=Path, default=None)
    parser.add_argument("--today", type=datetime.date.fromisoformat, default=None)
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or Path(__file__).resolve().parent.parent).resolve()
    today = args.today or datetime.date.today()

    if args.files:
        candidates = [Path(f) for f in args.files]
    elif args.base_ref:
        candidates = changed_files_from_git(args.base_ref, repo_root)
    else:
        print("error: pass FILES or --base-ref", file=sys.stderr)
        return 2

    files = filter_content_files(candidates, repo_root)
    if not files:
        print("nothing to validate: no content markdown files changed")
        return 0

    checks = list(CHECK_IDS) if args.check == "all" else [args.check]

    # Diff-scoped checks: with --base-ref use real added lines; without it
    # (local sweeps) treat every line of the given files as added.
    added: dict[str, list[tuple[int, str]]] = {}
    if any(c in checks for c in ("evidence-tags", "pr-body")):
        if args.base_ref:
            added = added_lines_from_git(args.base_ref, files, repo_root)
        else:
            for path in files:
                rel = _rel(path, repo_root)
                added[rel] = [(i + 1, line) for i, line in enumerate(_read_lines(path))]

    findings: list[Finding] = []
    for check in checks:
        if check == "format":
            findings += check_format(files, repo_root)
        elif check == "alphabetical":
            findings += check_alphabetical(files, repo_root)
        elif check == "duplicates":
            findings += check_duplicates(files, repo_root)
        elif check == "verified-markers":
            findings += check_verified_markers(files, repo_root, today)
        elif check == "style-bans":
            findings += check_style_bans(files, repo_root)
        elif check == "evidence-tags":
            findings += check_evidence_tags(files, added, repo_root)
        elif check == "pr-body":
            if args.pr_body_file is None:
                if args.check == "all":
                    print("skipping pr-body: no --pr-body-file given")
                    continue
                print("error: pr-body requires --pr-body-file", file=sys.stderr)
                return 2
            body = args.pr_body_file.read_text(encoding="utf-8")
            has_claims = bool(scoped_claims(files, added, repo_root))
            findings += check_pr_body(body, has_claims)

    _emit(findings)
    label = args.check
    print(f"{len(findings)} finding(s) for check '{label}' across {len(files)} file(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
