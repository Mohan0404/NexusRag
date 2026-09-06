"""Phase 11 — Document Upload API tests (POST /api/v1/documents/upload).

Tests file validation, path traversal defense, streaming size limits,
and ingestion pipeline integration including cache invalidation hooks.
Zero real calls to Gemini, OpenRouter, ChromaDB, or Redis.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_ingestion_pipeline, get_settings
from app.cache.redis_cache import BaseQueryCache
from app.chunking.chunker import DocumentChunker
from app.core.config import Settings
from app.embeddings.embedder import BaseEmbeddingService
from app.ingestion.document_service import DocumentService
from app.ingestion.loader import EmptyContentError, IngestionError
from app.ingestion.pipeline import IngestionPipeline, IngestionResult
from app.main import app
from app.vectordb.chroma_store import ChromaStore


@pytest.fixture
def client() -> TestClient:
    """Provides a TestClient with cleanly managed dependency overrides."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ingestion_pipeline() -> MagicMock:
    """Mock IngestionPipeline instance returning a canned IngestionResult."""
    pipeline = MagicMock(spec=IngestionPipeline)
    pipeline.index_file.return_value = IngestionResult(
        filename="test.txt",
        file_type=".txt",
        file_size_bytes=1024,
        chunks_created=3,
        chunk_ids=["id_0", "id_1", "id_2"],
        cache_cleared=True,
    )
    return pipeline


# =====================================================================
# Document Upload Endpoint Tests
# =====================================================================


