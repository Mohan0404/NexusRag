# Phase 13 — Testing & Quality Engineering

## 1. Objective

Phase 13 establishes a comprehensive, deterministic, zero-network automated software testing and quality engineering framework for the Genworx Knowledge Assistant (NexusRAG).

The primary objectives are:
1. Guarantee individual component correctness across core domain, caching, vector indexing, and API layers.
2. Verify component integration boundaries without external cloud dependencies.
3. Eliminate test isolation defects, specifically resolving staging file resource leaks during document ingestion.
4. Establish centralized, reusable test fixtures and semantic test doubles.
5. Create a deterministic end-to-end (E2E) integration test validating the entire document upload, indexing, retrieval, and caching lifecycle.
6. Provide comprehensive test coverage and regression protection for backend and frontend codebases.

> [!IMPORTANT]
> Phase 13 focuses exclusively on **software correctness, reliability, and engineering quality**. Quantitative RAG answer evaluation (faithfulness, answer relevance, precision, recall, MRR, nDCG, RAGAS) belongs strictly to Phase 14.

---

## 2. Existing Test Baseline vs Final State

| Metric | Pre-Phase 13 Baseline | Post-Phase 13 Final State | Delta |
| :--- | :---: | :---: | :---: |
| **Backend Tests (pytest)** | 147 | **158** | +11 tests |
| **Frontend Tests (Vitest)** | 17 | **21** | +4 tests |
| **Total Automated Tests** | **164** | **179** | **+15 tests** |
| **Total Test Duration** | ~10.4s (BE) / ~2.4s (FE) | ~7.7s (BE) / ~2.5s (FE) | Maintained < 10s |
| **Backend Line Coverage** | Unmeasured | **88%** (1,345 / 1,523 stmts) | Measured via `pytest-cov` |
| **Cloud API Dependencies** | 0 external calls | **0 external calls** | 100% offline & isolated |

---

## 3. Test Pyramid Architecture

NexusRAG employs an industry-standard testing pyramid. Exact percentages are not rigid targets; the structure prioritizes fast, isolated unit tests, supplemented by contract-verifying integration tests and a minimal set of critical E2E tests:

```
                  ┌─────────────────┐
                  │   End-to-End    │  1 High-Value System Test
                  │  (Deterministic)│  FastAPI + Ingestion + Chroma + RAG + Cache
             ┌────┴─────────────────┴────┐
             │     Integration Tests     │  Component Seams & Contracts
             │   API Adapters & Pipelines │  ChromaStore, Ingestion, Cache, FastAPI
        ┌────┴───────────────────────────┴────┐
        │              Unit Tests             │  Isolated Logic & Edge Cases
        │   Chunker, Models, Prompts, Mocks   │  Pure functions, formatters, validation
        └─────────────────────────────────────┘
```

### Why Each Layer Exists
1. **Unit Tests:** Verify individual functions, edge cases, string normalization, and error translation in memory. Execution is sub-millisecond per test.
2. **Integration Tests:** Verify that concrete components (e.g. `Retriever` and `ChromaStore`) collaborate according to their contracts without mock drift.
3. **End-to-End Tests:** Exercise the complete assembled application from HTTP entry through vector persistence, retrieval, generation, and query caching.

---

## 4. Unit Testing

Unit tests focus on deterministic algorithmic verification without network or filesystem side effects:
- **`DocumentChunker` (`test_chunking.py` — 11 tests):** Verifies recursive character chunking, token sizing, overlap constraints, metadata propagation, and validation on invalid bounds.
- **`Settings` & Configuration (`test_config.py` — 6 tests):** Validates YAML configuration parsing, environment overrides, temperature boundaries, and secret masking.
- **Logging Redaction (`test_logging.py` — 4 tests):** Tests that sensitive tokens, keys, and credentials are automatically redacted from application log streams.
- **Redis Query Cache Units (`test_cache.py` — 17 tests):** Tests SHA-256 query normalization, TTL assignment, metrics accounting, corrupt JSON rejection, and fail-open fallbacks.
- **Input Validation Boundaries (`test_chat.py` — 11 tests):** Tests question length boundaries, including empty strings (422), whitespace (422), excessive length >2,000 characters (422), and exact 2,000-character boundary acceptance (200 OK).

