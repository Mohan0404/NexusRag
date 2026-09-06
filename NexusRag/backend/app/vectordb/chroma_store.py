import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import EmbeddedChunk

logger = get_logger(__name__)


# =====================================================================
# Vector Store Exceptions
# =====================================================================


class VectorStoreError(Exception):
    """Base exception for all vector store operations."""

    pass


class CollectionError(VectorStoreError):
    """Raised when a ChromaDB collection cannot be created, opened, or accessed."""

    pass


class PersistenceError(VectorStoreError):
    """Raised when the ChromaDB persistent storage path is invalid or inaccessible."""

    pass


class InvalidEmbeddingError(VectorStoreError, ValueError):
    """Raised when embedding vectors are empty, malformed, or dimension-mismatched."""

    pass


class MetadataError(VectorStoreError, ValueError):
    """Raised when metadata contains unsupported types for ChromaDB storage."""

    pass


# =====================================================================
# ChromaDB Abstraction Layer
# =====================================================================


class ChromaStore:
    """Production abstraction over ChromaDB persistent vector storage.

    Responsibilities:
    - Manages a single named ChromaDB collection.
    - Accepts pre-embedded chunks from Phase 5 (EmbeddedChunk objects).
    - Generates deterministic, collision-resistant chunk IDs.
    - Sanitizes metadata to ChromaDB-supported primitives.
    - Provides CRUD operations (add/upsert, get, delete) and collection stats.
    - Provides similarity search for retrieval (Phase 7).
    - Does NOT generate embeddings (Phase 5).

    Persistence:
    - Uses chromadb.PersistentClient for durable on-disk storage.
    - Path sourced from Settings.CHROMA_PATH (configurable via .env).
    - Collection name sourced from Settings.vectordb_collection_name (configurable via config.yaml).
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        """Initializes ChromaStore with configuration.

        Args:
            settings: Centralized application settings. Defaults to get_settings().
            persist_directory: Optional override for the ChromaDB storage path.
                Defaults to Settings.CHROMA_PATH.
            collection_name: Optional override for the collection name.
                Defaults to Settings.vectordb_collection_name.

        Raises:
            PersistenceError: If the persist directory cannot be created or accessed.
        """
        self._settings = settings or get_settings()

        self._persist_directory = (
            persist_directory or self._settings.CHROMA_PATH
        )
        self._collection_name = (
            collection_name or self._settings.vectordb_collection_name
        )

        self._client = None
        self._collection = None

        logger.info(
            "ChromaStore configured: persist_directory='%s', collection='%s'",
            self._persist_directory,
            self._collection_name,
        )

    # =================================================================
    # Collection Lifecycle
    # =================================================================

    def _ensure_client(self):
        """Lazily initializes the ChromaDB PersistentClient."""
        if self._client is not None:
            return self._client

        try:
            import chromadb

            persist_path = Path(self._persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)

            self._client = chromadb.PersistentClient(path=str(persist_path))
            logger.info(
                "ChromaDB PersistentClient initialized at '%s'", persist_path
            )
            return self._client
        except PermissionError as e:
            raise PersistenceError(
                f"Permission denied for ChromaDB directory '{self._persist_directory}': {e}"
            ) from e
        except Exception as e:
            raise PersistenceError(
                f"Failed to initialize ChromaDB PersistentClient at "
                f"'{self._persist_directory}': {e}"
            ) from e

    def get_or_create_collection(self):
        """Opens or creates the named ChromaDB collection.

        Returns:
            The ChromaDB Collection object.

        Raises:
            CollectionError: If the collection cannot be created or accessed.
        """
        if self._collection is not None:
            return self._collection

        client = self._ensure_client()

        try:
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
            )
            logger.info(
                "ChromaDB collection '%s' ready (current count: %d)",
                self._collection_name,
                self._collection.count(),
            )
            return self._collection
        except Exception as e:
            raise CollectionError(
                f"Failed to get or create ChromaDB collection "
                f"'{self._collection_name}': {e}"
            ) from e

    def _ensure_collection(self):
        """Ensures the collection is initialized before operations."""
        if self._collection is None:
            self.get_or_create_collection()
        return self._collection

    # =================================================================
    # ID Generation
    # =================================================================

    @staticmethod
    def generate_chunk_id(source: str, chunk_index: int) -> str:
        """Generates a deterministic, collision-resistant chunk ID.

        Strategy: SHA-256 hash of '{source}::chunk_{chunk_index}', truncated to
        16 hex characters (64 bits of entropy).

        This ensures:
        - Same document + same chunk position → identical ID (idempotent).
        - Re-ingestion produces identical IDs → upsert replaces cleanly.
        - No random UUIDs that would cause duplication on re-ingestion.

        Args:
            source: Source filename (e.g. 'report.pdf').
            chunk_index: Zero-based chunk position index.

        Returns:
            16-character hex string ID.
        """
        raw = f"{source}::chunk_{chunk_index}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    # =================================================================
    # Metadata Sanitization
    # =================================================================

    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes metadata to ChromaDB-supported primitive types.

        ChromaDB 1.5.x accepts: str, int, float, bool, List[str|int|float|bool].
        ChromaDB rejects: None values.

        This method:
        1. Strips keys with None values.
        2. Converts unsupported types to their string representations.
        3. Logs warnings for unexpected metadata types.

        Args:
            metadata: Raw metadata dictionary from EmbeddedChunk.

        Returns:
            Sanitized metadata dictionary safe for ChromaDB storage.
        """
        sanitized: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                logger.debug(
                    "Stripping None-valued metadata key '%s' for ChromaDB compatibility",
                    key,
                )
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # ChromaDB supports List[str|int|float|bool]
                sanitized[key] = [
                    v if isinstance(v, (str, int, float, bool)) else str(v)
                    for v in value
                    if v is not None
                ]
            else:
                logger.warning(
                    "Converting non-primitive metadata key '%s' (type=%s) to string for ChromaDB",
                    key,
                    type(value).__name__,
                )
                sanitized[key] = str(value)
        return sanitized

    # =================================================================
    # Write Operations
    # =================================================================

    def add_embedded_chunks(self, chunks: Sequence[EmbeddedChunk]) -> int:
        """Upserts a sequence of EmbeddedChunk objects into the ChromaDB collection.

        Uses deterministic IDs derived from source + chunk_index metadata.
        Existing records with the same ID are updated (idempotent upsert).

        Args:
            chunks: Sequence of EmbeddedChunk objects from Phase 5.

        Returns:
            Number of chunks upserted.

        Raises:
            InvalidEmbeddingError: If any embedding vector is empty.
            VectorStoreError: If the ChromaDB upsert operation fails.
        """
        if not chunks:
            logger.debug("add_embedded_chunks called with empty chunk list.")
            return 0

        collection = self._ensure_collection()

        ids: List[str] = []
        documents: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            # Validate embedding is present and non-empty
            if not chunk.embedding:
                raise InvalidEmbeddingError(
                    f"Empty embedding vector for chunk from source "
                    f"'{chunk.metadata.get('source', 'unknown')}'."
                )

            source = chunk.metadata.get("source", "unknown")
            chunk_index = chunk.metadata.get("chunk_index", 0)

            chunk_id = self.generate_chunk_id(source, chunk_index)
            sanitized_meta = self._sanitize_metadata(chunk.metadata)

            ids.append(chunk_id)
            documents.append(chunk.content)
            embeddings.append(chunk.embedding)
            metadatas.append(sanitized_meta)

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error("ChromaDB upsert failed: %s", error_msg)
            if "dimension" in error_msg.lower():
                raise InvalidEmbeddingError(
                    f"Embedding dimension mismatch during ChromaDB upsert: {error_msg}"
                ) from e
            raise VectorStoreError(
                f"ChromaDB upsert operation failed: {error_msg}"
            ) from e

        logger.info(
            "Upserted %d chunks into collection '%s' (total count: %d)",
            len(ids),
            self._collection_name,
            collection.count(),
        )
        return len(ids)

    # =================================================================
    # Read Operations (NOT similarity search)
    # =================================================================

    def get_by_ids(
        self,
        ids: List[str],
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Retrieves records by their deterministic chunk IDs.

        Args:
            ids: List of chunk ID strings.
            include: Optional list of fields to include. Defaults to
                ['documents', 'metadatas', 'embeddings'].

        Returns:
            ChromaDB GetResult dictionary with keys: ids, documents, metadatas, embeddings.
        """
        collection = self._ensure_collection()
        include = include or ["documents", "metadatas", "embeddings"]

        try:
            return collection.get(ids=ids, include=include)
        except Exception as e:
            raise VectorStoreError(
                f"Failed to retrieve records by IDs: {e}"
            ) from e

    @staticmethod
    def _canonicalize_source(source: Optional[str]) -> str:
        """Canonicalizes document source, stripping legacy 32-hex UUID staging prefixes.

        Example:
            '2cfa38edf3294abf9292b2bda6f77155_Genworx_Cracking_Roadmap.md'
            -> 'Genworx_Cracking_Roadmap.md'
        """
        if not source or not str(source).strip():
            return "Unknown Document"
        clean = str(source).strip()
        match = re.match(r"^[0-9a-fA-F]{32}_(.+)$", clean)
        if match:
            return match.group(1)
        return clean

    @staticmethod
    def _normalize_file_type(file_type: Optional[str], canonical_source: str) -> str:
        """Normalizes file extension to lowercase with leading dot (e.g. '.md')."""
        if file_type and str(file_type).strip():
            clean = str(file_type).strip().lower()
            return f".{clean.lstrip('.')}"
        suffix = Path(canonical_source).suffix.lower()
        return suffix if suffix else ""

    def get_chunk_ids_by_source(self, source: str) -> List[str]:
        """Finds all chunk IDs belonging to a source (matching exact source or canonicalized source).

        Args:
            source: Source filename (canonical or legacy UUID-prefixed).

        Returns:
            List of matching chunk IDs.
        """
        collection = self._ensure_collection()
        target_canonical = self._canonicalize_source(source)

        try:
            # First try exact query via where clause
            exact = collection.get(where={"source": source}, include=[])
            direct_ids = exact.get("ids", []) or []
            if direct_ids:
                return direct_ids

            # If no direct match, check all records for legacy UUID-prefixed sources matching target_canonical
            all_records = collection.get(include=["metadatas"])
            metadatas = all_records.get("metadatas", []) or []
            ids = all_records.get("ids", []) or []

            matching_ids: List[str] = []
            for chunk_id, meta in zip(ids, metadatas):
                if not meta:
                    continue
                raw_source = meta.get("source", "")
                if raw_source == source or self._canonicalize_source(raw_source) == target_canonical:
                    matching_ids.append(chunk_id)

            return matching_ids
        except Exception as e:
            raise VectorStoreError(
                f"Failed to find chunk IDs for source '{source}': {e}"
            ) from e

    def get_by_source(
        self,
        source: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Retrieves all chunks originating from a specific source file (canonical or legacy).

        Args:
            source: Source filename (canonical or legacy UUID-prefixed).
            include: Optional list of fields to include.

        Returns:
            ChromaDB GetResult dictionary.
        """
        collection = self._ensure_collection()
        include = include or ["documents", "metadatas"]

        try:
            exact = collection.get(where={"source": source}, include=include)
            if exact.get("ids"):
                return exact

            chunk_ids = self.get_chunk_ids_by_source(source)
            if chunk_ids:
                return collection.get(ids=chunk_ids, include=include)

            return {"ids": [], "documents": [], "metadatas": []}
        except Exception as e:
            raise VectorStoreError(
                f"Failed to retrieve records for source '{source}': {e}"
            ) from e

    def count_by_source(self, source: str) -> int:
        """Returns the number of actual Chroma records stored for a specific source document.

        Args:
            source: Source filename (canonical or legacy).

        Returns:
            Integer count of actual stored records for that source. 0 if not found.
        """
        try:
            return len(self.get_chunk_ids_by_source(source))
        except VectorStoreError:
            return 0

    def list_sources(self) -> List[Dict[str, Any]]:
        """Lists all distinct source documents currently indexed in the collection.

        Performs a metadata-only scan of the collection and aggregates per-document
        summaries. The physical number of Chroma records is the single source of truth
        for chunk_count.

        Returns:
            List of dictionaries, each representing a distinct document:
                - source (str): Canonical filename (legacy UUID prefix stripped).
                - file_type (str): Normalized file extension (e.g. '.pdf', '.md').
                - chunk_count (int): Actual number of physical Chroma records.
                - indexed_at (str | None): ISO-8601 timestamp of earliest chunk, or
                  None for documents indexed before this field was introduced.

        Raises:
            VectorStoreError: If the ChromaDB metadata scan fails.
        """
        collection = self._ensure_collection()

        try:
            result = collection.get(include=["metadatas"])
        except Exception as e:
            raise VectorStoreError(
                f"Failed to retrieve collection metadata for source listing: {e}"
            ) from e

        metadatas: List[Dict[str, Any]] = result.get("metadatas", []) or []

        # Aggregate per-source statistics based on actual physical records
        source_map: Dict[str, Dict[str, Any]] = {}
        for meta in metadatas:
            if not meta:
                continue
            raw_source = meta.get("source")
            canonical_source = self._canonicalize_source(raw_source)

            if canonical_source not in source_map:
                normalized_type = self._normalize_file_type(
                    meta.get("file_type"), canonical_source
                )
                source_map[canonical_source] = {
                    "source": canonical_source,
                    "file_type": normalized_type,
                    "chunk_count": 0,
                    "indexed_at": meta.get("indexed_at"),
                }

            # Physical records are the single source of truth for chunk_count
            source_map[canonical_source]["chunk_count"] += 1

            # Keep the earliest indexed_at seen for this source
            current_ts = source_map[canonical_source]["indexed_at"]
            chunk_ts = meta.get("indexed_at")
            if chunk_ts and (not current_ts or chunk_ts < current_ts):
                source_map[canonical_source]["indexed_at"] = chunk_ts

        documents = sorted(
            source_map.values(),
            key=lambda d: (d["indexed_at"] or "", d["source"]),
            reverse=True,
        )

        logger.debug(
            "list_sources: found %d distinct document(s) in collection '%s'",
            len(documents),
            self._collection_name,
        )
        return documents

    # =================================================================
    # Similarity Search (Phase 7)
    # =================================================================

    def similarity_search(
        self,
        query_embedding: List[float],
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Performs similarity search using a pre-computed query embedding vector.

        Uses ChromaDB's default L2 squared (Euclidean squared) distance metric.
        Lower distance values indicate higher similarity (0.0 = identical).

        The outer list wrapper from ChromaDB's multi-query response format is
        unwrapped, returning flat lists for single-query convenience.

        Args:
            query_embedding: Pre-computed query vector (from embed_query()).
            n_results: Maximum number of results to return.
            where: Optional metadata filter dictionary.

        Returns:
            Dictionary with flat lists:
                - ids: List[str]
                - documents: List[str]
                - metadatas: List[Dict]
                - distances: List[float]

        Raises:
            VectorStoreError: If the ChromaDB query operation fails.
        """
        collection = self._ensure_collection()

        try:
            raw_result = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            raise VectorStoreError(
                f"ChromaDB similarity search failed: {e}"
            ) from e

        # Unwrap outer list (ChromaDB wraps results per query; we send one query)
        return {
            "ids": raw_result["ids"][0] if raw_result["ids"] else [],
            "documents": raw_result["documents"][0] if raw_result["documents"] else [],
            "metadatas": raw_result["metadatas"][0] if raw_result["metadatas"] else [],
            "distances": raw_result["distances"][0] if raw_result["distances"] else [],
        }

    # =================================================================
    # Delete Operations
    # =================================================================

    def delete_by_ids(self, ids: List[str]) -> None:
        """Deletes specific chunks by their deterministic IDs.

        Args:
            ids: List of chunk ID strings to delete.
        """
        if not ids:
            return

        collection = self._ensure_collection()

        try:
            collection.delete(ids=ids)
            logger.info(
                "Deleted %d chunk(s) by ID from collection '%s'",
                len(ids),
                self._collection_name,
            )
        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete records by IDs: {e}"
            ) from e

    def delete_by_source(
        self, source: str, exclude_ids: Optional[List[str]] = None
    ) -> int:
        """Deletes all chunks belonging to a document (canonical or legacy).

        Args:
            source: Source filename (canonical or legacy UUID-prefixed).
            exclude_ids: Optional list of chunk IDs to preserve.

        Returns:
            Integer count of actual records deleted.
        """
        matching_ids = self.get_chunk_ids_by_source(source)
        if exclude_ids:
            matching_ids = [cid for cid in matching_ids if cid not in exclude_ids]

        if not matching_ids:
            # Fallback to direct collection delete where source=source if no metadata scan found IDs
            try:
                collection = self._ensure_collection()
                collection.delete(where={"source": source})
            except Exception:
                pass
            return 0

        self.delete_by_ids(matching_ids)
        logger.info(
            "Deleted %d chunk(s) for source '%s' from collection '%s'",
            len(matching_ids),
            source,
            self._collection_name,
        )
        return len(matching_ids)

    # =================================================================
    # Collection Information
    # =================================================================

    def count(self) -> int:
        """Returns the total number of stored chunks in the collection.

        Returns:
            Integer count of records.
        """
        collection = self._ensure_collection()
        return collection.count()

    def collection_info(self) -> Dict[str, Any]:
        """Returns collection metadata and statistics.

        Returns:
            Dictionary containing collection name, record count,
            persist directory, and configured provider.
        """
        collection = self._ensure_collection()
        return {
            "name": self._collection_name,
            "count": collection.count(),
            "persist_directory": self._persist_directory,
            "provider": self._settings.vectordb_provider,
        }

    # =================================================================
    # Collection Reset
    # =================================================================

    def reset_collection(self) -> None:
        """Drops and recreates the collection.

        Use this when embedding model or dimensionality changes require
        a full re-embedding of all documents.

        Raises:
            CollectionError: If drop or recreation fails.
        """
        client = self._ensure_client()

        try:
            client.delete_collection(name=self._collection_name)
            logger.warning(
                "Dropped ChromaDB collection '%s'", self._collection_name
            )
        except Exception as e:
            raise CollectionError(
                f"Failed to drop collection '{self._collection_name}': {e}"
            ) from e

        self._collection = None

        try:
            self.get_or_create_collection()
            logger.info(
                "Recreated ChromaDB collection '%s'", self._collection_name
            )
        except Exception as e:
            raise CollectionError(
                f"Failed to recreate collection '{self._collection_name}': {e}"
            ) from e
