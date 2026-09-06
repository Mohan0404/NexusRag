from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import (
    BaseEmbeddingService,
    EmbeddingError,
    EmbeddingProviderError,
    EmptyEmbeddingInputError,
)
from app.vectordb.chroma_store import ChromaStore, VectorStoreError

logger = get_logger(__name__)


# =====================================================================
# Retrieval Data Structures
# =====================================================================


@dataclass
class RetrievedChunk:
    """Represents a single document chunk returned from similarity search.

    Attributes:
        content: The text content of the retrieved document chunk.
        metadata: Full metadata dictionary from ingestion and chunking phases.
            Includes: source, file_name, file_path, file_type, page,
            total_pages, file_size_bytes, chunk_index, chunk_count, char_count.
        distance: ChromaDB L2 squared (Euclidean squared) distance from the query vector.
            Lower values indicate higher similarity (0.0 = identical vectors).
            This is NOT a normalized similarity score.
    """

    content: str
    metadata: Dict[str, Any]
    distance: float


# =====================================================================
# Retrieval Exceptions
# =====================================================================


class RetrievalError(Exception):
    """Base exception for all retrieval operations."""

    pass


class EmptyQueryError(RetrievalError, ValueError):
    """Raised when the user query is empty or whitespace-only."""

    pass


class QueryEmbeddingError(RetrievalError):
    """Raised when the embedding service fails to generate a query vector."""

    pass


class VectorSearchError(RetrievalError):
    """Raised when ChromaDB similarity search fails."""

    pass


# =====================================================================
# Retriever Implementation
# =====================================================================


class Retriever:
    """Orchestrates similarity-based document retrieval.

    Pipeline:
        User Query
            ↓
        Embedding Service (embed_query)
            ↓
        Query Vector (768-dim)
            ↓
        ChromaStore (similarity_search)
            ↓
        ChromaDB L2 squared distance search
            ↓
        Top-K RetrievedChunk objects

    Responsibilities:
    - Validates user queries.
    - Generates query embeddings via the Phase 5 embedding service.
    - Delegates similarity search to the Phase 6 ChromaStore abstraction.
    - Converts raw ChromaDB results into clean RetrievedChunk objects.
    - Preserves document content, metadata, and distance information.

    Does NOT:
    - Generate LLM answers (Phase 8/9).
    - Construct prompts (Phase 9).
    - Cache results (Phase 10).
    - Implement hybrid search, reranking, or BM25.
    """

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        chroma_store: ChromaStore,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initializes the Retriever with required dependencies.

        Args:
            embedding_service: Phase 5 embedding service (must implement embed_query).
            chroma_store: Phase 6 ChromaDB abstraction (must have similarity_search).
            settings: Centralized application settings. Defaults to get_settings().
        """
        self._embedding_service = embedding_service
        self._chroma_store = chroma_store
        self._settings = settings or get_settings()

        logger.info(
            "Retriever initialized with top_k=%d (configurable via Settings)",
            self._settings.top_k,
        )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        """Accepts a user query and returns the most relevant document chunks.

        Pipeline:
        1. Validate the query (non-empty, non-whitespace).
        2. Generate a query embedding using the embedding service.
        3. Query ChromaDB via ChromaStore for the top-k most similar chunks.
        4. Convert raw results into RetrievedChunk objects.

        Args:
            query: User search query string (e.g. "What is the leave policy?").
            top_k: Optional override for the number of results. Defaults to
                Settings.top_k (configured in config.yaml under rag.top_k).

        Returns:
            List of RetrievedChunk objects ordered by ascending distance
            (most similar first). May be empty if the collection has no data
            or no results match.

        Raises:
            EmptyQueryError: If query is empty or whitespace-only.
            QueryEmbeddingError: If the embedding service fails.
            VectorSearchError: If ChromaDB similarity search fails.
        """
        # Step 1: Validate query
        self._validate_query(query)

        effective_top_k = top_k if top_k is not None else self._settings.top_k
        logger.info(
            "Retrieval started: query_length=%d, top_k=%d",
            len(query),
            effective_top_k,
        )

        # Step 2: Generate query embedding
        query_embedding = self._generate_query_embedding(query)

        # Step 3: Similarity search via ChromaStore
        raw_results = self._search(query_embedding, effective_top_k)

        # Step 4: Convert to RetrievedChunk objects
        chunks = self._build_retrieved_chunks(raw_results)

        logger.info(
            "Retrieval completed: requested=%d, returned=%d",
            effective_top_k,
            len(chunks),
        )

        return chunks

    # =================================================================
    # Internal Pipeline Steps
    # =================================================================

    @staticmethod
    def _validate_query(query: str) -> None:
        """Validates the user query is non-empty and non-whitespace.

        Args:
            query: Raw user query string.

        Raises:
            EmptyQueryError: If the query is empty or whitespace-only.
        """
        if not query or not query.strip():
            raise EmptyQueryError(
                "Query must not be empty or whitespace-only."
            )

    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generates a query embedding vector using the Phase 5 embedding service.

        Uses RETRIEVAL_QUERY task type (handled internally by embed_query).

        Args:
            query: Validated user query string.

        Returns:
            Query embedding vector (List[float]).

        Raises:
            QueryEmbeddingError: If the embedding service fails.
        """
        try:
            embedding = self._embedding_service.embed_query(query)
            logger.info(
                "Query embedding generated: dimension=%d",
                len(embedding),
            )
            return embedding
        except EmptyEmbeddingInputError as e:
            raise EmptyQueryError(str(e)) from e
        except EmbeddingError as e:
            logger.error("Failed to generate query embedding: %s", e)
            raise QueryEmbeddingError(
                f"Failed to generate embedding for query: {e}"
            ) from e

    def _search(
        self, query_embedding: List[float], top_k: int
    ) -> Dict[str, Any]:
        """Delegates similarity search to ChromaStore.

        Args:
            query_embedding: Pre-computed query vector.
            top_k: Maximum number of results.

        Returns:
            Flat dictionary with ids, documents, metadatas, distances.

        Raises:
            VectorSearchError: If ChromaDB query fails.
        """
        try:
            results = self._chroma_store.similarity_search(
                query_embedding=query_embedding,
                n_results=top_k,
            )
            return results
        except VectorStoreError as e:
            logger.error("ChromaDB similarity search failed: %s", e)
            raise VectorSearchError(
                f"Vector database search failed: {e}"
            ) from e

    @staticmethod
    def _build_retrieved_chunks(
        raw_results: Dict[str, Any],
    ) -> List[RetrievedChunk]:
        """Converts raw ChromaDB query results into RetrievedChunk objects.

        Preserves ordering returned by ChromaDB (ascending distance).

        Args:
            raw_results: Flat dictionary from ChromaStore.similarity_search().

        Returns:
            List of RetrievedChunk objects.
        """
        ids = raw_results.get("ids", [])
        documents = raw_results.get("documents", [])
        metadatas = raw_results.get("metadatas", [])
        distances = raw_results.get("distances", [])

        chunks: List[RetrievedChunk] = []
        for i in range(len(ids)):
            chunks.append(
                RetrievedChunk(
                    content=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    distance=distances[i] if i < len(distances) else 0.0,
                )
            )

        return chunks
