# Datasets for RAG Benchmarking

You cannot improve what you cannot measure. Production-grade RAG requires rigorous
evaluation against ground-truth datasets. This list covers general-purpose
benchmarks and domain-specific corpora.

---

## The Leaderboards

Before choosing a model, check these live leaderboards:

- **[MTEB (Massive Text Embedding Benchmark)](https://huggingface.co/spaces/mteb/leaderboard)**
  - The gold standard for choosing an embedding model (Retrieval, Clustering,
    Reranking quality).
- **[Open Compass](https://opencompass.org.cn/leaderboard-llm)**
  - Comprehensive LLM evaluation which includes retrieving capabilities.
- **[Hugging Face Open LLM Leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)**
  - General LLM performance.

---

## General Knowledge (Open Domain QA)

- **[MS MARCO](https://microsoft.github.io/msmarco/)** - 1M+ Queries.
  - Making AI the first truly conversational search engine.
  - _(Best For: Retrieval)_
- **[HotpotQA](https://hotpotqa.github.io/)** - 113k pairs.
  - Question answering requiring multi-hop reasoning.
  - _(Best For: Reasoning)_
- **[Natural Questions (NQ)](https://ai.google.com/research/NaturalQuestions)** - 300k+.
  - Real user queries issued to Google Search.
  - _(Best For: Realism)_
- **[TriviaQA](https://nlp.cs.washington.edu/triviaqa/)** - 95k.
  - Reading comprehension dataset containing triples of (question, answer,
    evidence).
  - _(Best For: Factuality)_

---

## Long-Context & Document Understanding

- **[SQuAD 2.0](https://rajpurkar.github.io/SQuAD-explorer/)** - Stanford Question Answering Dataset.
  - Includes unanswerable questions.
  - _(Best For: Hallucination Detection)_
- **[Qasper](https://allenai.org/data/qasper)** - Question answering over NLP papers.
  - _(Best For: Technical/Scientific)_
- **[NarrativeQA](https://github.com/deepmind/narrativeqa)** - QA over collected stories
  (books and movie scripts).
  - _(Best For: Long Context)_

---

## Synthetic Data Generation

Don't have a dataset? Generate one from your own internal documents.

- **[Ragas Synthetic Data Generator](https://docs.ragas.io/)**
  - create "Golden Datasets" (Question-Answer-Context triples) automatically.
- **[LlamaIndex Data Generator](https://docs.llamaindex.ai/)**
  - Built-in utils to generate questions from your indexed nodes.

---

([back to main resource](README.md#contents))
