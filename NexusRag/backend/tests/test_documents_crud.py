"""Phase 14 — Document Management CRUD API tests.

Tests:
- GET    /api/v1/documents         (List documents, empty and populated)
- DELETE /api/v1/documents/{source} (Delete document, cache invalidation, 404 handling)
- PUT    /api/v1/documents/{source} (Replace/re-index document, validation, 404 handling)
- ChromaStore.list_sources() and count_by_source()
Zero real calls to Gemini, OpenRouter, ChromaDB, or Redis.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_chroma_store,
    get_ingestion_pipeline,
    get_query_cache,
    get_settings,
)
from app.cache.redis_cache import BaseQueryCache
from app.core.config import Settings
from app.embeddings import EmbeddedChunk, EmbeddingProviderError
from app.ingestion.pipeline import IngestionPipeline, IngestionResult
from app.main import app
from app.vectordb.chroma_store import ChromaStore, VectorStoreError


@pytest.fixture
def client() -> TestClient:
    """Provides a TestClient with cleanly managed dependency overrides."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_chroma_store() -> MagicMock:
    """Mock ChromaStore instance for CRUD operations."""
    store = MagicMock(spec=ChromaStore)
    return store


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock Redis query cache."""
    cache = MagicMock(spec=BaseQueryCache)
    return cache


@pytest.fixture
def mock_ingestion_pipeline() -> MagicMock:
    """Mock IngestionPipeline instance returning a canned IngestionResult."""
    pipeline = MagicMock(spec=IngestionPipeline)
    pipeline.index_file.return_value = IngestionResult(
        filename="new_manual.pdf",
        file_type=".pdf",
        file_size_bytes=2048,
        chunks_created=5,
        chunk_ids=["id_0", "id_1", "id_2", "id_3", "id_4"],
        cache_cleared=True,
    )
    return pipeline


# =====================================================================
# 1. GET /api/v1/documents
# =====================================================================


def test_documents_list_empty(client: TestClient, mock_chroma_store: MagicMock) -> None:
    """GET /documents returns empty list and total_chunks=0 when no documents indexed."""
    mock_chroma_store.list_sources.return_value = []
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["documents"] == []
    assert data["total_chunks"] == 0


def test_documents_list_populated(client: TestClient, mock_chroma_store: MagicMock) -> None:
    """GET /documents returns formatted document summaries with aggregate chunk count."""
    mock_chroma_store.list_sources.return_value = [
        {
            "source": "handbook.pdf",
            "file_type": ".pdf",
            "chunk_count": 12,
            "indexed_at": "2026-09-06T12:00:00Z",
        },
        {
            "source": "notes.txt",
            "file_type": ".txt",
            "chunk_count": 4,
            "indexed_at": "2026-09-06T11:00:00Z",
        },
    ]
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 2
    assert data["total_chunks"] == 16
    assert data["documents"][0]["source"] == "handbook.pdf"
    assert data["documents"][0]["chunk_count"] == 12
    assert data["documents"][0]["indexed_at"] == "2026-09-06T12:00:00Z"
    assert data["documents"][1]["source"] == "notes.txt"
    assert data["documents"][1]["chunk_count"] == 4


def test_documents_list_handles_vector_store_error(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """GET /documents returns 500 when ChromaStore raises VectorStoreError."""
    mock_chroma_store.list_sources.side_effect = VectorStoreError("ChromaDB connection failure")
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 500
    assert "Failed to retrieve indexed documents" in response.json()["detail"]


# =====================================================================
# 2. DELETE /api/v1/documents/{source}
# =====================================================================


def test_documents_delete_success(
    client: TestClient, mock_chroma_store: MagicMock, mock_cache: MagicMock
) -> None:
    """DELETE /documents/{source} deletes chunks, clears cache, and returns 200."""
    mock_chroma_store.count_by_source.return_value = 8
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_query_cache] = lambda: mock_cache

    response = client.delete("/api/v1/documents/handbook.pdf")

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "handbook.pdf"
    assert data["chunks_deleted"] == 8
    assert data["status"] == "deleted"
    mock_chroma_store.delete_by_source.assert_called_once_with("handbook.pdf")
    mock_cache.clear.assert_called_once()


def test_documents_delete_not_found(
    client: TestClient, mock_chroma_store: MagicMock, mock_cache: MagicMock
) -> None:
    """DELETE /documents/{source} returns 404 when document does not exist."""
    mock_chroma_store.count_by_source.return_value = 0
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_query_cache] = lambda: mock_cache

    response = client.delete("/api/v1/documents/nonexistent.pdf")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    mock_chroma_store.delete_by_source.assert_not_called()
    mock_cache.clear.assert_not_called()


def test_documents_delete_handles_vector_store_error(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """DELETE /documents/{source} returns 500 when ChromaStore fails."""
    mock_chroma_store.count_by_source.return_value = 5
    mock_chroma_store.delete_by_source.side_effect = VectorStoreError("Deletion failed")
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.delete("/api/v1/documents/handbook.pdf")

    assert response.status_code == 500
    assert "Failed to delete document" in response.json()["detail"]


# =====================================================================
# 3. PUT /api/v1/documents/{source}
# =====================================================================


def test_documents_replace_success(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} deletes old doc, ingests replacement, and returns 200."""
    mock_chroma_store.count_by_source.return_value = 3
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("new_manual.pdf", b"%PDF-1.4 Mock PDF replacement", "application/pdf")}
    response = client.put("/api/v1/documents/old_manual.pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "new_manual.pdf"
    assert data["chunks_created"] == 5
    assert data["status"] == "success"
    mock_chroma_store.delete_by_source.assert_called_once_with("old_manual.pdf")
    mock_ingestion_pipeline.index_file.assert_called_once()


def test_documents_replace_target_not_found(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} returns 404 when old document does not exist."""
    mock_chroma_store.count_by_source.return_value = 0
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("new_manual.pdf", b"Some replacement text content", "application/pdf")}
    response = client.put("/api/v1/documents/missing.pdf", files=files)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    mock_chroma_store.delete_by_source.assert_not_called()
    mock_ingestion_pipeline.index_file.assert_not_called()


def test_documents_replace_invalid_extension(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} returns 400 for unsupported file extension."""
    mock_chroma_store.count_by_source.return_value = 4
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("virus.exe", b"binary data", "application/octet-stream")}
    response = client.put("/api/v1/documents/handbook.pdf", files=files)

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]
    mock_chroma_store.delete_by_source.assert_not_called()
    mock_ingestion_pipeline.index_file.assert_not_called()


