# Changelog

Notable changes to this list, grouped by month (newest first). The format is
adapted from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); as a
curated list, this repository does not use semantic versions. Planned work is
tracked in [ROADMAP.md](ROADMAP.md).

## 2026-08

### Added

- Safety net for the CI bypass: a new `main-validation` workflow replays the
  entry checks and Python tooling against whatever lands on `main`. Fork PRs
  from first-time contributors sit behind "Approve and run workflows", so
  merging one without approving its checks meant the PR suite never ran at
  all — the checks were absent, not failing. Failures now open a
  `main-validation` tracking issue that closes itself once `main` is green.
- Broken links have an owner again: the weekly link checker renders its
  findings through `scripts/link_report.py` into a long-lived `broken-links`
  issue, fingerprinted so an unchanged set refreshes the body instead of
  commenting every Monday. Previously the results went only to a job summary.
- Shared `.github/scripts/tracking-issue.sh` helper backing all three
  tracking issues. It selects the lowest-numbered bot-authored issue with a
  matching title, so a stray issue can no longer silently take over a feed.
- `.github/DISCOVERY_TRIAGE.md` — durable accept/reject record for discovery
  candidates, seeding the `OUT_OF_SCOPE_REPOS` denylist.
- New entries: KServe, SkyPilot, Triton Inference Server (Deployment &
  Serving), OpenDataLoader PDF (Data Ingestion), PageIndex (Retrieval).
- Root `.gitattributes` pinning `*.sh` / `*.yml` to LF, so a CRLF checkout on
  Windows cannot break a script on the Linux runners.

### Fixed

- **The benchmark freshness check never matched anything.** Its regex required
  a full `YYYY-MM-DD`, but every date in `benchmarks.md` is written `2024` or
  `2022-12`, so it scanned 36 table rows, matched zero, and reported "all
  benchmark rows are current" every week. It now reads each table's Date
  column (located from the header, so an arXiv id in a Source cell is never
  mistaken for a date) and accepts partial dates, resolving them to the end of
  the period. A `(paper)` marker exempts fixed publication dates.
- Weekly discovery could lose an entire run: if every GitHub API request
  failed, `check_listed_tool_freshness` raised `NameError` on an unbound
  `response`, which propagated out and skipped the report-posting step
  entirely. Fixed with a sentinel, plus `if: always()` on the posting step.
- `check_benchmark_freshness` did not create `.github/` before writing, so its
  report was silently lost whenever it ran before the discovery step.
- Dead and misdirected links: `chonkie` (moved to `feyninc/chonkie`),
  LlamaIndex `KnowledgeGraphIndex` (superseded by `PropertyGraphIndex`),
  Pinecone SLA (99.9% → 99.95%, new URL), the Transformers book, and the
  Anthropic prompt-caching docs (moved to `platform.claude.com`).
- Cohere embed-v4 was listed with a 512-token context window — that is the v3
  figure; v4 is a 128K-token multimodal model. Corrected in both the README
  table and `embedding-model-selection.md`.
- OpenAI Assistants API sunsets 2026-08-26; the entry now points at the
  Responses API migration guide.
- Stale-upstream notes for Pachyderm, ARES, RAGatouille, Byaldi, and GPTCache;
  Prometheus and G-Eval now point at their maintained successors.

### Changed

- `<!-- verified: YYYY-MM-DD -->` is now **required** on entries a PR adds, and
  CI enforces it. Existing marker-less entries are grandfathered, and the
  weekly audit no longer reports them — that count never moved and drowned out
  the findings that needed action.
- `.github/PROPOSED_UPDATES.md` is no longer tracked. It was both committed and
  gitignored, so it stayed frozen at a 2026-05-11 snapshot and made the roadmap
  chase a discovery outage that was not happening.

## 2026-07

### Added

- PR validation suite: every pull request now runs ~15 automated checks
  (OpenClaw-inspired). A new `pr-validation` workflow fans out
  `scripts/pr_entry_validator.py` across six blocking entry checks (format,
  alphabetical order, duplicates, verified markers, style bans, evidence
  tags), validates the PR body against the template policy, link-checks the
  changed files (advisory), and runs `pytest`/`ruff` when Python tooling
  changes. A `pr-labeler` workflow adds `area/*` and `size/*` labels.
- Shared entry-grammar module (`scripts/entry_patterns.py`) reused by the
  discovery engine and the PR validator, plus unit tests for every check.
- Shared `lychee.toml` so the weekly link checker and the per-PR link check
  use one configuration; `pyproject.toml` with `ruff` and `pytest` settings.
- CONTRIBUTING: new "CI Checks on Pull Requests" section documenting each
  check, its gate, and the `<!-- no-alphabetical -->` /
  `<!-- allow-duplicate -->` escape hatches (now marking intentionally
  curated sections and cross-listings).

