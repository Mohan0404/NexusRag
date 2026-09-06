"""Phase 10 — Redis Query Caching tests.

All unit tests use an in-memory FakeRedisClient or MagicMock.
Zero external network, Docker, or running Redis daemon required.

Verifies:
1. Cache miss executes RAG (Retriever + LLM called)
2. Cache hit skips Retriever
3. Cache hit skips LLM
4. Cached RAGResponse is correctly reconstructed (answer, sources, query, model, context_chunks)
5. Cache SET occurs after successful RAG
6. TTL is applied to Redis SETEX
7. Cache key is deterministic across whitespace/casing variations
8. Different queries create different keys
9. Model changes create different keys
10. top_k changes create different keys
11. Redis GET failure falls back to RAG (fail-open)
12. Redis SET failure does not break response (fail-open)
13. Corrupt cached data becomes a miss and falls back to RAG
14. Cache metrics work (hits, misses, errors, hit_ratio, latencies)
15. Empty retrieval (NO_CONTEXT_ANSWER) is NOT cached
16. RAGPipeline still works with cache=None (Phase 9 backward compatibility)
17. Integration test (optional, marked with @pytest.mark.integration)
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
import pytest
import redis

from app.cache.redis_cache import (
    BaseQueryCache,
    CacheMetrics,
    RedisQueryCache,
    build_cache_key,
    deserialize_rag_response,
    normalize_query,
    serialize_rag_response,
)
from app.llm.llm_service import BaseLLMService, LLMResponse
from app.rag.pipeline import (
    NO_CONTEXT_ANSWER,
    RAGPipeline,
    RAGResponse,
    SourceReference,
)
from app.retrieval.retriever import RetrievedChunk, Retriever


# =====================================================================
# In-Memory Fake Redis Client
# =====================================================================


class FakeRedisClient:
    """In-memory Redis mock client for deterministic zero-daemon unit tests."""

    def __init__(
        self,
        raises_on_get: bool = False,
        raises_on_set: bool = False,
    ) -> None:
        self._store: Dict[str, str] = {}
        self._ttls: Dict[str, int] = {}
        self.raises_on_get = raises_on_get
        self.raises_on_set = raises_on_set
        self.get_calls = 0
        self.set_calls = 0
        self.setex_calls = 0

    def get(self, key: str) -> Optional[str]:
        self.get_calls += 1
        if self.raises_on_get:
            raise redis.ConnectionError("Simulated Redis connection failure on GET")
        return self._store.get(key)

    def set(self, key: str, value: str) -> bool:
        self.set_calls += 1
        if self.raises_on_set:
            raise redis.ConnectionError("Simulated Redis connection failure on SET")
        self._store[key] = value
        return True

    def setex(self, key: str, time: int, value: str) -> bool:
        self.setex_calls += 1
        if self.raises_on_set:
            raise redis.ConnectionError("Simulated Redis connection failure on SETEX")
        self._store[key] = value
        self._ttls[key] = time
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                count += 1
        return count

    def keys(self, pattern: str) -> List[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]


# =====================================================================
# Test Fixtures & Fakes
# =====================================================================


class FakeLLMService(BaseLLMService):
    """Test LLM service that captures prompt and returns configured response."""

    def __init__(
        self,
        canned_response: str = "This is a generated answer.",
        model: str = "google/gemini-2.5-flash",
    ) -> None:
        self.canned_response = canned_response
        self.model = model
        self.generate_calls: List[str] = []

    def generate(self, prompt: str) -> LLMResponse:
        self.generate_calls.append(prompt)
        return LLMResponse(
            content=self.canned_response,
            model=self.model,
            usage={"total_tokens": 42},
        )


def make_chunk(
    content: str,
    source: str = "doc.pdf",
    page: int = 1,
    file_type: str = "pdf",
) -> RetrievedChunk:
    """Helper to build a realistic RetrievedChunk."""
    return RetrievedChunk(
        content=content,
        metadata={
            "source": source,
            "page": page,
            "file_type": file_type,
            "chunk_index": 0,
        },
        distance=0.15,
    )


# =====================================================================
# Unit Tests
# =====================================================================


def test_1_cache_miss_executes_rag():
    """1. Cache miss causes Retriever and LLM to execute normally."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis, default_ttl=3600)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("PTO is 20 days.", "hr.pdf", 1)]
    fake_llm = FakeLLMService(canned_response="You get 20 days PTO.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)
    response = pipeline.query("How many vacation days do I get?")

    assert response.answer == "You get 20 days PTO."
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 1
    assert fake_redis.get_calls == 1
    assert fake_redis.setex_calls == 1
    assert cache.metrics.misses == 1
    assert cache.metrics.hits == 0


def test_2_and_3_cache_hit_skips_retriever_and_llm():
    """2 & 3. Cache hit skips both Retriever and LLM execution."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis, default_ttl=3600)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("PTO is 20 days.", "hr.pdf", 1)]
    fake_llm = FakeLLMService(canned_response="You get 20 days PTO.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)

    # First query -> Cache MISS
    resp1 = pipeline.query("How many vacation days do I get?")
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 1

    # Second identical query -> Cache HIT
    resp2 = pipeline.query("How many vacation days do I get?")
    assert mock_retriever.retrieve.call_count == 1  # Not incremented!
    assert len(fake_llm.generate_calls) == 1       # Not incremented!
    assert resp2.answer == resp1.answer
    assert cache.metrics.hits == 1
    assert cache.metrics.misses == 1


def test_4_cached_rag_response_reconstructed():
    """4. Deserialized RAGResponse preserves all fields, sources, and page numbers."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    original_response = RAGResponse(
        answer="Remote work allowed up to 3 days/week.",
        sources=[
            SourceReference(source="wfh_policy.pdf", file_type="pdf", page=4),
            SourceReference(source="hr_guidelines.md", file_type="md", page=1),
        ],
        query="What is the remote work policy?",
        model="google/gemini-2.5-flash",
        context_chunks_used=2,
    )

    key = cache.build_key("What is the remote work policy?", model="google/gemini-2.5-flash", top_k=4)
    cache.set(key, original_response)

    cached_response = cache.get(key)
    assert cached_response is not None
    assert cached_response.answer == original_response.answer
    assert cached_response.query == original_response.query
    assert cached_response.model == original_response.model
    assert cached_response.context_chunks_used == 2
    assert len(cached_response.sources) == 2
    assert cached_response.sources[0].source == "wfh_policy.pdf"
    assert cached_response.sources[0].page == 4
    assert cached_response.sources[0].file_type == "pdf"
    assert cached_response.sources[1].source == "hr_guidelines.md"
    assert cached_response.sources[1].page == 1


