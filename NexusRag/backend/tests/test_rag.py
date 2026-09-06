"""Phase 9 — RAG Pipeline tests.

All tests use mocked Retriever and a FakeLLMService.
Zero real API calls to Gemini, OpenRouter, or ChromaDB.
"""

from typing import List
from unittest.mock import MagicMock, call

import pytest

from app.llm.llm_service import BaseLLMService, LLMError, LLMProviderError, LLMResponse
from app.prompts.templates import build_rag_prompt
from app.rag import (
    NO_CONTEXT_ANSWER,
    RAGPipeline,
    RAGPipelineError,
    RAGResponse,
    SourceReference,
)
from app.retrieval.retriever import (
    RetrievalError,
    RetrievedChunk,
    Retriever,
    VectorSearchError,
)


# =====================================================================
# Test Helpers
# =====================================================================


class FakeLLMService(BaseLLMService):
    """Deterministic fake LLM service. Returns a canned response.

    Captures the prompt passed to generate() for assertions.
    """

    def __init__(self, answer: str = "The leave policy allows 20 days PTO."):
        self.answer = answer
        self.last_prompt: str | None = None
        self.call_count: int = 0

    def generate(self, prompt: str) -> LLMResponse:
        self.last_prompt = prompt
        self.call_count += 1
        return LLMResponse(
            content=self.answer,
            model="google/gemini-2.5-flash",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )


class FailingLLMService(BaseLLMService):
    """LLM service that always raises LLMError."""

    def generate(self, prompt: str) -> LLMResponse:
        raise LLMProviderError("OpenRouter request failed: 500 Internal Server Error")


def _make_chunk(
    content: str,
    source: str = "report.pdf",
    file_type: str = "pdf",
    page: int = 1,
    chunk_index: int = 0,
    distance: float = 0.25,
) -> RetrievedChunk:
    """Factory for RetrievedChunk test fixtures."""
    return RetrievedChunk(
        content=content,
        metadata={
            "source": source,
            "file_name": source,
            "file_type": file_type,
            "page": page,
            "total_pages": 10,
            "file_size_bytes": 204800,
            "chunk_index": chunk_index,
            "chunk_count": 5,
            "char_count": len(content),
        },
        distance=distance,
    )


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def sample_chunks() -> List[RetrievedChunk]:
    """Three chunks from two documents across different pages."""
    return [
        _make_chunk(
            content="Employees are entitled to 20 days of paid time off per year.",
            source="hr_policy.pdf",
            page=3,
            chunk_index=0,
            distance=0.10,
        ),
        _make_chunk(
            content="Remote work is allowed up to 3 days per week with manager approval.",
            source="hr_policy.pdf",
            page=5,
            chunk_index=1,
            distance=0.20,
        ),
        _make_chunk(
            content="The onboarding process includes a 2-week orientation program.",
            source="onboarding_guide.md",
            file_type="md",
            page=1,
            chunk_index=0,
            distance=0.35,
        ),
    ]


@pytest.fixture
def fake_llm() -> FakeLLMService:
    return FakeLLMService()


@pytest.fixture
def mock_retriever(sample_chunks) -> MagicMock:
    """Mock Retriever that returns sample chunks."""
    retriever = MagicMock(spec=Retriever)
    retriever.retrieve.return_value = sample_chunks
    return retriever


@pytest.fixture
def pipeline(mock_retriever, fake_llm) -> RAGPipeline:
    return RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)


# =====================================================================
# Test 1: Retriever Receives the Original Query
# =====================================================================


def test_retriever_receives_original_query(
    mock_retriever, fake_llm
) -> None:
    """Verify the user's original question is passed unchanged to Retriever.retrieve()."""
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)
    question = "What is the leave policy?"

    pipeline.query(question)

    mock_retriever.retrieve.assert_called_once_with(question)


# =====================================================================
# Test 2: Retrieved Chunks Appear in the Prompt
# =====================================================================


