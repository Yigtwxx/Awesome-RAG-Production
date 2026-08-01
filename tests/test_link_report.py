"""Unit tests for ``link_report`` — the weekly broken-link report renderer.

Fully offline: every test feeds a hand-built payload, so no lychee binary or
network access is needed. The schema variants covered here (``error_map`` vs
``fail_map``, string vs object ``status``) are the ones lychee has shipped
across versions; the parser must tolerate all of them and degrade to "no
findings" on anything else rather than crash the workflow.
"""

import datetime
from pathlib import Path

import link_report
import pytest

TODAY = datetime.date(2026, 8, 1)
RUN_URL = "https://example.com/run/1"


def _payload(source: str, url: str, status: object) -> dict:
    return {"error_map": {source: [{"url": url, "status": status}]}}


def test_parse_lychee_json_error_map_object_status() -> None:
    links = link_report.parse_lychee_json(
        _payload("README.md", "https://a.co/x", {"code": 404, "text": "Not Found"})
    )
    assert len(links) == 1, f"Expected one link, got {links}"
    assert links[0].status == "404 Not Found", f"Got {links[0].status!r}"
    assert links[0].sources == ["README.md"], f"Got {links[0].sources}"


def test_parse_lychee_json_string_status_accepted() -> None:
    links = link_report.parse_lychee_json(
        _payload("books.md", "https://a.co/y", "Timeout")
    )
    assert links[0].status == "Timeout", f"Got {links[0].status!r}"


def test_parse_lychee_json_legacy_fail_map_key() -> None:
    """Older lychee versions call the key `fail_map`."""
    payload = {"fail_map": {"README.md": [{"url": "https://a.co/z", "status": "404"}]}}
    links = link_report.parse_lychee_json(payload)
    assert len(links) == 1, f"fail_map must still parse, got {links}"


def test_parse_lychee_json_unknown_schema_returns_empty() -> None:
    """A schema change must degrade to no findings, never raise."""
    links = link_report.parse_lychee_json({"totally": {"different": "shape"}})
    assert links == [], f"Unknown schema must yield no findings, got {links}"


def test_parse_lychee_json_same_url_in_two_files_merges_sources() -> None:
    payload = {
        "error_map": {
            "README.md": [{"url": "https://a.co/dup", "status": "404"}],
            "chunking-strategies.md": [{"url": "https://a.co/dup", "status": "404"}],
        }
    }
    links = link_report.parse_lychee_json(payload)
    assert len(links) == 1, f"Duplicate URL must collapse to one row, got {links}"
    assert links[0].sources == ["README.md", "chunking-strategies.md"], (
        f"Got {links[0].sources}"
    )


def test_fingerprint_ignores_status_flapping() -> None:
    """A 404 that becomes a timeout is the same finding — no new comment."""
    a = link_report.parse_lychee_json(_payload("README.md", "https://a.co/x", "404"))
    b = link_report.parse_lychee_json(
        _payload("README.md", "https://a.co/x", "Timeout")
    )
    assert link_report.fingerprint(a) == link_report.fingerprint(b), (
        "Status change must not alter the fingerprint"
    )


def test_fingerprint_changes_when_url_set_changes() -> None:
    a = link_report.parse_lychee_json(_payload("README.md", "https://a.co/x", "404"))
    b = link_report.parse_lychee_json(
        _payload("README.md", "https://a.co/other", "404")
    )
    assert link_report.fingerprint(a) != link_report.fingerprint(b), (
        "A different URL set must produce a different fingerprint"
    )


def test_render_issue_body_round_trips_fingerprint() -> None:
    links = link_report.parse_lychee_json(
        _payload("README.md", "https://a.co/x", "404 Not Found")
    )
    body = link_report.render_issue_body(links, RUN_URL, TODAY)
    assert "https://a.co/x" in body, "URL must appear in the table"
    assert "`README.md`" in body, "Source file must appear in the table"
    assert link_report.extract_fingerprint(body) == link_report.fingerprint(links), (
        "Fingerprint must round-trip through the rendered body"
    )


def test_render_issue_body_empty_reports_all_clear() -> None:
    body = link_report.render_issue_body([], RUN_URL, TODAY)
    assert "No broken links" in body, f"Got {body!r}"
    assert link_report.extract_fingerprint(body) is not None, (
        "Even an all-clear body carries a fingerprint"
    )


def test_extract_fingerprint_absent_marker_returns_none() -> None:
    assert link_report.extract_fingerprint("plain body, no marker") is None


def test_main_unreadable_input_still_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A malformed report must not fail the weekly job."""
    missing = tmp_path / "nope.json"
    code = link_report.main(["--input", str(missing), "--run-url", RUN_URL])
    assert code == 0, f"Expected exit 0, got {code}"
    assert "unavailable" in capsys.readouterr().out