---

## 5. Integration Testing

Integration tests verify component seams using deterministic in-memory doubles and temporary disk directories:

### Boundary A: IngestionPipeline Orchestration
- Orchestrates `DocumentService` -> `DocumentChunker` -> `BaseEmbeddingService` -> `ChromaStore` -> `RedisQueryCache.clear()`.
- Validates strict call ordering and verifies that if an intermediate step fails (e.g., embedding generation or ChromaDB disk full), downstream steps and cache invalidation are safely aborted.

### Boundary B: ChromaStore + VectorRetriever
- Uses a real `ChromaStore` targeting an isolated `tmp_path` directory with `FakeEmbeddingService`.
- Ingests multiple distinct documents and asserts that `Retriever.retrieve()` returns the correct semantic chunk with intact metadata.

### Boundary C: RAGPipeline + RedisQueryCache
- Tests that the first query executes retrieval and LLM generation, storing the result in Redis.
- Tests that a subsequent equivalent query with varying casing or whitespace results in a cache hit, completely skipping retriever and LLM calls.

---

## 6. End-to-End Testing

Implemented in `backend/tests/test_e2e_integration.py` (`test_full_system_e2e_workflow`).

### The Verified E2E Workflow
1. **Environment Setup:** Creates an isolated ephemeral ChromaDB on pytest `tmp_path` with `FakeEmbeddingService`, `FakeLLMService`, and `FakeRedisClient`.
2. **Document Upload:** `POST /api/v1/documents/upload` with `nexus_guide.txt` ("NexusRAG is built by Genworx for enterprise AI.").
   - *Assertions:* HTTP 200, `status="success"`, `chunks_created >= 1`.
   - *Resource Verification:* Staged file in `data/uploads/` is cleanly unlinked.
3. **First Question:** `POST /api/v1/chat` with `"What is NexusRAG and who built it?"`.
   - *Assertions:* HTTP 200, answer contains `"Genworx"`, sources cite `"nexus_guide.txt"`, `FakeLLMService` called exactly once.
4. **Second Equivalent Question:** `POST /api/v1/chat` with `"what is nexusrag and who built it?"`.
   - *Assertions:* HTTP 200, identical logical response, `FakeLLMService` call count remains 1, confirming an end-to-end cache hit through the HTTP API.

---

## 7. Central Fixtures (`conftest.py`)

Centralized in `backend/tests/conftest.py`:
- `fake_embedding_service`: Semantic-like concept hashing with L2 unit normalization.
- `fake_llm_service`: Predictable prompt recording and canned generation.
- `fake_redis_client`: In-memory dictionary client implementing hash keys, pattern matching (`keys`), TTL tracking, and fail-open simulations.
- `tmp_chroma_store`: Isolated ephemeral ChromaStore instance on `tmp_path`, automatically cleaned up after each test.

---

## 8. Test Isolation Strategy

### Prevention of Shared State & Resource Leaks
1. **Vector DB Isolation:** Real ChromaDB tests write exclusively to `tmp_path / "chroma_test_db"`. Production `backend/data/chroma` is never touched.
2. **Redis Isolation:** Tests use `FakeRedisClient` in memory; keys are isolated per test function without communicating with a live Redis daemon.
3. **Upload Staging Isolation:** Resolved the staging leak in `routes_documents.py`; temporary files are unlinked in the route `finally:` block.
4. **Environment Isolation:** Tests never read production API keys from `.env`.

---

## 9. Mock vs Fake vs Real Dependencies