def test_documents_replace_empty_file(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} returns 400 when uploaded replacement is 0 bytes."""
    mock_chroma_store.count_by_source.return_value = 4
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("empty.txt", b"", "text/plain")}
    response = client.put("/api/v1/documents/handbook.pdf", files=files)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
    mock_chroma_store.delete_by_source.assert_not_called()
    mock_ingestion_pipeline.index_file.assert_not_called()


# =====================================================================
# 4. Phase 14 / Bug Fix Verification Tests
# =====================================================================


def test_documents_list_35_chunks_single_document(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """GET /documents for a 35-chunk document returns exact canonical name and 35 total chunks."""
    mock_chroma_store.list_sources.return_value = [
        {
            "source": "Genworx_Cracking_Roadmap.md",
            "file_type": ".md",
            "chunk_count": 35,
            "indexed_at": "2026-09-06T20:08:17Z",
        }
    ]
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["total_chunks"] == 35
    assert data["documents"][0]["source"] == "Genworx_Cracking_Roadmap.md"
    assert data["documents"][0]["file_type"] == ".md"
    assert data["documents"][0]["chunk_count"] == 35


def test_documents_list_two_documents_total_chunks(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """GET /documents for Doc A (35 chunks) + Doc B (12 chunks) returns total_chunks == 47."""
    mock_chroma_store.list_sources.return_value = [
        {
            "source": "Document_A.md",
            "file_type": ".md",
            "chunk_count": 35,
            "indexed_at": "2026-09-06T20:08:17Z",
        },
        {
            "source": "Document_B.pdf",
            "file_type": ".pdf",
            "chunk_count": 12,
            "indexed_at": "2026-09-06T19:00:00Z",
        },
    ]
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 2
    assert data["total_chunks"] == 47


def test_documents_list_missing_indexed_at(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """GET /documents returns None/null for legacy documents without indexed_at timestamp."""
    mock_chroma_store.list_sources.return_value = [
        {
            "source": "legacy_doc.pdf",
            "file_type": ".pdf",
            "chunk_count": 5,
            "indexed_at": None,
        }
    ]
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["documents"][0]["indexed_at"] is None


def test_documents_replace_embedding_failure_preserves_old_document(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} fails safely without deleting old document when embedding/indexing fails."""
    mock_chroma_store.count_by_source.return_value = 3
    mock_ingestion_pipeline.index_file.side_effect = EmbeddingProviderError("Gemini quota exhausted")
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("new_manual.pdf", b"Some replacement text", "application/pdf")}
    response = client.put("/api/v1/documents/old_manual.pdf", files=files)

    assert response.status_code == 500
    # Crucial safety invariant: old document vectors must NOT be deleted!
    mock_chroma_store.delete_by_source.assert_not_called()


