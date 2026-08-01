"""Unit tests for ``pr_entry_validator`` — the PR CI gate.

All checks are offline (they read markdown files under a tmp_path repo) and
accept injectable inputs (``today``, ``added`` line mappings), so these tests
are fully deterministic and need no network, git, or mocks.
"""

import datetime
from pathlib import Path

import pr_entry_validator as v
import pytest

# Fixed "now" so date math never depends on the wall clock.
TODAY = datetime.date(2026, 7, 9)


def _make_repo(tmp_path: Path, **files: str) -> Path:
    """Write keyword-named markdown files under ``tmp_path`` (README=README.md)."""
    for name, body in files.items():
        filename = "README.md" if name == "readme" else f"{name}.md"
        (tmp_path / filename).write_text(body, encoding="utf-8")
    return tmp_path


def _checks(findings: list[v.Finding]) -> list[str]:
    return [f.message for f in findings]


# --- format -----------------------------------------------------------------


def test_check_format_two_line_entry_passes(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  <!-- verified: 2026-06-20 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert findings == [], f"Expected no findings, got {_checks(findings)}"


def test_check_format_single_line_entry_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme="- [Qdrant](https://github.com/qdrant/qdrant) - Vector DB.\n",
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert any("one-line entry" in m for m in _checks(findings)), (
        f"Expected one-line-entry finding, got {_checks(findings)}"
    )


def test_check_format_missing_description_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Milvus](https://github.com/milvus-io/milvus)\n"
            "  - Cloud-native vector database.\n"
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert any("missing its indented description" in m for m in _checks(findings)), (
        f"Expected missing-description finding, got {_checks(findings)}"
    )


def test_check_format_bare_link_reference_list_exempt(tmp_path: Path) -> None:
    """A run of bare link bullets (e.g. Further Reading) needs no descriptions."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "**Further Reading:**\n"
            "\n"
            "- [Guide A](https://example.com/a)\n"
            "- [Guide B](https://example.com/b)\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert findings == [], f"Expected reference-list exemption, got {_checks(findings)}"


def test_check_format_description_without_period_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - High-performance vector database\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert any("terminal punctuation" in m for m in _checks(findings)), (
        f"Expected punctuation finding, got {_checks(findings)}"
    )


def test_check_format_junk_after_link_flagged_as_malformed(tmp_path: Path) -> None:
    """Emoji/labels after the link would hide the entry from other checks."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Chroma](https://github.com/chroma-core/chroma) 🚀\n"
            "  - Embedded vector store.\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert any("malformed entry line" in m for m in _checks(findings)), (
        f"Expected malformed-entry finding, got {_checks(findings)}"
    )