| Component | Test Level | Implementation | Rationale |
| :--- | :--- | :--- | :--- |
| **Google Gemini API** | Unit / Integration / E2E | Mock SDK / `FakeEmbeddingService` | Avoids network latency, paid API consumption, and rate limits. |
| **OpenRouter API** | Unit / Integration / E2E | Mock ChatOpenAI / `FakeLLMService` | Eliminates external dependency and non-deterministic generation. |
| **ChromaDB** | Integration / E2E | Real Local (`tmp_path`) | Validates actual SQLite vector distance computations in an ephemeral directory. |
| **Redis** | Unit / Integration / E2E | `FakeRedisClient` | In-memory dictionary provides deterministic hashing and TTL testing without requiring Docker or Redis server. |
| **FastAPI** | Integration / E2E | Real `TestClient` | Executes full ASGI request parsing, dependency injection, and schema validation. |
| **React UI** | Frontend Unit | Vitest + RTL + Mocked `fetch` | Verifies DOM behavior and user interactions deterministically. |

---

## 10. Upload Cleanup Resource Bug and Resolution

### Root Cause
In Phase 11, `POST /api/v1/documents/upload` streamed uploaded files into `data/uploads/{uuid}_{filename}`. On successful ingestion, `DocumentUploadResponse` was returned without unlinking the staged file. As a result, orphan test files accumulated indefinitely on disk.

### Solution
Modified `backend/app/api/routes_documents.py` to ensure safe cleanup in the `finally:` block:
```python
finally:
    await file.close()
    if staged_path.exists():
        try:
            staged_path.unlink(missing_ok=True)
        except Exception as cleanup_err:
            logger.warning("Failed to remove staged file '%s': %s", staged_path, cleanup_err)
```
- Cleanup executes after both successful and failed ingestion.
- Original exceptions are preserved.
- Missing files are handled harmlessly.
- Verified by regression tests `test_21_staged_file_cleaned_up_after_successful_ingestion` and `test_22_staged_file_cleaned_up_after_failed_ingestion`.

---

## 11. ChromaDB Testing

- Tests verify collection creation, persistence reopening, vector insertion, metadata sanitization, chunk retrieval, ID-based deletion, and source-based deletion.
- All ChromaDB tests run against isolated `tmp_path` directories with automatic teardown, guaranteeing zero contamination of development data.

---

## 12. Redis Testing

- Verified fail-open contract:
  - Redis GET failure -> warning logged, treated as cache miss, RAG executes normally.
  - Redis SET failure -> warning logged, response returned to user without interruption.
  - Corrupt cached payload -> treated as cache miss.
  - Redis outage during document upload -> `cache.clear()` failure logged as non-fatal warning; document upload succeeds.

---

## 13. Embedding Testing

- Uses modern `gemini-embedding-2` model architecture as established in Phase 5.
- Normal test suites never contact Google Gemini servers.
- `FakeEmbeddingService` provides deterministic semantic vector projection:
  - Known conceptual anchors (`nexusrag`, `genworx`, `leave`, `policy`) map to dedicated vector dimensions with elevated weights.
  - Other tokens map deterministically via token hashing.
  - Vectors are L2-normalized so Euclidean distance calculations in ChromaDB behave predictably.

---

## 14. LLM Testing

- Normal test suites never contact OpenRouter or Gemini LLMs.
- Mocked unit tests verify retry policies:
  - Transient errors (HTTP 429, 500, 503) trigger exponential backoff retry.
  - Permanent errors (HTTP 401, 403, 400) fail immediately without retry.
  - Timeouts and malformed responses are translated into `LLMProviderError` and `LLMResponseError`.

---

## 15. FastAPI Testing

- Tests use `FastAPI TestClient` and dependency injection overrides (`app.dependency_overrides`).
- Verified status mappings:
  - `200 OK`: Successful chat response, successful document upload, health check.
  - `400 Bad Request`: Unsupported extension, empty file, blank filename.
  - `413 Content Too Large`: File exceeding 10 MB limit.
  - `422 Unprocessable Entity`: Schema validation failure, empty/whitespace question, document with zero extractable text.
  - `502 Bad Gateway`: Upstream LLM provider failure (`LLMProviderError`).
  - `500 Internal Server Error`: Vector search failure or unhandled exception.

