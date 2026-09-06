# Phase 8 — LLM Provider Integration

## 1. Objective

Implement the LLM generation layer that routes prompts through OpenRouter to a Gemini model and returns clean, application-level responses.

The LLM layer is provider-independent — the rest of the application calls `llm.generate(prompt)` without knowing whether the backend is OpenRouter, a direct Gemini API, or any other LLM provider.

This phase does **not** implement the RAG pipeline (Phase 9). It only provides the LLM generation capability.

---

## 2. Files Created/Modified

| Action | File | Responsibility |
|--------|------|----------------|
| **IMPLEMENTED** | `app/llm/llm_service.py` | `BaseLLMService` ABC, `LLMResponse` dataclass, exception hierarchy |
| **IMPLEMENTED** | `app/llm/openrouter.py` | `OpenRouterLLMService` — OpenRouter provider using `ChatOpenAI` |
| **IMPLEMENTED** | `app/llm/__init__.py` | Public module API exports |
| **DELETED** | `app/llm/gemini.py` | Removed — Gemini LLM is accessed through OpenRouter, not directly |
| **MODIFIED** | `app/core/config.py` | Expanded `LLMConfig` with provider, model, max_tokens, timeout, max_retries |
| **MODIFIED** | `config.yaml` | Expanded `llm:` section with full generation configuration |
| **MODIFIED** | `.env.example` | Updated LLM_PROVIDER/LLM_MODEL to OpenRouter defaults |
| **MODIFIED** | `requirements.txt` | Added `langchain-openai>=0.3.0` |
| **CREATED** | `tests/test_llm.py` | 15 tests — all mocked, zero real API calls |

---

## 3. Architecture

```
Application code
    ↓
BaseLLMService.generate(prompt)    ← provider-independent interface
    ↓
OpenRouterLLMService               ← concrete implementation
    ↓
LangChain ChatOpenAI               ← OpenAI-compatible client
    ↓  (base_url = https://openrouter.ai/api/v1)
OpenRouter API                     ← LLM gateway
    ↓
google/gemini-2.5-flash            ← Gemini model (configurable)
    ↓
LLMResponse(content, model, usage) ← clean application-level result
```

Key separation:

```
EMBEDDINGS (Phase 5)             LLM GENERATION (Phase 8)
────────────────────             ─────────────────────────
google-genai SDK                 langchain-openai
    ↓                                ↓
Gemini Embedding API             OpenRouter API
    ↓                                ↓
gemini-embedding-2               google/gemini-2.5-flash
    ↓                                ↓
Vectors → ChromaDB               Generated text
```

These are deliberately separate paths. Embeddings go directly to the Gemini Embedding API. LLM generation goes through OpenRouter.

---

## 4. Why OpenRouter?

1. **Model flexibility** — OpenRouter aggregates 200+ models from multiple providers. The project can switch from Gemini to Claude, GPT, or Llama by changing one config value.
2. **OpenAI-compatible API** — OpenRouter exposes an OpenAI-compatible endpoint, so LangChain's `ChatOpenAI` works directly. No custom SDK needed.
3. **Cost optimization** — OpenRouter finds the cheapest provider for a given model automatically.
4. **Rate limit aggregation** — OpenRouter pools rate limits across multiple upstream providers.
5. **Interview demonstration** — Shows understanding of provider abstraction and API gateway patterns.

---

## 5. Provider Abstraction

```python
class BaseLLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        pass
```

The application only depends on `BaseLLMService`. The concrete implementation (`OpenRouterLLMService`) is injected at construction time.

**Why this matters:**

- **Testability** — tests mock `ChatOpenAI`, not the entire LLM interface.
- **Swappability** — switching providers requires only a new implementation of `BaseLLMService`.
- **Decoupling** — FastAPI endpoints (Phase 11) and the RAG pipeline (Phase 9) depend on the interface, not OpenRouter.

---

## 6. LangChain Integration

```python
from langchain_openai import ChatOpenAI

self._llm = ChatOpenAI(
    model="google/gemini-2.5-flash",     # from config.yaml
    api_key=resolved_key,                 # from .env (SecretStr)
    base_url="https://openrouter.ai/api/v1",
    temperature=0.2,                      # from config.yaml
    max_tokens=4096,                      # from config.yaml
    timeout=60,                           # from config.yaml
    max_retries=3,                        # from config.yaml
)
```