def test_retrieved_chunks_appear_in_prompt(
    mock_retriever, sample_chunks
) -> None:
    """Verify all retrieved chunk texts appear in the prompt sent to the LLM."""
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)

    pipeline.query("What is the leave policy?")

    prompt = fake_llm.last_prompt
    assert prompt is not None

    for chunk in sample_chunks:
        assert chunk.content in prompt, (
            f"Chunk content not found in prompt: {chunk.content[:50]}..."
        )


# =====================================================================
# Test 3: Original Query Appears in the Prompt
# =====================================================================


def test_original_query_appears_in_prompt(
    mock_retriever,
) -> None:
    """Verify the user's original question appears verbatim in the prompt."""
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)
    question = "What is the remote work policy at Genworx?"

    pipeline.query(question)

    assert question in fake_llm.last_prompt


# =====================================================================
# Test 4: LLM Receives the Constructed Prompt
# =====================================================================


def test_llm_receives_constructed_prompt(
    mock_retriever, sample_chunks
) -> None:
    """Verify the LLM receives a properly structured prompt with context + question."""
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)
    question = "What is the leave policy?"

    pipeline.query(question)

    prompt = fake_llm.last_prompt
    # Prompt must contain the system instructions
    assert "CONTEXT" in prompt
    assert "QUESTION" in prompt
    assert "ANSWER" in prompt
    # Source headers must be present
    assert "[Source 1:" in prompt
    assert "hr_policy.pdf" in prompt


# =====================================================================
# Test 5: LLM is NOT Called When No Chunks Are Retrieved
# =====================================================================


def test_llm_not_called_when_no_chunks(fake_llm) -> None:
    """Verify the LLM is NOT called when retrieval returns an empty list.

    The pipeline should return a controlled 'no relevant info' response.
    """
    empty_retriever = MagicMock(spec=Retriever)
    empty_retriever.retrieve.return_value = []
    pipeline = RAGPipeline(retriever=empty_retriever, llm_service=fake_llm)

    result = pipeline.query("What is the company stock plan?")

    assert fake_llm.call_count == 0
    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == []
    assert result.context_chunks_used == 0
    assert result.model == ""
    assert result.query == "What is the company stock plan?"


# =====================================================================
# Test 6: Sources Preserve Page-Level Information
# =====================================================================


def test_sources_preserve_page_info(pipeline, sample_chunks) -> None:
    """Verify source citations preserve page-level granularity.

    sample_chunks has:
    - hr_policy.pdf, Page 3
    - hr_policy.pdf, Page 5
    - onboarding_guide.md, Page 1

    All three should appear as separate SourceReference entries.
    """
    result = pipeline.query("What is the leave policy?")

    assert len(result.sources) == 3

    # Check each source preserves its page
    sources_tuples = [(s.source, s.page) for s in result.sources]
    assert ("hr_policy.pdf", 3) in sources_tuples
    assert ("hr_policy.pdf", 5) in sources_tuples
    assert ("onboarding_guide.md", 1) in sources_tuples

    # Verify file_type preserved
    md_source = [s for s in result.sources if s.source == "onboarding_guide.md"][0]
    assert md_source.file_type == "md"


# =====================================================================
# Test 7: Retrieval Error Handled
# =====================================================================


def test_retrieval_error_handled(fake_llm) -> None:
    """Verify retrieval failures are wrapped in RAGPipelineError."""
    failing_retriever = MagicMock(spec=Retriever)
    failing_retriever.retrieve.side_effect = VectorSearchError(
        "ChromaDB similarity search failed"
    )
    pipeline = RAGPipeline(retriever=failing_retriever, llm_service=fake_llm)

    with pytest.raises(RAGPipelineError, match="Failed to retrieve"):
        pipeline.query("What is the leave policy?")

    # LLM should not have been called
    assert fake_llm.call_count == 0


# =====================================================================
# Test 8: LLM Error Handled
# =====================================================================


