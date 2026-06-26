# Changelog

Notable changes to this list, grouped by month (newest first). The format is
adapted from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); as a
curated list, this repository does not use semantic versions. Planned work is
tracked in [ROADMAP.md](ROADMAP.md).

## 2026-06

### Added

- New tools: Omnigraph (Vector Databases), psql_bm25s (Retrieval & Reranking), KB Arena (Evaluation & Benchmarking), and Future AGI (Observability & Tracing).
- PaddleOCR added to Data Ingestion & Parsing (Apache-2.0 OCR / document-parsing toolkit).
- RAG Made Simple added to the RAG section of the recommended books list ([books.md](books.md)).
- FAQ ([FAQ.md](FAQ.md)) answering the most common scope, evidence, and contribution questions.
- This changelog ([CHANGELOG.md](CHANGELOG.md)) and a public roadmap ([ROADMAP.md](ROADMAP.md)).
- Internal repository audit (REPO-ANALIZ.md) with a re-scored 2026-06-12 review.
- Per-entry "last verified" convention (CONTRIBUTING § 5): an optional `verified: YYYY-MM-DD` marker for the last human review, audited weekly by `discovery_engine.py`, with the engine's first unit tests.
- Live documentation site (MkDocs Material) at <https://yigtwxx.github.io/awesome-rag-production/>, auto-deployed from `main` via the `docs` workflow, with build-time markdown staging (`docs-site/stage_docs.sh`), a per-page SEO meta-description hook, and a GitHub social preview card.
- Discovery engine (`scripts/discovery_engine.py`): a weekly freshness audit that flags listed tools with no push in 180+ days, benchmark citations older than 365 days, and stale per-entry verified dates, wired into the `discovery` workflow.
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