def test_5_cache_set_after_successful_rag():
    """5. Cache SET occurs after a successful RAG response."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("Context.", "doc.txt", 1)]
    fake_llm = FakeLLMService(canned_response="Answer.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)
    assert len(fake_redis._store) == 0

    pipeline.query("What is the protocol?")
    assert len(fake_redis._store) == 1


def test_6_ttl_is_applied():
    """6. Configured TTL is applied to Redis SETEX."""
    fake_redis = FakeRedisClient()
    custom_ttl = 1800
    cache = RedisQueryCache(redis_client=fake_redis, default_ttl=custom_ttl)

    response = RAGResponse(answer="Answer.", sources=[], query="test", model="m", context_chunks_used=1)
    key = cache.build_key("test")
    cache.set(key, response)

    assert fake_redis.setex_calls == 1
    assert fake_redis._ttls[key] == 1800


def test_7_deterministic_cache_key():
    """7. Whitespace variations and casing differences map to identical cache keys."""
    key1 = build_cache_key("What is the leave policy?", model="gemini", top_k=4)
    key2 = build_cache_key("  what is  the   LEAVE policy?  ", model="gemini", top_k=4)
    key3 = build_cache_key("WHAT IS THE LEAVE POLICY?", model="gemini", top_k=4)

    assert key1 == key2
    assert key2 == key3
    assert key1.startswith("nexusrag:query:v1:")


def test_8_different_queries_different_keys():
    """8. Different queries create distinct cache keys."""
    key1 = build_cache_key("How do I request leave?", model="gemini", top_k=4)
    key2 = build_cache_key("What are the office hours?", model="gemini", top_k=4)

    assert key1 != key2


def test_9_model_changes_create_different_keys():
    """9. Changing the LLM model creates a different cache key."""
    key_flash = build_cache_key("What is X?", model="google/gemini-2.5-flash", top_k=4)
    key_pro = build_cache_key("What is X?", model="google/gemini-2.5-pro", top_k=4)

    assert key_flash != key_pro


def test_10_top_k_changes_create_different_keys():
    """10. Changing top_k creates a different cache key."""
    key_top4 = build_cache_key("What is X?", model="gemini", top_k=4)
    key_top8 = build_cache_key("What is X?", model="gemini", top_k=8)

    assert key_top4 != key_top8


def test_11_redis_get_failure_falls_back_to_rag():
    """11. Redis GET failure logs warning and falls back to normal RAG (fail-open)."""
    failing_redis = FakeRedisClient(raises_on_get=True)
    cache = RedisQueryCache(redis_client=failing_redis)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("Policy text.", "doc.pdf", 1)]
    fake_llm = FakeLLMService(canned_response="Answer during Redis outage.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)

    # Must NOT raise exception despite Redis connection failure
    response = pipeline.query("Does it still work without Redis?")

    assert response.answer == "Answer during Redis outage."
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 1
    assert cache.metrics.errors == 1
    assert cache.metrics.misses == 1


def test_12_redis_set_failure_does_not_break_response():
    """12. Redis SET failure logs warning and still returns generated response."""
    failing_redis = FakeRedisClient(raises_on_set=True)
    cache = RedisQueryCache(redis_client=failing_redis)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("Health benefits info.", "benefits.pdf", 2)]
    fake_llm = FakeLLMService(canned_response="Health insurance is provided.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)

    # Must NOT raise exception despite Redis SET failure
    response = pipeline.query("What about healthcare?")

    assert response.answer == "Health insurance is provided."
    assert cache.metrics.errors == 1


def test_13_corrupt_cached_data_treated_as_miss():
    """13. Malformed JSON in Redis logs warning and falls back to RAG."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    key = cache.build_key("Corrupt query")
    fake_redis._store[key] = "NOT_A_VALID_JSON{{"

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("Fresh context.", "fresh.txt", 1)]
    fake_llm = FakeLLMService(canned_response="Freshly generated answer.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)
    response = pipeline.query("Corrupt query")

    assert response.answer == "Freshly generated answer."
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 1
    assert cache.metrics.misses == 1


def test_14_cache_metrics_tracking():
    """14. Cache metrics accurately track hits, misses, errors, and hit_ratio."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    resp = RAGResponse(answer="A", sources=[], query="q", model="m", context_chunks_used=1)
    key = cache.build_key("q")

    # Initial state
    assert cache.metrics.hits == 0
    assert cache.metrics.misses == 0
    assert cache.metrics.hit_ratio == 0.0

    # 1 Miss
    cache.get(key)
    assert cache.metrics.misses == 1
    assert cache.metrics.hits == 0
    assert cache.metrics.hit_ratio == 0.0

    # Store
    cache.set(key, resp)

    # 1 Hit
    cache.get(key)
    assert cache.metrics.hits == 1
    assert cache.metrics.misses == 1
    assert cache.metrics.total_requests == 2
    assert cache.metrics.hit_ratio == 0.5
    assert cache.metrics.avg_hit_latency_ms >= 0.0

    metrics_dict = cache.get_metrics()
    assert metrics_dict["hits"] == 1
    assert metrics_dict["misses"] == 1
    assert metrics_dict["total_requests"] == 2
    assert metrics_dict["hit_ratio"] == 0.5


def test_15_empty_retrieval_not_cached():
    """15. NO_CONTEXT_ANSWER responses from empty retrieval are NOT cached."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = []  # Empty retrieval!
    fake_llm = FakeLLMService()

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=cache)
    response = pipeline.query("Unknown topic with zero documents")

    assert response.answer == NO_CONTEXT_ANSWER
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 0  # LLM skipped
    assert len(fake_redis._store) == 0        # NOT CACHED!


