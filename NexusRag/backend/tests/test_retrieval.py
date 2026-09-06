from typing import List, Sequence
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.core.config import Settings
from app.embeddings.embedder import (
    BaseEmbeddingService,
    EmbeddedChunk,
    EmbeddingProviderError,
    EmptyEmbeddingInputError,
)
from app.retrieval import (
    EmptyQueryError,
    QueryEmbeddingError,
    RetrievedChunk,
    Retriever,
    VectorSearchError,
)
from app.vectordb.chroma_store import ChromaStore, VectorStoreError


# =====================================================================
# Fixtures
# =====================================================================


class FakeEmbeddingService(BaseEmbeddingService):
    """Deterministic fake embedding service for testing.

    Returns a fixed vector for embed_query and embed_text.
    No real Gemini API calls are made.
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.last_query = None

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise EmptyEmbeddingInputError("Cannot embed empty text.")
        return [0.1] * self.dimension

    def embed_query(self, query: str) -> List[float]:
        if not query or not query.strip():
            raise EmptyEmbeddingInputError("Cannot embed empty query.")
        self.last_query = query
        # Return a predictable vector: first element is 1.0, rest 0.0
        vec = [0.0] * self.dimension
        vec[0] = 1.0
        return vec

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        return [[0.1] * self.dimension for _ in texts]

    def embed_documents(self, documents: Sequence[Document]) -> List[EmbeddedChunk]:
        embeddings = self.embed_texts([doc.page_content for doc in documents])
        return [
            EmbeddedChunk(content=doc.page_content, embedding=emb, metadata=dict(doc.metadata))
            for doc, emb in zip(documents, embeddings)
        ]


@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """Provides a temporary directory for ChromaDB storage."""
    chroma_dir = tmp_path / "test_chroma_retrieval"
    chroma_dir.mkdir()
    return str(chroma_dir)


@pytest.fixture
def embedding_service() -> FakeEmbeddingService:
    """Provides a deterministic fake embedding service."""
    return FakeEmbeddingService(dimension=768)


@pytest.fixture
def chroma_store(tmp_chroma_dir) -> ChromaStore:
    """Provides a ChromaStore instance with temporary storage."""
    store = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="retrieval_test",
    )
    store.get_or_create_collection()
    return store


@pytest.fixture
def sample_embedded_chunks() -> List[EmbeddedChunk]:
    """Provides 5 pre-embedded chunks with distinct vectors for distance ordering."""
    chunks = []
    contents = [
        "Employees receive 20 days of paid time off annually.",
        "The engineering hiring process includes four interview rounds.",
        "Quarterly revenue targets were exceeded by 15 percent.",
        "Remote work policy allows three days per week from home.",
        "Annual performance reviews happen in December each year.",
    ]
    sources = [
        "hr-policy.pdf", "hiring-guide.pdf", "finance-report.txt",
        "remote-policy.md", "performance-guide.pdf",
    ]

    for i, (content, source) in enumerate(zip(contents, sources)):
        # Create distinct embeddings: each chunk has a 1.0 at a different position
        embedding = [0.0] * 768
        embedding[i] = 1.0
        chunks.append(
            EmbeddedChunk(
                content=content,
                embedding=embedding,
                metadata={
                    "source": source,
                    "file_name": source,
                    "file_path": f"C:/docs/{source}",
                    "file_type": source.rsplit(".", 1)[-1],
                    "page": 1,
                    "total_pages": 1,
                    "file_size_bytes": 5000,
                    "chunk_index": i,
                    "chunk_count": 5,
                    "char_count": len(content),
                },
            )
        )
    return chunks


@pytest.fixture
def populated_store(chroma_store, sample_embedded_chunks) -> ChromaStore:
    """Provides a ChromaStore pre-populated with 5 test chunks."""
    chroma_store.add_embedded_chunks(sample_embedded_chunks)
    return chroma_store


@pytest.fixture
def retriever(embedding_service, populated_store) -> Retriever:
    """Provides a fully wired Retriever with fake embedding + populated ChromaStore."""
    return Retriever(
        embedding_service=embedding_service,
        chroma_store=populated_store,
    )


# =====================================================================
# Test 1: Successful Query Retrieval
# =====================================================================


def test_successful_retrieval(retriever: Retriever) -> None:
    """Verify a valid query returns RetrievedChunk objects."""
    results = retriever.retrieve("What is the leave policy?")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, RetrievedChunk) for r in results)


# =====================================================================
# Test 2: Query Embedding Is Generated
# =====================================================================


def test_query_embedding_generated(
    embedding_service: FakeEmbeddingService,
    populated_store: ChromaStore,
) -> None:
    """Verify embed_query is called with the correct query string."""
    retriever = Retriever(
        embedding_service=embedding_service,
        chroma_store=populated_store,
    )
    retriever.retrieve("What is the hiring process?")

    assert embedding_service.last_query == "What is the hiring process?"


# =====================================================================
# Test 3: ChromaDB Queried With Embedding
# =====================================================================


def test_chromadb_queried_with_embedding(
    embedding_service: FakeEmbeddingService,
    populated_store: ChromaStore,
) -> None:
    """Verify ChromaStore receives the generated query vector."""
    retriever = Retriever(
        embedding_service=embedding_service,
        chroma_store=populated_store,
    )

    with patch.object(populated_store, "similarity_search", wraps=populated_store.similarity_search) as mock_search:
        retriever.retrieve("leave policy query")
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        query_vec = call_kwargs.kwargs.get("query_embedding") or call_kwargs[1].get("query_embedding") if call_kwargs[1] else call_kwargs[0][0]
        # The FakeEmbeddingService returns [1.0, 0.0, 0.0, ...]
        assert query_vec[0] == 1.0


# =====================================================================
# Test 4: Top-K Respected
# =====================================================================


def test_top_k_respected(retriever: Retriever) -> None:
    """Verify requesting top_k=3 returns at most 3 results from 5 stored chunks."""
    results = retriever.retrieve("leave policy", top_k=3)

    assert len(results) == 3


# =====================================================================
# Test 5: Result Ordering Preserved
# =====================================================================


def test_result_ordering_preserved(retriever: Retriever) -> None:
    """Verify results maintain ascending distance order (most similar first)."""
    results = retriever.retrieve("query text", top_k=5)

    distances = [r.distance for r in results]
    assert distances == sorted(distances), (
        f"Results not in ascending distance order: {distances}"
    )


# =====================================================================
# Test 6: Result Content Preserved
# =====================================================================


def test_result_content_preserved(retriever: Retriever) -> None:
    """Verify RetrievedChunk.content matches stored document text."""
    results = retriever.retrieve("leave policy", top_k=5)

    expected_contents = {
        "Employees receive 20 days of paid time off annually.",
        "The engineering hiring process includes four interview rounds.",
        "Quarterly revenue targets were exceeded by 15 percent.",
        "Remote work policy allows three days per week from home.",
        "Annual performance reviews happen in December each year.",
    }
    returned_contents = {r.content for r in results}

    assert returned_contents == expected_contents


# =====================================================================
# Test 7: Result Metadata Preserved
# =====================================================================


def test_result_metadata_preserved(retriever: Retriever) -> None:
    """Verify source, page, chunk_index, file_type metadata round-trip correctly."""
    results = retriever.retrieve("leave policy", top_k=5)

    # Find the hr-policy chunk
    hr_chunks = [r for r in results if r.metadata.get("source") == "hr-policy.pdf"]
    assert len(hr_chunks) == 1

    meta = hr_chunks[0].metadata
    assert meta["source"] == "hr-policy.pdf"
    assert meta["file_type"] == "pdf"
    assert meta["page"] == 1
    assert meta["chunk_index"] == 0
    assert "file_name" in meta
    assert "file_path" in meta


# =====================================================================
# Test 8: Distance Information Preserved
# =====================================================================


def test_distance_preserved(retriever: Retriever) -> None:
    """Verify RetrievedChunk.distance contains numeric ChromaDB distance values."""
    results = retriever.retrieve("query", top_k=5)

    for chunk in results:
        assert isinstance(chunk.distance, (int, float))
        assert chunk.distance >= 0.0  # L2 squared distance is non-negative


# =====================================================================
# Test 9: Empty Query Rejected
# =====================================================================


def test_empty_query_rejected(retriever: Retriever) -> None:
    """Verify empty string query raises EmptyQueryError."""
    with pytest.raises(EmptyQueryError):
        retriever.retrieve("")


# =====================================================================
# Test 10: Whitespace-Only Query Rejected
# =====================================================================


def test_whitespace_query_rejected(retriever: Retriever) -> None:
    """Verify whitespace-only query raises EmptyQueryError."""
    with pytest.raises(EmptyQueryError):
        retriever.retrieve("   \n\t  ")


# =====================================================================
# Test 11: Empty Collection Returns Empty List
# =====================================================================


def test_empty_collection_returns_empty(
    embedding_service: FakeEmbeddingService,
    tmp_chroma_dir,
) -> None:
    """Verify querying an empty collection returns an empty list, not an error."""
    empty_store = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="empty_collection",
    )
    empty_store.get_or_create_collection()

    retriever = Retriever(
        embedding_service=embedding_service,
        chroma_store=empty_store,
    )

    results = retriever.retrieve("any query")
    assert results == []


# =====================================================================
# Test 12: Fewer Results Than Top-K
# =====================================================================


def test_fewer_results_than_top_k(retriever: Retriever) -> None:
    """Verify requesting top_k=20 with 5 stored chunks returns 5 (no error)."""
    results = retriever.retrieve("leave policy", top_k=20)

    assert len(results) == 5


# =====================================================================
# Test 13: Embedding Failure Propagated
# =====================================================================


def test_embedding_failure_propagated(
    populated_store: ChromaStore,
) -> None:
    """Verify embedding service failure is wrapped as QueryEmbeddingError."""
    failing_service = MagicMock(spec=BaseEmbeddingService)
    failing_service.embed_query.side_effect = EmbeddingProviderError(
        "Gemini API rate limit exceeded"
    )

    retriever = Retriever(
        embedding_service=failing_service,
        chroma_store=populated_store,
    )

    with pytest.raises(QueryEmbeddingError, match="Failed to generate embedding"):
        retriever.retrieve("any query")


# =====================================================================
# Test 14: ChromaDB Failure Handled
# =====================================================================


def test_chromadb_failure_handled(
    embedding_service: FakeEmbeddingService,
) -> None:
    """Verify ChromaStore failure is wrapped as VectorSearchError."""
    failing_store = MagicMock(spec=ChromaStore)
    failing_store.similarity_search.side_effect = VectorStoreError(
        "ChromaDB connection lost"
    )

    retriever = Retriever(
        embedding_service=embedding_service,
        chroma_store=failing_store,
    )

    with pytest.raises(VectorSearchError, match="Vector database search failed"):
        retriever.retrieve("any query")


# =====================================================================
# Test 15: Configuration Respected
# =====================================================================


def test_configuration_respected(
    embedding_service: FakeEmbeddingService,
    populated_store: ChromaStore,
) -> None:
    """Verify top_k from Settings is used as default when not overridden."""
    retriever = Retriever(
        embedding_service=embedding_service,
        chroma_store=populated_store,
    )

    # Default top_k from config.yaml is 4
    with patch.object(populated_store, "similarity_search", wraps=populated_store.similarity_search) as mock_search:
        retriever.retrieve("leave policy")
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        # n_results should match Settings.top_k (4)
        n_results = call_kwargs.kwargs.get("n_results")
        assert n_results == 4
