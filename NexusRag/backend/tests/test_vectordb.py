import hashlib
import os
import shutil
import tempfile
from typing import Dict, List

import pytest

from app.core.config import Settings
from app.embeddings.embedder import EmbeddedChunk
from app.vectordb import (
    ChromaStore,
    CollectionError,
    InvalidEmbeddingError,
    VectorStoreError,
)
from app.vectordb.chroma_store import PersistenceError


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """Provides a temporary directory for ChromaDB persistent storage."""
    chroma_dir = tmp_path / "test_chroma"
    chroma_dir.mkdir()
    yield str(chroma_dir)


@pytest.fixture
def chroma_store(tmp_chroma_dir) -> ChromaStore:
    """Provides a ChromaStore instance using a temporary persist directory."""
    store = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="test_collection",
    )
    store.get_or_create_collection()
    return store


@pytest.fixture
def sample_chunks() -> List[EmbeddedChunk]:
    """Provides sample EmbeddedChunk objects mirroring Phase 5 output."""
    return [
        EmbeddedChunk(
            content="NexusRAG provides sub-second retrieval for enterprise knowledge bases.",
            embedding=[0.1] * 768,
            metadata={
                "source": "architecture.pdf",
                "file_name": "architecture.pdf",
                "file_path": "C:/docs/architecture.pdf",
                "file_type": "pdf",
                "page": 1,
                "total_pages": 5,
                "file_size_bytes": 102400,
                "chunk_index": 0,
                "chunk_count": 3,
                "char_count": 72,
            },
        ),
        EmbeddedChunk(
            content="The chunking layer uses RecursiveCharacterTextSplitter with 800-char windows.",
            embedding=[0.2] * 768,
            metadata={
                "source": "architecture.pdf",
                "file_name": "architecture.pdf",
                "file_path": "C:/docs/architecture.pdf",
                "file_type": "pdf",
                "page": 2,
                "total_pages": 5,
                "file_size_bytes": 102400,
                "chunk_index": 1,
                "chunk_count": 3,
                "char_count": 80,
            },
        ),
        EmbeddedChunk(
            content="Embeddings are generated using Google Gemini Embedding 2 with MRL dimension 768.",
            embedding=[0.3] * 768,
            metadata={
                "source": "architecture.pdf",
                "file_name": "architecture.pdf",
                "file_path": "C:/docs/architecture.pdf",
                "file_type": "pdf",
                "page": 3,
                "total_pages": 5,
                "file_size_bytes": 102400,
                "chunk_index": 2,
                "chunk_count": 3,
                "char_count": 83,
            },
        ),
    ]


@pytest.fixture
def secondary_chunks() -> List[EmbeddedChunk]:
    """Provides chunks from a different source document."""
    return [
        EmbeddedChunk(
            content="Company leave policy allows 20 days of paid time off per year.",
            embedding=[0.5] * 768,
            metadata={
                "source": "hr-policy.txt",
                "file_name": "hr-policy.txt",
                "file_path": "C:/docs/hr-policy.txt",
                "file_type": "txt",
                "page": 1,
                "total_pages": 1,
                "file_size_bytes": 5000,
                "chunk_index": 0,
                "chunk_count": 1,
                "char_count": 62,
            },
        ),
    ]


# =====================================================================
# Test 1: Collection Creation
# =====================================================================


def test_collection_creation(tmp_chroma_dir) -> None:
    """Verify get_or_create_collection creates a named ChromaDB collection."""
    store = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="creation_test",
    )
    store.get_or_create_collection()

    assert store.count() == 0
    info = store.collection_info()
    assert info["name"] == "creation_test"
    assert info["count"] == 0
    assert info["provider"] == "chroma"


# =====================================================================
# Test 2: Persistent Collection Reopening
# =====================================================================


def test_persistent_collection_reopening(
    tmp_chroma_dir, sample_chunks
) -> None:
    """Verify data survives across two ChromaStore instances pointing at the same path."""
    # First instance: add data
    store1 = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="persist_test",
    )
    store1.get_or_create_collection()
    store1.add_embedded_chunks(sample_chunks)
    count_before = store1.count()
    assert count_before == 3

    # Destroy the first instance
    del store1

    # Second instance: verify data persists
    store2 = ChromaStore(
        persist_directory=tmp_chroma_dir,
        collection_name="persist_test",
    )
    store2.get_or_create_collection()
    count_after = store2.count()
    assert count_after == count_before


# =====================================================================
# Test 3: Add Embedded Chunks
# =====================================================================


