"""Shared regexes describing the catalog entry grammar.

Single source of truth for the per-entry conventions documented in
CONTRIBUTING.md (§ Formatting, § Last Verified Date). Consumed by both
discovery_engine.py (weekly cron) and pr_entry_validator.py (PR CI gate).
Stdlib-only so the PR validator needs no pip install.
"""

import re

# Matches github.com/{owner}/{repo} links; trailing delimiters end the repo group.
REPO_URL_RE = re.compile(r"github\.com/([\w.\-]+)/([\w.\-]+?)(?:[/?#\s\)\]\"']|$)")

# A catalog entry is a top-level link bullet `- [Name](URL)` followed by an
# indented description sub-bullet; an optional `<!-- verified: YYYY-MM-DD -->`
# line in between records the last human review.
ENTRY_ANCHOR_RE = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)\s*$")
ENTRY_DESC_RE = re.compile(r"^\s+- \S")
VERIFIED_RE = re.compile(r"<!--\s*verified:\s*(\d{4}-\d{2}-\d{2})\s*-->")
