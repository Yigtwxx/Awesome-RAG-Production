#!/usr/bin/env bash
# Shared helpers for the long-lived tracking issues this repo's automation posts
# into (discovery feed, broken links, main-branch validation failures).
#
# Usage — source it, then call:
#   . .github/scripts/tracking-issue.sh
#   NUM=$(find_or_create_tracking_issue "broken-links" "Broken links" body.md)
#
# Requires: gh (authenticated via GH_TOKEN) and GH_REPO set to owner/repo.
# Filtering uses gh's built-in --jq, so no external jq binary is needed. The
# title is passed through the environment rather than interpolated into the jq
# expression, so it can never be parsed as jq syntax.
#
# Why this exists: the original inline lookup took `.[0].number` from the open
# issues carrying a label. With more than one such issue the winner depended on
# API ordering — silently. These helpers pick deterministically and complain
# loudly instead.

# find_or_create_tracking_issue LABEL TITLE BODY_FILE [LABEL_DESCRIPTION]
#   -> prints the issue number
#
# Selects the lowest-numbered *bot-authored* open issue whose title matches
# exactly. Lowest number means the original, and it cannot be reordered by the
# API. Requiring bot authorship stops a human-opened issue that happens to carry
# the label from hijacking the feed. Emits a ::warning:: (not a failure) when
# strays exist, because these reports must never turn a run red.
find_or_create_tracking_issue() {
  local label="$1" title="$2" body_file="$3"
  local description="${4:-Automated tracking issue: $label}"

  gh label create "$label" \
    --repo "$GH_REPO" \
    --description "$description" \
    --color "0E8A16" \
    --force >/dev/null 2>&1 || true

  local nums
  nums=$(TRACKING_TITLE="$title" gh issue list \
    --repo "$GH_REPO" \
    --label "$label" \
    --state open \
    --limit 100 \
    --json number,title,author \
    --jq '[.[] | select(.title == env.TRACKING_TITLE and .author.is_bot)]
          | map(.number) | sort | .[]')

  if [ -z "$nums" ]; then
    gh issue create \
      --repo "$GH_REPO" \
      --title "$title" \
      --label "$label" \
      --body-file "$body_file" \
      | grep -oE '[0-9]+$'
    return
  fi

  local first count
  first=$(printf '%s\n' "$nums" | head -1)
  count=$(printf '%s\n' "$nums" | grep -c . || true)

  if [ "$count" -gt 1 ]; then
    echo "::warning::Multiple open '$label' issues ($(printf '%s' "$nums" | tr '\n' ' ')); using #$first — close the strays" >&2
  fi

  printf '%s\n' "$first"
}

# find_open_tracking_issue LABEL TITLE -> prints the issue number, or nothing
#
# Read-only counterpart used by the "recovered, close it" paths. Prints an empty
# string when no matching issue is open, so callers can no-op silently.
find_open_tracking_issue() {
  local label="$1" title="$2"

  TRACKING_TITLE="$title" gh issue list \
    --repo "$GH_REPO" \
    --label "$label" \
    --state open \
    --limit 100 \
    --json number,title,author \
    --jq '[.[] | select(.title == env.TRACKING_TITLE and .author.is_bot)]
          | map(.number) | sort | .[0] // empty' \
    2>/dev/null
}
