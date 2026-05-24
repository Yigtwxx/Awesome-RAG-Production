# Benchmarks & Evidence

> Publicly citable measurements backing numeric claims in
> [README.md](README.md) and [rag-pitfalls.md](rag-pitfalls.md).
>
> **Evidence tags** — every row carries exactly one:
>
> | Tag | Meaning |
> | :--- | :--- |
> | **\[3P\]** | Third-party measured — academic paper, independent benchmark, neutral reproduction |
> | **\[V\]** | Vendor-stated — vendor's own blog, docs, or whitepaper |
> | **\[A\]** | Anecdotal — production case-study self-report (engineering blog, talk) |
>
> **Reading rule:** A `[V]` row standing alone without a corresponding `[3P]`
> row for the same metric is a *gap* (see [§ Gaps](#9-gaps--not-publicly-measured)),
> not independent evidence.
>
> **Methodology note:** Benchmark numbers are always hardware- and workload-dependent.
> Row values are starting points, not guarantees for your cluster.
>
> *Last reviewed: 2026-05-08*

---

## How to read this file

Each row provides: **Metric → Value → Tag → Source → Date → Methodology**. All
six fields must be present for a row to appear here; numbers with fewer fields go
to [§ Gaps](#9-gaps--not-publicly-measured). "Date" is the publication or last-refresh
date of the cited source, not this file's date. Where sources are vendor-published
but no independent reproduction exists, the `[V]` tag is the disclosure mechanism.

---

## 1. Vector Databases

### 1a. Recall & Latency (single-node HNSW)

| System | Dataset | Recall@10 | p99 Latency | Tag | Source | Date | Methodology |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Qdrant | gist-960-euclidean | 0.990 | ~1 ms (RPS-optimised) | \[V\] | [qdrant.tech/benchmarks](https://qdrant.tech/benchmarks/) | 2024 | [Benchmark FAQ](https://qdrant.tech/benchmarks/benchmark-faq/) — open-source, reproducible |
| Qdrant | dbpedia-openai-1M-1536-angular | 0.990 | ~2 ms | \[V\] | [qdrant.tech/benchmarks](https://qdrant.tech/benchmarks/) | 2024 | Same as above |
| Milvus | ANN benchmarks (SIFT-128) | ~0.995 | varies by index | \[V\] | [milvus.io/docs/benchmark.md](https://milvus.io/docs/benchmark.md) | 2024 | VectorDBBench open harness |
| All major systems | SIFT-1M | 0.95–0.99 | 1–20 ms (HNSW) | \[3P\] | [ann-benchmarks.com](https://ann-benchmarks.com/) | 2024 | [github.com/erikbern/ann-benchmarks](https://github.com/erikbern/ann-benchmarks) — standardized, reproducible |

**Note:** Both the Qdrant and Milvus rows above are **vendor-published**
benchmarks. For independent reproduction, use
[ANN-Benchmarks](https://ann-benchmarks.com/). Recall@10 depends heavily on HNSW
`ef_search`; tuning for throughput vs. recall is a production trade-off, not a
fixed property of the system.

### 1b. Scale & Cost

Publicly available cost-at-scale data is sparse. Most cloud vector database
providers do not publish $/M-vectors directly; contact vendors for sizing quotes.
See [§ Gaps](#9-gaps--not-publicly-measured) for details.

---

## 2. Embeddings & Retrieval

### 2a. MTEB Leaderboard (English retrieval, snapshot)

The [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) \[3P\] is
the canonical benchmark for text embedding models. Scores below are from the
**Retrieval** category only (nDCG@10 average across BEIR datasets) — overall MTEB
averages include tasks irrelevant to RAG retrieval.

| Model | Retrieval nDCG@10 | Tag | Source | Snapshot Date |
| :--- | :--- | :--- | :--- | :--- |
| Gemini Embedding 001 | 67.71 | \[3P\] | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | 2025 |
| Cohere embed-v4 | 65.2 | \[3P\] | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | 2025 |
| OpenAI text-embedding-3-large | 64.6 | \[3P\] | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | 2025 |
| BGE-M3 (BAAI) | 63.0 | \[3P\] | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | 2025 |

**Freshness warning:** MTEB scores change weekly as new models are submitted.
Always verify current rankings at the live leaderboard before making decisions.

**MTEB caveat:** See [§ Methodology Disputes](#8-methodology-disputes) for known
contamination and evaluation concerns.

---

## 3. Reranking

Cross-encoder rerankers (e.g., Cohere Rerank, BGE-Reranker, Jina Rerank)
significantly outperform bi-encoder retrievers on out-of-domain benchmarks. The
evidence for this is robust:

| Comparison | Improvement | Tag | Source | Date | Methodology |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Cross-encoder vs bi-encoder (BEIR zero-shot, nDCG@10) | +4 points average | \[3P\] | [arxiv.org/abs/2212.06121](https://arxiv.org/abs/2212.06121) | 2022-12 | 15 BEIR datasets, zero-shot |
| Cross-encoder vs bi-encoder (MS MARCO, nDCG@10) | up to +10 points | \[3P\] | [arxiv.org/abs/2212.06121](https://arxiv.org/abs/2212.06121) | 2022-12 | In-domain, full fine-tune |
| ColBERT + RoBERTa cross-encoder (MS MARCO DEV-SMALL, MRR@10) | 0.863 | \[3P\] | [arxiv.org/abs/2212.06121](https://arxiv.org/abs/2212.06121) | 2022-12 | Combining late-interaction + cross-encoder |

**Domain variability:** Reranking gains vary substantially by domain (technical
docs, legal, medical, conversational). The "4 nDCG@10 points" figure is an
average over heterogeneous BEIR datasets. Some domains show larger gains; some
smaller. No single number applies universally — evaluate on your own corpus
(using datasets from [datasets.md](datasets.md)).

---

## 4. Caching (Prompt + Semantic)

### 4a. Provider-side Prompt Caching

| Provider | Metric | Value | Tag | Source | Date | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Anthropic (Claude) | Input token cost on cache hit | 10% of standard price (−90%) | \[V\] | [Anthropic Prompt Caching Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) | 2024 (active doc) | Cache TTL: 5 min. Requires `cache_control` breakpoint in request |
| Anthropic (Claude) | Latency reduction on cache hit | Up to −85% | \[V\] | [Anthropic Prompt Caching Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) | 2024 (active doc) | Long-context prompts; figures are upper-bound under ideal conditions |
| OpenAI (GPT-4o / o-series) | Input token price on cache hit | 50% discount | \[V\] | [OpenAI Prompt Caching](https://openai.com/index/api-prompt-caching/) | 2024-10 | Automatic, no code changes; min. 1,024 cached tokens |
| OpenAI (GPT-4o / o-series) | Latency reduction on cache hit | Up to −80% | \[V\] | [OpenAI Prompt Caching Docs](https://platform.openai.com/docs/guides/prompt-caching) | 2024-10 | Input-token processing overhead removed |

**All four rows above are vendor-stated `[V]`.** No independent third-party
reproduction of these caching figures exists in the public literature at time of
writing. They represent what the provider claims under optimal conditions (high
cache-hit rate, long shared prefix). See
[§ Gaps](#9-gaps--not-publicly-measured).

### 4b. Semantic Caching (Application Layer)

No comparable publicly available benchmarks exist for GPTCache, LangChain Cache,
LiteLLM Cache, or RedisVL Semantic Cache with reproducible datasets and
methodology. Effectiveness depends heavily on query repetition rate, similarity
threshold tuning, and domain — figures quoted by vendors are illustrative, not
transferable. See [§ Gaps](#9-gaps--not-publicly-measured).

---

## 5. LLM Serving

| System | Metric | Value | Tag | Source | Date | Hardware / Config |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| vLLM (PagedAttention) | Throughput vs FasterTransformer + Orca | 2–4× improvement | \[3P\] | [arxiv.org/abs/2309.06180](https://arxiv.org/abs/2309.06180) (SOSP 2023) | 2023-09 | A100 80GB; same latency SLO; LLaMA / OPT models |
| vLLM (PagedAttention) | KV cache memory waste | <4% (vs 60–80% in prior systems) | \[3P\] | [arxiv.org/abs/2309.06180](https://arxiv.org/abs/2309.06180) (SOSP 2023) | 2023-09 | OS virtual memory analogy; all measured model sizes |

**Note:** These numbers are from the original 2023 publication. vLLM has evolved
substantially; for current benchmarks run `vllm/benchmarks/` against your own
hardware. SGLang and TGI have also published competing numbers under different
workloads.

---

## 6. End-to-End Case Studies

These are self-reported production results — tagged `[A]` (anecdotal). They have
not been independently reproduced or peer-reviewed. Treat them as directional
evidence, not exact benchmarks.

| Company | System | Reported Result | Tag | Source | Date |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Discord | Trillion-message search (ANN + Rust + ScyllaDB) | ANN search at trillions-of-messages scale | \[A\] | [Discord Engineering Blog](https://discord.com/blog/how-discord-stores-trillions-of-messages) | 2023 |
| LinkedIn | Conversational job search (in-house VDB + BERT) | Member-personalized recommendations at LinkedIn scale | \[A\] | [LinkedIn Engineering Blog](https://engineering.linkedin.com/blog) | Ongoing — no specific post with RAG metrics confirmed |

**Important caveat:** The Shopify "18% → 4% hallucination reduction" figure has been moved to
[§ Gaps](#9-gaps--not-publicly-measured) as no public Shopify Engineering post
confirming this specific figure was found. If you have the original source, please open a PR.

---

## 7. Reliability / SLA

| Provider | Published SLA | Tag | Source | Date |
| :--- | :--- | :--- | :--- | :--- |
| Pinecone | 99.9% uptime (Serverless) | \[V\] | [Pinecone SLA](https://www.pinecone.io/sla/) | 2024 |
| Weaviate Cloud | 99.9% uptime | \[V\] | [Weaviate SLA](https://weaviate.io/service/sla) | 2024 |
| Qdrant Cloud | 99.9% uptime | \[V\] | [Qdrant Cloud SLA](https://qdrant.tech/cloud/) | 2024 |

Self-hosted Milvus, Chroma, pgvector, and vLLM have no provider SLA — reliability
is entirely operator-managed. RTO/RPO figures are not publicly disclosed by any
major provider.

---

## 8. Methodology Disputes

Being aware of these disputes is itself a production skill.

**MTEB contamination.** Several models on the MTEB leaderboard have been found to
train on MTEB evaluation data, inflating scores. Use MTEB for directional
comparison; validate on a held-out domain split from your own corpus before
committing to a model. See [embeddings-benchmark/mteb#issues](https://github.com/embeddings-benchmark/mteb/issues)
for ongoing discussion.

**Vendor-run benchmarks.** Qdrant, Milvus, and Weaviate each publish benchmarks
comparing themselves favorably. Parameter choices (HNSW `ef_construction`,
`ef_search`, segment count) are not always optimal for competing systems. The
`[V]` tag on their rows signals this. Use [ANN-Benchmarks](https://ann-benchmarks.com/)
or [VectorDBBench](https://github.com/zilliztech/VectorDBBench) for independently
run comparisons.

**Hardware sensitivity.** ANN-Benchmarks runs on specific CPU/memory
configurations. GPU-accelerated vector search (Milvus GPU index, FAISS on CUDA)
can outperform CPU benchmarks by an order of magnitude for large batches.
"Benchmark results" from a different hardware class are not directly transferable.

**Caching figures are upper bounds.** Vendor caching claims (Anthropic 90% cost,
OpenAI 50% discount) assume near-100% cache hit rate and long shared prefixes.
Real-world hit rates depend on prompt structure, TTL, and query repetition.
Measure your own hit rate with `cache_creation_input_tokens` and
`cache_read_input_tokens` from the API response.

**Reranking domain variance.** The "+4 nDCG@10 on BEIR" figure is averaged across
heterogeneous datasets. On highly specialized corpora (legal, medical, internal
documentation) the gain can be anywhere from 1 to 20+ points.

---

## 9. Gaps — Not Publicly Measured

This section is the most production-relevant part of this file. The absence of
data is itself information engineers need when making sourcing decisions.

- **No public head-to-head latency benchmark** exists for any of the three
  Reference Architectures (Local / Mid-Scale / Enterprise stack) as a complete
  pipeline. Component-level data exists; system-level data does not.

- **Shopify "18% → 4% hallucination reduction" (E-commerce chatbot)** is the
  most widely cited RAG production figure in the community, but no public Shopify
  Engineering post confirming these specific percentages has been found. The claim
  is treated as unverified and absent from [§6](#6-end-to-end-case-studies) until
  a primary source is identified. If you have the URL, open a PR with the full
  Evidence Tier (Source URL, Date, Tag, Methodology).

- **Cohere Rerank "MRR uplift of 10-20%"** is stated in Cohere marketing material
  and widely propagated. A specific benchmark dataset + baseline configuration
  backing this exact range has not been identified. The cross-encoder paper
  (§ Reranking) provides independent evidence of improvement magnitude, but not
  for Cohere Rerank specifically.

- **Semantic cache hit rates and ROI** are never reported with methodology. GPTCache,
  LangChain Cache, and LiteLLM Cache all lack published benchmarks on standardized
  query corpora. Real-world performance depends entirely on query repetition
  distribution.

- **$/M-vector** pricing for managed vector databases (Pinecone, Qdrant Cloud,
  Weaviate Cloud, Zilliz) is not publicly listed in a comparable format. Vendors
  use different unit structures (storage vs. compute vs. pod size). Contact vendors
  for sizing quotes.

- **Reranking latency overhead** in production pipelines (round-trip to Cohere
  Rerank API, or BGE-Reranker on CPU/GPU) has not been benchmarked publicly under
  realistic concurrency and p99 conditions.

- **ColPali "10–50× storage overhead"** was a rough estimate. The published figure
  from the ColPali paper (ICLR 2025) is **257.5 KB per page** (multi-vector,
  D=128), vs. a typical text-chunk embedding at ~6 KB (1,536-dim float32). Actual
  ratio depends on page density and chunk strategy. See [§ LLM Serving row 3](#5-llm-serving)
  for the citable ColPali source.

- **Chain-of-thought prompting for LLM judges "improves consistency by 15-20%"**
  is cited in several RAG blogs but is not a stated result of the G-Eval paper
  (Liu et al., EACL 2024). The paper demonstrates better human correlation with
  CoT, not a specific consistency percentage improvement. This figure should not
  be used without a primary citation.

---

## Contributing Benchmark Data

Found a public, reproducible benchmark that belongs here? Open a PR with:

- **Source URL** (primary source, not a blog aggregating it)
- **Date** (`YYYY-MM-DD` — publication or leaderboard snapshot date)
- **Tag** (`[3P]` / `[V]` / `[A]`)
- **Methodology link** — the harness, dataset, or reproduction script
- **Hardware / config** — what was the test environment?

We prefer 20 well-cited rows over 80 half-cited ones. If you find evidence that
contradicts a current row (e.g., a `[3P]` result lower than a `[V]` claim),
open a PR to add it — showing where tools underperform is as valuable as showing
where they excel.
