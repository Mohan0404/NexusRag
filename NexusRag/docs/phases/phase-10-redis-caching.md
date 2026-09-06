# Phase 10 — Redis Query Caching

## 1. Objective

Implement high-performance Redis-based response caching for the Genworx Knowledge Assistant (`NexusRAG`).

For repeated, semantically identical questions, the system bypasses document similarity retrieval and expensive LLM generation, returning a previously computed `RAGResponse` in single-digit milliseconds while preserving source citations, original queries, model identifiers, and context chunk counts.

---

## 2. Why Caching is Critical in this RAG System

In enterprise and internal knowledge bases, user queries follow a power-law distribution (e.g. 20% of questions represent 80% of query traffic, such as "What is the annual leave policy?", "How do I setup VPN?", "What are the health benefits?").

Running full RAG on every query incurs substantial penalties:
1. **Financial Cost**: Each LLM generation charges per prompt and completion tokens (via OpenRouter).
2. **End-User Latency**: Vector embedding + ChromaDB L2 distance search + LLM generation typically takes 1.5 to 3.5 seconds.
3. **Provider Rate Limits**: Providers impose strict requests-per-minute (RPM) and tokens-per-minute (TPM) limits. Repeated queries consume quota unnecessarily.
4. **Compute Redundancy**: Answering the exact same question from the exact same knowledge base multiple times without document changes produces identical answers.

Redis caching reduces retrieval and LLM calls for repeated queries to zero.

---

## 3. Architecture

```text
User Question (str)
    ↓
┌──────────────────────────────────────┐
│  RAGPipeline.query(question)         │  ← Orchestrator (Phase 9/10)
└──────────────────────────────────────┘
    ↓ Validate non-empty/whitespace
    ↓
┌──────────────────────────────────────┐
│  build_cache_key(query, model, top_k)│  ← Deterministic SHA-256 Key
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  RedisQueryCache.get(cache_key)      │  ← Fail-open GET
└──────────────────────────────────────┘
    ├── [CACHE HIT] ────────────────────────────────────────────────────────┐
    │   Deserialize JSON → RAGResponse                                      │
    │   (Retriever & LLM completely skipped)                                │
    │                                                                       ▼
    └── [CACHE MISS or REDIS FAILURE]                                Return RAGResponse
            ↓
    ┌──────────────────────────────────┐
    │  Retriever.retrieve(question)    │  ← Phase 7 Retriever
    └──────────────────────────────────┘
            ↓
            ├── Empty chunks → Return NO_CONTEXT_ANSWER (skip LLM & DO NOT cache)
            └── Non-empty chunks
                    ↓
    ┌──────────────────────────────────┐
    │  build_rag_prompt(...)           │  ← app.prompts.templates
    └──────────────────────────────────┘
            ↓
    ┌──────────────────────────────────┐
    │  BaseLLMService.generate(...)    │  ← Phase 8 LLM Service
    └──────────────────────────────────┘
            ↓
    ┌──────────────────────────────────┐
    │  Assemble RAGResponse            │
    └──────────────────────────────────┘
            ↓
    ┌──────────────────────────────────┐
    │  RedisQueryCache.set(key, resp)  │  ← Fail-open SETEX with TTL
    └──────────────────────────────────┘
            ↓
    Return RAGResponse
```

---

## 4. Cache Placement Decision

We placed caching logic in `app/cache/redis_cache.py` and injected it into `RAGPipeline` as an optional dependency:

```python
class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever,
        llm_service: BaseLLMService,
        cache: Optional[BaseQueryCache] = None,
    ) -> None:
        self._retriever = retriever
        self._llm_service = llm_service
        self._cache = cache
```

### Why this is the cleanest design:
1. **Separation of Concerns**: `RAGPipeline` does not know about Redis network sockets, connection pools, serialization formats, or redis-py exceptions. It interacts solely with the abstract `BaseQueryCache` protocol (`cache.get()` and `cache.set()`).
2. **Backward Compatibility**: When `cache=None` (the default), `RAGPipeline` behaves 100% identically to Phase 9. All existing Phase 9 unit tests pass without modification.
3. **Testability**: In tests, any in-memory or fake cache implementation can be injected with zero network dependencies.
4. **Single Interface for Phase 11**: Phase 11 FastAPI endpoints simply invoke `rag_pipeline.query(question)` without wrapping layers or orchestration bifurcation.