- `langchain-openai` 1.6.0 provides `ChatOpenAI` which accepts `base_url` to redirect to OpenRouter.
- The `openai` SDK (3.8.0) is installed as a dependency of `langchain-openai`.
- `langchain-google-genai` is **not** used for LLM generation — it remains relevant only to the embedding path.

---

## 7. Configuration

### Secrets (`.env`)

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Stored as `SecretStr` in `Settings`. Never logged, never exposed in responses.

### Non-Secret Parameters (`config.yaml`)

```yaml
llm:
  provider: openrouter
  model: "google/gemini-2.5-flash"
  temperature: 0.2
  max_tokens: 4096
  timeout: 60        # seconds
  max_retries: 3
```

### LLMConfig (Pydantic Model)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | str | `openrouter` | LLM provider name |
| `model` | str | `google/gemini-2.5-flash` | OpenRouter model identifier |
| `temperature` | float | `0.2` | Sampling temperature (0.0–2.0) |
| `max_tokens` | int | `4096` | Maximum completion tokens |
| `timeout` | int | `60` | Request timeout in seconds |
| `max_retries` | int | `3` | Bounded retry count (0–10) |

### Model Selection

`google/gemini-2.5-flash` was selected based on:
- **Availability**: Currently active on OpenRouter (verified via API).
- **Context window**: 1,048,576 tokens (1M) — sufficient for RAG with large context.
- **Max completion tokens**: 65,535 — ample for generated answers.
- **Supported parameters**: `temperature`, `top_p`, `max_tokens`, `stop`, `response_format`.
- **Cost**: $0.30/M input, $2.50/M output — cost-effective for an interview project.
- **Reasoning capability**: Built-in thinking mode (optional).

---

## 8. Error Handling

### Exception Hierarchy

```
LLMError (base)
├── LLMMissingAPIKeyError (ValueError)  — no OPENROUTER_API_KEY configured
├── LLMConfigurationError (ValueError)  — invalid model, bad parameters
├── LLMAuthenticationError              — HTTP 401/403 (PERMANENT)
├── LLMProviderError                    — HTTP 429, 5xx, network, timeout (TRANSIENT)
└── LLMResponseError                    — empty/malformed response content
```

### Error Classification

| Error | Type | Retryable | Action |
|-------|------|-----------|--------|
| Missing API key | Permanent | ❌ | Raise immediately |
| 401 Unauthorized | Permanent | ❌ | Raise `LLMAuthenticationError` |
| 403 Forbidden | Permanent | ❌ | Raise `LLMAuthenticationError` |
| 404 Model not found | Permanent | ❌ | Raise `LLMConfigurationError` |
| 429 Rate limited | Transient | ✅ | ChatOpenAI retries, then `LLMProviderError` |
| 500/502/503/504 | Transient | ✅ | ChatOpenAI retries, then `LLMProviderError` |
| Network timeout | Transient | ✅ | Raise `LLMProviderError` |
| Empty response | Data | ❌ | Raise `LLMResponseError` |

---

## 9. Retry Strategy

Retry behavior is handled by LangChain's `ChatOpenAI` internally:

1. **max_retries = 3** (configurable in `config.yaml`).
2. **Bounded exponential backoff** with jitter (built into the OpenAI SDK).
3. **Retried status codes**: 429, 500, 502, 503, 504.
4. **NOT retried**: 401, 403, 404, and other permanent errors.
5. After all retries are exhausted, the exception surfaces to `OpenRouterLLMService`, which translates it to the application-level exception.

No custom retry loop is implemented — LangChain/OpenAI SDK retry semantics are used directly.

---

## 10. Testing

### Test Suite: `tests/test_llm.py` — 15 tests

