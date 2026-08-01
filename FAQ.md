# FAQ

Frequently asked questions about the scope, selection process, and maintenance
of this list. If your question is not answered here, open a
[Q&A discussion](https://github.com/Yigtwxx/Awesome-RAG-Production/discussions).

---

## Scope & Selection

### Why isn't tool X listed?

Every entry must meet the four [Quality Standards](CONTRIBUTING.md#quality-standards):

1. **Production focus** — it solves a real-world problem like scalability, latency, or reliability.
2. **Activity** — the project has been updated within the last 6 months.
3. **Documentation** — a clear README, API reference, or case study exists.
4. **No "marketing only" links** — open-source tools and transparent technical posts are preferred over marketing fluff.

A tool that does not meet all four is not listed, no matter how popular it is.
If you believe a tool qualifies, see
[How do I propose a new tool?](#how-do-i-propose-a-new-tool)

### Why aren't Dify, Flowise, Open WebUI, or AnythingLLM listed?

They are excellent projects, but they are **end-user applications and low-code
platforms**, while this list focuses on **infrastructure building blocks** for
engineering teams that assemble and operate their own production RAG pipelines —
ingestion, retrieval, evaluation, observability, serving, and so on. The weekly
[discovery feed](.github/DISCOVERY_TRIAGE.md) regularly surfaces these projects
as raw candidates, and they are triaged against this scope rule.

### Which framework or vector database is "best"?

The list deliberately avoids absolute rankings — the answer depends on your
constraints. Start with the
[Decision Guide](README.md#decision-guide-how-to-choose), the per-category
comparison tables, and the
[Reference Architectures](README.md#reference-architectures). Numeric
comparisons live in [benchmarks.md](benchmarks.md) with explicit sources and
evidence tags.

## Contributing

### How do I propose a new tool?

Read [CONTRIBUTING.md](CONTRIBUTING.md), then either open an issue with the
[Add Resource template](https://github.com/Yigtwxx/Awesome-RAG-Production/issues/new?template=add_resource.yml)
or submit a PR that follows the two-line bullet format and alphabetical order.
Explain the production problem the tool solves — that is the main acceptance
criterion.

### Can I submit my own project?

Yes. Self-submissions are welcome and are evaluated against exactly the same
[Quality Standards](CONTRIBUTING.md#quality-standards) as any other entry.
Please disclose your affiliation in the issue or PR description.

### Why was my issue or PR marked stale?

Issues and PRs with no activity for 60 days are labeled stale and closed 7 days
later by automation. Leaving any comment resets the timer. If your contribution
was closed and is still relevant, feel free to reopen it or open a new one.

## Evidence & Benchmarks

### What do the [3P], [V], and [A] tags mean?

Every numeric claim in this repository carries one of three evidence tags:

- `[3P]` — third-party measured (academic paper, independent benchmark, neutral reproduction).
- `[V]` — vendor-stated (the vendor's own blog, docs, or whitepaper).
- `[A]` — anecdotal (self-reported production case study, engineering talk).

The full policy is described in the
[Evidence Tier section of CONTRIBUTING.md](CONTRIBUTING.md#4-evidence-tier-required-for-numeric-claims).

### Why was a number I added removed or hedged?

Numeric claims must supply all four Evidence Tier fields: source URL, date,
tag, and (when available) a methodology link. Claims that cannot supply them
are moved to
[benchmarks.md § Gaps](benchmarks.md#9-gaps--not-publicly-measured) or removed
entirely. We prefer 20 well-cited rows over 80 half-cited ones.

## Maintenance & Style

### When are tools removed from the list?

Per the [Removal & Deprecation Policy](CONTRIBUTING.md#removal--deprecation-policy):
inactivity for 6+ months, an archived or deleted upstream repository, a clearly
superior replacement, or retracted evidence. The weekly
[discovery engine](scripts/discovery_engine.py) automatically flags listed
repositories with no push in 180+ days. Widely referenced tools are
soft-deprecated (annotated inline) rather than deleted; hard removal is
reserved for dead links and archived repos.

### Why does this list deviate from strict awesome-lint?

Deliberately. The two-line bullet format, decision guides, reference
architectures, and evidence tables are the production-grade differentiators of
this list, and they deviate from strict `awesome-lint` formatting. The linter
runs as advisory (non-blocking) CI for that reason — see the style notes in
[CONTRIBUTING.md](CONTRIBUTING.md#3-formatting-rules).

### Is the list available in languages other than English?

No — English only, by design. A single source language keeps every entry,
benchmark citation, and policy document in one reviewable place; translations
drift out of date quickly in a list that changes weekly. Translation PRs are
therefore not accepted.