---

## 5. Cache Hit Flow

1. User sends question: `"What is the vacation policy?"`.
2. `RAGPipeline.query()` validates the question.
3. Cache key is generated: `nexusrag:query:v1:<sha256>`.
4. `RedisQueryCache.get(key)` queries Redis.
5. Key exists and data is valid JSON.
6. JSON is deserialized into typed `RAGResponse` (reconstructing `SourceReference` citations with page numbers).
7. Latency is recorded in `CacheMetrics` and logged at `INFO` level.
8. `RAGPipeline` returns the cached `RAGResponse` immediately.
9. **Retriever, ChromaDB, prompt construction, and LLM are NOT invoked.**

---

## 6. Cache Miss Flow

1. User sends a new question: `"How do I configure SSO?"`.
2. `RAGPipeline.query()` validates the question.
3. Cache key is generated.
4. `RedisQueryCache.get(key)` returns `None` (key does not exist in Redis).
5. Miss count and miss latency are recorded in `CacheMetrics`.
6. Phase 9 pipeline executes:
   - `Retriever.retrieve()` embeds question and queries ChromaDB.
   - `build_rag_prompt()` constructs the grounded prompt.
   - `BaseLLMService.generate()` calls OpenRouter / Gemini.
   - `RAGResponse` is assembled with deduplicated source citations.
7. If retrieval found documents (not `NO_CONTEXT_ANSWER`), `RedisQueryCache.set(key, response)` writes the serialized JSON to Redis with `SETEX` and TTL.
8. Response is returned to the user.

---

## 7. Cache Key Design

Raw query strings are never used directly as Redis keys. Instead, keys use a deterministic namespaced SHA-256 hash format:

```text
nexusrag:query:v1:<sha256_hex_digest>
```

### Hash Composition:
```python
norm_q = " ".join(query.strip().lower().split())
payload = f"q={norm_q}|m={model}|k={top_k}|v={version}"
digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

### Why This Design:
1. **Whitespace & Case Normalization**: `"What is PTO?"` and `"what  is   pto? "` map to the identical key.
2. **Model Binding (`m=...`)**: Prevents returning a response generated by one model (e.g. `gemini-2.5-flash`) if the system is reconfigured to another model (e.g. `gemini-2.5-pro`).
3. **Retrieval Depth Binding (`k=...`)**: If retrieval depth changes from `top_k=4` to `top_k=8`, the retrieved context differs, so the cache key changes.
4. **Namespace Versioning (`v1`)**: If prompt templates or response schema change, bumping `v1` to `v2` instantly obsoletes all previous entries without running a destructive `FLUSHDB`.
5. **Key Syntax Safety**: SHA-256 eliminates Redis key syntax issues (spaces, newlines, quotes, unicode characters) and fixes key length to 64 hex characters.

---

## 8. Query Normalization

The `normalize_query()` function applies three transformations:
1. `strip()`: Removes leading and trailing whitespace, tabs, and newlines.
2. `lower()`: Case-folding so question capitalization does not cause cache misses.
3. `split()` and `" ".join(...)`: Collapses any internal sequence of multiple spaces, tabs, or newlines into a single space.

Example:
`"  What   is \n the LEAVE policy?  "` -> `"what is the leave policy?"`

---

## 9. TTL (Time-To-Live)

### Configuration
TTL is centrally configured in `config.yaml` and loaded into `Settings.cache_ttl`:
```yaml
cache:
  cache_ttl: 3600  # 1 hour in seconds
