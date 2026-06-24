# Vector Database Comparison for RAG

Choosing a vector database is one of the few RAG decisions that is expensive to
reverse — once millions of embeddings are indexed and your filtering, sharding,
and ops are built around one engine, migrating is a project, not a config change.
This guide compares the leading vector databases for production
Retrieval-Augmented Generation along the dimensions that actually drive the
choice: scale, deployment model, filtering, hybrid search, and operational cost.

> This is the deep-dive companion to the
> [Vector Databases section in the main list](README.md#vector-databases).
> Numeric recall/latency claims live in
> [benchmarks.md §1](benchmarks.md#1-vector-databases) with source citations —
> this page stays qualitative on purpose, because published benchmarks are
> hardware- and workload-dependent and rarely transfer to your cluster.

---

## TL;DR — Which one should I pick?

- **Already running PostgreSQL?** Start with **pgvector**. One fewer system to
  operate beats marginal recall gains until you outgrow it.
- **Strong metadata filtering under ~50M vectors?** **Qdrant** — excellent
  payload filtering and a generous free tier.
- **Scaling toward billions of vectors?** **Milvus** — built for distributed,
  horizontally-scaled workloads.
- **Want zero ops / serverless?** **Pinecone** — fully managed, no infrastructure
  to run.
- **Hybrid (vector + keyword) as a first-class citizen?** **Weaviate** or
  **Vespa**.
- **Local prototyping or embedded/multimodal?** **Chroma** or **LanceDB**.

There is no single "best" vector database — match it to your constraints, not to
a leaderboard.

---

## Decision framework

Work through these four questions in order. The first one that gives a hard
constraint usually decides the shortlist.

### 1. What scale are you indexing?

| Vector count | Reasonable choices | Notes |
| :--- | :--- | :--- |
| < 1M | pgvector, Chroma, LanceDB | Any engine works; optimize for developer velocity. |
| 1M–50M | Qdrant, pgvector, Weaviate, Pinecone | Filtering quality and ops burden start to matter. |
| 50M–500M | Milvus, Pinecone, Vespa, Qdrant (clustered) | Distributed indexing and memory budgeting become central. |
| 500M–billions | Milvus, Vespa | Horizontal sharding and disk-backed indexes are required. |

Vector count is not the same as RAM cost: an HNSW index keeps graph links in
memory, so dimensionality and `M`/`ef_construction` settings drive your real
footprint. Engines with quantization (scalar/product) or disk-backed indexes
(Milvus DiskANN, Qdrant on-disk) change this math substantially.

### 2. Managed or self-hosted?

| | Managed (Pinecone, Qdrant Cloud, Weaviate Cloud, Zilliz) | Self-hosted (pgvector, Milvus, Qdrant, Chroma, Vespa) |
| :--- | :--- | :--- |
| **Ops burden** | Near-zero | You own upgrades, backups, scaling |
| **Data sovereignty** | Data leaves your VPC (unless BYOC) | Full control |
| **Cost shape** | Predictable opex, scales with usage | Capex/infra + engineering time |
| **SLA** | Provider-backed (~99.9%, see [benchmarks.md §7](benchmarks.md#7-reliability--sla)) | Operator-managed; no external SLA |

If you have no dedicated infra/SRE capacity, a managed service is almost always
cheaper once engineering time is priced in — until you reach a scale where
per-vector pricing dominates.

### 3. How important is filtering and hybrid search?

Production RAG almost never does pure vector search. You filter by tenant,
recency, ACL, or document type, and you usually combine dense vectors with
keyword (BM25) retrieval. These needs vary by engine:

| Capability | Strong support |
| :--- | :--- |
| Rich payload / metadata filtering | Qdrant, Weaviate, Milvus, Vespa |
| Native hybrid (dense + sparse/BM25) | Weaviate, Vespa, Qdrant, Milvus |
| SQL-native filtering alongside vectors | pgvector (full SQL `WHERE`) |
| Graph + vector + BM25 in one runtime | Omnigraph, Vespa |

Pre-filtering (filter then search) vs. post-filtering (search then filter)
behaves very differently under selective filters — verify which your engine does,
because aggressive post-filtering can silently collapse recall.

### 4. What does your team already operate?

The cheapest database to run is the one your team already knows. **pgvector**
inside an existing PostgreSQL fleet inherits your backups, replication,
monitoring, and access control for free. That operational leverage frequently
outweighs a few points of recall — at least until scale forces a dedicated
engine.

---

## Comparison at a glance

| Engine | Sweet spot | Deployment | Hybrid search | Filtering | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [pgvector](https://github.com/pgvector/pgvector) | Existing PostgreSQL shops | Self-host / managed Postgres | Via extensions / SQL | Full SQL `WHERE` | — |
| [Qdrant](https://github.com/qdrant/qdrant) | < 50M, filter-heavy | Self-host / Cloud | Native | Excellent payload filters | [\[V\]](benchmarks.md#1-vector-databases) [\[3P\]](benchmarks.md#1-vector-databases) |
| [Milvus](https://github.com/milvus-io/milvus) | Billions of vectors | Self-host / Zilliz Cloud | Native | Strong | [\[V\]](benchmarks.md#1-vector-databases) |
| [Pinecone](https://www.pinecone.io/) | Zero-ops serverless | Managed only | Sparse-dense | Metadata filters | — |
| [Weaviate](https://github.com/weaviate/weaviate) | Hybrid search | Self-host / Cloud | Native (first-class) | Strong | — |
| [Vespa](https://github.com/vespa-engine/vespa) | Web-scale hybrid serving | Self-host / Cloud | Native (first-class) | Strong + ranking | — |
| [Chroma](https://github.com/chroma-core/chroma) | Local / dev / mid-scale | Self-host / embedded | Basic | Metadata filters | — |
| [LanceDB](https://github.com/lancedb/lancedb) | Embedded & multimodal | Embedded / serverless | Basic | Metadata filters | — |

See the [main Vector Databases table](README.md#vector-databases) for one-line
strengths, and [benchmarks.md §1](benchmarks.md#1-vector-databases) for the
recall/latency numbers behind the `[V]`/`[3P]` tags.

---

## Don't trust a benchmark you didn't run

Every vendor publishes a benchmark where they win. Parameter choices
(`ef_construction`, `ef_search`, segment count, quantization) are rarely optimal
for the competitors in a vendor-run comparison — this is exactly why
[benchmarks.md](benchmarks.md#8-methodology-disputes) tags those rows `[V]`
(vendor-stated).

Before committing, run an apples-to-apples test on **your** data and hardware:

- [ANN-Benchmarks](https://ann-benchmarks.com/) — standardized, reproducible ANN
  comparisons across engines (`[3P]`).
- [VectorDBBench](https://github.com/zilliztech/VectorDBBench) — end-to-end
  database benchmark harness (cost, recall, latency, filtering).

Hold recall fixed (e.g. recall@10 ≥ 0.95) and compare latency and cost at *that*
recall — comparing raw latency at different recall levels is meaningless.

---

## Cost: the part nobody publishes cleanly

Comparable `$/M-vector` pricing across managed providers effectively does not
exist publicly — vendors price on different units (pods vs. compute vs. storage),
so direct comparison requires a sizing quote. See
[benchmarks.md §9 (Gaps)](benchmarks.md#9-gaps--not-publicly-measured) for why
this number is treated as unmeasured here.

Practical cost levers, in rough order of impact:

1. **Quantization** (scalar/product/binary) — can cut memory several-fold at a
   tunable recall cost; test the recall hit on your data.
2. **Dimensionality** — smaller embeddings (or Matryoshka truncation) shrink both
   storage and index RAM; see
   [embedding-model-selection.md](embedding-model-selection.md).
3. **Disk-backed indexes** (DiskANN, on-disk HNSW) — trade latency for far cheaper
   storage of cold vectors.
4. **Index parameters** — higher `M`/`ef_construction` improves recall but
   inflates memory and build time.

---

## Migration & versioning

Because switching engines is costly, treat your index as a versioned artifact
from day one. Upgrading an embedding model (dimension/tokenizer change) forces a
full re-index, and schema changes reshape chunk boundaries — both are high-risk
without rollback. See
[Data & Index Versioning](README.md#data--index-versioning) for tools (DVC,
lakeFS, Pachyderm, Oxen) that make re-indexing reversible.

---

## Selection checklist

Before you commit to a vector database, confirm:

- ✅ It handles your **target scale** with headroom (and you've priced the RAM).
- ✅ Its **filtering model** (pre- vs post-filter) preserves recall under your
  real filters.
- ✅ **Hybrid search** is supported if your queries need keyword precision.
- ✅ The **deployment model** matches your ops capacity and data-sovereignty needs.
- ✅ You've benchmarked **your** data with [ANN-Benchmarks](https://ann-benchmarks.com/)
  or [VectorDBBench](https://github.com/zilliztech/VectorDBBench) at fixed recall.
- ✅ A **re-index / rollback** path exists for embedding-model upgrades.
- ✅ Backups, monitoring, and access control are covered (managed) or planned
  (self-hosted).

---

## Further reading

- [Vector Databases — main list](README.md#vector-databases)
- [Benchmarks & Evidence §1 — recall, latency, SLA](benchmarks.md#1-vector-databases)
- [Embedding Model Selection](embedding-model-selection.md) — dimensionality
  drives your index cost
- [Chunking Strategies](chunking-strategies.md) — what you store before you index
- [Common RAG Pitfalls — Retrieval Strategy](rag-pitfalls.md#retrieval-strategy)

([back to main resource](README.md))