---

## 16. Frontend Testing

- 21 Vitest unit and integration tests across 3 test modules:
  - `chat.test.jsx` (11 tests): Navbar rendering, health status ("Connected" / "Offline"), input validation, character limit (2,000), Enter to submit, message rendering, source citations, loading indicator, 500/502 error toasts.
  - `upload.test.jsx` (6 tests): Dropzone rendering, client-side format rejection (.exe), 10MB limit enforcement, zero-byte file check, FormData dispatch, chunk count notification.
  - `routing.test.jsx` (4 tests): Direct navigation to `/chat`, `/documents`, root redirect (`/` -> `/chat`), and navigation link switching between views.

---

## 17. Code Coverage Results

Measured using `pytest-cov` on `backend/app/`:
```
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
backend\app\api\dependencies.py                49      3    94%   62-67
backend\app\api\routes_chat.py                 27      4    85%   65-72
backend\app\api\routes_documents.py            74      8    89%   146, 160, 166, 180-187, 197-198
backend\app\api\routes_health.py                8      0   100%
backend\app\cache\redis_cache.py              177     37    79%   66, 73, 92-96, 202-203, ...
backend\app\chunking\chunker.py                51      0   100%
backend\app\core\config.py                    168     17    90%   208, 212, 216, 220, ...
backend\app\core\logging.py                    66     15    77%   36-37, 96-109
backend\app\embeddings\embedder.py            133     12    91%   76, 81, 86, 91, ...
backend\app\ingestion\document_service.py      64      7    89%   50, 119-121, 139, 151-152
backend\app\ingestion\loader.py               113     17    85%   77, 83, 109, 158-162, ...
backend\app\ingestion\pipeline.py              46      0   100%
backend\app\llm\llm_service.py                 24      1    96%   109
backend\app\llm\openrouter.py                  79     14    82%   103-105, 124, 145-147, ...
backend\app\main.py                            28      2    93%   62-63
backend\app\models\requests.py                 11      1    91%   33
backend\app\models\responses.py                25      0   100%
backend\app\prompts\templates.py               25      1    96%   61
backend\app\rag\pipeline.py                   106      6    94%   359, 362-363, 371, 378-379
backend\app\retrieval\retriever.py             66      1    98%   223
backend\app\vectordb\chroma_store.py          157     32    80%   126-131, 146, ...
-------------------------------------------------------------------------
TOTAL                                        1523    178    88%
```
Overall coverage: **88%**. Critical business logic (`chunker`, `pipeline`, `retriever`, `rag`, `models`) achieved **≥ 90%** coverage.

---

## 18. Test Commands

### Backend Suite
```powershell
# Run full backend test suite (158 tests)
d:\Academic-Projects\RAG\.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Run with line coverage
d:\Academic-Projects\RAG\.venv\Scripts\python.exe -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing

# Run E2E integration tests only
d:\Academic-Projects\RAG\.venv\Scripts\python.exe -m pytest backend/tests/test_e2e_integration.py -v
```

### Frontend Suite
```powershell
# Run Vitest test suite (21 tests)
cd frontend
npm test

# Run frontend production build validation
npm run build
```

---

## 19. CI Readiness

The test suite satisfies all requirements for automated headless Continuous Integration (CI):
- **Zero Secrets:** Requires no live API keys for Gemini or OpenRouter.
- **Zero Daemons:** Requires no active Redis service or ChromaDB server.
- **Cross-Platform Paths:** Uses `pathlib.Path` throughout.
- **No Residual Side Effects:** All files write to OS temporary directories (`tmp_path`) and are automatically reclaimed.
- **Fast Feedback:** Entire test suite runs in under 10 seconds.

---