def test_documents_replace_ordering_index_before_delete(
    client: TestClient,
    mock_chroma_store: MagicMock,
    mock_ingestion_pipeline: MagicMock,
) -> None:
    """PUT /documents/{source} executes index_file BEFORE delete_by_source."""
    call_order = []
    mock_chroma_store.count_by_source.return_value = 3

    def fake_index(*args, **kwargs):
        call_order.append("index")
        return IngestionResult(
            filename="new.pdf",
            file_type=".pdf",
            file_size_bytes=100,
            chunks_created=5,
            chunk_ids=["id1"],
            cache_cleared=True,
        )

    mock_ingestion_pipeline.index_file.side_effect = fake_index
    mock_chroma_store.delete_by_source.side_effect = lambda *args, **kwargs: call_order.append("delete")

    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("new.pdf", b"content", "application/pdf")}
    response = client.put("/api/v1/documents/old.pdf", files=files)

    assert response.status_code == 200
    assert call_order == ["index", "delete"]


def test_documents_list_physical_count_truth_prevents_metadata_masking(
    client: TestClient, mock_chroma_store: MagicMock
) -> None:
    """CRITICAL: GET /documents must report the physical Chroma record count (1),
    NOT fabricating 35 from metadata chunk_count."""
    mock_chroma_store.list_sources.return_value = [
        {
            "source": "Genworx_Cracking_Roadmap.md",
            "file_type": ".md",
            "chunk_count": 1,  # Only 1 vector exists physically
            "indexed_at": "2026-09-06T20:08:17Z",
        }
    ]
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["chunk_count"] == 1
    assert data["total_chunks"] == 1


def test_documents_delete_legacy_source(
    client: TestClient, mock_chroma_store: MagicMock, mock_cache: MagicMock
) -> None:
    """DELETE /documents/{source} using canonical name deletes legacy UUID-prefixed records."""
    mock_chroma_store.count_by_source.return_value = 1
    mock_chroma_store.delete_by_source.return_value = 1
    app.dependency_overrides[get_chroma_store] = lambda: mock_chroma_store
    app.dependency_overrides[get_query_cache] = lambda: mock_cache

    response = client.delete("/api/v1/documents/Genworx_Cracking_Roadmap.md")

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "Genworx_Cracking_Roadmap.md"
    assert data["chunks_deleted"] == 1
    assert data["status"] == "deleted"
    mock_chroma_store.delete_by_source.assert_called_once_with("Genworx_Cracking_Roadmap.md")