def test_check_format_attribution_hybrid_passes(tmp_path: Path) -> None:
    """blogs.md house style: dash attribution plus description bullet."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Pinecone Learn](https://www.pinecone.io/learn/) - Pinecone.\n"
            "  - Technical guides on vector databases.\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert findings == [], f"Hybrid attribution must pass, got {_checks(findings)}"


def test_check_format_wrong_marker_indent_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "    <!-- verified: 2026-06-20 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    findings = v.check_format([repo / "README.md"], repo)
    assert any("indented exactly 2 spaces" in m for m in _checks(findings)), (
        f"Expected marker-indent finding, got {_checks(findings)}"
    )


# --- alphabetical -----------------------------------------------------------

SORTED_SECTION = (
    "## Vector Databases\n"
    "\n"
    "- [Milvus](https://github.com/milvus-io/milvus)\n"
    "  - Cloud-native vector database.\n"
    "- [Qdrant](https://github.com/qdrant/qdrant)\n"
    "  - High-performance vector database.\n"
)

UNSORTED_SECTION = (
    "## Vector Databases\n"
    "\n"
    "- [Qdrant](https://github.com/qdrant/qdrant)\n"
    "  - High-performance vector database.\n"
    "- [Milvus](https://github.com/milvus-io/milvus)\n"
    "  - Cloud-native vector database.\n"
)


def test_check_alphabetical_sorted_run_passes(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, readme=SORTED_SECTION)
    findings = v.check_alphabetical([repo / "README.md"], repo)
    assert findings == [], f"Expected no findings, got {_checks(findings)}"


def test_check_alphabetical_out_of_order_pair_flagged_with_both_lines(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, readme=UNSORTED_SECTION)
    findings = v.check_alphabetical([repo / "README.md"], repo)
    assert len(findings) == 1, f"Expected 1 finding, got {_checks(findings)}"
    assert findings[0].line == 5, f"Expected line 5, got {findings[0].line}"
    assert "line 3" in findings[0].message, (
        f"Expected reference to line 3, got {findings[0].message}"
    )


def test_check_alphabetical_case_insensitive_compare(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "## Tools\n"
            "\n"
            "- [abc](https://example.com/abc)\n"
            "  - First tool.\n"
            "- [DEF](https://example.com/def)\n"
            "  - Second tool.\n"
        ),
    )
    findings = v.check_alphabetical([repo / "README.md"], repo)
    assert findings == [], f"Expected no findings, got {_checks(findings)}"


def test_check_alphabetical_no_alphabetical_comment_exempts_section(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme="## Vector Databases\n\n<!-- no-alphabetical -->\n"
        + UNSORTED_SECTION.split("\n", 2)[2],
    )
    findings = v.check_alphabetical([repo / "README.md"], repo)
    assert findings == [], f"Expected exemption, got {_checks(findings)}"


def test_check_alphabetical_prose_between_runs_resets_ordering(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "## Tools\n"
            "\n"
            "- [Zeta](https://example.com/zeta)\n"
            "  - Last-alphabet tool.\n"
            "\n"
            "Some prose splitting the section into two runs.\n"
            "\n"
            "- [Alpha](https://example.com/alpha)\n"
            "  - First-alphabet tool.\n"
        ),
    )
    findings = v.check_alphabetical([repo / "README.md"], repo)
    assert findings == [], f"Expected run reset, got {_checks(findings)}"


# --- duplicates ---------------------------------------------------------------


def test_check_duplicates_same_url_across_files_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - High-performance vector database.\n"
        ),
        blogs=(
            "- [Qdrant Engine](https://github.com/qdrant/qdrant/)\n"
            "  - Same repo, trailing slash.\n"
        ),
    )
    findings = v.check_duplicates([repo / "blogs.md"], repo)
    assert len(findings) == 1, f"Expected 1 finding, got {_checks(findings)}"
    assert "README.md:1" in findings[0].message, (
        f"Expected pointer to README.md:1, got {findings[0].message}"
    )


def test_check_duplicates_same_name_diff_url_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - The vector database.\n"
            "- [Qdrant](https://qdrant.tech)\n"
            "  - The company site.\n"
        ),
    )
    findings = v.check_duplicates([repo / "README.md"], repo)
    assert any("name" in f.message for f in findings), (
        f"Expected same-name finding, got {_checks(findings)}"
    )


def test_check_duplicates_preexisting_dupe_in_untouched_file_ignored(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=("- [Qdrant](https://github.com/qdrant/qdrant)\n  - Listed here.\n"),
        blogs=("- [Qdrant](https://github.com/qdrant/qdrant)\n  - Also listed here.\n"),
        datasets=(
            "- [BEIR](https://github.com/beir-cellar/beir)\n"
            "  - Retrieval benchmark suite.\n"
        ),
    )
    findings = v.check_duplicates([repo / "datasets.md"], repo)
    assert findings == [], (
        f"PR must not be blamed for untouched dupes, got {_checks(findings)}"
    )


def test_check_duplicates_allow_duplicate_comment_exempts(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n  - Listed in the catalog.\n"
        ),
        blogs=(
            "<!-- allow-duplicate -->\n"
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - Intentional overlap with the catalog.\n"
        ),
    )
    findings = v.check_duplicates([repo / "blogs.md"], repo)
    assert findings == [], f"Expected exemption, got {_checks(findings)}"


# --- verified-markers ---------------------------------------------------------


def test_check_verified_markers_valid_marker_passes(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  <!-- verified: 2026-06-20 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    findings = v.check_verified_markers([repo / "README.md"], repo, TODAY)
    assert findings == [], f"Expected no findings, got {_checks(findings)}"


def test_check_verified_markers_future_date_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  <!-- verified: 2027-01-01 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    findings = v.check_verified_markers([repo / "README.md"], repo, TODAY)
    assert any("in the future" in m for m in _checks(findings)), (
        f"Expected future-date finding, got {_checks(findings)}"
    )


def test_check_verified_markers_malformed_date_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  <!-- verified: 2026-13-99 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    findings = v.check_verified_markers([repo / "README.md"], repo, TODAY)
    assert any("invalid date" in m for m in _checks(findings)), (
        f"Expected invalid-date finding, got {_checks(findings)}"
    )


def test_check_verified_markers_orphan_marker_flagged(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme=("Some prose.\n<!-- verified: 2026-06-20 -->\nMore prose.\n"),
    )
    findings = v.check_verified_markers([repo / "README.md"], repo, TODAY)
    assert any("directly under an entry" in m for m in _checks(findings)), (
        f"Expected placement finding, got {_checks(findings)}"
    )


# --- new-entry markers --------------------------------------------------------


def test_check_new_entry_markers_added_entry_without_marker_flagged(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - High-performance vector database.\n"
        ),
    )
    added = {
        "README.md": [
            (1, "- [Qdrant](https://github.com/qdrant/qdrant)"),
            (2, "  - High-performance vector database."),
        ]
    }
    findings = v.check_new_entry_markers([repo / "README.md"], added, repo)
    assert any("must carry a" in m for m in _checks(findings)), (
        f"Expected a missing-marker finding, got {_checks(findings)}"
    )


def test_check_new_entry_markers_added_entry_with_marker_passes(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  <!-- verified: 2026-06-20 -->\n"
            "  - High-performance vector database.\n"
        ),
    )
    added = {
        "README.md": [
            (1, "- [Qdrant](https://github.com/qdrant/qdrant)"),
            (2, "  <!-- verified: 2026-06-20 -->"),
            (3, "  - High-performance vector database."),
        ]
    }
    findings = v.check_new_entry_markers([repo / "README.md"], added, repo)
    assert findings == [], f"Expected no findings, got {_checks(findings)}"


def test_check_new_entry_markers_description_only_edit_not_flagged(
    tmp_path: Path,
) -> None:
    """Rewording a description must not demand a marker on an old entry."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - Reworded description only.\n"
        ),
    )
    # -U0 emits no context lines, so only the description line is "added".
    added = {"README.md": [(2, "  - Reworded description only.")]}
    findings = v.check_new_entry_markers([repo / "README.md"], added, repo)
    assert findings == [], (
        f"Anchor untouched, so no marker is required, got {_checks(findings)}"
    )