| # | Test | Verifies |
|---|------|----------|
| 1 | `test_successful_generation` | Valid prompt → LLMResponse with content |
| 2 | `test_prompt_passed_correctly` | Exact prompt string reaches ChatOpenAI.invoke() |
| 3 | `test_correct_provider_configured` | base_url = OpenRouter API |
| 4 | `test_correct_model_configured` | model = config value |
| 5 | `test_response_content_extracted` | LLMResponse.content matches AIMessage.content |
| 6 | `test_empty_response_handled` | Empty content → LLMResponseError |
| 7 | `test_missing_api_key` | No API key → LLMMissingAPIKeyError |
| 8 | `test_authentication_failure` | 401 → LLMAuthenticationError |
| 9 | `test_invalid_model` | 404 → LLMConfigurationError |
| 10 | `test_rate_limit_retry` | 429 → LLMProviderError |
| 11 | `test_server_error_retry` | 500 → LLMProviderError |
| 12 | `test_permanent_error_no_infinite_retry` | 403 → single invoke call (no retry) |
| 13 | `test_retry_limit_respected` | 502 → exception surfaces after retries |
| 14 | `test_timeout_failure` | TimeoutError → LLMProviderError |
| 15 | `test_malformed_response` | Non-AIMessage object → LLMResponseError |

**Strategy**: All tests patch `ChatOpenAI` at the module level. Zero real API calls.

---

## 11. Design Decisions

### Why OpenRouter instead of direct Gemini API

The embedding path uses the Gemini API directly because `google-genai` provides the best embedding SDK with Matryoshka dimensionality and task-type support. The LLM generation path uses OpenRouter because it provides model flexibility, cost optimization, and an OpenAI-compatible API that integrates cleanly with LangChain.

### Why embeddings remain separate

Embeddings require model-specific features (asymmetric task types: `RETRIEVAL_DOCUMENT` vs `RETRIEVAL_QUERY`, Matryoshka output dimensionality) that are only available through the native Gemini Embedding API. OpenRouter does not expose these. The two paths are therefore deliberately separate.

### Why provider abstraction exists

The rest of the application depends on `BaseLLMService.generate()`, not on `ChatOpenAI` or OpenRouter. This means:
- Swapping providers (Anthropic, Cohere, local models) requires only a new `BaseLLMService` implementation.
- Tests mock the abstract interface, not provider internals.
- FastAPI endpoints and the RAG pipeline are decoupled from infrastructure.

### Why RAG prompting is not implemented yet

Phase 8 provides raw LLM generation: `prompt → text`. Phase 9 will combine retrieved context chunks with the user query into a grounded RAG prompt, then pass it to this LLM service.

### Why agents are not needed

This is a straightforward RAG application, not an autonomous agent system. The LLM receives a complete prompt and returns text — no tool calling, planning, or multi-step reasoning loops.

### Why streaming is not implemented yet

Streaming adds complexity (SSE endpoints, partial response handling, UI buffering) that isn't needed until the frontend (Phase 12) is built. The synchronous `.invoke()` API is sufficient for the current pipeline.

### Why `gemini.py` was deleted

Gemini LLM generation is accessed exclusively through OpenRouter in V1. A separate `gemini.py` file would be empty boilerplate with no functionality. If direct Gemini LLM access is needed in V2, a new provider implementation can be created.

---

## 12. Future Phase Connection

Phase 9 (RAG Pipeline) will:

1. Accept a user question.
2. Call `Retriever.retrieve(question)` to get relevant chunks (Phase 7).
3. Construct a RAG prompt combining:
   - System instructions (grounding rules)
   - Retrieved context chunks
   - User question
4. Call `LLMService.generate(rag_prompt)` (this phase).
5. Return the grounded answer with source citations.

```
User Question
    ↓
Retriever.retrieve()        ← Phase 7
    ↓
[RetrievedChunk, ...]
    ↓
RAG Prompt Construction     ← Phase 9
    ↓
LLMService.generate()       ← Phase 8 (this phase)
    ↓
Grounded Answer + Sources
```

---

## 13. Interview Knowledge

### LLM vs Embedding Model

An **embedding model** (Phase 5) converts text into fixed-dimensional numerical vectors that capture semantic meaning. These vectors enable similarity search — finding documents that are semantically close to a query. Embeddings are deterministic and don't generate text.

An **LLM** (this phase) generates natural language text given a prompt. It's a generative model that produces variable-length responses based on learned patterns. LLMs are used for question answering, summarization, and reasoning.

