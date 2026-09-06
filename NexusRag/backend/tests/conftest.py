"""Phase 13 — Centralized Test Fixtures and Reusable Test Doubles.

Provides deterministic, isolated, zero-network test doubles for:
- FakeEmbeddingService (concept-mapped semantic hashing with L2 normalization)
- FakeLLMService (predictable prompt tracking and generation)
- FakeRedisClient (in-memory dictionary-based Redis mock)
- Temporary ChromaStore (isolated on pytest tmp_path)
"""

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import pytest
from langchain_core.documents import Document

from app.embeddings.embedder import BaseEmbeddingService, EmbeddedChunk
from app.llm.llm_service import BaseLLMService, LLMResponse
from app.vectordb.chroma_store import ChromaStore

# Known conceptual anchor dimensions for semantic-like deterministic testing
CONCEPT_DIMENSIONS: Dict[str, int] = {
    "nexusrag": 0,
    "genworx": 1,
    "rag": 2,
    "leave": 3,
    "policy": 4,
    "holiday": 5,
    "vacation": 6,
    "salary": 7,
    "benefits": 8,
    "ai": 9,
    "enterprise": 10,
    "assistant": 11,
}


class FakeEmbeddingService(BaseEmbeddingService):
    """Deterministic, zero-network embedding double for integration and E2E testing.

    Features:
    - Fixed output dimensionality (default: 768).
    - Concept-mapped semantic projection: texts containing the same keywords
      produce vectors with high cosine similarity, while unrelated texts
      produce nearly orthogonal vectors.
    - L2 unit normalization ensuring valid distance calculation in ChromaDB.
    """

    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension
        self.call_count = 0

    def _generate_vector(self, text: str) -> List[float]:
        self.call_count += 1
        vec = [0.0] * self._dimension
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        if not tokens:
            vec[0] = 1.0
            return vec

        for token in tokens:
            if token in CONCEPT_DIMENSIONS:
                dim_idx = CONCEPT_DIMENSIONS[token] % self._dimension
                vec[dim_idx] += 3.0  # High weight for known concept anchors
            else:
                dim_idx = abs(hash(token)) % self._dimension
                vec[dim_idx] += 1.0

        # L2-normalize to unit vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        vec[0] = 1.0
        return vec

    def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def embed_query(self, query: str) -> List[float]:
        return self._generate_vector(query)

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_documents(self, documents: Sequence[Document]) -> List[EmbeddedChunk]:
        results: List[EmbeddedChunk] = []
        for doc in documents:
            vector = self._generate_vector(doc.page_content)
            results.append(
                EmbeddedChunk(
                    content=doc.page_content,
                    embedding=vector,
                    metadata=dict(doc.metadata),
                )
            )
        return results


class FakeLLMService(BaseLLMService):
    """Deterministic, zero-network LLM double for integration and E2E testing."""

    def __init__(
        self,
        canned_response: str = "NexusRAG is built by Genworx for enterprise AI.",
        model_name: str = "fake-llm-model",
    ) -> None:
        self.canned_response = canned_response
        self.model_name = model_name
        self.calls: List[str] = []

    def generate(self, prompt: str) -> LLMResponse:
        self.calls.append(prompt)
        return LLMResponse(
            content=self.canned_response,
            model=self.model_name,
            usage={"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40},
        )


class FakeRedisClient:
    """In-memory Redis mock client for deterministic zero-daemon testing."""

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
        self.delete_calls = 0

    def get(self, key: str) -> Optional[str]:
        self.get_calls += 1
        if self.raises_on_get:
            raise ConnectionError("Simulated Redis GET network failure")
        return self._store.get(key)

    def set(self, key: str, value: str) -> bool:
        self.set_calls += 1
        if self.raises_on_set:
            raise ConnectionError("Simulated Redis SET network failure")
        self._store[key] = value
        return True

    def setex(self, key: str, time: int, value: str) -> bool:
        self.setex_calls += 1
        if self.raises_on_set:
            raise ConnectionError("Simulated Redis SETEX network failure")
        self._store[key] = value
        self._ttls[key] = time
        return True

    def delete(self, *keys: str) -> int:
        self.delete_calls += 1
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                count += 1
        return count

    def keys(self, pattern: str = "*") -> List[str]:
        import fnmatch
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def flushdb(self) -> bool:
        self._store.clear()
        self._ttls.clear()
        return True

    def ping(self) -> bool:
        return True


# =====================================================================
# Central Reusable Pytest Fixtures
# =====================================================================


@pytest.fixture
def fake_embedding_service() -> FakeEmbeddingService:
    """Provides a fresh deterministic FakeEmbeddingService (768-dim)."""
    return FakeEmbeddingService(dimension=768)


@pytest.fixture
def fake_llm_service() -> FakeLLMService:
    """Provides a fresh deterministic FakeLLMService."""
    return FakeLLMService()


@pytest.fixture
def fake_redis_client() -> FakeRedisClient:
    """Provides a clean in-memory FakeRedisClient."""
    return FakeRedisClient()


@pytest.fixture
def tmp_chroma_store(tmp_path: Path) -> ChromaStore:
    """Provides an isolated ChromaStore instance using a temporary directory."""
    chroma_dir = tmp_path / "chroma_test_db"
    store = ChromaStore(
        persist_directory=str(chroma_dir),
        collection_name="test_ephemeral_collection",
    )
    yield store
    try:
        store.reset()
    except Exception:
        pass