def test_check_new_entry_markers_untouched_entry_not_flagged(tmp_path: Path) -> None:
    """The grandfathered backlog in files this PR did not touch stays silent."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - Pre-existing entry with no marker.\n"
        ),
        blogs=("- [New Blog](https://example.com/blog) - Author.\n"),
    )
    added = {"blogs.md": [(1, "- [New Blog](https://example.com/blog) - Author.")]}
    findings = v.check_new_entry_markers(
        [repo / "README.md", repo / "blogs.md"], added, repo
    )
    assert findings == [], (
        f"PR must not be blamed for untouched files, got {_checks(findings)}"
    )


def test_check_new_entry_markers_attribution_entry_not_flagged(tmp_path: Path) -> None:
    """blogs.md/datasets.md attribution one-liners never parse as entries."""
    repo = _make_repo(
        tmp_path,
        blogs=("- [Some Blog](https://example.com/blog) - Jane Doe.\n"),
    )
    added = {"blogs.md": [(1, "- [Some Blog](https://example.com/blog) - Jane Doe.")]}
    findings = v.check_new_entry_markers([repo / "blogs.md"], added, repo)
    assert findings == [], (
        f"Attribution entries are immune by construction, got {_checks(findings)}"
    )


def test_check_new_entry_markers_bare_reference_link_not_flagged(
    tmp_path: Path,
) -> None:
    """A link bullet with no description sub-bullet is not a catalog entry."""
    repo = _make_repo(
        tmp_path,
        readme=("- [More lists](https://example.com/more)\n\nFollowing prose.\n"),
    )
    added = {"README.md": [(1, "- [More lists](https://example.com/more)")]}
    findings = v.check_new_entry_markers([repo / "README.md"], added, repo)
    assert findings == [], (
        f"Bare reference links are not entries, got {_checks(findings)}"
    )


def test_check_new_entry_markers_empty_added_map_is_noop(tmp_path: Path) -> None:
    """A local sweep with no --base-ref must never flag the existing catalog."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Qdrant](https://github.com/qdrant/qdrant)\n"
            "  - Entry with no marker.\n"
            "- [Weaviate](https://github.com/weaviate/weaviate)\n"
            "  - Another entry with no marker.\n"
        ),
    )
    findings = v.check_new_entry_markers([repo / "README.md"], {}, repo)
    assert findings == [], f"Empty added map must be a no-op, got {_checks(findings)}"


