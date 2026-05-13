# ADR-001: LLM Provider Selection

**Date:** 2026-05-01
**Status:** Accepted
**Deciders:** Haider Ahmad

---

## Context

DataLens requires an LLM to power two features: the natural-language chat interface and the executive summary generator. The spec mandates that the LLM must support **function/tool-calling** — the pattern where the backend exposes Python functions the LLM can invoke (e.g., `query_data`, `get_statistics`) to ground its answers in real data rather than hallucinating.

The project was developed as a university assignment with student budget constraints. The viable options were:

| Provider | Model used | Tool-calling support | Monthly cost at ~500 queries |
|----------|-----------|----------------------|------------------------------|
| Anthropic Claude | claude-haiku-4-5 | First-class, well-documented | ~$0.50 |
| OpenAI | gpt-4o-mini | Mature, widely documented | ~$0.75 |
| Google Gemini | gemini-1.5-flash | Supported but fewer examples | ~$0.30 |
| Groq | llama3-8b | Function-calling varies by model | Free tier |

---

## Options Considered

**Option A — Anthropic Claude (claude-haiku-4-5)**
Tool-calling is a core design principle of the Claude API, not an add-on. The SDK provides structured `ToolUseBlock` and `ToolResultBlock` types that make multi-turn tool loops straightforward to implement. The `claude-haiku-4-5` model is the fastest and cheapest in the Claude family. Documentation for tool-use is extensive and well-maintained.

**Option B — OpenAI (gpt-4o-mini)**
OpenAI has the largest community and most examples online. However, the project was already using Anthropic's Cowork tool for development, making the Anthropic API the natural choice for integration coherence. Cost is slightly higher than Haiku.

**Option C — Google Gemini (gemini-1.5-flash)**
Cheapest option. Tool-calling is supported but the Python SDK had fewer community examples at the time of decision. Integration risk was higher given the project timeline.

**Option D — Groq**
Free tier is attractive for development. However, Groq's tool-calling support varies by model and is not as well-documented. Reliability risk for a graded submission was unacceptable.

---

## Decision

We chose **Anthropic Claude (claude-haiku-4-5)**.

The primary reasons:

1. **Tool-calling is first-class.** The Anthropic Python SDK's `ToolUseBlock`/`ToolResultBlock` types make implementing the multi-turn tool loop clean and explicit. The code in `llm.py` loops up to 5 rounds, processes tool calls, and returns the final answer with minimal boilerplate.

2. **Development coherence.** The project was directed using Claude (Cowork). Using the same provider for both development and runtime means we understand the model's strengths and failure modes directly from experience.

3. **Cost efficiency.** Haiku is cheaper per token than gpt-4o-mini and produces high-quality results for SQL-grounded Q&A tasks where factual accuracy is enforced by the tool results, not the model's memory.

4. **Structured output reliability.** Tool arguments are returned as typed JSON, which simplifies validation.

---

## Trade-offs

**What we gave up:**
- The Groq free tier (we have a small but non-zero API cost)
- The larger OpenAI community for troubleshooting (fewer Anthropic-specific examples for advanced tool-calling patterns)
- Gemini's lower cost per token

**What we accepted:**
- A dependency on Anthropic's API uptime
- The requirement that users obtain their own Anthropic API key (no bundled key)

**Mitigation:**
The `llm.py` module wraps all Anthropic calls in try/except and returns graceful error messages to the frontend if the API is unavailable. The rest of the app (upload, profiling, charts, filters) works without an API key.
