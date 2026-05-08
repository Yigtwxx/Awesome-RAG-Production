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

## How to Contribute

Please follow these steps to propose a change:

### 1. Search First

Before adding a new resource, please check if it is already in the list or if a
similar PR is already open.

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

> **Style Notes (intentional deviations from strict `awesome-lint`):**
> This list runs `awesome-lint` as advisory CI, not blocking. The following
> production-grade differentiators intentionally deviate from strict mode:
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

### 5. Commit and Push

Use a descriptive commit message:

```bash
git commit -m "Add [Resource Name] to [Category Name]"
```

### 6. Open a Pull Request

- Fill out the PR template (if available).
- Explain **why** this resource is "Awesome" and how it helps in a production environment.

---

## License

By contributing, you agree that your contributions will be licensed under the
**CC0 1.0 Universal** license of this repository.

---

**Thank you for helping us build the best RAG resource on GitHub!**
