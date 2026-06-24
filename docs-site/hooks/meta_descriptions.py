"""mkdocs hook: inject a unique per-page meta description.

Source markdown lives at the repo root and is also rendered by GitHub, so we
cannot add YAML front-matter to it (GitHub would show a metadata table). This
hook sets page.meta['description'] at build time instead, giving each page a
distinct <meta name="description"> for search snippets without altering source.
"""

from __future__ import annotations

from typing import Any

# Keyed by Page.file.src_uri (path relative to docs_dir, forward slashes).
# Each description is kept under ~160 chars to fit Google's snippet limit.
DESCRIPTIONS: dict[str, str] = {
    "README.md": (
        "Curated, evidence-cited tools, frameworks, and best practices for "
        "building, scaling, and monitoring production-grade "
        "Retrieval-Augmented Generation systems."
    ),
    "rag-pitfalls.md": (
        "The most frequent mistakes teams make scaling RAG from prototype to "
        "production — chunking, retrieval, evaluation, and cost pitfalls, with "
        "concrete fixes."
    ),
    "benchmarks.md": (
        "Publicly citable benchmarks and measurements backing the numeric "
        "claims across this RAG list, each tagged by evidence type and source."
    ),
    "datasets.md": (
        "General-purpose and domain-specific datasets for benchmarking and "
        "evaluating production RAG systems against ground truth."
    ),
    "vector-database-comparison.md": (
        "Compare vector databases for production RAG — pgvector, Qdrant, Milvus, "
        "Pinecone, Weaviate, and more — by scale, filtering, hybrid search, "
        "and cost."
    ),
    "chunking-strategies.md": (
        "RAG chunking strategies compared — fixed-size, recursive, semantic, "
        "document-aware, hierarchical, and late chunking — with sizing, tooling, "
        "and evaluation."
    ),
    "embedding-model-selection.md": (
        "How to choose an embedding model for RAG — retrieval quality, MTEB "
        "caveats, dimensionality, multilingual, hosting, cost, and when to "
        "fine-tune."
    ),
    "books.md": (
        "A curated reading list of essential books on Retrieval-Augmented "
        "Generation, LLMs, machine learning, and deep learning."
    ),
    "blogs.md": (
        "High-quality blogs and resources for staying current on "
        "Retrieval-Augmented Generation, LLMs, and applied machine learning."
    ),
    "showcase.md": (
        "Real-world RAG engineering blogs, whitepapers, and talks on "
        "architecture, latency, evaluation, and scaling from teams running RAG "
        "in production."
    ),
    "FAQ.md": (
        "Answers about the scope, selection criteria, and maintenance of the "
        "Awesome RAG Production list."
    ),
    "ROADMAP.md": (
        "Planned improvements and automation for the Awesome RAG Production "
        "list — a living roadmap of upcoming work."
    ),
    "CHANGELOG.md": (
        "Notable changes to the Awesome RAG Production list, grouped by month, "
        "newest first."
    ),
    "CONTRIBUTING.md": (
        "How to contribute resources to Awesome RAG Production, including "
        "quality standards and the submission process for production-grade RAG "
        "links."
    ),
    "SECURITY.md": (
        "Security policy for the Awesome RAG Production repository and how to "
        "report a security concern."
    ),
    "CODE_OF_CONDUCT.md": (
        "The Contributor Covenant Code of Conduct governing participation in "
        "the Awesome RAG Production community."
    ),
}


def on_page_markdown(markdown: str, *, page: Any, config: Any, files: Any) -> str:
    """Set a per-page meta description if one is mapped and not already set."""
    description = DESCRIPTIONS.get(page.file.src_uri)
    if description and "description" not in page.meta:
        page.meta["description"] = description
    return markdown