def test_12_valid_txt_upload_success(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """12. Uploading a valid .txt file succeeds with HTTP 200 and chunk metadata."""
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("notes.txt", b"Employee benefits overview notes.", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "notes.txt"
    assert data["file_type"] == ".txt"
    assert data["status"] == "success"
    assert data["chunks_created"] == 3
    mock_ingestion_pipeline.index_file.assert_called_once()


def test_13_valid_pdf_upload_success(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """13. Uploading a valid .pdf file succeeds with HTTP 200 and chunk metadata."""
    mock_ingestion_pipeline.index_file.return_value = IngestionResult(
        filename="policy.pdf",
        file_type=".pdf",
        file_size_bytes=2048,
        chunks_created=5,
        chunk_ids=["c1", "c2", "c3", "c4", "c5"],
        cache_cleared=True,
    )
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("policy.pdf", b"%PDF-1.4 dummy pdf bytes", "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "policy.pdf"
    assert data["file_type"] == ".pdf"
    assert data["chunks_created"] == 5


def test_14_valid_markdown_upload_success(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """14. Uploading a valid .md file succeeds with HTTP 200 and chunk metadata."""
    mock_ingestion_pipeline.index_file.return_value = IngestionResult(
        filename="guide.md",
        file_type=".md",
        file_size_bytes=512,
        chunks_created=2,
        chunk_ids=["m1", "m2"],
        cache_cleared=True,
    )
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("guide.md", b"# Architecture Guide\nContent here.", "text/markdown")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "guide.md"
    assert data["chunks_created"] == 2


def test_15_unsupported_extension_returns_400(client: TestClient) -> None:
    """15. Uploading an unpermitted extension (.exe, .csv) returns 400 Bad Request."""
    files = {"file": ("program.exe", b"MZ executable bytes", "application/octet-stream")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_16_empty_file_returns_400(client: TestClient) -> None:
    """16. Uploading a 0-byte file returns 400 Bad Request."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]


def test_17_oversized_file_returns_413(client: TestClient) -> None:
    """17. Uploading a file exceeding configured max size returns 413 Payload Too Large."""
    # Mock settings to have a tiny 100-byte limit for testing
    mock_settings = MagicMock()
    mock_settings.allowed_extensions = [".pdf", ".txt", ".md"]
    mock_settings.max_file_size_bytes = 100  # 100 bytes limit
    mock_settings.ingestion = MagicMock(max_file_size_mb=1)

    app.dependency_overrides[get_settings] = lambda: mock_settings

    files = {"file": ("large.txt", b"x" * 200, "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_path_traversal_filename_sanitized(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """Extra: Path traversal characters in filename are stripped safely."""
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("../../etc/passwd.txt", b"secret info", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    # Filename in response should be sanitized to base name
    assert response.json()["filename"] == "passwd.txt"


def test_blank_filename_returns_400(client: TestClient) -> None:
    """Extra: Blank/whitespace filename is rejected with 400 Bad Request."""
    files = {"file": ("   ", b"some content", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    assert "Filename must not be empty or blank" in response.json()["detail"]


def test_missing_file_field_returns_422(client: TestClient) -> None:
    """Extra: Missing file in multipart form returns 422 Unprocessable Entity."""
    response = client.post("/api/v1/documents/upload", data={"other": "field"})
    assert response.status_code == 422


# =====================================================================
# IngestionPipeline & Cache Invalidation Unit Tests
# =====================================================================


def test_18_successful_ingestion_clears_cache() -> None:
    """18. Successful ChromaDB indexing triggers cache.clear()."""
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.ingest_file.return_value = ["dummy_doc"]

    mock_chunker = MagicMock(spec=DocumentChunker)
    mock_chunker.chunk_documents.return_value = ["dummy_chunk_1", "dummy_chunk_2"]

    mock_embedder = MagicMock(spec=BaseEmbeddingService)
    mock_embedder.embed_documents.return_value = ["embedded_chunk_1", "embedded_chunk_2"]

    mock_chroma = MagicMock(spec=ChromaStore)
    mock_chroma.add_embedded_chunks.return_value = 2

    mock_cache = MagicMock()

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    fake_path = Path("test_doc.txt")
    result = pipeline.index_file(fake_path)

    assert result.chunks_created == 2
    assert result.cache_cleared is True
    mock_cache.clear.assert_called_once()


def test_19_failed_ingestion_does_not_clear_cache() -> None:
    """19. If parsing or indexing fails, cache.clear() is NOT called."""
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.ingest_file.side_effect = IngestionError("Corrupted file header")

    mock_chunker = MagicMock(spec=DocumentChunker)
    mock_embedder = MagicMock(spec=BaseEmbeddingService)
    mock_chroma = MagicMock(spec=ChromaStore)
    mock_cache = MagicMock()

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    with pytest.raises(IngestionError):
        pipeline.index_file(Path("corrupt.pdf"))

    mock_cache.clear.assert_not_called()


def test_20_cache_clear_failure_does_not_break_ingestion() -> None:
    """20. If cache.clear() raises an exception, document ingestion still succeeds."""
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.ingest_file.return_value = ["doc"]

    mock_chunker = MagicMock(spec=DocumentChunker)
    mock_chunker.chunk_documents.return_value = ["chunk"]

    mock_embedder = MagicMock(spec=BaseEmbeddingService)
    mock_embedder.embed_documents.return_value = ["emb"]

    mock_chroma = MagicMock(spec=ChromaStore)
    mock_chroma.add_embedded_chunks.return_value = 1

    # Cache clear fails with simulated network error
    mock_cache = MagicMock()
    mock_cache.clear.side_effect = Exception("Redis connection refused")

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    result = pipeline.index_file(Path("notes.txt"))

    # Must NOT raise exception; document indexing was successful
    assert result.chunks_created == 1
    assert result.cache_cleared is False


# =====================================================================
# Phase 13 — Resource Lifecycle & Edge Case Tests
# =====================================================================


def test_21_staged_file_cleaned_up_after_successful_ingestion(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """21. Regression test: Staged file in data/uploads/ is deleted after successful indexing."""
    captured_path: List[Path] = []

    def spy_index_file(path: Path) -> IngestionResult:
        captured_path.append(path)
        # Verify the staged file exists during indexing
        assert path.exists(), f"Staged file {path} should exist when index_file is called"
        return IngestionResult(
            filename=path.name,
            file_type=path.suffix,
            file_size_bytes=100,
            chunks_created=1,
            cache_cleared=True,
        )

    mock_ingestion_pipeline.index_file.side_effect = spy_index_file
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("cleanup_test.txt", b"Temporary file content to verify unlinking.", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    assert len(captured_path) == 1
    # Verify the staged file was unlinked and does NOT linger on disk
    assert not captured_path[0].exists(), f"Staged file {captured_path[0]} must be deleted after upload completes"


def test_22_staged_file_cleaned_up_after_failed_ingestion(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """22. Regression test: Staged file is cleaned up even if ingestion throws an exception."""
    captured_path: List[Path] = []

    def failing_index_file(path: Path) -> IngestionResult:
        captured_path.append(path)
        assert path.exists()
        raise IngestionError("Simulated pipeline ingestion crash")

    mock_ingestion_pipeline.index_file.side_effect = failing_index_file
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("failing_doc.txt", b"Content that triggers pipeline crash.", "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 500
    assert len(captured_path) == 1
    # Verify staged file was unlinked in finally block despite exception
    assert not captured_path[0].exists(), f"Staged file {captured_path[0]} must be deleted even after failure"


def test_23_zero_extractable_text_returns_422(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """23. Document with valid structure but zero extractable text returns 422 Unprocessable Entity."""
    mock_ingestion_pipeline.index_file.side_effect = EmptyContentError(
        "Document contains no extractable textual content (e.g. scanned image PDF)."
    )
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    files = {"file": ("scanned_blank.pdf", b"%PDF-1.4 dummy pdf without text", "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 422
    assert "no extractable textual content" in response.json()["detail"]


def test_24_duplicate_filename_upload_creates_isolated_staging(
    client: TestClient, mock_ingestion_pipeline: MagicMock
) -> None:
    """24. Consecutive uploads with the same filename stage to unique UUID paths without collision."""
    captured_paths: List[Path] = []

    def recording_index_file(path: Path) -> IngestionResult:
        captured_paths.append(path)
        return IngestionResult(
            filename=path.name,
            file_type=path.suffix,
            file_size_bytes=50,
            chunks_created=1,
            cache_cleared=True,
        )

    mock_ingestion_pipeline.index_file.side_effect = recording_index_file
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion_pipeline

    # Upload 1
    res1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("handbook.txt", b"First version content.", "text/plain")},
    )
    assert res1.status_code == 200

    # Upload 2 with identical filename
    res2 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("handbook.txt", b"Second version content.", "text/plain")},
    )
    assert res2.status_code == 200

    assert len(captured_paths) == 2
    # Ensure UUID prefix made paths unique
    assert captured_paths[0] != captured_paths[1]
    # Both paths should be cleanly removed
    assert not captured_paths[0].exists()
    assert not captured_paths[1].exists()
