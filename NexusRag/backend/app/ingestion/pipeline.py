"""Ingestion Pipeline — Phase 11 application-level orchestrator.

Responsibility:
Coordinates DocumentService (loading/validation), DocumentChunker (chunking),
BaseEmbeddingService (dense embeddings), and ChromaStore (vector indexing),
followed by the Redis query cache invalidation hook.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.cache.redis_cache import BaseQueryCache
from app.chunking.chunker import DocumentChunker
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import BaseEmbeddingService
from app.ingestion.document_service import DocumentService
from app.vectordb.chroma_store import ChromaStore

logger = get_logger(__name__)


@dataclass
class IngestionResult:
    """Result of full document ingestion, chunking, embedding, and indexing."""

    filename: str
    file_type: str
    file_size_bytes: int
    chunks_created: int
    chunk_ids: List[str] = field(default_factory=list)
    cache_cleared: bool = False


class IngestionPipeline:
    """Orchestrates document loading, chunking, embedding, ChromaDB indexing, and cache invalidation.

    Pipeline:
        Staged File Path
            ↓
        DocumentService.ingest_file(file_path)         → List[Document]
            ↓
        DocumentChunker.chunk_documents(documents)     → List[Document]
            ↓
        BaseEmbeddingService.embed_documents(chunks)   → List[EmbeddedChunk]
            ↓
        ChromaStore.add_documents(embedded_chunks)     → List[str] (chunk IDs)
            ↓ (Only on success!)
        RedisQueryCache.clear()                        → Invalidate query cache
            ↓
        IngestionResult
    """

    def __init__(
        self,
        document_service: DocumentService,
        chunker: DocumentChunker,
        embedding_service: BaseEmbeddingService,
        chroma_store: ChromaStore,
        cache: Optional[BaseQueryCache] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._document_service = document_service
        self._chunker = chunker
        self._embedding_service = embedding_service
        self._chroma_store = chroma_store
        self._cache = cache
        self._settings = settings or get_settings()

    def index_file(self, file_path: Path) -> IngestionResult:
        """Executes the full end-to-end ingestion and indexing pipeline for a file.

        Args:
            file_path: Filesystem path of the file to ingest.

        Returns:
            IngestionResult with metadata and indexing statistics.

        Raises:
            IngestionError: If file loading or validation fails.
            ChunkingError: If text splitting fails.
            EmbeddingError: If vector generation fails.
            VectorStoreError: If ChromaDB persistence fails.
        """
        filename = file_path.name
        file_type = file_path.suffix.lower()
        file_size_bytes = file_path.stat().st_size if file_path.exists() else 0

        logger.info("Starting ingestion pipeline for file: '%s'", filename)

        # Step 1: Load and parse document
        documents = self._document_service.ingest_file(file_path)

        # Step 2: Split into chunks
        chunks = self._chunker.chunk_documents(documents)

        # Step 3: Generate dense embeddings
        embedded_chunks = self._embedding_service.embed_documents(chunks)

        # Step 4: Index into ChromaDB
        chunks_indexed = self._chroma_store.add_embedded_chunks(embedded_chunks)

        logger.info(
            "Successfully indexed '%s' into ChromaDB: chunks=%d",
            filename,
            chunks_indexed,
        )

        # Step 5: Invalidate Redis query cache (Correction #2)
        cache_cleared = False
        if self._cache is not None:
            try:
                self._cache.clear()
                cache_cleared = True
                logger.info("Redis query cache cleared after successful document indexing.")
            except Exception as exc:
                # Redis failure is non-fatal; document indexing succeeded
                logger.warning(
                    "Failed to clear Redis query cache after indexing (non-fatal): %s",
                    exc,
                )

        return IngestionResult(
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            chunks_created=len(chunks),
            cache_cleared=cache_cleared,
        )
