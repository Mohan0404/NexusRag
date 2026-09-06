"""Redis Query Caching layer for NexusRAG (Phase 10).

Responsibility:
- Cache successfully generated RAGResponse objects for identical queries.
- Provide deterministic SHA-256 cache key generation.
- Enforce TTL expiration (default 3600s).
- Serialize/deserialize RAGResponse using standard JSON.
- Maintain fail-open resilience (Redis outages never break core RAG).
- Track lightweight in-memory cache metrics (hits, misses, latencies, errors).

This module does NOT:
- Implement embedding caching or retrieval chunk caching (Phase 10 scope).
- Implement document-aware cache invalidation hooks (future phase).
- Implement rate limiting, session storage, or conversation memory.
- Depend on Prometheus, Grafana, or heavy observability libraries.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# =====================================================================
# Cache Metrics
# =====================================================================


@dataclass
class CacheMetrics:
    """Lightweight in-memory metrics for cache performance monitoring.

    Tracks hit/miss counts, Redis operational errors, and lookup latencies.
    Note: Lookup latency measures the Redis GET round-trip, NOT overall RAG latency.
    """

    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_hit_latency_ms: float = 0.0
    total_miss_latency_ms: float = 0.0

    @property
    def total_requests(self) -> int:
        """Total number of cache lookup requests (hits + misses)."""
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        """Ratio of cache hits to total requests (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def avg_hit_latency_ms(self) -> float:
        """Average latency in milliseconds for cache hits."""
        if self.hits == 0:
            return 0.0
        return self.total_hit_latency_ms / self.hits

    @property
    def avg_miss_latency_ms(self) -> float:
        """Average latency in milliseconds for cache misses."""
        if self.misses == 0:
            return 0.0
        return self.total_miss_latency_ms / self.misses

    def to_dict(self) -> Dict[str, Any]:
        """Returns a serializable dictionary of all metrics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_ratio": round(self.hit_ratio, 4),
            "total_hit_latency_ms": round(self.total_hit_latency_ms, 2),
            "total_miss_latency_ms": round(self.total_miss_latency_ms, 2),
            "avg_hit_latency_ms": round(self.avg_hit_latency_ms, 2),
            "avg_miss_latency_ms": round(self.avg_miss_latency_ms, 2),
        }

    def reset(self) -> None:
        """Resets all metrics counters to zero."""
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_hit_latency_ms = 0.0
        self.total_miss_latency_ms = 0.0


# =====================================================================
# Key Generation & Normalization
# =====================================================================


def normalize_query(query: str) -> str:
    """Normalizes query text for deterministic cache lookup.

    Performs:
    1. Leading and trailing whitespace stripping.
    2. Lowercase folding.
    3. Collapsing consecutive internal whitespace into single spaces.

    Args:
        query: Raw query string from the user.

    Returns:
        Normalized query string.
    """
    if not query:
        return ""
    return " ".join(query.strip().lower().split())


def build_cache_key(
    query: str,
    model: str = "",
    top_k: int = 4,
    version: str = "v1",
) -> str:
    """Generates a deterministic namespaced SHA-256 cache key.

    Binds the normalized query, model identifier, retrieval top_k parameter,
    and cache schema version into a fixed-length SHA-256 hash.

    Format:
        nexusrag:query:{version}:{sha256_hexdigest}

    Args:
        query: Raw user query string (normalized internally).
        model: LLM model identifier (e.g. 'google/gemini-2.5-flash').
        top_k: Number of retrieved chunks configured for the query.
        version: Cache schema/namespace version (default 'v1').

    Returns:
        Deterministic Redis key string.
    """
    norm_q = normalize_query(query)
    payload = f"q={norm_q}|m={model.strip()}|k={top_k}|v={version.strip()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"nexusrag:query:{version}:{digest}"


# =====================================================================
# Serialization Helpers (Standard JSON)
# =====================================================================


def serialize_rag_response(response: Any) -> str:
    """Serializes a RAGResponse instance into a clean JSON string.

    Pickle is explicitly avoided for security (CWE-502) and portability.

    Args:
        response: RAGResponse dataclass instance.

    Returns:
        JSON string representation.
    """
    sources_data = [
        {
            "source": s.source,
            "file_type": s.file_type,
            "page": s.page,
        }
        for s in getattr(response, "sources", [])
    ]

    payload = {
        "answer": getattr(response, "answer", ""),
        "sources": sources_data,
        "query": getattr(response, "query", ""),
        "model": getattr(response, "model", ""),
        "context_chunks_used": getattr(response, "context_chunks_used", 0),
    }
    return json.dumps(payload, ensure_ascii=False)


def deserialize_rag_response(raw_json: str) -> Optional[Any]:
    """Deserializes a JSON string into a verified RAGResponse instance.

    Validates schema structure. Malformed, incomplete, or corrupted JSON
    is safely rejected by returning None (treated as a cache miss).

    Args:
        raw_json: Serialized JSON string from Redis.

    Returns:
        RAGResponse instance if valid, None if corrupt or malformed.
    """
    try:
        data = json.loads(raw_json)
        if not isinstance(data, dict):
            logger.warning("Corrupt cached entry: root is not a dictionary.")
            return None

        if "answer" not in data:
            logger.warning("Corrupt cached entry: missing 'answer' field.")
            return None

        # Deferred import to prevent circular import loops
        from app.rag.pipeline import RAGResponse, SourceReference

        raw_sources = data.get("sources", [])
        sources: List[SourceReference] = []
        if isinstance(raw_sources, list):
            for s in raw_sources:
                if isinstance(s, dict):
                    sources.append(
                        SourceReference(
                            source=str(s.get("source", "unknown")),
                            file_type=str(s.get("file_type", "")),
                            page=int(s.get("page", 1)),
                        )
                    )

        return RAGResponse(
            answer=str(data.get("answer", "")),
            sources=sources,
            query=str(data.get("query", "")),
            model=str(data.get("model", "")),
            context_chunks_used=int(data.get("context_chunks_used", 0)),
        )
    except Exception as exc:
        logger.warning("Failed to deserialize cached RAG response: %s", exc)
        return None


# =====================================================================
# Base Cache Interface
# =====================================================================


class BaseQueryCache(ABC):
    """Abstract interface for RAG query result caching."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieves and deserializes a cached RAGResponse by key.

        Args:
            key: Deterministic cache key.

        Returns:
            RAGResponse if cache hit and valid; None on miss, error, or corruption.
        """
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        response: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Serializes and caches a RAGResponse with TTL.

        Args:
            key: Deterministic cache key.
            response: Successful RAGResponse to cache.
            ttl: Optional TTL override in seconds. Defaults to configured TTL.

        Returns:
            True if successfully cached; False on failure or skipped caching.
        """
        pass

    @abstractmethod
    def build_key(self, query: str, model: str = "", top_k: int = 4) -> str:
        """Constructs a deterministic cache key for a query and configuration."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Returns snapshot dictionary of in-memory cache metrics."""
        pass


# =====================================================================
# Redis Query Cache Implementation
# =====================================================================


class RedisQueryCache(BaseQueryCache):
    """Production Redis-based query cache implementation.

    Resilience Policy:
    - FAIL-OPEN: Redis is treated as a performance optimization.
    - If Redis is unreachable, times out, or throws an error, warnings are logged,
      the error is tracked in metrics, and the operation safely returns None (on GET)
      or False (on SET) without raising an exception.
    - Core RAG question-answering remains 100% operational during Redis outages.

    Empty Retrieval Policy:
    - Responses matching NO_CONTEXT_ANSWER are NOT cached to avoid poisoning the
      cache when new documents are ingested.
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        redis_url: Optional[str] = None,
        default_ttl: Optional[int] = None,
        version: str = "v1",
    ) -> None:
        """Initializes the Redis query cache.

        Args:
            redis_client: Pre-configured Redis client (used for unit testing with mocks/fakes).
            redis_url: Redis connection URL (e.g. 'redis://localhost:6379/0').
            default_ttl: Default TTL in seconds. If None, pulled from central Settings.cache_ttl.
            version: Schema namespace version (default 'v1').
        """
        self._version = version
        self._metrics = CacheMetrics()

        settings = get_settings()
        self._default_ttl = (
            default_ttl if default_ttl is not None else settings.cache_ttl
        )

        if redis_client is not None:
            self._client = redis_client
        else:
            url = redis_url or settings.REDIS_URL
            try:
                import redis

                self._client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
                logger.info("RedisQueryCache initialized connecting to %s", url)
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Redis client (%s). Operating in fail-open mode: %s",
                    url,
                    exc,
                )
                self._client = None

    @property
    def metrics(self) -> CacheMetrics:
        """Direct access to the CacheMetrics tracker."""
        return self._metrics

    @property
    def default_ttl(self) -> int:
        """The configured default TTL in seconds."""
        return self._default_ttl

    def build_key(self, query: str, model: str = "", top_k: int = 4) -> str:
        """Constructs a deterministic cache key using the cache's version namespace."""
        return build_cache_key(
            query=query,
            model=model,
            top_k=top_k,
            version=self._version,
        )

    def get(self, key: str) -> Optional[Any]:
        """Looks up a cached RAGResponse by key with fail-open error handling.

        Args:
            key: Deterministic cache key.

        Returns:
            RAGResponse on cache hit; None on miss, corruption, or Redis failure.
        """
        if self._client is None:
            self._metrics.misses += 1
            return None

        start_time = time.perf_counter()
        try:
            raw_data = self._client.get(key)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if raw_data is None:
                self._metrics.misses += 1
                self._metrics.total_miss_latency_ms += latency_ms
                logger.info("Cache MISS: key=%s (latency: %.2f ms)", key, latency_ms)
                return None

            response = deserialize_rag_response(raw_data)
            if response is None:
                # Malformed/corrupt JSON in cache
                self._metrics.misses += 1
                self._metrics.total_miss_latency_ms += latency_ms
                logger.warning(
                    "Cache CORRUPT: key=%s could not be deserialized, treated as MISS",
                    key,
                )
                return None

            self._metrics.hits += 1
            self._metrics.total_hit_latency_ms += latency_ms
            logger.info("Cache HIT: key=%s (latency: %.2f ms)", key, latency_ms)
            return response

        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self._metrics.errors += 1
            self._metrics.misses += 1
            self._metrics.total_miss_latency_ms += latency_ms
            logger.warning(
                "Redis GET failed (fail-open to RAG pipeline): key=%s, error=%s",
                key,
                exc,
            )
            return None

    def set(
        self,
        key: str,
        response: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Caches a successful RAGResponse with TTL.

        Never raises exceptions on Redis failure (fail-open).
        Does NOT cache NO_CONTEXT_ANSWER responses.

        Args:
            key: Deterministic cache key.
            response: RAGResponse to cache.
            ttl: Optional TTL in seconds (defaults to self._default_ttl).

        Returns:
            True if stored in Redis, False if skipped or failed.
        """
        if self._client is None:
            return False

        # Deferred import to check empty retrieval answer
        from app.rag.pipeline import NO_CONTEXT_ANSWER

        if getattr(response, "answer", "") == NO_CONTEXT_ANSWER:
            logger.info("Skipping cache SET for empty retrieval result: key=%s", key)
            return False

        effective_ttl = ttl if ttl is not None else self._default_ttl

        try:
            payload = serialize_rag_response(response)
            if effective_ttl > 0:
                self._client.setex(key, effective_ttl, payload)
            else:
                self._client.set(key, payload)

            logger.info("Cache SET successful: key=%s, ttl=%ds", key, effective_ttl)
            return True
        except Exception as exc:
            self._metrics.errors += 1
            logger.warning(
                "Redis SET failed (non-fatal, continuing): key=%s, error=%s",
                key,
                exc,
            )
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Returns snapshot dictionary of cache metrics."""
        return self._metrics.to_dict()

    def clear(self) -> bool:
        """Optional maintenance hook to clear keys matching the version prefix.

        Fail-open: logs warnings if Redis fails and returns False.
        """
        if self._client is None:
            return False

        try:
            pattern = f"nexusrag:query:{self._version}:*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
                logger.info("Cleared %d cache keys matching '%s'", len(keys), pattern)
            return True
        except Exception as exc:
            self._metrics.errors += 1
            logger.warning("Failed to clear cache keys: %s", exc)
            return False
