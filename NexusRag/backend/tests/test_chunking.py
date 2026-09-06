import pytest
from langchain_core.documents import Document

from app.chunking import (
    ChunkingConfigurationError,
    DocumentChunker,
)
from app.core.config import get_settings


@pytest.fixture
def chunker() -> DocumentChunker:
    """Fixture providing a DocumentChunker configured from application settings."""
    return DocumentChunker()


def test_centralized_config_integration() -> None:
    """Verify DocumentChunker reads chunk_size and chunk_overlap from centralized settings."""
    settings = get_settings()
    chunker = DocumentChunker()
    assert chunker.chunk_size == settings.chunk_size
    assert chunker.chunk_overlap == settings.chunk_overlap


def test_basic_document_chunking(chunker: DocumentChunker) -> None:
    """Verify a document larger than chunk_size is split into multiple distinct chunks."""
    long_text = "Paragraph 1: NexusRAG architecture and ingestion pipeline.\n\n" * 40
    doc = Document(page_content=long_text, metadata={"source": "overview.txt", "page": 1})

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    for chunk in chunks:
        assert isinstance(chunk, Document)
        assert len(chunk.page_content) > 0
        assert chunk.metadata["source"] == "overview.txt"


def test_multiple_documents_batch(chunker: DocumentChunker) -> None:
    """Verify chunk_documents processes a sequence of documents and aggregates all chunks."""
    docs = [
        Document(
            page_content="Content from doc 1 " * 50,
            metadata={"source": "doc1.txt", "page": 1},
        ),
        Document(
            page_content="Content from doc 2 " * 50,
            metadata={"source": "doc2.txt", "page": 1},
        ),
    ]

    all_chunks = chunker.chunk_documents(docs)
    assert len(all_chunks) >= 2

    sources = {c.metadata["source"] for c in all_chunks}
    assert "doc1.txt" in sources
    assert "doc2.txt" in sources


def test_document_shorter_than_chunk_size(chunker: DocumentChunker) -> None:
    """Verify documents shorter than chunk_size produce exactly 1 chunk without modification."""
    short_text = "This is a concise paragraph well below the 800-character chunk limit."
    doc = Document(page_content=short_text, metadata={"source": "short.md", "page": 1})

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].page_content == short_text
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["chunk_count"] == 1
    assert chunks[0].metadata["char_count"] == len(short_text)


def test_empty_and_whitespace_documents(chunker: DocumentChunker) -> None:
    """Verify empty or whitespace-only documents are handled gracefully without errors."""
    empty_doc = Document(page_content="", metadata={"source": "empty.txt"})
    ws_doc = Document(page_content="   \n\n\t   \n  ", metadata={"source": "ws.txt"})

    assert chunker.chunk_document(empty_doc) == []
    assert chunker.chunk_document(ws_doc) == []
    assert chunker.chunk_documents([]) == []


def test_metadata_preservation(chunker: DocumentChunker) -> None:
    """Verify all original metadata keys are preserved in every generated chunk."""
    content = "Detailed HR policies and corporate operational guidelines.\n\n" * 30
    original_metadata = {
        "source": "hr_policy.pdf",
        "file_name": "hr_policy.pdf",
        "file_type": "pdf",
        "page": 4,
        "total_pages": 12,
        "file_size_bytes": 45000,
    }
    doc = Document(page_content=content, metadata=original_metadata)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1

    for chunk in chunks:
        for key, value in original_metadata.items():
            assert key in chunk.metadata
            assert chunk.metadata[key] == value


def test_chunk_indexing_and_counts(chunker: DocumentChunker) -> None:
    """Verify sequential chunk indexing and accurate total chunk count annotations."""
    content = "Chunk index validation text content block.\n\n" * 30
    doc = Document(page_content=content, metadata={"source": "indexing.txt"})

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1

    for idx, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == idx
        assert chunk.metadata["chunk_count"] == len(chunks)
        assert chunk.metadata["char_count"] == len(chunk.page_content)


def test_deterministic_chunking(chunker: DocumentChunker) -> None:
    """Verify that chunking produces 100% deterministic output across multiple invocations."""
    content = "Reproducible chunking output verification with structured text.\n\n" * 25
    doc = Document(page_content=content, metadata={"source": "deterministic.txt"})

    run_1 = chunker.chunk_document(doc)
    run_2 = chunker.chunk_document(doc)

    assert len(run_1) == len(run_2)
    for c1, c2 in zip(run_1, run_2):
        assert c1.page_content == c2.page_content
        assert c1.metadata == c2.metadata


def test_invalid_chunk_size_validation() -> None:
    """Verify ChunkingConfigurationError is raised when chunk_size <= 0."""
    with pytest.raises(ChunkingConfigurationError):
        DocumentChunker(chunk_size=0, chunk_overlap=0)

    with pytest.raises(ChunkingConfigurationError):
        DocumentChunker(chunk_size=-100, chunk_overlap=10)


def test_invalid_overlap_negative_validation() -> None:
    """Verify ChunkingConfigurationError is raised when chunk_overlap is negative."""
    with pytest.raises(ChunkingConfigurationError):
        DocumentChunker(chunk_size=500, chunk_overlap=-1)


def test_invalid_overlap_greater_equal_chunk_size() -> None:
    """Verify ChunkingConfigurationError is raised when chunk_overlap >= chunk_size."""
    with pytest.raises(ChunkingConfigurationError):
        DocumentChunker(chunk_size=500, chunk_overlap=500)

    with pytest.raises(ChunkingConfigurationError):
        DocumentChunker(chunk_size=500, chunk_overlap=550)
