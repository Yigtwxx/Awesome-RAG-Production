# Contributing to Awesome RAG Production

First off, thank you for taking the time to contribute! It is people like you who
make this list a valuable resource for the AI engineering community.

As a repository focused on **Production-Grade RAG**, we maintain high standards
for the resources we include. Please follow these guidelines to ensure a smooth
contribution process.

---

## Quality Standards

We don't just collect links; we curate **engineering excellence**. To be
accepted, a resource must meet the following criteria:

1. **Production Focus:** Does it solve a real-world problem like scalability, latency, or reliability?
2. **Activity:** Is the project maintained? We generally don't accept repositories that haven't been updated in the last 6 months.
3. **Documentation:** Does it have a clear README, API reference, or case study?
4. **No "Marketing Only" Links:** We prefer open-source tools or transparent technical blog posts over pure marketing fluff.

---

## Removal & Deprecation Policy

A resource may be flagged for removal or deprecation when any of the following apply:

1. **Inactivity:** The repository has not received a commit in 6+ months (mirrors the
   Activity criterion in Quality Standards above).
2. **Archived or deleted:** The upstream repository is archived on GitHub or the URL
   returns 404 / has moved without a redirect.
3. **Superseded:** A clearly superior, actively maintained alternative exists and the
   original resource adds no unique production value.
4. **Evidence retracted:** A numeric claim underpinning the listing has been publicly
   disputed or its source withdrawn, and no replacement evidence is available.

**Process:**

- The weekly [discovery_engine](scripts/discovery_engine.py) automatically flags
  listed repos that exceed 180 days without a push, under the "Stale Listed
  Tools" section of the report it posts to the discovery-feed issue.
- A maintainer reviews flagged entries and either (a) confirms the tool is still
  maintained (e.g., stable release cadence) and updates the flag threshold, or
  (b) opens a PR to remove or annotate the entry.
- **Soft deprecation** (preferred for widely referenced tools): add a note inline —
  `(deprecated — use [Replacement](url))` — and keep the entry for historical
  reference. Hard removal is reserved for dead links and archived repos.
- Any community member may open a `removal` issue using the issue template.

---

## How to Contribute

Please follow these steps to propose a change:

### 1. Search First

Before adding a new resource, please check if it is already in the list or if a
similar PR is already open. Also check the [FAQ](FAQ.md) — it explains why some
popular tools (for example, end-user chat platforms) are intentionally not listed.

### 2. Fork and Branch

1. Fork the repository.
2. Create a new branch from `main`:

   ```bash
   git checkout -b add-[resource-name]
   ```

### 3. Formatting Rules

To keep the list clean, please follow the existing format:

- **Alphabetical Order:** Add your resource to the appropriate category in alphabetical order.
- **Link Format** (two-line style — used throughout this repo):

  ```markdown
  - [Resource Name](URL)
    - One or two sentence description. Focus on production relevance. End with a period.
  ```

  Single-sentence descriptions are preferred. Use a second sentence only when the production context
  requires it (e.g., citing a benchmark or explaining an important trade-off).
- **No emoji in list items.** Emoji are reserved for Mermaid diagrams only.
- **No bold inline labels** (`**Use Case:**`, `**Key Insight:**`) inside list bullets — fold the information into prose.
- **Citations:** See the Evidence Tier section below — required for any numeric claim.
- **Last Verified date:** New or substantially edited entries should carry a per-entry review marker — see § 5.

> **Style Notes (intentional deviations from strict `awesome-lint`):**
> This list runs `awesome-lint` as advisory CI, not blocking. The following
> production-grade differentiators intentionally deviate from strict mode:
>
> - Two-line bullet format (vs. single-line) — improves readability for rich descriptions.
> - Sections with decision guides, reference architectures, and trade-offs — contextual content that makes this list useful in practice.
> - Evidence tables with `[3P]`/`[V]`/`[A]` tags — required by this repo's Evidence Tier policy.
> Do not "fix" these by flattening them to strict awesome-lint format.

### 4. Evidence Tier (Required for numeric claims)

If your PR introduces or modifies any numeric claim (latency, recall, precision,
cost reduction, throughput, hallucination rate, etc.), you **must** provide all
four of the following in the PR description:

- **Source URL** — link to the original measurement (vendor doc, paper, blog,
  leaderboard snapshot). Secondary sources that aggregate numbers are not
  sufficient; trace back to the primary source.
