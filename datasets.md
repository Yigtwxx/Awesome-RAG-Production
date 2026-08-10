# Datasets for RAG Benchmarking

You cannot improve what you cannot measure. Production-grade RAG requires rigorous
evaluation against ground-truth datasets. This list covers general-purpose
benchmarks and domain-specific corpora.

---

## The Leaderboards

<!-- no-alphabetical -->

Before choosing a model, check these live leaderboards:

- [MTEB (Massive Text Embedding Benchmark)](https://huggingface.co/spaces/mteb/leaderboard)
  - The gold standard for choosing an embedding model (Retrieval, Clustering,
    Reranking quality).
- [Open Compass](https://rank.opencompass.org.cn/leaderboard-llm-v2)
  - Comprehensive LLM evaluation which includes retrieving capabilities.
- [Hugging Face Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard)
  - General LLM performance.

---

## General Knowledge (Open Domain QA)

- [MS MARCO](https://microsoft.github.io/msmarco/) - 1M+ Queries.
  - Making AI the first truly conversational search engine.
  - _(Best For: Retrieval)_
- [HotpotQA](https://hotpotqa.github.io/) - 113k pairs.
  - Question answering requiring multi-hop reasoning.
  - _(Best For: Reasoning)_
- [Natural Questions (NQ)](https://ai.google.com/research/NaturalQuestions/) - 300k+.
  - Real user queries issued to Google Search.
  - _(Best For: Realism)_
- [TriviaQA](https://nlp.cs.washington.edu/triviaqa/) - 95k.
  - Reading comprehension dataset containing triples of (question, answer,
    evidence).
  - _(Best For: Factuality)_

---

## Long-Context & Document Understanding

- [SQuAD 2.0](https://rajpurkar.github.io/SQuAD-explorer/) - Stanford Question Answering Dataset.
  - Includes unanswerable questions.
  - _(Best For: Hallucination Detection)_
- [Qasper](https://huggingface.co/datasets/allenai/qasper) - Question answering over NLP papers.
  - _(Best For: Technical/Scientific)_
- [NarrativeQA](https://github.com/google-deepmind/narrativeqa) - QA over collected stories
  (books and movie scripts).
  - _(Best For: Long Context)_

---

## BEIR Benchmark Suite

The de facto zero-shot retrieval benchmark — 18 heterogeneous datasets, 9 task
types — spanning bio-medical IR, fact-checking, argument retrieval, and more.

- [BEIR](https://github.com/beir-cellar/beir) - 18 datasets, 9 task types.
  - Heterogeneous benchmark for zero-shot evaluation of dense and sparse
    retrievers across domains.
  - _(Best For: Zero-Shot Retrieval)_
- [MIRACL](https://github.com/project-miracl/miracl) - 18 languages, 700k+ queries.
  - Multilingual retrieval benchmark over Wikipedia in typologically diverse
    languages.
  - _(Best For: Multilingual Retrieval)_
- [SciFact](https://github.com/allenai/scifact) - 1.4k scientific claims.
  - Claim verification against a corpus of research literature.
  - _(Best For: Scientific Faithfulness)_

---

## Legal & Contracts

- [CUAD](https://www.atticusprojectai.org/cuad/) - 13k+ labels, 510 contracts.
  - Expert-annotated commercial contracts across 41 clause categories.
  - _(Best For: Clause Extraction)_
- [LegalBench](https://hazyresearch.stanford.edu/legalbench/) - 162 tasks.
  - Collaborative benchmark for legal reasoning, built with practicing lawyers.
  - _(Best For: Legal Reasoning)_
- [CaseHOLD](https://reglab.stanford.edu/data/casehold-benchmark/) - 53k+ holdings.
  - Multiple-choice case-holding identification over US legal opinions.
  - _(Best For: Case Law Retrieval)_
- [Open Australian Legal Corpus](https://huggingface.co/datasets/isaacus/open-australian-legal-corpus) - 200k+ documents.
  - Largest open, permissively licensed (CC-BY) legal corpus suitable for
    pretraining and fine-tuning.
  - _(Best For: Legal Pretraining)_

---

## Medical & Biomedical

- [PubMedQA](https://pubmedqa.github.io/) - 1k expert + 211k auto.
  - Yes/No/Maybe QA over biomedical research abstracts.
  - _(Best For: Biomedical QA)_
- [BioASQ](https://bioasq.org/) - Annual challenge.
  - Large-scale biomedical semantic indexing and question answering
    (registration required).
  - _(Best For: Semantic Indexing)_
- [MedQA (USMLE)](https://github.com/jind11/MedQA) - 12k+ MCQs.
  - Medical board exam questions across English, Chinese, and Taiwanese
    licensure.
  - _(Best For: Clinical Reasoning)_
- [MIMIC-IV](https://physionet.org/content/mimiciv/3.1/) - De-identified clinical notes.
  - ICU and ED records from Beth Israel Deaconess; PhysioNet credentialing
    required.
  - _(Best For: Clinical Notes)_

---

## Finance & Markets

- [FinQA](https://github.com/czyssrs/FinQA) - 8k+ QA pairs.
  - Numerical reasoning over S&P 500 earnings reports (text + tables).
  - _(Best For: Numerical Reasoning)_
- [TAT-QA](https://nextplusplus.github.io/TAT-QA/) - 16k+ QA pairs.
  - Hybrid tabular and textual QA over real-world financial reports.
  - _(Best For: Tabular Reasoning)_
- [ConvFinQA](https://github.com/czyssrs/ConvFinQA) - Conversational extension.
  - Multi-turn numerical reasoning over financial documents.
  - _(Best For: Conversational Finance)_

---

## Industrial & Field Service

- [Industrial Manual RAG Evaluation Pack](https://github.com/kylecoutray/industrial-manual-rag-eval)
  <!-- verified: 2026-08-10 -->
  - Small synthetic corpus with current and superseded manuals,
    neighboring-equipment traps, service-bulletin precedence, restricted and
    withdrawn sources, twelve expected-answer cases, and critical-failure
    scoring. Maintained by InHouse Compute; every product and procedure is
    fictional and not for real equipment.

---

## Synthetic Data Generation

Don't have a dataset? Generate one from your own internal documents.

<!-- no-alphabetical -->

- [Ragas Synthetic Data Generator](https://docs.ragas.io/en/stable/)
  - Create "Golden Datasets" (Question-Answer-Context triples) automatically.
- [LlamaIndex Data Generator](https://developers.llamaindex.ai/python/framework/)
  - Built-in utils to generate questions from your indexed nodes.

---

([back to main resource](README.md#contents))