def test_add_embedded_chunks(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify EmbeddedChunk objects are upserted into ChromaDB."""
    added = chroma_store.add_embedded_chunks(sample_chunks)

    assert added == 3
    assert chroma_store.count() == 3


# =====================================================================
# Test 4: Stored Text Retrieval
# =====================================================================


def test_stored_text_retrieval(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify retrieved documents match original chunk content."""
    chroma_store.add_embedded_chunks(sample_chunks)

    chunk_id = ChromaStore.generate_chunk_id("architecture.pdf", 0)
    result = chroma_store.get_by_ids([chunk_id], include=["documents"])

    assert len(result["ids"]) == 1
    assert result["documents"][0] == sample_chunks[0].content


# =====================================================================
# Test 5: Stored Metadata Preserved
# =====================================================================


def test_stored_metadata_preserved(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify all Phase 3/4 metadata fields round-trip correctly through ChromaDB."""
    chroma_store.add_embedded_chunks(sample_chunks)

    chunk_id = ChromaStore.generate_chunk_id("architecture.pdf", 1)
    result = chroma_store.get_by_ids([chunk_id], include=["metadatas"])

    meta = result["metadatas"][0]
    assert meta["source"] == "architecture.pdf"
    assert meta["file_name"] == "architecture.pdf"
    assert meta["file_type"] == "pdf"
    assert meta["page"] == 2
    assert meta["total_pages"] == 5
    assert meta["file_size_bytes"] == 102400
    assert meta["chunk_index"] == 1
    assert meta["chunk_count"] == 3
    assert meta["char_count"] == 80


# =====================================================================
# Test 6: Stored IDs Correct
# =====================================================================


def test_stored_ids_correct(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify deterministic IDs match generate_chunk_id output."""
    chroma_store.add_embedded_chunks(sample_chunks)

    for chunk in sample_chunks:
        expected_id = ChromaStore.generate_chunk_id(
            chunk.metadata["source"], chunk.metadata["chunk_index"]
        )
        result = chroma_store.get_by_ids([expected_id], include=["documents"])
        assert len(result["ids"]) == 1
        assert result["ids"][0] == expected_id


# =====================================================================
# Test 7: Multiple Chunks Stored
# =====================================================================


def test_multiple_chunks_stored(
    chroma_store: ChromaStore, sample_chunks, secondary_chunks
) -> None:
    """Verify batch of N chunks from multiple sources results in correct count."""
    chroma_store.add_embedded_chunks(sample_chunks)
    chroma_store.add_embedded_chunks(secondary_chunks)

    assert chroma_store.count() == 4


# =====================================================================
# Test 8: Upsert Idempotency
# =====================================================================


def test_upsert_idempotency(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify same chunks added twice: count stays the same, content updated."""
    chroma_store.add_embedded_chunks(sample_chunks)
    assert chroma_store.count() == 3

    # Modify content but keep same source/chunk_index → same IDs
    updated_chunks = [
        EmbeddedChunk(
            content="UPDATED: " + chunk.content,
            embedding=chunk.embedding,
            metadata=dict(chunk.metadata),
        )
        for chunk in sample_chunks
    ]
    chroma_store.add_embedded_chunks(updated_chunks)
    assert chroma_store.count() == 3  # No duplicates

    # Verify content was actually updated
    chunk_id = ChromaStore.generate_chunk_id("architecture.pdf", 0)
    result = chroma_store.get_by_ids([chunk_id], include=["documents"])
    assert result["documents"][0].startswith("UPDATED:")


# =====================================================================
# Test 9: Delete by IDs
# =====================================================================


def test_delete_by_ids(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify specific chunk IDs are removed."""
    chroma_store.add_embedded_chunks(sample_chunks)
    assert chroma_store.count() == 3

    id_to_delete = ChromaStore.generate_chunk_id("architecture.pdf", 1)
    chroma_store.delete_by_ids([id_to_delete])

    assert chroma_store.count() == 2
    result = chroma_store.get_by_ids([id_to_delete], include=["documents"])
    assert len(result["ids"]) == 0


# =====================================================================
# Test 10: Delete by Source
# =====================================================================


def test_delete_by_source(
    chroma_store: ChromaStore, sample_chunks, secondary_chunks
) -> None:
    """Verify all chunks from a source file are removed."""
    chroma_store.add_embedded_chunks(sample_chunks)
    chroma_store.add_embedded_chunks(secondary_chunks)
    assert chroma_store.count() == 4

    chroma_store.delete_by_source("architecture.pdf")

    assert chroma_store.count() == 1
    result = chroma_store.get_by_source("architecture.pdf")
    assert len(result["ids"]) == 0

    # Secondary source still exists
    result2 = chroma_store.get_by_source("hr-policy.txt")
    assert len(result2["ids"]) == 1


# =====================================================================
# Test 11: Collection Count and Info
# =====================================================================


def test_collection_count_and_info(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify count() and collection_info() return correct values."""
    assert chroma_store.count() == 0

    chroma_store.add_embedded_chunks(sample_chunks)

    assert chroma_store.count() == 3
    info = chroma_store.collection_info()
    assert info["count"] == 3
    assert info["name"] == "test_collection"
    assert info["provider"] == "chroma"
    assert "persist_directory" in info


# =====================================================================
# Test 12: Invalid Embedding Handling
# =====================================================================


def test_invalid_embedding_handling(chroma_store: ChromaStore) -> None:
    """Verify empty embedding vectors raise InvalidEmbeddingError."""
    bad_chunk = EmbeddedChunk(
        content="This chunk has no embedding.",
        embedding=[],
        metadata={"source": "bad.pdf", "chunk_index": 0},
    )

    with pytest.raises(InvalidEmbeddingError):
        chroma_store.add_embedded_chunks([bad_chunk])


# =====================================================================
# Test 13: Empty Input Handling
# =====================================================================


def test_empty_input_handling(chroma_store: ChromaStore) -> None:
    """Verify empty chunk list returns 0 with no error."""
    result = chroma_store.add_embedded_chunks([])
    assert result == 0
    assert chroma_store.count() == 0


# =====================================================================
# Test 14: Metadata Sanitization
# =====================================================================


def test_metadata_sanitization(chroma_store: ChromaStore) -> None:
    """Verify None values in metadata are stripped before ChromaDB insertion."""
    chunk_with_none = EmbeddedChunk(
        content="Testing None metadata handling.",
        embedding=[0.4] * 768,
        metadata={
            "source": "sanitize_test.pdf",
            "chunk_index": 0,
            "page": 1,
            "optional_field": None,  # Should be stripped
            "file_type": "pdf",
        },
    )

    chroma_store.add_embedded_chunks([chunk_with_none])

    chunk_id = ChromaStore.generate_chunk_id("sanitize_test.pdf", 0)
    result = chroma_store.get_by_ids([chunk_id], include=["metadatas"])

    meta = result["metadatas"][0]
    assert "optional_field" not in meta  # None stripped
    assert meta["source"] == "sanitize_test.pdf"
    assert meta["page"] == 1


# =====================================================================
# Test 15: Reset Collection
# =====================================================================


def test_reset_collection(
    chroma_store: ChromaStore, sample_chunks
) -> None:
    """Verify reset_collection() drops all data and recreates."""
    chroma_store.add_embedded_chunks(sample_chunks)
    assert chroma_store.count() == 3

    chroma_store.reset_collection()
    assert chroma_store.count() == 0


# =====================================================================
# Test 16: Get by Source
# =====================================================================


def test_get_by_source(
    chroma_store: ChromaStore, sample_chunks, secondary_chunks
) -> None:
    """Verify retrieval filtered by source metadata returns correct chunks."""
    chroma_store.add_embedded_chunks(sample_chunks)
    chroma_store.add_embedded_chunks(secondary_chunks)

    # Get all chunks from architecture.pdf
    result = chroma_store.get_by_source("architecture.pdf")
    assert len(result["ids"]) == 3

    # Get all chunks from hr-policy.txt
    result2 = chroma_store.get_by_source("hr-policy.txt")
    assert len(result2["ids"]) == 1
    assert result2["documents"][0] == secondary_chunks[0].content

    # Get from non-existent source
    result3 = chroma_store.get_by_source("nonexistent.pdf")
    assert len(result3["ids"]) == 0


# =====================================================================
# Deterministic ID Generation Unit Tests
# =====================================================================


def test_generate_chunk_id_deterministic() -> None:
    """Verify generate_chunk_id produces identical output for identical inputs."""
    id1 = ChromaStore.generate_chunk_id("report.pdf", 3)
    id2 = ChromaStore.generate_chunk_id("report.pdf", 3)
    assert id1 == id2
    assert len(id1) == 16

    # Different inputs produce different IDs
    id3 = ChromaStore.generate_chunk_id("report.pdf", 4)
    assert id1 != id3

    id4 = ChromaStore.generate_chunk_id("other.pdf", 3)
    assert id1 != id4
