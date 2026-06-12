# Roadmap

Planned improvements to this list and its automation. This is a living
document: items are unordered within each horizon, carry no date commitments,
and may change as the ecosystem evolves. Contributions toward any item are
welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Completed work is recorded
in the [Changelog](CHANGELOG.md).

## Near-term

- Diagnose and restore the weekly discovery output cadence — `.github/PROPOSED_UPDATES.md` was last regenerated on 2026-05-11 despite the weekly schedule.
- Triage the current discovery candidates with explicit accept / reject notes against the production-infrastructure scope (see the [FAQ](FAQ.md)).
- Add a CI check that validates every `benchmarks.md` row against the six-field schema (Metric, Value, Tag, Source, Date, Methodology) and a valid evidence tag.

## Mid-term

- Unit tests for `scripts/discovery_engine.py` (URL and date parsing, markdown generation).
- A per-entry "last verified" convention so human review dates are visible alongside automated freshness flags.
- Extend the decision tree beyond frameworks and vector databases to embedding selection, reranking, and chunking strategy.

## Longer-term

- A postmortem / failure case studies section, cross-linked with [rag-pitfalls.md](rag-pitfalls.md).
- Evaluate splitting the largest README sections (for example, Agentic RAG and Multimodal RAG) into side documents as they grow.

## Out of Scope

These are deliberate decisions, not gaps:

- **Translations / i18n** — the list is maintained in English as a single source of truth; see the [FAQ](FAQ.md#is-the-list-available-in-languages-other-than-english).
- **End-user chat platforms and low-code builders** — see the [FAQ](FAQ.md#why-arent-dify-flowise-open-webui-or-anythingllm-listed) for the scope rationale.
- **Absolute "best tool" rankings** — the list provides decision guides and evidence, not verdicts.
