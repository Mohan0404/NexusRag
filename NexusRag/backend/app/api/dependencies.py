"""FastAPI dependency injection providers for NexusRAG (Phase 11).

Provides shared, reusable service instances for route handlers while
enabling effortless dependency overrides in automated tests.
"""

from functools import lru_cache
from typing import Optional

from fastapi import Depends

from app.cache.redis_cache import BaseQueryCache, RedisQueryCache
from app.chunking.chunker import DocumentChunker
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import BaseEmbeddingService, GeminiEmbeddingService
from app.ingestion.document_service import DocumentService
from app.ingestion.pipeline import IngestionPipeline
from app.llm.llm_service import BaseLLMService
from app.llm.openrouter import OpenRouterLLMService
from app.rag.pipeline import RAGPipeline
from app.retrieval.retriever import Retriever
from app.vectordb.chroma_store import ChromaStore

logger = get_logger(__name__)


# =====================================================================
# Shared Infrastructure Services (Singletons via @lru_cache)
# =====================================================================


@lru_cache
def get_embedding_service() -> BaseEmbeddingService:
    """Returns the shared Gemini embedding service instance."""
    settings = get_settings()
    return GeminiEmbeddingService(settings=settings)


@lru_cache
def get_chroma_store() -> ChromaStore:
    """Returns the shared ChromaDB vector store instance."""
    settings = get_settings()
    return ChromaStore(settings=settings)


@lru_cache
def get_llm_service() -> BaseLLMService:
    """Returns the shared OpenRouter LLM service instance."""
    settings = get_settings()
    return OpenRouterLLMService(settings=settings)


@lru_cache
def get_query_cache() -> Optional[BaseQueryCache]:
    """Returns the shared Redis query cache instance.

    Operates fail-open: returns None if Redis initialization fails.
    """
    try:
        return RedisQueryCache()
    except Exception as exc:
        logger.warning(
            "RedisQueryCache initialization failed (operating in fail-open mode): %s",
            exc,
        )
        return None


@lru_cache
def get_document_service() -> DocumentService:
    """Returns the shared DocumentService instance."""
    settings = get_settings()
    return DocumentService(settings=settings)


@lru_cache
def get_document_chunker() -> DocumentChunker:
    """Returns the shared DocumentChunker instance."""
    settings = get_settings()
    return DocumentChunker(settings=settings)


# =====================================================================
# Application Orchestrator Providers (Request-Scoped / Composed)
# =====================================================================


def get_retriever(
    embeddings: BaseEmbeddingService = Depends(get_embedding_service),
    chroma_store: ChromaStore = Depends(get_chroma_store),
    settings: Settings = Depends(get_settings),
) -> Retriever:
    """Provides a configured Retriever instance."""
    return Retriever(
        embedding_service=embeddings,
        chroma_store=chroma_store,
        settings=settings,
    )


def get_rag_pipeline(
    retriever: Retriever = Depends(get_retriever),
    llm_service: BaseLLMService = Depends(get_llm_service),
    cache: Optional[BaseQueryCache] = Depends(get_query_cache),
) -> RAGPipeline:
    """Provides a configured RAGPipeline orchestrator."""
    return RAGPipeline(
        retriever=retriever,
        llm_service=llm_service,
        cache=cache,
    )


def get_ingestion_pipeline(
    document_service: DocumentService = Depends(get_document_service),
    chunker: DocumentChunker = Depends(get_document_chunker),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    chroma_store: ChromaStore = Depends(get_chroma_store),
    cache: Optional[BaseQueryCache] = Depends(get_query_cache),
    settings: Settings = Depends(get_settings),
) -> IngestionPipeline:
    """Provides a configured IngestionPipeline orchestrator."""
    return IngestionPipeline(
        document_service=document_service,
        chunker=chunker,
        embedding_service=embedding_service,
        chroma_store=chroma_store,
        cache=cache,
        settings=settings,
    )