# --- style-bans ---------------------------------------------------------------


@pytest.mark.parametrize(
    "line,expected_fragment",
    [
        ("- [Tool](https://example.com) 🚀\n  - Great tool.\n", "emoji"),
        (
            "- [Tool](https://example.com)\n  - **Use Case:** production.\n",
            "bold inline labels",
        ),
    ],
)
def test_check_style_bans_banned_pattern_flagged(
    tmp_path: Path, line: str, expected_fragment: str
) -> None:
    repo = _make_repo(tmp_path, readme=line)
    findings = v.check_style_bans([repo / "README.md"], repo)
    assert any(expected_fragment in m for m in _checks(findings)), (
        f"Expected '{expected_fragment}' finding, got {_checks(findings)}"
    )


def test_check_style_bans_emoji_inside_mermaid_fence_ignored(
    tmp_path: Path,
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=("```mermaid\ngraph TD\n  - A[🚀 Ingest] --> B[Index]\n```\n"),
    )
    findings = v.check_style_bans([repo / "README.md"], repo)
    assert findings == [], f"Fenced emoji must pass, got {_checks(findings)}"


# --- evidence-tags ------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expect_finding",
    [
        ("Achieves 12ms latency on 1M vectors.", True),
        ("Recall of 0.98 measured on BEIR.", True),
        ("Cuts costs by 40% in steady state.", True),
        ("Achieves 12ms latency [3P](https://example.com/bench).", False),
        (r"p95 latency 120ms \[V\] per vendor docs.", False),
        ("Supports 3 chunking strategies.", False),
        ("Released in 2024 with new features.", False),
        ("Improves recall@10 for ambiguous queries.", False),
    ],
)
def test_check_evidence_tags_entry_claim_detection(
    tmp_path: Path, text: str, expect_finding: bool
) -> None:
    repo = _make_repo(
        tmp_path,
        readme=f"- [Tool](https://example.com/tool)\n  - {text}\n",
    )
    added = {"README.md": [(2, f"  - {text}")]}
    findings = v.check_evidence_tags([repo / "README.md"], added, repo)
    assert bool(findings) == expect_finding, (
        f"Line {text!r}: expected finding={expect_finding}, got {_checks(findings)}"
    )


