from typing import List, Optional, Sequence
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# =====================================================================
# Chunking Exceptions
# =====================================================================


class ChunkingError(Exception):
    """Base exception for all document chunking errors."""

    pass


class ChunkingConfigurationError(ChunkingError, ValueError):
    """Raised when chunking parameters are invalid (e.g. overlap >= chunk_size)."""

    pass


# =====================================================================
# Document Chunker Implementation
# =====================================================================


class DocumentChunker:
    """Splits LangChain Document objects into smaller chunks using recursive text splitting.

    Parameters are sourced from centralized application configuration (Settings),
    guaranteeing strict validation, deterministic output, and complete metadata preservation.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        """Initializes the DocumentChunker with configuration or explicit overrides.

        Args:
            settings: Centralized application Settings. Defaults to get_settings().
            chunk_size: Optional override for chunk size (in characters).
            chunk_overlap: Optional override for chunk overlap (in characters).

        Raises:
            ChunkingConfigurationError: If chunk_size <= 0, chunk_overlap < 0,
                                         or chunk_overlap >= chunk_size.
        """
        app_settings = settings or get_settings()

        self.chunk_size = (
            chunk_size if chunk_size is not None else app_settings.chunk_size
        )
        self.chunk_overlap = (
            chunk_overlap if chunk_overlap is not None else app_settings.chunk_overlap
        )

        self._validate_configuration(self.chunk_size, self.chunk_overlap)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
        )

        logger.info(
            "DocumentChunker initialized with chunk_size=%d, chunk_overlap=%d",
            self.chunk_size,
            self.chunk_overlap,
        )

    @staticmethod
    def _validate_configuration(chunk_size: int, chunk_overlap: int) -> None:
        """Enforces boundary invariants on chunking hyperparameters."""
        if chunk_size <= 0:
            raise ChunkingConfigurationError(
                f"chunk_size must be strictly greater than 0, got {chunk_size}."
            )
        if chunk_overlap < 0:
            raise ChunkingConfigurationError(
                f"chunk_overlap cannot be negative, got {chunk_overlap}."
            )
        if chunk_overlap >= chunk_size:
            raise ChunkingConfigurationError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})."
            )

    def chunk_document(self, document: Document) -> List[Document]:
        """Splits a single LangChain Document into smaller chunks with enriched metadata.

        Args:
            document: Input LangChain Document.

        Returns:
            List of generated chunk Documents with preserved and indexed metadata.
        """
        if not document or not document.page_content or not document.page_content.strip():
            logger.debug(
                "Skipping empty or whitespace-only document '%s'",
                document.metadata.get("source", "unknown") if document else "None",
            )
            return []

        # Split document using RecursiveCharacterTextSplitter
        raw_chunks = self._splitter.split_documents([document])
        total_chunks = len(raw_chunks)

        enriched_chunks: List[Document] = []
        for index, chunk in enumerate(raw_chunks):
            # Preserve existing metadata and attach chunk sequence indicators
            merged_metadata = dict(chunk.metadata)
            merged_metadata["chunk_index"] = index
            merged_metadata["chunk_count"] = total_chunks
            merged_metadata["char_count"] = len(chunk.page_content)

            enriched_chunks.append(
                Document(page_content=chunk.page_content, metadata=merged_metadata)
            )

        return enriched_chunks

    def chunk_documents(self, documents: Sequence[Document]) -> List[Document]:
        """Splits a sequence of LangChain Documents into smaller chunks.

        Args:
            documents: Sequence of LangChain Document objects.

        Returns:
            Aggregated list of all generated chunk Documents.
        """
        if not documents:
            logger.debug("chunk_documents called with empty document collection.")
            return []

        logger.info("Starting chunking for %d input document(s)", len(documents))

        all_chunks: List[Document] = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(
            "Chunking completed: generated %d chunk(s) from %d document(s)",
            len(all_chunks),
            len(documents),
        )
        return all_chunks