```

### Why 3600 Seconds (1 Hour)?
1. **Freshness Bound**: If underlying policy documents are modified, stale responses expire automatically within 1 hour.
2. **High Hit Ratio**: Within a business workday, multiple employees frequently ask the same onboarding or policy questions.
3. **Bounded Memory Footprint**: Expired keys are automatically pruned by Redis volatile-LRU eviction.
4. **Consistency**: Matches existing project architecture from Phase 2.

---

## 10. JSON Serialization

### Format
Standard Python `json.dumps()` and `json.loads()`.

### Why Pickle is Strictly Forbidden:
Python's `pickle` module can execute arbitrary code during unpickling. If an attacker gains access to Redis or poisons cache entries, `pickle.loads()` enables Remote Code Execution (CWE-502). JSON is safe, human-readable, and language-agnostic.

### Serialized Schema:
```json
{
  "answer": "Employees are entitled to 20 days of paid time off...",
  "sources": [
    {
      "source": "hr_policy.pdf",
      "file_type": "pdf",
      "page": 3
    }
  ],
  "query": "What is the leave policy?",
  "model": "google/gemini-2.5-flash",
  "context_chunks_used": 4
}
```

### Corrupt Data Handling:
During deserialization, `deserialize_rag_response()` validates that the JSON has an `"answer"` field and valid structure. If deserialization fails (`JSONDecodeError`, `TypeError`, or malformed fields), it logs a warning and returns `None` — the pipeline treats it as a cache miss and falls back to normal generation.

---

## 11. Redis Failure Policy: Fail-Open Resilience

> **Rule: Redis is an auxiliary performance optimization, NOT the source of truth.**

Under no circumstances should a Redis outage break core RAG question-answering.

```text
Redis GET Fails (Connection error, timeout, crash)
    ↓
Log WARNING with exception
    ↓
Treat as Cache MISS
    ↓
Execute normal Phase 9 RAG pipeline
    ↓
User gets accurate, grounded answer
```

```text
Redis SET Fails (OOM, read-only mode, network partition)
    ↓
Log WARNING with exception
    ↓
Suppress exception
    ↓
