# Roadmap

Planned improvements to this list and its automation. This is a living
document: items are unordered within each horizon, carry no date commitments,
and may change as the ecosystem evolves. Contributions toward any item are
welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Completed work is recorded
in the [Changelog](CHANGELOG.md).

## Near-term

- Re-verify the benchmark rows the weekly audit still flags as stale — the vendor
  figures in [§1 Vector Databases](benchmarks.md#1-vector-databases),
  [§4 Caching](benchmarks.md#4-caching-prompt--semantic), and
  [§7 Reliability / SLA](benchmarks.md#7-reliability--sla) predate the current
  365-day window and their sources have not been independently re-checked.
- Add a CI check that validates every `benchmarks.md` row against the six-field schema (Metric, Value, Tag, Source, Date, Methodology) and a valid evidence tag.
- Strengthen the thinnest sections — Structured & SQL RAG, FinOps & Cost Management, Tutorials, and Real-World Case Studies each carry only two or three entries.

## Mid-term

- Unit tests for `scripts/discovery_engine.py` covering URL parsing and discovery markdown generation (the verified-date, benchmark-freshness, and rate-limit paths are now tested).
- Extend the decision tree beyond frameworks and vector databases to embedding selection, reranking, and chunking strategy.

## Longer-term

- A postmortem / failure case studies section, cross-linked with [rag-pitfalls.md](rag-pitfalls.md).
- Evaluate splitting the largest README sections (for example, Agentic RAG and Multimodal RAG) into side documents as they grow.

## Out of Scope

These are deliberate decisions, not gaps:

- **Translations / i18n** — the list is maintained in English as a single source of truth; see the [FAQ](FAQ.md#is-the-list-available-in-languages-other-than-english).
- **End-user chat platforms and low-code builders** — see the [FAQ](FAQ.md#why-arent-dify-flowise-open-webui-or-anythingllm-listed) for the scope rationale.
- **Absolute "best tool" rankings** — the list provides decision guides and evidence, not verdicts.