def test_16_pipeline_works_with_cache_none():
    """16. RAGPipeline instantiated with cache=None functions identically to Phase 9."""
    mock_retriever = MagicMock(spec=Retriever)
    mock_retriever.retrieve.return_value = [make_chunk("Context chunk.", "manual.pdf", 3)]
    fake_llm = FakeLLMService(canned_response="Standard Phase 9 answer.")

    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm, cache=None)
    assert pipeline.cache is None

    response = pipeline.query("What does the manual say?")
    assert response.answer == "Standard Phase 9 answer."
    assert mock_retriever.retrieve.call_count == 1
    assert len(fake_llm.generate_calls) == 1


def test_17_normalize_query_handles_edge_cases():
    """17. Normalization cleanly handles multiline text, tabs, and empty inputs."""
    assert normalize_query("") == ""
    assert normalize_query("   ") == ""
    assert normalize_query("Hello\n\tWorld   RAG  ") == "hello world rag"


def test_18_cache_clear_method():
    """18. Cache clear method deletes keys matching version pattern."""
    fake_redis = FakeRedisClient()
    cache = RedisQueryCache(redis_client=fake_redis)

    key1 = cache.build_key("q1")
    key2 = cache.build_key("q2")
    cache.set(key1, RAGResponse(answer="A1", sources=[]))
    cache.set(key2, RAGResponse(answer="A2", sources=[]))

    assert len(fake_redis._store) == 2
    success = cache.clear()
    assert success is True
    assert len(fake_redis._store) == 0