## 20. Failure Testing

Failure handling verified through automated tests:
1. **Empty Query:** Rejected with 422 before reaching the retriever.
2. **Excessive Query (>2,000 chars):** Rejected with 422 by Pydantic.
3. **No Context Match:** Returns polite fallback answer without invoking the LLM.
4. **LLM Provider 5xx/429:** Mapped cleanly to HTTP 502 Bad Gateway.
5. **ChromaDB Outage:** Mapped cleanly to HTTP 500 Internal Server Error.
6. **Redis Network Outage:** Fail-open; query answered via live RAG.
7. **Corrupt Uploaded File:** Caught and mapped to HTTP 422 Unprocessable Entity.
8. **Staging Cleanup on Error:** Files deleted from disk even when indexing fails.

---

## 21. Design Decisions

1. **Deterministic Concept-Anchored Fake Embeddings:** Rather than returning flat constant vectors or random floats, `FakeEmbeddingService` maps known domain keywords (`nexusrag`, `genworx`, `policy`, `leave`) to specific vector dimensions and applies L2 normalization. This enables realistic similarity ranking in ChromaDB tests without calling external APIs.
2. **Resource Cleanup in `finally:` Block:** Staging cleanup in `routes_documents.py` executes inside `finally:`, ensuring temporary upload files are unlinked on both 200 successes and 4xx/5xx failures.
3. **Centralized Fixtures via `conftest.py`:** Fixtures are registered in `backend/tests/conftest.py` so new test modules can immediately leverage `fake_embedding_service`, `fake_llm_service`, `fake_redis_client`, and `tmp_chroma_store` without duplicating test doubles.

---

## 22. Limitations

1. **Optical Character Recognition (OCR):** Scanned PDF documents containing only rasterized images without an OCR text layer are identified as having zero extractable text (`EmptyContentError`) and rejected with HTTP 422. Handling rasterized scans requires an OCR pipeline.
2. **In-Memory Redis Simulation:** `FakeRedisClient` operates strictly in-memory. While it faithfully validates key generation, TTL, metrics, and fail-open fallbacks, testing Redis cluster failover or distributed locks requires containerized integration testing.

---

## 23. Future Improvements

1. **CI/CD Pipeline Workflow:** Implement a GitHub Actions workflow executing backend pytest, frontend vitest, and frontend build on every pull request.
2. **Contract Testing with OpenAPI:** Add automated schema diffing between the backend `/openapi.json` specification and frontend API client types.
3. **Containerized Integration Suite:** Establish an optional integration suite running against actual Docker containers for Redis and ChromaDB under an `@pytest.mark.docker` marker.

---

## 24. Interview Questions and Answers

### Q1: What is the Test Pyramid, and why is it important in RAG systems?
**A:** The test pyramid organizes tests into Unit (base, highest volume), Integration (middle), and End-to-End (top, smallest volume). In RAG systems, external LLM and embedding APIs are slow, expensive, and non-deterministic. Placing the bulk of testing at the unit and boundary-integration layers using deterministic doubles enables sub-second test execution and stable CI, reserving E2E tests for verifying critical user journeys.

### Q2: What is the difference between a Mock, a Stub, and a Fake?
**A:**
- **Stub:** Returns canned, static data without logic (e.g. `mock.return_value = "hello"`).
- **Mock:** Verifies behavior, interaction, and protocol contracts (e.g. asserting a method was called once with specific parameters).
- **Fake:** A lightweight, working implementation with actual internal state (e.g. `FakeRedisClient` using a Python dictionary, or `FakeEmbeddingService` using token hashing and L2 normalization).

### Q3: Why is test isolation critical, and how was it enforced in NexusRAG?
**A:** Test isolation guarantees that tests execute independently of execution order and leave no side effects. In NexusRAG:
1. ChromaDB instances are isolated using pytest's `tmp_path` fixture.
2. Redis query caching uses ephemeral in-memory dictionary clients.
3. Document staging files in `data/uploads/` are unlinked in the route's `finally:` block.

