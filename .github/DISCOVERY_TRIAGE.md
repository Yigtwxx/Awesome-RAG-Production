# Discovery Triage Log

Durable record of accept/reject verdicts for repositories surfaced by the weekly
[discovery engine](../scripts/discovery_engine.py). Rejected entries seed the
`OUT_OF_SCOPE_REPOS` denylist in that script, so the same repos stop reappearing
in every weekly report.

This file is tracked on purpose. The generated report it came from
(`.github/PROPOSED_UPDATES.md`) is ephemeral CI output and is gitignored — the
human verdicts below are not reproducible from the generator, so they live here.

Verdicts are applied against the
[CONTRIBUTING Quality Standards](../CONTRIBUTING.md#quality-standards) and the
[FAQ scope rule](../FAQ.md#why-arent-dify-flowise-open-webui-or-anythingllm-listed):
end-user applications and low-code platforms are out of scope — this list curates
infrastructure building blocks.

---

## 2026-08-21

Triaged from the 2026-08-03, 2026-08-10, and 2026-08-17 discovery reports
(16 unique candidates after deduplication across the three cycles).

| Project | Verdict |
| :--- | :--- |
| [promptfoo](https://github.com/promptfoo/promptfoo) | **Accepted** — MIT, declarative evals with CLI and CI/CD gating plus adversarial red-teaming; listed under Evaluation & Benchmarking. |
| [LightRAG](https://github.com/HKUDS/LightRAG) | **Accepted** — the 2026-08-01 deferral is resolved: incremental updates, a server, and pluggable production storage (PostgreSQL, Neo4j, MongoDB, OpenSearch) are now shipped; listed under Retrieval & Reranking § GraphRAG. |
| [headroom](https://github.com/headroomlabs-ai/headroom) | **Deferred (blocked on a scope decision)** — Apache-2.0 context compression for tool outputs and RAG chunks, actively developed. It is not a cache, so Caching & Performance is the wrong home; listing it means opening a context-compression subsection. That is a maintainer call, not a triage call. |
| [Graphify](https://github.com/Graphify-Labs/graphify) | **Reject (already rejected)** — same project as `safishamsi/graphify`, moved orgs; a code knowledge graph for coding assistants, explicitly vector-store-free. Both slugs are now on the denylist. |
| [llm-app](https://github.com/pathwaycom/llm-app) | **Reject** (was Deferred 2026-08-01) — ready-to-run template gallery, not an infrastructure building block. Resolving the deferral so it stops recurring weekly. |
| [WeKnora](https://github.com/Tencent/WeKnora) | **Reject** — end-user knowledge platform and self-maintaining wiki; out of scope per FAQ. Non-standard license (`NOASSERTION`). |
| [MaxKB](https://github.com/1Panel-dev/MaxKB) | **Reject** — enterprise agent platform with a visual builder; out of scope per FAQ. |
| [coze-studio](https://github.com/coze-dev/coze-studio) | **Reject** — all-in-one visual agent development platform; out of scope per FAQ. |
| [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) | **Reject** — end-to-end AI-plus-data assistant product. The Structured & SQL RAG section lists composable pieces (Vanna, WrenAI), not platforms. |
| [DocsGPT](https://github.com/arc53/DocsGPT) | **Reject** — end-user chat-with-your-documents application; out of scope per FAQ. |
| [eliza](https://github.com/elizaOS/eliza) | **Reject** — general agentic operating system; agent infrastructure, not RAG infrastructure. |
| [ai-agent-book](https://github.com/bojieli/ai-agent-book) | **Reject** — book manuscript with companion code; educational, no production-infrastructure focus. |
| [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) | **Reject** — tutorial collection. |
| [agents-towards-production](https://github.com/NirDiamant/agents-towards-production) | **Reject** — tutorial collection; the production framing is pedagogical, not a shippable component. |
| [ai-guide](https://github.com/liyupi/ai-guide) | **Reject** — general AI resource collection and beginner tutorials. |
| [CV](https://github.com/AccumulateMore/CV) | **Reject** — deep-learning lecture notes; not RAG-related at all. |

All rejects above are seeded into `OUT_OF_SCOPE_REPOS` in
[discovery_engine.py](../scripts/discovery_engine.py) so they stop reappearing.

**Backlog not covered by this triage** — the same reports carry two other
sections that need separate passes:

- *Stale Benchmark Citations* — 10 rows in `benchmarks.md` older than 365 days.
  One of them (Weaviate Cloud SLA) was fixed in #86; the other nine still need
  their sources re-verified or moved to § Gaps.
- *Stale Listed Tools* — 11 listed repos with no push in over 180 days
  (byaldi 566d, pachyderm 560d, ARES 507d, prometheus-eval 479d,
  RAGatouille 457d, GPTCache 402d, tokencost 346d, R2R 283d, omniparse 248d,
  nano-graphrag 202d, vanna 196d). RAGatouille and GPTCache already carry
  inline maintenance warnings; the rest need a deprecate-or-keep decision per
  the Removal & Deprecation Policy.

---

## 2026-08-01

Triaged from the 2026-07-27 discovery report.

| Project | Verdict |
| :--- | :--- |
| [PageIndex](https://github.com/VectifyAI/PageIndex) | **Accepted** — reasoning-based hierarchical document index; listed under Retrieval & Reranking. |
| [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) | **Accepted** — Apache-2.0 PDF parser; listed under Data Ingestion & Parsing. |
| [LightRAG](https://github.com/HKUDS/LightRAG) | **Deferred** — EMNLP 2025 GraphRAG variant; revisit once production adoption is clearer. |
| [headroom](https://github.com/headroomlabs-ai/headroom) | **Deferred** — context compression; evaluate against the Caching & Performance section. |
| [llm-app](https://github.com/pathwaycom/llm-app) | **Deferred** — live-data RAG templates; closer to a template gallery than infrastructure. |
| [khoj](https://github.com/khoj-ai/khoj) | **Reject** — end-user "second brain" application; out of scope per FAQ. |
| [kotaemon](https://github.com/Cinnamon/kotaemon) | **Reject** — end-user chat-with-documents UI; out of scope per FAQ. |
| [FastGPT](https://github.com/labring/FastGPT) | **Reject** — low-code knowledge-base platform; out of scope per FAQ. |
| [onyx](https://github.com/onyx-dot-app/onyx) | **Reject** — end-user AI chat platform; out of scope per FAQ. |
| [sim](https://github.com/simstudioai/sim) | **Reject** — visual agent-workflow builder; out of scope per FAQ. |
| [DeepTutor](https://github.com/HKUDS/DeepTutor) | **Reject** — end-user tutoring application. |
| [happy-llm](https://github.com/datawhalechina/happy-llm) | **Reject** — educational from-scratch tutorial; no production-infrastructure focus. |
| [ai-engineering-hub](https://github.com/patchy631/ai-engineering-hub) | **Reject** — tutorial collection, not production tooling. |
| [Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | **Reject** — general-purpose AI scraper; ingestion-adjacent but not RAG infrastructure. |

---

## 2026-06-12

Triaged from the 2026-05-11 discovery report.

> **Filters:** Stars >= 100, updated in the last 90 days.

> **Triage (2026-06-12):** Verdicts below applied against the
> [CONTRIBUTING Quality Standards](../CONTRIBUTING.md#quality-standards) and the
> [FAQ scope rule](../FAQ.md#why-arent-dify-flowise-open-webui-or-anythingllm-listed)
> (end-user applications and low-code platforms are out of scope — this list curates
> infrastructure building blocks). Result: 1 accept candidate (PaddleOCR),
> 10 out-of-scope rejects, 4 rejects already listed.

| Project | Stars | Description | Last Update | Triage (2026-06-12) |
| :--- | :--- | :--- | :--- | :--- |
| [dify](https://github.com/langgenius/dify) | 140896 | Production-ready platform for agentic workflow development. | 2026-05-11 | **Reject** — end-user / low-code platform; explicitly out of scope per FAQ scope rule. |
| [open-webui](https://github.com/open-webui/open-webui) | 136538 | User-friendly AI Interface (Supports Ollama, OpenAI API, ...) | 2026-05-11 | **Reject** — end-user chat interface, not an infrastructure building block; out of scope per FAQ. |
| [langchain](https://github.com/langchain-ai/langchain) | 136368 | The agent engineering platform. | 2026-05-11 | **Reject (already listed)** — duplicate; in README § Frameworks. |
| [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | 109688 | 100+ AI Agent & RAG apps you can actually run — clone, customize, ship. | 2026-05-11 | **Reject** — meta-list of runnable demo apps/tutorials, not production infrastructure. |
| [ragflow](https://github.com/infiniflow/ragflow) | 80207 | RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-e... | 2026-05-11 | **Reject (already listed)** — duplicate; in README § Frameworks (RAGFlow). |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | 77573 | Turn any PDF or image document into structured data for your AI. A powerful, lightweight OCR tool... | 2026-05-11 | **Accepted** — production-grade OCR/document-parsing toolkit; fits Data Ingestion & Parsing. ✅ Quality Standards review passed 2026-06-25; now listed in README § Data Ingestion & Parsing. |
| [claude-mem](https://github.com/thedotmack/claude-mem) | 74603 | Persistent Context Across Sessions for Every Agent –  Captures everything your agent does during ... | 2026-05-11 | **Reject** — session-memory plugin for AI coding assistants, not a memory layer for building RAG/agent systems. |
| [Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | 74415 | 🐙 Guides, papers, lessons, notebooks and resources for prompt engineering, context engineering, R... | 2026-05-11 | **Reject** — general educational guide; no production-infrastructure focus (Quality Standard #1). |
| [anything-llm](https://github.com/Mintplex-Labs/anything-llm) | 59842 | The all-in-one AI productivity accelerator. On device and privacy first with no annoying setup or... | 2026-05-11 | **Reject** — all-in-one end-user application; explicitly out of scope per FAQ. |
| [mem0](https://github.com/mem0ai/mem0) | 55354 | Universal memory layer for AI Agents | 2026-05-11 | **Reject (already listed)** — duplicate; in README § Agent Memory (Mem0). |
| [Flowise](https://github.com/FlowiseAI/Flowise) | 52716 | Build AI Agents, Visually | 2026-05-11 | **Reject** — visual low-code agent builder; explicitly out of scope per FAQ. |
| [llama_index](https://github.com/run-llama/llama_index) | 49326 | LlamaIndex is the leading document agent and OCR platform | 2026-05-11 | **Reject (already listed)** — duplicate; in README § Frameworks (LlamaIndex). |
| [hello-agents](https://github.com/datawhalechina/hello-agents) | 47000 | 📚 《从零开始构建智能体》——从零开始的智能体原理与实践教程 | 2026-05-11 | **Reject** — educational from-scratch tutorial (textbook), not production tooling. |
| [graphify](https://github.com/safishamsi/graphify) | 46262 | AI coding assistant skill (Claude Code, Codex, OpenCode, Cursor, Gemini CLI, and more). Turn any ... | 2026-05-11 | **Reject** — AI coding-assistant skill; unrelated to RAG infrastructure. |
| [JeecgBoot](https://github.com/jeecgboot/JeecgBoot) | 46171 | AI低代码平台，支持「低代码 + 零代码」双模式：零代码 5 分钟搭建业务系统，低代码模式一键生成前后端代码。 内置AI 应用，支持AI聊天、知识库、流程编排、MCP与插件，支持各种模型。Ski... | 2026-05-11 | **Reject** — low-code business application platform; end-user/low-code, out of scope per FAQ. |