- **Date** — when the measurement was published or last refreshed (`YYYY-MM-DD`).
- **Tag** — one of:
  - `[3P]` third-party measured (academic paper, independent benchmark,
    neutral reproduction)
  - `[V]` vendor-stated (vendor's own blog, docs, whitepaper)
  - `[A]` anecdotal (self-reported production case study, engineering talk)
- **Methodology link** (when available) — the benchmark harness, dataset, or
  reproduction script (e.g., ANN-Benchmarks, BEIR runner, VectorDBBench).

Numeric claims that cannot supply all four fields will be moved to
[`benchmarks.md#gaps`](benchmarks.md#9-gaps--not-publicly-measured) or removed
entirely. **We prefer 20 well-cited rows over 80 half-cited ones.**

For non-numeric resource additions (a new tool or framework with no benchmark
claim), the Evidence Tier does not apply — but an Engineering Context note in the
PR is still appreciated.

### 5. Last Verified Date (per-entry review)

Automated freshness checks tell us a repository is still *active* (its
`pushed_at` date is recent). They cannot tell us a maintainer has actually
re-read an entry and confirmed the link still resolves, the description is still
accurate, and the tool is still production-relevant. The **Last Verified** marker
records that human review.

Place an optional HTML comment between the link line and its description:

```markdown
- [Resource Name](URL)
  <!-- verified: 2026-06-25 -->
  - One or two sentence description. ...
```

Rules:

- The date is **ISO 8601** (`YYYY-MM-DD`) — the day you confirmed the entry by hand.
- The comment sits on its own line, indented two spaces, **directly under the link**
  and before the description. It is invisible in the rendered page.
- It is **required for new or substantially edited entries**, and CI enforces it
  (`Entry verified-markers`). Renaming an entry or changing its URL counts as a
  substantial edit, because both rewrite the link line.
- Entries that predate the rule are **grandfathered** — there is no bulk backfill
  requirement, and the weekly audit never reports them. Coverage grows as entries
  are touched.
- A marker is considered stale after **180 days** (matching the 6-month activity rule).
  [`discovery_engine.py`](scripts/discovery_engine.py) reports stale markers in the
  weekly freshness audit, alongside the automated `pushed_at` signal.
- "Verified" means *a human checked the link, description, and production relevance* — it
  complements, and does not replace, the automated activity check.

### 6. Commit and Push

Use a descriptive commit message:

```bash
git commit -m "Add [Resource Name] to [Category Name]"
```

### 7. Open a Pull Request

- Fill out the PR template (if available).
- Explain **why** this resource is "Awesome" and how it helps in a production environment.

---

## CI Checks on Pull Requests

Every PR runs an automated validation suite. Blocking checks must pass before
merge; advisory checks report problems without blocking.

| Check | Enforces | Gate |
| :--- | :--- | :--- |
| `Entry format` | Two-line entry format, description ends with punctuation, marker indentation (§ 3) | Blocking |
| `Entry alphabetical` | Alphabetical order within sections (§ 3) | Blocking |
| `Entry duplicates` | No duplicate names/URLs across all content files (§ 1) | Blocking |
| `Entry verified-markers` | Valid `verified: YYYY-MM-DD` syntax and placement; entries added by the PR must carry one (§ 5) | Blocking |
| `Entry style-bans` | No emoji or bold inline labels in entries (§ 3) | Blocking |
| `Entry evidence-tags` | Numeric claims carry a `[3P]`/`[V]`/`[A]` tag (§ 4) | Blocking |
| `PR body policy` | Checklist ticked; Engineering Context filled when claims are added (§ 4) | Blocking |
| `pytest` / `ruff lint` / `ruff format` | Python tooling quality (only when `scripts/`, `tests/`, or `pyproject.toml` change) | Blocking |
| `Markdown Lint` | markdownlint rules (`.markdownlint-cli2.jsonc`) | Blocking |
| `Links (changed files)` | Liveness of links in changed markdown files | Advisory |
| `awesome-lint` | Upstream awesome-list conventions | Advisory |
| `Area labels` / `Size label` | Automatic PR labeling | Non-gating |

### Safety net on `main`

Fork PRs from first-time contributors sit behind GitHub's "Approve and run
workflows" gate. Merging one without approving its checks means the PR suite
never ran at all — the checks are absent, not failing. `Main Validation` replays
the entry checks and Python tooling against whatever landed on `main`, so a
bypass surfaces instead of passing silently. On failure it opens a
`main-validation` tracking issue and closes it once `main` is green again.

The PR body policy is the one check the safety net cannot replay: a push event
carries no PR description. Approve the workflows on fork PRs so it runs where it
belongs.

Escape hatches (maintainer-reviewed, use sparingly):

- `<!-- no-alphabetical -->` after a heading exempts that section from
  alphabetical ordering (for intentionally curated order).
- `<!-- allow-duplicate -->` on the line directly above an entry allows an
  intentional cross-listing (e.g. README ↔ topic guide).
- The `policy-exempt` label (maintainer-applied) skips the PR body policy.

Run the same checks locally before pushing:

```bash
python scripts/pr_entry_validator.py --check all README.md
```

Pass the files you touched. The diff-scoped rules (new-entry markers, evidence
tags) stay quiet in this mode, so a clean run here means "nothing structurally
wrong", not "the PR checks will pass" — CI compares against the base branch.
Adding `--base-ref` locally reproduces that comparison, but only on a **clean
working tree**: line numbers come from the diff while the files are read from
disk, so uncommitted edits shift them out of alignment and produce phantom
findings.

---

## License

By contributing, you agree that your contributions will be licensed under the
**CC0 1.0 Universal** license of this repository.

---

**Thank you for helping us build the best RAG resource on GitHub!**
