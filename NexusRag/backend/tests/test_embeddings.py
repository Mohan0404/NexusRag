from unittest.mock import MagicMock, patch
import pytest
from google.genai import types
from langchain_core.documents import Document

from app.core.config import Settings
from app.embeddings import (
    EmbeddedChunk,
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    EmptyEmbeddingInputError,
    GeminiEmbeddingService,
    MissingAPIKeyError,
)


@pytest.fixture
def mock_client():
    """Fixture to mock google.genai.Client and its models.embed_content method."""
    with patch("google.genai.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield client


@pytest.fixture
def embedding_service(mock_client) -> GeminiEmbeddingService:
    """Fixture providing a GeminiEmbeddingService configured with test settings."""
    return GeminiEmbeddingService(
        api_key="test-gemini-dummy-key-12345",
        model="gemini-embedding-2",
        batch_size=2,
        output_dimension=768,
    )


def test_embed_single_text(mock_client, embedding_service: GeminiEmbeddingService) -> None:
    """Verify single document text embedding uses RETRIEVAL_DOCUMENT and MRL dimension 768."""
    mock_resp = types.EmbedContentResponse(
        embeddings=[types.ContentEmbedding(values=[0.1, 0.2, 0.3, 0.4])]
    )
    mock_client.models.embed_content.return_value = mock_resp

    vec = embedding_service.embed_text("NexusRAG retrieval architecture.")
    assert vec == [0.1, 0.2, 0.3, 0.4]

    mock_client.models.embed_content.assert_called_once()
    call_kwargs = mock_client.models.embed_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-embedding-2"
    assert call_kwargs["contents"] == "NexusRAG retrieval architecture."
    assert isinstance(call_kwargs["config"], types.EmbedContentConfig)
    assert call_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert call_kwargs["config"].output_dimensionality == 768


def test_embed_query(mock_client, embedding_service: GeminiEmbeddingService) -> None:
    """Verify search query embedding uses RETRIEVAL_QUERY and MRL dimension 768."""
    mock_resp = types.EmbedContentResponse(
        embeddings=[types.ContentEmbedding(values=[0.5, 0.6, 0.7, 0.8])]
    )
    mock_client.models.embed_content.return_value = mock_resp

    vec = embedding_service.embed_query("What is the chunking strategy?")
    assert vec == [0.5, 0.6, 0.7, 0.8]

    mock_client.models.embed_content.assert_called_once()
    call_kwargs = mock_client.models.embed_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-embedding-2"
    assert call_kwargs["contents"] == "What is the chunking strategy?"
    assert isinstance(call_kwargs["config"], types.EmbedContentConfig)
    assert call_kwargs["config"].task_type == "RETRIEVAL_QUERY"
    assert call_kwargs["config"].output_dimensionality == 768


def test_matryoshka_dimension_override(mock_client) -> None:
    """Verify custom output_dimension sets Matryoshka Representation Learning dimension."""
    custom_service = GeminiEmbeddingService(
        api_key="test-key",
        model="gemini-embedding-2",
        batch_size=5,
        output_dimension=256,
    )
    mock_resp = types.EmbedContentResponse(
        embeddings=[types.ContentEmbedding(values=[0.9] * 256)]
    )
    mock_client.models.embed_content.return_value = mock_resp

    vec = custom_service.embed_text("Testing Matryoshka dimensionality.")
    assert len(vec) == 256

    call_kwargs = mock_client.models.embed_content.call_args.kwargs
    assert call_kwargs["config"].output_dimensionality == 256


def test_embed_documents_and_metadata_preservation(
    mock_client, embedding_service: GeminiEmbeddingService
) -> None:
    """Verify Phase 4 Document chunks are embedded while preserving 100% of metadata."""
    docs = [
        Document(
            page_content="Chunk 1 content",
            metadata={"source": "doc.pdf", "page": 1, "chunk_index": 0},
        ),
        Document(
            page_content="Chunk 2 content",
            metadata={"source": "doc.pdf", "page": 1, "chunk_index": 1},
        ),
    ]
    mock_resp = types.EmbedContentResponse(
        embeddings=[
            types.ContentEmbedding(values=[0.11, 0.22]),
            types.ContentEmbedding(values=[0.33, 0.44]),
        ]
    )
    mock_client.models.embed_content.return_value = mock_resp

    embedded_chunks = embedding_service.embed_documents(docs)

    assert len(embedded_chunks) == 2
    for chunk in embedded_chunks:
        assert isinstance(chunk, EmbeddedChunk)

    assert embedded_chunks[0].content == "Chunk 1 content"
    assert embedded_chunks[0].embedding == [0.11, 0.22]
    assert embedded_chunks[0].metadata["source"] == "doc.pdf"
    assert embedded_chunks[0].metadata["chunk_index"] == 0

    assert embedded_chunks[1].content == "Chunk 2 content"
    assert embedded_chunks[1].embedding == [0.33, 0.44]
    assert embedded_chunks[1].metadata["source"] == "doc.pdf"
    assert embedded_chunks[1].metadata["chunk_index"] == 1

    # Verify lossless roundtrip back to LangChain Document
    doc_reconverted = embedded_chunks[0].to_document()
    assert doc_reconverted.page_content == "Chunk 1 content"
    assert doc_reconverted.metadata["source"] == "doc.pdf"
    assert doc_reconverted.metadata["chunk_index"] == 0


def test_batching_behavior(mock_client, embedding_service: GeminiEmbeddingService) -> None:
    """Verify batching splits texts into discrete sub-batches respecting batch_size."""
    texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
    # Service configured with batch_size=2: Expect 3 calls with sizes 2, 2, 1
    mock_client.models.embed_content.side_effect = [
        types.EmbedContentResponse(
            embeddings=[
                types.ContentEmbedding(values=[0.1, 0.1]),
                types.ContentEmbedding(values=[0.2, 0.2]),
            ]
        ),
        types.EmbedContentResponse(
            embeddings=[
                types.ContentEmbedding(values=[0.3, 0.3]),
                types.ContentEmbedding(values=[0.4, 0.4]),
            ]
        ),
        types.EmbedContentResponse(
            embeddings=[
                types.ContentEmbedding(values=[0.5, 0.5]),
            ]
        ),
    ]

    embeddings = embedding_service.embed_texts(texts)

    assert len(embeddings) == 5
    assert mock_client.models.embed_content.call_count == 3
    assert embeddings[0] == [0.1, 0.1]
    assert embeddings[4] == [0.5, 0.5]


def test_empty_input_handling(mock_client, embedding_service: GeminiEmbeddingService) -> None:
    """Verify validation on empty strings and empty collections."""
    with pytest.raises(EmptyEmbeddingInputError):
        embedding_service.embed_text("")

    with pytest.raises(EmptyEmbeddingInputError):
        embedding_service.embed_text("   \n\t  ")

    with pytest.raises(EmptyEmbeddingInputError):
        embedding_service.embed_query("")

    assert embedding_service.embed_texts([]) == []
    assert embedding_service.embed_documents([]) == []
    assert mock_client.models.embed_content.call_count == 0


def test_missing_api_key_error() -> None:
    """Verify MissingAPIKeyError is raised when no API key is provided."""
    custom_settings = Settings(GEMINI_API_KEY=None)
    service = GeminiEmbeddingService(settings=custom_settings, api_key=None)

    with pytest.raises(MissingAPIKeyError) as excinfo:
        service.embed_text("Test without API key")
    assert "GEMINI_API_KEY" in str(excinfo.value)


def test_provider_api_failure(mock_client, embedding_service: GeminiEmbeddingService) -> None:
    """Verify generic Google GenAI API failures are wrapped into EmbeddingProviderError."""
    mock_client.models.embed_content.side_effect = Exception("Connection refused by Google servers")

    with pytest.raises(EmbeddingProviderError) as excinfo:
        embedding_service.embed_text("Sample input")
    assert "embedding request failed" in str(excinfo.value)


def test_provider_rate_limit_failure(
    mock_client, embedding_service: GeminiEmbeddingService
) -> None:
    """Verify rate limit / 429 quota exhaustion errors are categorized as rate limits."""
    mock_client.models.embed_content.side_effect = Exception(
        "429 ResourceExhausted: Quota exceeded for model gemini-embedding-2"
    )

    with pytest.raises(EmbeddingProviderError) as excinfo:
        embedding_service.embed_text("Sample input")
    assert "rate limit / quota exceeded" in str(excinfo.value)


def test_malformed_response_handling(
    mock_client, embedding_service: GeminiEmbeddingService
) -> None:
    """Verify malformed API responses raise EmbeddingProviderError."""
    # Case 1: embeddings field is None
    mock_client.models.embed_content.return_value = MagicMock(embeddings=None)
    with pytest.raises(EmbeddingProviderError):
        embedding_service.embed_text("Sample input")

    # Case 2: embedding element has unexpected structure
    mock_client.models.embed_content.return_value = MagicMock(embeddings=["invalid_string_instead_of_vector"])
    with pytest.raises(EmbeddingProviderError):
        embedding_service.embed_text("Sample input")


def test_model_consistency_from_config() -> None:
    """Verify embedding service defaults to the centrally configured model and dimension."""
    service = GeminiEmbeddingService()
    settings = service.settings

    assert service.model == settings.embedding_model
    assert service.model == "gemini-embedding-2"
    assert service.batch_size == settings.embedding_batch_size
    assert service.batch_size == 100
    assert service.output_dimension == settings.embedding_output_dimension
    assert service.output_dimension == 768


def test_invalid_configuration() -> None:
    """Verify EmbeddingConfigurationError is raised when batch_size or output_dimension <= 0."""
    with pytest.raises(EmbeddingConfigurationError):
        GeminiEmbeddingService(batch_size=0)

    with pytest.raises(EmbeddingConfigurationError):
        GeminiEmbeddingService(batch_size=-10)

    with pytest.raises(EmbeddingConfigurationError):
        GeminiEmbeddingService(output_dimension=0)

    with pytest.raises(EmbeddingConfigurationError):
        GeminiEmbeddingService(output_dimension=-50)


# =====================================================================
# Phase 14 / Bug Fix: Multi-Text Batch Embedding Invariant Tests
# =====================================================================


def test_batch_embed_texts_produces_n_vectors(
    mock_client, embedding_service: GeminiEmbeddingService
) -> None:
    """Verify N input texts produce exactly N embedding vectors without drop or truncation."""
    texts = [f"Text snippet {i}" for i in range(5)]
    mock_resp = types.EmbedContentResponse(
        embeddings=[
            types.ContentEmbedding(values=[float(i)] * 4) for i in range(2)
        ]
    )
    mock_resp_2 = types.EmbedContentResponse(
        embeddings=[
            types.ContentEmbedding(values=[float(i)] * 4) for i in range(2, 4)
        ]
    )
    mock_resp_3 = types.EmbedContentResponse(
        embeddings=[
            types.ContentEmbedding(values=[4.0] * 4)
        ]
    )
    mock_client.models.embed_content.side_effect = [mock_resp, mock_resp_2, mock_resp_3]

    embeddings = embedding_service.embed_texts(texts)

    assert len(embeddings) == 5
    for i, vec in enumerate(embeddings):
        assert len(vec) == 4
        assert vec[0] == float(i)

    # Verify each call packaged contents as individual types.Content objects
    for call in mock_client.models.embed_content.call_args_list:
        contents_arg = call.kwargs["contents"]
        assert isinstance(contents_arg, list)
        for item in contents_arg:
            assert isinstance(item, types.Content)
            assert len(item.parts) == 1
            assert isinstance(item.parts[0], types.Part)


def test_batch_embed_documents_35_chunks(mock_client) -> None:
    """Verify 35 Document chunks produce exactly 35 EmbeddedChunk objects with metadata intact."""
    service = GeminiEmbeddingService(
        api_key="test-key",
        batch_size=50,  # Single batch for 35 chunks
    )
    docs = [
        Document(
            page_content=f"Genworx Roadmap section {i}",
            metadata={
                "source": "Genworx_Cracking_Roadmap.md",
                "chunk_index": i,
                "chunk_count": 35,
            },
        )
        for i in range(35)
    ]
    mock_resp = types.EmbedContentResponse(
        embeddings=[
            types.ContentEmbedding(values=[float(i) * 0.1] * 16) for i in range(35)
        ]
    )
    mock_client.models.embed_content.return_value = mock_resp

    embedded_chunks = service.embed_documents(docs)

    assert len(embedded_chunks) == 35
    for i, chunk in enumerate(embedded_chunks):
        assert chunk.content == f"Genworx Roadmap section {i}"
        assert chunk.metadata["source"] == "Genworx_Cracking_Roadmap.md"
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["chunk_count"] == 35
        assert chunk.embedding == [float(i) * 0.1] * 16


def test_embedding_count_mismatch_raises_error(mock_client) -> None:
    """Verify that if Gemini returns fewer embeddings than documents (e.g. 1 instead of 35),
    EmbeddingProviderError is raised immediately to prevent silent chunk dropping."""
    service = GeminiEmbeddingService(
        api_key="test-key",
        batch_size=50,
    )
    docs = [
        Document(
            page_content=f"Chunk {i}",
            metadata={"source": "test.md", "chunk_index": i},
        )
        for i in range(35)
    ]
    # Simulate Gemini batch bug: 35 input docs, but only 1 embedding returned
    mock_resp = types.EmbedContentResponse(
        embeddings=[types.ContentEmbedding(values=[0.1] * 16)]
    )
    mock_client.models.embed_content.return_value = mock_resp

    with pytest.raises(EmbeddingProviderError) as excinfo:
        service.embed_documents(docs)

    assert "Embedding count mismatch" in str(excinfo.value)
    assert "expected 35 vectors" in str(excinfo.value)
    assert "received 1" in str(excinfo.value)

