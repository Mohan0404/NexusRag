"""Chat API endpoint router for NexusRAG (Phase 11).

Exposes POST /api/v1/chat for user question answering via the RAG pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_rag_pipeline
from app.core.logging import get_logger
from app.llm.llm_service import LLMProviderError
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.rag.pipeline import RAGPipeline, RAGPipelineError
from app.retrieval.retriever import RetrievalError

logger = get_logger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Knowledge Base via RAG",
    description="Accepts a user question, retrieves grounded context, and generates an answer with source citations.",
    responses={
        200: {"description": "Successful answer generated or controlled no-context message."},
        422: {"description": "Validation error: question is empty, whitespace-only, or invalid length."},
        502: {"description": "Upstream LLM provider temporarily unavailable."},
        500: {"description": "Internal RAG pipeline or retrieval failure."},
    },
)
def chat(
    request: ChatRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> ChatResponse:
    """Answers a user question using the injected RAG pipeline.

    Synchronous def is intentionally used so FastAPI delegates execution
    to a background worker threadpool, preventing blocking of the main event loop.
    """
    logger.info("Received chat question (len=%d)", len(request.question))

    try:
        rag_response = pipeline.query(request.question)
        return ChatResponse.from_rag_response(rag_response)

    except RAGPipelineError as exc:
        cause = exc.__cause__
        logger.error("RAGPipeline failed for question: %s", exc, exc_info=True)

        if isinstance(cause, LLMProviderError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM generation provider temporarily unavailable. Please retry shortly.",
            ) from exc

        if isinstance(cause, RetrievalError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document retrieval search failed.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question via RAG pipeline.",
        ) from exc

    except Exception as exc:
        logger.error("Unexpected error in chat endpoint: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question.",
        ) from exc