In a RAG system, both are used: embeddings for retrieval, LLMs for generation.

### Inference

**Inference** is the process of running a trained model on new input to produce output. When we call `llm.generate(prompt)`, we're performing inference — the model uses its learned weights to generate a response. Inference is computationally expensive, which is why models are hosted on GPU-equipped servers and accessed via API.

### Tokens

**Tokens** are the fundamental units of text that LLMs process. A token is approximately 4 characters or ¾ of a word. Both input (prompt) and output (response) are measured in tokens. Pricing, rate limiting, and context window capacity are all token-based.

Gemini 2.5 Flash pricing: $0.30/M input tokens, $2.50/M output tokens.

### Context Window

The **context window** is the maximum number of tokens the model can process in a single request (input + output combined). Gemini 2.5 Flash has a 1,048,576-token (1M) context window, meaning it can process approximately 750K words in a single request. This is important for RAG because the context window must accommodate both the retrieved chunks and the generated answer.

### Temperature and Sampling

**Temperature** controls the randomness of generation:
- `0.0` = deterministic (always picks the most likely token)
- `0.2` = mostly deterministic with slight variation (our default for RAG)
- `1.0` = balanced creativity
- `2.0` = highly creative/random

For RAG applications, low temperature (0.2) is preferred because we want factual, grounded responses based on the retrieved context, not creative/hallucinatory responses.

Other sampling parameters:
- **top_p** (nucleus sampling): Considers tokens whose cumulative probability exceeds `p`.
- **max_tokens**: Maximum tokens in the generated response.

### API Rate Limiting

Rate limiting prevents abuse and ensures fair resource allocation. When the API returns HTTP 429 (Too Many Requests), the client should:

1. Read the `Retry-After` header.
2. Wait the specified duration.
3. Retry with exponential backoff.

Our implementation handles this automatically through LangChain's `ChatOpenAI`, which uses bounded exponential backoff with jitter. The `max_retries` parameter (default: 3) caps the number of attempts.

### Retries

Not all errors should be retried:

| Error Type | Retryable | Why |
|------------|-----------|-----|
| 429 Rate limit | ✅ | Temporary — quota resets |
| 500 Server error | ✅ | Temporary — server may recover |
| 401 Auth failure | ❌ | Same credentials will always fail |
| 404 Not found | ❌ | Model doesn't exist |
| Timeout | ✅ | Network may stabilize |

Bounded retries (max 3) prevent infinite loops. Exponential backoff (1s → 2s → 4s) prevents thundering herd on rate-limited APIs.

### Provider Abstraction

A **provider abstraction** decouples business logic from specific API implementations. Without it:

```python
# Tightly coupled — changing providers requires changing every call site
response = openai.ChatCompletion.create(model="gpt-4", ...)
```

With abstraction:

```python
# Loosely coupled — swap providers by changing only the implementation
response = llm_service.generate(prompt)
```

This is the **Strategy pattern** from design patterns: define an interface (`BaseLLMService`), implement it for each provider (`OpenRouterLLMService`), and inject the desired implementation.

### OpenAI-Compatible APIs

OpenAI's chat completions API (`/v1/chat/completions`) has become a de facto standard. Providers like OpenRouter, Together AI, Groq, and Azure OpenAI all expose this same interface:

```json
POST /v1/chat/completions
{
  "model": "google/gemini-2.5-flash",
  "messages": [{"role": "user", "content": "..."}],
  "temperature": 0.2,
  "max_tokens": 4096
}
```

This means a single client library (`langchain-openai`) can communicate with dozens of different LLM providers by changing only the `base_url` and `api_key`.

### External Service Reliability

External APIs (OpenRouter, Gemini, any cloud service) are inherently unreliable. Production applications must handle:

1. **Network partitions** — The server may be unreachable.
2. **Rate limiting** — Usage exceeds allocated quota.
3. **Server errors** — The provider's infrastructure fails.
4. **Latency spikes** — Response times become unpredictable.
5. **Data issues** — Malformed or empty responses.

Our implementation addresses all five through: bounded retry with backoff, timeouts, error classification (permanent vs transient), clean exception hierarchy, and response validation.