def test_llm_error_handled(mock_retriever) -> None:
    """Verify LLM generation failures are wrapped in RAGPipelineError."""
    failing_llm = FailingLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=failing_llm)

    with pytest.raises(RAGPipelineError, match="Failed to generate"):
        pipeline.query("What is the leave policy?")


# =====================================================================
# Test 9: Successful RAG Query End-to-End
# =====================================================================


def test_successful_rag_query(pipeline) -> None:
    """Verify the full pipeline returns a valid RAGResponse."""
    result = pipeline.query("What is the leave policy?")

    assert isinstance(result, RAGResponse)
    assert result.answer == "The leave policy allows 20 days PTO."
    assert result.query == "What is the leave policy?"
    assert result.model == "google/gemini-2.5-flash"
    assert result.context_chunks_used == 3
    assert len(result.sources) == 3


# =====================================================================
# Test 10: Empty Query Rejected
# =====================================================================


def test_empty_query_rejected(pipeline) -> None:
    """Verify empty or whitespace-only queries are rejected."""
    with pytest.raises(RAGPipelineError, match="empty"):
        pipeline.query("")

    with pytest.raises(RAGPipelineError, match="empty"):
        pipeline.query("   ")


# =====================================================================
# Test 11: LLM Called Exactly Once
# =====================================================================


def test_llm_called_once(mock_retriever) -> None:
    """Verify LLM.generate() is called exactly once per query."""
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)

    pipeline.query("What is the leave policy?")

    assert fake_llm.call_count == 1


# =====================================================================
# Test 12: Source Deduplication at Page Level
# =====================================================================


def test_source_deduplication_at_page_level() -> None:
    """Verify that two chunks from the same (source, page) produce one SourceReference,
    but chunks from different pages of the same source are preserved.
    """
    chunks = [
        _make_chunk("Chunk A from page 3", source="policy.pdf", page=3, chunk_index=0),
        _make_chunk("Chunk B from page 3", source="policy.pdf", page=3, chunk_index=1),
        _make_chunk("Chunk C from page 7", source="policy.pdf", page=7, chunk_index=2),
    ]

    retriever = MagicMock(spec=Retriever)
    retriever.retrieve.return_value = chunks
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=retriever, llm_service=fake_llm)

    result = pipeline.query("Tell me about the policy")

    # Page 3 deduplicated to one entry, Page 7 separate = 2 total
    assert len(result.sources) == 2
    pages = [s.page for s in result.sources]
    assert 3 in pages
    assert 7 in pages


# =====================================================================
# Test 13: RAGResponse Includes Model Info
# =====================================================================


def test_response_includes_model_info(pipeline) -> None:
    """Verify RAGResponse includes the model name from the LLM."""
    result = pipeline.query("What is the leave policy?")

    assert result.model == "google/gemini-2.5-flash"


# =====================================================================
# Test 14: Prompt Contains Grounding Instructions
# =====================================================================


def test_prompt_contains_grounding_instructions(mock_retriever) -> None:
    """Verify the prompt includes grounding instructions from the system prompt."""
    fake_llm = FakeLLMService()
    pipeline = RAGPipeline(retriever=mock_retriever, llm_service=fake_llm)

    pipeline.query("What is the leave policy?")

    prompt = fake_llm.last_prompt
    # System prompt should contain grounding rules
    assert "ONLY the context" in prompt
    assert "Do not guess" in prompt


# =====================================================================
# Test 15: Retrieval Error Preserves Cause Chain
# =====================================================================


def test_retrieval_error_preserves_cause(fake_llm) -> None:
    """Verify RAGPipelineError chains the original RetrievalError as __cause__."""
    original_error = VectorSearchError("ChromaDB connection lost")
    failing_retriever = MagicMock(spec=Retriever)
    failing_retriever.retrieve.side_effect = original_error
    pipeline = RAGPipeline(retriever=failing_retriever, llm_service=fake_llm)

    with pytest.raises(RAGPipelineError) as exc_info:
        pipeline.query("test question")

    assert exc_info.value.__cause__ is original_error
