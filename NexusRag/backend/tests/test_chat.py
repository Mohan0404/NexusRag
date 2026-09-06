"""Phase 11 — Chat API tests (POST /api/v1/chat).

All tests use FastAPI TestClient and dependency overrides.
Zero real calls to Gemini, OpenRouter, ChromaDB, or Redis.
"""

from typing import List
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_rag_pipeline
from app.llm.llm_service import LLMProviderError
from app.main import app
from app.rag.pipeline import (
    NO_CONTEXT_ANSWER,
    RAGPipeline,
    RAGPipelineError,
    RAGResponse,
    SourceReference,
)
from app.retrieval.retriever import RetrievalError, VectorSearchError


@pytest.fixture
def client() -> TestClient:
    """Provides a TestClient with cleanly managed dependency overrides."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_pipeline() -> MagicMock:
    """Mock RAGPipeline instance."""
    pipeline = MagicMock(spec=RAGPipeline)
    pipeline.query.return_value = RAGResponse(
        answer="Employees are entitled to 20 days of paid vacation annually.",
        sources=[
            SourceReference(source="hr_policy.pdf", file_type="pdf", page=4),
            SourceReference(source="handbook.md", file_type="md", page=1),
        ],
        query="What is the annual leave policy?",
        model="google/gemini-2.5-flash",
        context_chunks_used=2,
    )
    return pipeline


# =====================================================================
# Chat Endpoint Tests
# =====================================================================


def test_1_and_2_valid_chat_returns_200_and_answer(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """1 & 2. Valid chat request returns HTTP 200 and contains generated answer."""
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    payload = {"question": "What is the annual leave policy?"}
    response = client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Employees are entitled to 20 days of paid vacation annually."
    assert data["model"] == "google/gemini-2.5-flash"
    assert data["context_chunks_used"] == 2


def test_3_response_contains_sources_and_page_numbers(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """3. Chat response preserves deduplicated source citations with page numbers."""
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    payload = {"question": "What is the annual leave policy?"}
    response = client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    sources = response.json()["sources"]
    assert len(sources) == 2
    assert sources[0]["source"] == "hr_policy.pdf"
    assert sources[0]["file_type"] == "pdf"
    assert sources[0]["page"] == 4
    assert sources[1]["source"] == "handbook.md"
    assert sources[1]["file_type"] == "md"
    assert sources[1]["page"] == 1


def test_4_route_delegates_exact_question_to_rag_pipeline(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """4. Route passes exact user question string directly to RAGPipeline.query()."""
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    question = "How do I setup corporate VPN?"
    client.post("/api/v1/chat", json={"question": question})

    mock_pipeline.query.assert_called_once_with(question)


def test_5_empty_question_returns_422(client: TestClient) -> None:
    """5. Empty string question triggers Pydantic validation failure (422)."""
    response = client.post("/api/v1/chat", json={"question": ""})
    assert response.status_code == 422


def test_6_whitespace_question_returns_422(client: TestClient) -> None:
    """6. Whitespace-only question triggers validation failure (422)."""
    response = client.post("/api/v1/chat", json={"question": "    \t\n  "})
    assert response.status_code == 422


def test_7_missing_question_returns_422(client: TestClient) -> None:
    """7. Missing question field in payload returns 422 Unprocessable Entity."""
    response = client.post("/api/v1/chat", json={})
    assert response.status_code == 422


def test_8_excessive_length_question_returns_422(client: TestClient) -> None:
    """8. Question exceeding 2000 characters triggers validation failure (422)."""
    long_question = "a" * 2001
    response = client.post("/api/v1/chat", json={"question": long_question})
    assert response.status_code == 422


def test_9_no_context_response_returns_200(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """9. Knowledge gap where no chunks are retrieved returns 200 with NO_CONTEXT_ANSWER."""
    mock_pipeline.query.return_value = RAGResponse(
        answer=NO_CONTEXT_ANSWER,
        sources=[],
        query="Unknown topic",
        model="",
        context_chunks_used=0,
    )
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    response = client.post("/api/v1/chat", json={"question": "Unknown topic"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == NO_CONTEXT_ANSWER
    assert data["sources"] == []
    assert data["context_chunks_used"] == 0


def test_10_llm_provider_failure_returns_502(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """10. RAGPipelineError wrapping LLMProviderError maps to 502 Bad Gateway."""
    provider_err = LLMProviderError("OpenRouter gateway timeout 504")
    rag_err = RAGPipelineError("Failed to generate answer: LLM error")
    rag_err.__cause__ = provider_err
    mock_pipeline.query.side_effect = rag_err

    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    response = client.post("/api/v1/chat", json={"question": "Will this fail?"})
    assert response.status_code == 502
    assert "LLM generation provider temporarily unavailable" in response.json()["detail"]


def test_11_retrieval_failure_returns_500(
    client: TestClient, mock_pipeline: MagicMock
) -> None:
    """11. RAGPipelineError wrapping RetrievalError maps to 500 Internal Server Error."""
    retrieval_err = VectorSearchError("ChromaDB connection refused")
    rag_err = RAGPipelineError("Failed to retrieve relevant documents")
    rag_err.__cause__ = retrieval_err
    mock_pipeline.query.side_effect = rag_err

    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    response = client.post("/api/v1/chat", json={"question": "Will this fail?"})
    assert response.status_code == 500
    assert "Document retrieval search failed" in response.json()["detail"]