### Q4: How does NexusRAG verify fail-open behavior for Redis caching?
**A:** Tests inject failure into `FakeRedisClient` by configuring `raises_on_get=True` or `raises_on_set=True` to raise `ConnectionError`. The tests verify that `RedisQueryCache` catches the error, logs a warning, tracks the error in metrics, and allows the RAG pipeline to continue live retrieval and generation without surfacing a 500 error to the user.

### Q5: What is the difference between Software Testing (Phase 13) and RAG Evaluation (Phase 14)?
**A:**
- **Software Testing (Phase 13):** Verifies deterministic system correctness — do API routes return correct status codes, are files cleaned up, are cache keys generated deterministically, and are exceptions caught properly?
- **RAG Evaluation (Phase 14):** Measures informational retrieval and answer quality — is the retrieved context relevant, does the LLM hallucinate, and is the answer faithful to the source documents?

---

## 25. Chat Persistence & Multi-Conversation Feature

### Previous Problem: ChatPage State Loss on Navigation

The original `useChat` hook stored all conversation messages in local React `useState`. When the user navigated from `/chat` to `/documents`, the `ChatPage` component unmounted, destroying all conversation state. Returning to `/chat` re-mounted the component with a fresh empty state — all messages were permanently lost.

**Root Cause:** React component-local state has the same lifetime as the component. No mechanism preserved messages across unmount/remount cycles.

### Solution: React Context + localStorage

The fix uses the **React Context + localStorage** pattern:

1. A new `ConversationContext` (`frontend/src/context/ConversationContext.jsx`) owns all conversation state at the App level.
2. `App.jsx` wraps the router in `<ConversationProvider>`, so state survives route changes regardless of which page is mounted.
3. `useChat.js` reads/writes conversations via `useConversation()` instead of `useState`. Only ephemeral state (`isLoading`, `error`) remains in local hook state — these are never persisted.

### localStorage Decision

Browser `localStorage` was chosen because:
- It is frontend-only (no backend API needed).
- It persists across browser refreshes.
- It works without authentication or user accounts.
- It requires no additional dependencies.

**Key:** `nexusrag:chat-history:v1` (versioned for future migration).

### Conversation Data Model

```js
{
  id: string,          // unique id generated from Date.now() + Math.random()
  title: string,       // "New Chat" → derived from first user message
  createdAt: string,   // ISO date string
  updatedAt: string,   // ISO date string (updated on each message)
  messages: [
    {
      id: string,
      role: "user" | "assistant",
      content: string,
      timestamp: string,    // ISO string (not Date object — JSON-safe)
      // assistant messages only:
      sources: [...],
      model: string,
      context_chunks_used: number,
      isError?: boolean
    }
  ]
}
```

**Loading state is never persisted.** The `isLoading` flag lives only in `useChat`'s local state.

### activeConversationId

The context tracks which conversation is currently displayed via `activeConversationId`. On load from localStorage, if the stored active ID no longer exists in the conversation list, the system falls back to the first conversation.

### Persistence Lifecycle

1. **App start:** `ConversationProvider` reads `nexusrag:chat-history:v1` from localStorage.
2. **Safe parse:** Invalid JSON, missing arrays, or invalid structures silently fall back to a new empty conversation.
3. **Message append:** `appendMessage()` updates context state → React re-renders → `useEffect` writes new state to localStorage.
4. **First save skip:** The `isFirstRender` ref prevents writing to localStorage on initial mount (we just read from it).
5. **Tab/refresh:** Next browser session reads the saved data.

### Navigation Behavior

`ConversationProvider` wraps the top-level `<Routes>`. Because it sits above the router outlet, it does not unmount when `ChatPage` unmounts. Messages are preserved.

```
App
 └── ConversationProvider  ← state lives here, never unmounts
      └── Navbar
      └── <Routes>
           ├── /chat → ChatPage (mounts/unmounts on navigation)
           └── /documents → DocumentsPage (mounts/unmounts on navigation)
```

