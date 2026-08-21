"""Unit tests for ``discovery_engine`` audit helpers.

``check_entry_verification_age`` is offline (it only reads README.md) and accepts
an injectable ``today``, so those tests are fully deterministic and need no
network or mocks. ``check_listed_tool_freshness`` reaches the GitHub API, so its
one test substitutes a session whose every request fails.
"""

import datetime
from pathlib import Path
from typing import Any

import discovery_engine
import pytest
import requests

# Fixed "now" so staleness math never depends on the wall clock.
TODAY = datetime.date(2026, 6, 25)


def _make_repo(tmp_path: Path, readme_body: str) -> Path:
    """Write ``readme_body`` to README.md under ``tmp_path`` and return the root."""
    (tmp_path / "README.md").write_text(readme_body, encoding="utf-8")
    return tmp_path


def _report(tmp_path: Path) -> str:
    """Return the PROPOSED_UPDATES.md text, or '' if the check wrote nothing."""
    path = tmp_path / ".github" / "PROPOSED_UPDATES.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def test_fresh_entry_is_not_flagged(tmp_path: Path) -> None:
    """A recent verified date produces no report (no stale, no missing)."""
    repo = _make_repo(
        tmp_path,
        "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        "  <!-- verified: 2026-06-20 -->\n"
        "  - High-performance vector database.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    assert _report(tmp_path) == ""


def test_stale_entry_is_flagged_with_days(tmp_path: Path) -> None:
    """A verified date older than 180 days lands in the stale table."""
    repo = _make_repo(
        tmp_path,
        "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        "  <!-- verified: 2025-01-01 -->\n"
        "  - High-performance vector database.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    report = _report(tmp_path)
    assert "Entry Verification Audit" in report
    assert "Days Since Review" in report
    assert "Qdrant" in report
    # 2025-01-01 -> 2026-06-25 is 540 days.
    assert "540" in report


def test_missing_marker_alone_produces_no_report(tmp_path: Path) -> None:
    """A marker-less entry is not a finding — the convention is forward-looking."""
    repo = _make_repo(
        tmp_path,
        "- [LangChain](https://github.com/langchain-ai/langchain)\n"
        "  - Framework for building LLM apps.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    report = _report(tmp_path)
    assert report == "", f"Missing markers must not be reported, got: {report!r}"


def test_all_entries_missing_markers_produces_no_report(tmp_path: Path) -> None:
    """The grandfathered backlog stays silent no matter how large it is."""
    repo = _make_repo(
        tmp_path,
        "- [LangChain](https://github.com/langchain-ai/langchain)\n"
        "  - Framework for building LLM apps.\n"
        "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        "  - Vector database.\n"
        "- [Weaviate](https://github.com/weaviate/weaviate)\n"
        "  - Vector search engine.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    report = _report(tmp_path)
    assert report == "", f"Backlog of missing markers must stay silent, got: {report!r}"


def test_malformed_date_is_skipped_silently(tmp_path: Path) -> None:
    """An unparseable date is neither flagged as stale nor counted as missing."""
    repo = _make_repo(
        tmp_path,
        "- [Weaviate](https://github.com/weaviate/weaviate)\n"
        "  <!-- verified: 2026-13-99 -->\n"
        "  - Vector search engine.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    # No stale row, no missing count -> nothing written.
    assert _report(tmp_path) == ""


def test_bare_link_bullet_is_not_an_entry(tmp_path: Path) -> None:
    """A link bullet with no description sub-bullet is not counted as an entry."""
    repo = _make_repo(
        tmp_path,
        "- [More lists](https://example.com/more)\n"
        "\n"
        "Some following prose, not a description.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    assert _report(tmp_path) == ""


def test_mixed_entries_report_lists_stale_with_coverage_line(tmp_path: Path) -> None:
    """When something is stale, the report carries the coverage line for context."""
    repo = _make_repo(
        tmp_path,
        "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        "  <!-- verified: 2026-06-20 -->\n"
        "  - Fresh entry.\n"
        "- [LlamaIndex](https://github.com/run-llama/llama_index)\n"
        "  <!-- verified: 2025-01-01 -->\n"
        "  - Stale entry.\n"
        "- [LangChain](https://github.com/langchain-ai/langchain)\n"
        "  - Missing-marker entry.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    report = _report(tmp_path)
    assert "2/3 entries" in report  # 2 of 3 carry a date
    assert "1 missing" in report
    assert "LlamaIndex" in report  # the stale one
    assert "Qdrant" not in report  # the fresh one is never listed


def _make_benchmarks(tmp_path: Path, body: str) -> Path:
    """Write ``body`` to benchmarks.md under ``tmp_path`` and return the root."""
    (tmp_path / "benchmarks.md").write_text(body, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "cell,expected",
    [
        ("2026-08-01", datetime.date(2026, 8, 1)),
        ("2024-10", datetime.date(2024, 10, 31)),  # partial -> end of month
        ("2022-12", datetime.date(2022, 12, 31)),
        ("2024", datetime.date(2024, 12, 31)),  # partial -> end of year
        ("2024 (active doc)", datetime.date(2024, 12, 31)),  # suffix tolerated
        ("2024-02", datetime.date(2024, 2, 29)),  # leap year month length
        ("Ongoing — no specific post confirmed", None),
        ("", None),
        ("2024-13", None),  # impossible month
        ("2022-12 (paper)", None),  # fixed publication date — exempt
        ("2023-09 (Paper)", None),  # marker is case-insensitive
    ],
)
def test_parse_row_date_reads_partial_dates_generously(
    cell: str, expected: datetime.date | None
) -> None:
    """Partial dates resolve to the LATEST day they could mean, never earlier."""
    result = discovery_engine.parse_row_date(cell)
    assert result == expected, f"parse_row_date({cell!r}) -> {result}, want {expected}"


def test_check_benchmark_freshness_flags_old_partial_date(tmp_path: Path) -> None:
    """A year-only date well past the window lands in the stale table."""
    repo = _make_benchmarks(
        tmp_path,
        "| System | Metric | Tag | Source | Date |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| vLLM | Throughput | \\[3P\\] | [paper](https://a.co/p) | 2023-09 |\n",
    )

    discovery_engine.check_benchmark_freshness(repo, today=TODAY)

    report = _report(tmp_path)
    assert "Stale Benchmark Citations" in report, (
        f"Expected a stale table, got {report!r}"
    )
    assert "vLLM" in report, f"Expected the vLLM row, got {report!r}"


def test_check_benchmark_freshness_recent_date_not_flagged(tmp_path: Path) -> None:
    repo = _make_benchmarks(
        tmp_path,
        "| System | Metric | Tag | Source | Date |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| Qdrant | Recall@10 | \\[V\\] | [bench](https://q.io/b) | 2026-05-01 |\n",
    )

    discovery_engine.check_benchmark_freshness(repo, today=TODAY)

    assert _report(tmp_path) == "", "A recent row must not be flagged"


def test_check_benchmark_freshness_ignores_arxiv_id_in_source_column(
    tmp_path: Path,
) -> None:
    """The old line-wide regex matched `abs/2212.06121`; column-aware parsing must not.

    Here the Date column is current, so a row that mentions an old-looking arXiv
    identifier elsewhere must stay unflagged.
    """
    repo = _make_benchmarks(
        tmp_path,
        "| Comparison | Improvement | Tag | Source | Date |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| Cross-encoder | +4 nDCG | \\[3P\\] | [x](https://arxiv.org/abs/2212.06121) "
        "| 2026-06-01 |\n",
    )

    discovery_engine.check_benchmark_freshness(repo, today=TODAY)

    report = _report(tmp_path)
    assert report == "", f"arXiv id must not be read as a date, got {report!r}"


def test_check_benchmark_freshness_recognises_snapshot_date_header(
    tmp_path: Path,
) -> None:
    """The MTEB table names its column 'Snapshot Date' rather than 'Date'."""
    repo = _make_benchmarks(
        tmp_path,
        "| Model | nDCG@10 | Tag | Source | Snapshot Date |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| BGE-M3 | 63.0 | \\[3P\\] | [MTEB](https://hf.co/mteb) | 2022 |\n",
    )

    discovery_engine.check_benchmark_freshness(repo, today=TODAY)

    assert "BGE-M3" in _report(tmp_path), "Snapshot Date column must be honoured"


def test_check_benchmark_freshness_table_without_date_column_ignored(
    tmp_path: Path,
) -> None:
    """A table with no date column contributes nothing, whatever digits it holds."""
    repo = _make_benchmarks(
        tmp_path,
        "| Tag | Meaning |\n"
        "| :--- | :--- |\n"
        "| \\[3P\\] | Third-party measured, e.g. arXiv 2212.06121 |\n",
    )

    discovery_engine.check_benchmark_freshness(repo, today=TODAY)

    assert _report(tmp_path) == "", "A table without a date column must be ignored"


class _AlwaysFailingSession:
    """Stand-in for ``requests.Session`` whose every GET raises."""

    def get(self, *args: Any, **kwargs: Any) -> None:
        raise requests.RequestException("simulated network outage")


def test_tool_freshness_all_requests_fail_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A total outage must not crash the run and take the weekly report with it.

    Every request failing used to leave ``response`` unbound, raising NameError
    out of ``run_discovery`` and killing the whole audit.
    """
    repo = _make_repo(
        tmp_path,
        "- [Qdrant](https://github.com/qdrant/qdrant)\n"
        "  - High-performance vector database.\n",
    )
    monkeypatch.setattr(
        discovery_engine, "_build_session", lambda: _AlwaysFailingSession()
    )

    discovery_engine.check_listed_tool_freshness(repo)

    report = _report(tmp_path)
    assert report == "", (
        f"No repo could be audited, so nothing to flag, got: {report!r}"
    )


# --- Out-of-scope denylist -------------------------------------------------
#
# The denylist used to match on `owner/name`. When a rejected project moved
# org, its slug changed while its id did not, so the entry stopped matching and
# an already-rejected repo returned to the top of three consecutive weekly
# reports. These tests pin the id-first behaviour that replaced it.


def _search_item(full_name: str, repo_id: int) -> dict[str, Any]:
    """Return the subset of a GitHub search result the filter actually reads."""
    return {"id": repo_id, "full_name": full_name}


def test_denylisted_repo_still_matches_after_a_rename() -> None:
    slug, repo_id = next(
        (slug, rid)
        for slug, rid in discovery_engine.OUT_OF_SCOPE_REPOS.items()
        if rid is not None
    )
    renamed = _search_item("BrandNewOrg/rebranded-name", repo_id)

    assert discovery_engine.is_out_of_scope(renamed), (
        f"{slug} moved org and slipped past the denylist; id {repo_id} is unchanged"
    )


def test_denylist_falls_back_to_the_slug_when_the_id_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(discovery_engine.OUT_OF_SCOPE_REPOS, "acme/no-id-yet", None)

    assert discovery_engine.is_out_of_scope(_search_item("Acme/No-Id-Yet", 999_001))


def test_repo_absent_from_the_denylist_is_not_filtered() -> None:
    assert not discovery_engine.is_out_of_scope(
        _search_item("some-org/genuinely-new", 999_002)
    )


def test_filter_candidates_splits_listed_from_out_of_scope() -> None:
    denied_id = next(
        rid for rid in discovery_engine.OUT_OF_SCOPE_REPOS.values() if rid is not None
    )
    projects = [
        _search_item("qdrant/qdrant", 999_003),
        _search_item("Renamed/still-out-of-scope", denied_id),
        _search_item("some-org/genuinely-new", 999_004),
    ]

    kept, listed_hits, denied_hits = discovery_engine.filter_candidates(
        projects, {"qdrant/qdrant"}
    )

    assert [p["full_name"] for p in kept] == ["some-org/genuinely-new"]
    assert (listed_hits, denied_hits) == (1, 1)


def test_every_denylist_entry_carries_a_repo_id() -> None:
    """Ratchet: a slug-only entry silently loses rename protection.

    Fill it in with `gh api repos/<owner>/<name> --jq .id`.
    """
    unresolved = sorted(
        slug for slug, rid in discovery_engine.OUT_OF_SCOPE_REPOS.items() if rid is None
    )

    assert unresolved == [], f"denylist entries missing a repo id: {unresolved}"
