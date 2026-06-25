"""Unit tests for ``discovery_engine.check_entry_verification_age``.

The check is offline (it only reads README.md) and accepts an injectable
``today``, so these tests are fully deterministic and need no network or mocks.
"""

import datetime
from pathlib import Path

import discovery_engine

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


def test_missing_marker_is_counted_not_listed(tmp_path: Path) -> None:
    """An entry without a marker increments the coverage count, not the table."""
    repo = _make_repo(
        tmp_path,
        "- [LangChain](https://github.com/langchain-ai/langchain)\n"
        "  - Framework for building LLM apps.\n",
    )

    discovery_engine.check_entry_verification_age(repo, today=TODAY)

    report = _report(tmp_path)
    assert "Entry Verification Audit" in report
    assert "0/1 entries" in report
    assert "1 missing" in report
    # Missing entries are summarised, never enumerated in the stale table.
    assert "Days Since Review" not in report


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


def test_mixed_entries_report_combines_stale_and_missing(tmp_path: Path) -> None:
    """A realistic README yields both a coverage count and a stale table."""
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