### Browser Refresh Behavior

Because all conversation state is serialized to `nexusrag:chat-history:v1` on every state change, a browser refresh immediately restores the full conversation list including all messages and source citations.

### New Chat Button Behavior

1. Clicking "+ New Chat" calls `createNewConversation()`.
2. If the active conversation is already empty (zero messages), the call is a no-op — no duplicate empty conversations are created.
3. Otherwise, a new conversation is created with `id = generateId()`, `title = "New Chat"`, and `messages = []`.
4. The new conversation becomes `activeConversationId`.
5. All previous conversations are preserved.

### Conversation Title Behavior

- New conversations start with `title = "New Chat"`.
- After the first user message, `deriveTitle(question)` is called:
  - Takes the first 6 words of the question.
  - Caps at 60 characters.
  - Deterministic — no API call, no LLM request.

```
"What is our company's remote work policy?" → "What is our company's remote"
"Leave allowance question"                  → "Leave allowance question"
""                                          → "New Chat"
```

### Malformed Storage Handling

`loadFromStorage()` wraps `JSON.parse` in a try/catch. If any of these conditions are true, the stored data is ignored and a fresh empty conversation is created:
- JSON parse throws (syntax error)
- `conversations` is not an array
- `conversations` is empty
- `activeConversationId` is not a string
- Any conversation object missing `id`, `title`, or `messages` fields

### Tests Added (18 Cases in `conversations.test.jsx`)

| # | Test Description |
| :---: | :--- |
| 1 | Empty localStorage creates exactly one valid new conversation |
| 2 | Existing conversations are restored from localStorage on mount |
| 3 | Messages inside a conversation are restored from localStorage |
| 4 | `activeConversationId` is restored from localStorage |
| 5 | Invalid `activeConversationId` falls back to first valid conversation |
| 6 | Malformed localStorage JSON falls back to a fresh empty conversation |
| 6b | Missing conversations array falls back gracefully |
| 7 | `appendMessage` adds a user message to the active conversation |
| 8 | `appendMessage` adds an assistant message with sources |
| 9 | Chat messages survive navigation Chat → Documents → Chat |
| 10 | Unmounting and remounting `ConversationProvider` restores from localStorage |
| 11 | "+ New Chat" button is rendered in the Navbar |
| 12 | Clicking "+ New Chat" on a non-empty conversation creates a new empty one |
| 13 | Previous conversation is still in storage after creating a New Chat |
| 14 | After clicking New Chat, the new conversation becomes active |
| 15 | New Chat does NOT create a duplicate when active conversation is already empty |
| 16 | `deriveTitle` generates deterministic titles from user questions |
| 17 | Source citations in assistant messages are preserved after localStorage restore |
| 18 | ChatPage renders correctly inside ConversationProvider (regression guard) |

### Test Counts After Chat Persistence Feature

| Suite | Before | After | Delta |
| :--- | :---: | :---: | :---: |
| Frontend (Vitest) | 21 | **40** | +19 tests |
| Backend (pytest) | 158 | 158 | unchanged |
| **Total** | **179** | **197** | **+18 tests** |

### Limitations of localStorage

- **Per-browser, per-device:** Conversations are not synced across devices or browsers.
- **Storage quota:** Browsers typically allow 5–10 MB. Very long conversations with large text answers could approach this limit.
- **No user isolation:** Any code on the same origin can read/write the key.

### Future: Production Migration to Server-Side Persistence

When multi-user support or cross-device sync is needed:
1. Add a `POST /api/v1/conversations` endpoint to persist conversations to PostgreSQL or Redis.
2. Add a `GET /api/v1/conversations` endpoint to restore them on login.
3. Replace `localStorage` calls in `ConversationContext` with API calls.
4. `ConversationProvider` and the conversation data model remain structurally unchanged — only the persistence layer changes.

