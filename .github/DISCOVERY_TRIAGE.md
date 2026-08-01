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