### Fixed

- Evidence hygiene: reworded two unsourced numeric claims (ARES, PrivateGPT)
  and tagged the managed-SLA figure in `vector-database-comparison.md` as
  vendor-stated, per the Evidence Tier policy.

## 2026-06

### Added

- New tools: Omnigraph (Vector Databases), psql_bm25s (Retrieval & Reranking), KB Arena (Evaluation & Benchmarking), and Future AGI (Observability & Tracing).
- PaddleOCR added to Data Ingestion & Parsing (Apache-2.0 OCR / document-parsing toolkit).
- RAG Made Simple added to the RAG section of the recommended books list ([books.md](books.md)).
- FAQ ([FAQ.md](FAQ.md)) answering the most common scope, evidence, and contribution questions.
- This changelog ([CHANGELOG.md](CHANGELOG.md)) and a public roadmap ([ROADMAP.md](ROADMAP.md)).
- Internal repository audit (REPO-ANALIZ.md) with a re-scored 2026-06-12 review.
- Per-entry "last verified" convention (CONTRIBUTING § 5): an optional `verified: YYYY-MM-DD` marker for the last human review, audited weekly by `discovery_engine.py`, with the engine's first unit tests.
- Live documentation site (MkDocs Material) at
  <https://yigtwxx.github.io/awesome-rag-production/>, auto-deployed from `main` via
  the `docs` workflow, with build-time markdown staging (`docs-site/stage_docs.sh`), a
  per-page SEO meta-description hook, and a GitHub social preview card.
- Discovery engine (`scripts/discovery_engine.py`): a weekly freshness audit that flags
  listed tools with no push in 180+ days, benchmark citations older than 365 days, and
  stale per-entry verified dates, wired into the `discovery` workflow.
- New decision guide: `vector-database-comparison.md`, covering scale, filtering, hybrid search, and cost trade-offs.
- README: production inclusion criteria and quick-start decision guides.

### Removed

- A short-lived `stale-link-audit` workflow (added 2026-06-01, removed 2026-06-09); weekly link checking remains covered by the `link-check` workflow.

## 2026-05

### Added

- `benchmarks.md` with the `[3P]` / `[V]` / `[A]` evidence-tag system, a Methodology Disputes section, and an explicit Gaps section.
- Evidence Tier policy in CONTRIBUTING.md — numeric claims now require a source URL, date, tag, and methodology link.
- Removal & Deprecation Policy in CONTRIBUTING.md.
- README sections: Embedding Fine-tuning, Data & Index Versioning, FinOps & Cost Management, Agent Memory & Stateful Context, Structured & SQL RAG, and Tutorials & Hands-on Code.
- Discovery engine freshness audit: flags listed tools with no push in 180+ days and benchmark citations older than 365 days.
- Multimodal RAG and Caching & Performance sections.
- Domain benchmark suites (legal, medical, financial) in datasets.md.
- New tools: DSPy, Crawl4AI, Docling, Vespa, TruLens, Opik.
- CI status badges (Markdown Lint, Link Check, Weekly Discovery) plus welcome and stale automation workflows.
- Dependabot configuration for GitHub Actions and pip dependencies.

### Fixed

- Two weekly workflow failures; bumped `actions/setup-python` from 5.3.0 to 6.2.0.

## 2026-04

### Added

- Weekly automated discovery workflow (trending RAG repositories via the GitHub API).
- Must-watch production talks in showcase.md.
- Dedicated RAG section in the recommended books list.

### Changed

- Repository-wide style standardization: removed decorative emojis, simplified markdown styling, and added the pull request template.
- Migrated linting to `markdownlint-cli2` with a shared configuration.

### Fixed

- Repaired redirected and broken URLs; hardened the link-checker configuration with retries and exclusions.

## 2026-02

### Added

- Agentset added to Frameworks.

## 2026-01

### Added

- `rag-pitfalls.md` — anti-patterns and a production checklist.
- Agentic RAG section, Real-World Case Studies, LLM-as-Judge evaluation, and the Framework Comparison table.

### Changed

- SEO-optimized README introduction; awesome-list standardization (alphabetized books, structure fixes).
- Link-check workflow improvements: retry logic and exclusions for bot-protected domains.

### Fixed

- Removed or replaced a large batch of broken resource links.

## 2025-12

### Added

- Initial release: curated README across the core categories, CONTRIBUTING.md, SECURITY.md, and the first version of the discovery engine with its weekly workflow.
- books.md, blogs.md, and the Contributor Covenant Code of Conduct.
- datasets.md and showcase.md.
- Markdown lint workflow and issue / discussion templates.