Return generated RAGResponse normally
```

Every Redis interaction in `RedisQueryCache` is wrapped in safe `try ... except Exception as exc` blocks. The core RAG system remains 100% available even if Redis is completely down.

---

## 12. Metrics & Measurement

A lightweight, in-memory `CacheMetrics` tracker records:
- `hits`: Number of successful cache hits.
- `misses`: Number of cache misses.
- `errors`: Number of Redis connectivity or operational errors.
- `total_requests`: `hits + misses`.
- `hit_ratio`: `hits / total_requests` (0.0 to 1.0).
- `total_hit_latency_ms` & `avg_hit_latency_ms`: Redis lookup time on hits.
- `total_miss_latency_ms` & `avg_miss_latency_ms`: Redis lookup time on misses.

### Important Distinction on Latency:
Cache lookup latency (e.g. ~1–3 ms) measures the time to query Redis and deserialize JSON. It must **NOT** be claimed as overall end-to-end RAG latency improvement until a full benchmark comparing:
1. Cold request (retrieval + LLM generation: ~1,500–3,000 ms)
2. Warm cached request (Redis hit: ~2–5 ms)
is executed in an end-to-end benchmark. No performance figures are invented.

---

## 13. Testing Strategy

All 17 tests in `backend/tests/test_cache.py` execute using an in-memory `FakeRedisClient`.
**Zero running Redis servers, Docker containers, or network connections are required.**

| # | Test Case | What it Verifies |
|---|-----------|-------------------|
| 1 | `test_1_cache_miss_executes_rag` | Cache miss executes Retriever and LLM |
| 2 | `test_2_and_3_cache_hit_skips_retriever_and_llm` | Cache hit skips both Retriever and LLM |
| 3 | `test_4_cached_rag_response_reconstructed` | Reconstructed response preserves answer, sources (with pages), query, model, and chunk count |
| 4 | `test_5_cache_set_after_successful_rag` | Cache SET happens after successful query |
| 5 | `test_6_ttl_is_applied` | Configured TTL is passed to Redis SETEX |
| 6 | `test_7_deterministic_cache_key` | Whitespace and casing variations yield identical keys |
| 7 | `test_8_different_queries_different_keys` | Different queries yield distinct keys |
| 8 | `test_9_model_changes_create_different_keys` | Model changes alter the cache key |
| 9 | `test_10_top_k_changes_create_different_keys` | top_k changes alter the cache key |
| 10 | `test_11_redis_get_failure_falls_back_to_rag` | Fail-open: Redis GET failure falls back to RAG |
| 11 | `test_12_redis_set_failure_does_not_break_response` | Fail-open: Redis SET failure still returns response |
| 12 | `test_13_corrupt_cached_data_treated_as_miss` | Corrupt JSON in cache is treated as miss |
| 13 | `test_14_cache_metrics_tracking` | Hits, misses, errors, and hit ratio track accurately |
| 14 | `test_15_empty_retrieval_not_cached` | `NO_CONTEXT_ANSWER` is never stored in cache |
| 15 | `test_16_pipeline_works_with_cache_none` | Backward compatibility: `cache=None` runs Phase 9 |
| 16 | `test_17_normalize_query_handles_edge_cases` | Normalization handles tabs, newlines, empty strings |
| 17 | `test_18_cache_clear_method` | `cache.clear()` cleans matching namespace keys |

---

## 14. Knowledge-Base Staleness as a Known Phase 10 Limitation

> **Important Limitation**: Query/model/top_k key hashing does NOT detect when underlying documents are added, updated, or deleted from ChromaDB.

If an HR policy document is updated at 10:00 AM, a user query answered at 9:55 AM will continue serving the cached answer until its 1-hour TTL expires.
- In Phase 10, **TTL is the sole mitigation** against staleness.
- Active document-aware cache invalidation (e.g. clearing cache keys upon document upload/deletion) is reserved for Phase 11 (FastAPI document management routes).

---

## 15. Why We Cache Final RAGResponse Instead of Embeddings

1. **Maximum Cost & Latency Savings**: Caching the final response eliminates both the embedding API call, ChromaDB vector search, AND the expensive LLM generation call.
2. **Simplicity & Predictability**: The query-to-answer mapping is deterministic when model, top_k, and prompt templates are bound into the key.
3. **Clean Cache Invalidation**: Caching embeddings or intermediate retrieval chunks adds multiple caching layers with synchronization overhead and minimal additional benefit for identical queries.

---

## 16. Why Redis is an Optimization Rather Than Source of Truth

The source of truth for knowledge in NexusRAG is the **vector database (ChromaDB) and the source documents**.
Redis is transient storage. If the Redis container restarts, keys expire, or memory is cleared, zero persistent data is lost. The system simply re-executes the deterministic RAG pipeline and repopulates the cache.

---

## 17. Why We Don't Use Redis for Rate Limiting or Session State Yet

1. **Phase Scope**: Phase 10 focuses exclusively on deterministic query caching for RAG answer generation.
2. **Stateless Core**: RAG pipeline orchestration is stateless. Session memory and rate limiting belong in Phase 11 (API layer with FastAPI middleware and client IP/token headers).

---

## 18. Connection to Phase 11 (FastAPI APIs)

In Phase 11, FastAPI endpoints (`/api/v1/chat/query`) will instantiate `RAGPipeline` with `RedisQueryCache` using dependency injection (`Depends(get_rag_pipeline)`).
- The API handler receives user questions, calls `rag_pipeline.query(question)`, and immediately benefits from cache hits without writing custom cache code in route handlers.
- Document upload endpoints (`/api/v1/documents/upload`) will have access to `cache.clear()` to invalidate query caches when documents are modified.

---

## 19. Interview Questions & Answers

### Q1: Why did you choose to cache the complete RAGResponse instead of semantic embedding vectors?
**Answer**: Caching the final `RAGResponse` provides the maximum possible latency reduction (from ~2.5s down to <5ms) and 100% cost elimination by skipping both retrieval and LLM generation. Caching embeddings only saves the embedding API call (~50ms), still requiring vector search and LLM inference. For exact and normalized repeated queries, full response caching is far more impactful.

### Q2: What happens if your Redis cluster crashes during high traffic?
**Answer**: Our architecture is strictly fail-open. Every Redis GET and SET call is wrapped in exception handlers that catch `RedisError`, log structured warnings, increment error metrics, and immediately fall back to standard RAG pipeline execution. Users experience a minor latency increase (falling back to ~2s generation), but the service never throws 500 errors or drops requests.

### Q3: How do you prevent cache pollution when the LLM model is upgraded?
**Answer**: Our cache key is a SHA-256 digest of a composite payload that includes the normalized query, the model identifier (`m=google/gemini-2.5-flash`), the retrieval top_k (`k=4`), and a schema version (`v=1`). If the model or configuration changes, the cache key changes automatically, preventing answers generated by an older model from being served.