def test_check_evidence_tags_tag_on_continuation_line_passes(
    tmp_path: Path,
) -> None:
    """The tag may sit on a wrapped continuation line of the same entry."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "- [Tool](https://example.com/tool)\n"
            "  - Delivers up to 90% cost reduction on cached context\n"
            "    (\\[V\\] [vendor docs](https://example.com/docs)).\n"
        ),
    )
    added = {
        "README.md": [(2, "  - Delivers up to 90% cost reduction on cached context")]
    }
    findings = v.check_evidence_tags([repo / "README.md"], added, repo)
    assert findings == [], f"Tag in same block must pass, got {_checks(findings)}"


def test_check_evidence_tags_prose_claim_out_of_scope(tmp_path: Path) -> None:
    """Guide prose (tuning advice) is not covered by the Evidence Tier rule."""
    repo = _make_repo(
        tmp_path,
        readme="Use ~20% overlap between chunks to preserve context.\n",
    )
    added = {"README.md": [(1, "Use ~20% overlap between chunks to preserve context.")]}
    findings = v.check_evidence_tags([repo / "README.md"], added, repo)
    assert findings == [], f"Prose must be out of scope, got {_checks(findings)}"


def test_check_evidence_tags_table_rows(tmp_path: Path) -> None:
    """Data rows need a tag; the header row (Recall@10 etc.) is exempt."""
    repo = _make_repo(
        tmp_path,
        readme=(
            "| System | Recall@10 | p99 Latency | Tag |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| Qdrant | 0.990 | ~1 ms | \\[V\\] |\n"
            "| Milvus | 0.995 | ~2 ms | |\n"
        ),
    )
    lines = (repo / "README.md").read_text(encoding="utf-8").splitlines()
    added = {"README.md": [(i + 1, line) for i, line in enumerate(lines)]}
    findings = v.check_evidence_tags([repo / "README.md"], added, repo)
    assert len(findings) == 1, f"Expected 1 finding, got {_checks(findings)}"
    assert findings[0].line == 4, (
        f"Expected line 4 (untagged row), got {findings[0].line}"
    )


# --- pr-body ------------------------------------------------------------------

FILLED_BODY = """## Description
Adds Qdrant.

## ✅ Checklist

- [x] I have checked that this resource is not already in the list.
- [x] This resource is actively maintained (updated in the last 6 months).

## Engineering Context

- **Source URL:** https://example.com/benchmark
- **Date (YYYY-MM-DD):** 2026-07-01
- **Tag:** [3P]
- **Methodology / harness link:** https://example.com/harness
"""

TEMPLATE_BODY = """## ✅ Checklist

- [ ] I have checked that this resource is not already in the list.

## Engineering Context

- **Source URL:**
- **Date (YYYY-MM-DD):**
- **Tag:** `[3P]` third-party measured / `[V]` vendor-stated / `[A]` anecdotal
- **Methodology / harness link:**
"""


def test_check_pr_body_unticked_checkbox_flagged() -> None:
    findings = v.check_pr_body(TEMPLATE_BODY, has_claims=False)
    assert any("not ticked" in m for m in _checks(findings)), (
        f"Expected unticked-checkbox finding, got {_checks(findings)}"
    )


def test_check_pr_body_context_required_only_when_claims_added() -> None:
    ticked_but_empty_context = TEMPLATE_BODY.replace("- [ ]", "- [x]")
    no_claim = v.check_pr_body(ticked_but_empty_context, has_claims=False)
    with_claim = v.check_pr_body(ticked_but_empty_context, has_claims=True)
    assert no_claim == [], f"No claims -> context optional, got {_checks(no_claim)}"
    assert any("Engineering Context" in m for m in _checks(with_claim)), (
        f"Claims -> context required, got {_checks(with_claim)}"
    )


def test_check_pr_body_filled_context_passes() -> None:
    findings = v.check_pr_body(FILLED_BODY, has_claims=True)
    assert findings == [], f"Filled body must pass, got {_checks(findings)}"


def test_check_pr_body_empty_body_flagged() -> None:
    findings = v.check_pr_body("", has_claims=True)
    assert len(findings) == 1, f"Expected 1 finding, got {_checks(findings)}"
    assert "empty" in findings[0].message, (
        f"Expected empty-body finding, got {findings[0].message}"
    )


# --- file filtering -----------------------------------------------------------


def test_filter_content_files_excludes_meta_and_nested(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        readme="- [A](https://example.com/a)\n  - Entry.\n",
        CONTRIBUTING="Meta file.\n",
    )
    (tmp_path / "docs-site").mkdir()
    (tmp_path / "docs-site" / "index.md").write_text("Nested.\n", encoding="utf-8")
    candidates = [
        repo / "README.md",
        repo / "CONTRIBUTING.md",
        repo / "docs-site" / "index.md",
        repo / "missing.md",
    ]
    result = v.filter_content_files(candidates, repo)
    assert result == [repo / "README.md"], (
        f"Expected only README.md, got {[p.name for p in result]}"
    )
