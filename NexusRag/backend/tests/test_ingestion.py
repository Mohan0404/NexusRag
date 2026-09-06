from pathlib import Path
import tempfile
import pytest

from app.core.config import Settings
from app.ingestion import (
    CorruptedFileError,
    DocumentService,
    EmptyContentError,
    EmptyFileError,
    FileNotFoundIngestionError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

# Minimal valid single-page PDF with text "NexusRAG Ingestion Test Page"
VALID_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 58 >> stream
BT
/F1 20 Tf
100 700 Td
(NexusRAG Ingestion Test Page) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000352 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
429
%%EOF"""


@pytest.fixture
def document_service() -> DocumentService:
    """Fixture providing a configured DocumentService instance."""
    return DocumentService()


def test_ingest_txt_file(document_service: DocumentService) -> None:
    """Verify loading, text cleaning, and metadata for .txt documents."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("FastAPI and LangChain\n\nProduction RAG architecture.\n")
        tmp_path = Path(f.name)

    try:
        docs = document_service.ingest_file(tmp_path)
        assert len(docs) == 1
        assert "FastAPI and LangChain" in docs[0].page_content
        assert docs[0].metadata["source"] == tmp_path.name
        assert docs[0].metadata["file_type"] == "txt"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["total_pages"] == 1
        assert docs[0].metadata["file_size_bytes"] > 0
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_markdown_file(document_service: DocumentService) -> None:
    """Verify loading and structure preservation for Markdown (.md) documents."""
    md_content = "# Project Overview\n\n- Component A: Ingestion\n- Component B: Chunking\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(md_content)
        tmp_path = Path(f.name)

    try:
        docs = document_service.ingest_file(tmp_path)
        assert len(docs) == 1
        assert "# Project Overview" in docs[0].page_content
        assert docs[0].metadata["file_type"] == "md"
        assert docs[0].metadata["source"] == tmp_path.name
        assert docs[0].metadata["page"] == 1
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_pdf_file(document_service: DocumentService) -> None:
    """Verify loading, text extraction, and page attribution for PDF documents."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(VALID_PDF_BYTES)
        tmp_path = Path(f.name)

    try:
        docs = document_service.ingest_file(tmp_path)
        assert len(docs) >= 1
        assert "NexusRAG Ingestion Test Page" in docs[0].page_content
        assert docs[0].metadata["source"] == tmp_path.name
        assert docs[0].metadata["file_type"] == "pdf"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["total_pages"] == 1
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_unsupported_extension(document_service: DocumentService) -> None:
    """Verify error handling for unsupported file extensions (e.g. .docx, .csv)."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(b"dummy docx binary content")
        tmp_path = Path(f.name)

    try:
        with pytest.raises(UnsupportedFileTypeError) as excinfo:
            document_service.ingest_file(tmp_path)
        assert "not supported" in str(excinfo.value)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_missing_file(document_service: DocumentService) -> None:
    """Verify error handling for non-existent file paths."""
    missing_path = Path("non_existent_folder/missing_file.pdf")
    with pytest.raises(FileNotFoundIngestionError):
        document_service.ingest_file(missing_path)


def test_ingest_empty_file(document_service: DocumentService) -> None:
    """Verify error handling for 0-byte files."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        with pytest.raises(EmptyFileError):
            document_service.ingest_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_corrupted_pdf(document_service: DocumentService) -> None:
    """Verify error handling for corrupted PDF files."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF header or content at all")
        tmp_path = Path(f.name)

    try:
        with pytest.raises(CorruptedFileError):
            document_service.ingest_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_empty_content(document_service: DocumentService) -> None:
    """Verify error handling when a document contains only whitespace."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("   \n\n\t   \r\n   ")
        tmp_path = Path(f.name)

    try:
        with pytest.raises(EmptyContentError):
            document_service.ingest_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_file_size_limit_enforced() -> None:
    """Verify that files exceeding the configured size limit are rejected."""
    # Create a custom settings object with a 1MB limit for testing
    custom_settings = Settings()
    custom_settings.ingestion.max_file_size_mb = 1  # 1 MB
    service = DocumentService(settings=custom_settings)

    # 1.5 MB dummy content
    large_content = "A" * int(1.5 * 1024 * 1024)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(large_content)
        tmp_path = Path(f.name)

    try:
        with pytest.raises(FileTooLargeError):
            service.ingest_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingest_directory_batch(document_service: DocumentService) -> None:
    """Verify batch ingestion over a directory skipping invalid files."""
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # Valid file 1 (.txt)
        (tmp_dir / "file1.txt").write_text("Hello from text", encoding="utf-8")
        # Valid file 2 (.md)
        (tmp_dir / "file2.md").write_text("# Hello Markdown", encoding="utf-8")
        # Unsupported file (.csv)
        (tmp_dir / "ignored.csv").write_text("a,b,c", encoding="utf-8")

        docs = document_service.ingest_directory(tmp_dir)
        assert len(docs) == 2
        sources = [d.metadata["source"] for d in docs]
        assert "file1.txt" in sources
        assert "file2.md" in sources
        assert "ignored.csv" not in sources
