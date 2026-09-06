"""RAG Pipeline — Phase 9 orchestrator.

Responsibility: Wire together the Retriever (Phase 7), prompt
construction (app/prompts/), and LLM generation (Phase 8) into
a single query interface.

This module does NOT:
- Perform retrieval logic (Phase 7 Retriever).
- Construct prompts (app/prompts/templates.py).
- Call provider APIs directly (Phase 8 LLM service).
- Cache results (Phase 10).
- Expose HTTP endpoints (Phase 11).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.cache.redis_cache import BaseQueryCache
from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.llm_service import BaseLLMService, LLMError, LLMResponse
from app.prompts.templates import build_rag_prompt
from app.retrieval.retriever import RetrievalError, RetrievedChunk, Retriever

logger = get_logger(__name__)


# =====================================================================
# RAG Response Data Structures
# =====================================================================

NO_CONTEXT_ANSWER = (
    "I could not find any relevant information in the knowledge base "
    "to answer your question. Please try rephrasing your question or "
    "ensure that the relevant documents have been ingested."
)


@dataclass
class SourceReference:
    """A single source citation extracted from a retrieved chunk.

    Preserves page-level granularity so that citations like
    "report.pdf, Page 3" are not collapsed into just "report.pdf".

    Deduplication is performed at the (source, page) level —
    multiple chunks from the same page produce one SourceReference.

    Attributes:
        source: Source document filename (e.g. "report.pdf").
        file_type: Document type (e.g. "pdf", "txt", "md").
        page: 1-indexed page number from the original document.
    """

    source: str
    file_type: str = ""
    page: int = 1


@dataclass
class RAGResponse:
    """Complete RAG pipeline result returned to the caller.

    Attributes:
        answer: The generated answer text from the LLM, or a controlled
            "no relevant info" message when no context was retrieved.
        sources: Deduplicated list of SourceReference objects preserving
            page-level citation information. Empty when no context found.
        query: The user's original question, preserved unchanged.
        model: The LLM model that generated the answer (empty string
            when the LLM was not called).
        context_chunks_used: Number of retrieved chunks that were included
            in the prompt context.
    """

    answer: str
    sources: List[SourceReference] = field(default_factory=list)
    query: str = ""
    model: str = ""
    context_chunks_used: int = 0


# =====================================================================
# RAG Pipeline Exception
# =====================================================================


class RAGPipelineError(Exception):
    """Raised when the RAG pipeline fails at the orchestration level.

    Wraps underlying RetrievalError or LLMError to provide a single
    exception boundary for callers (e.g. FastAPI endpoints in Phase 11).

    The original cause is always preserved via exception chaining.
    """

    pass


# =====================================================================
# RAG Pipeline
# =====================================================================


class RAGPipeline:
    """Orchestrates the Retrieval-Augmented Generation pipeline.

    Pipeline:
        User Question
            ↓
        Retriever.retrieve(question)         → List[RetrievedChunk]
            ↓
        (if empty → return "no info" RAGResponse, skip LLM)
            ↓
        build_rag_prompt(question, chunks)   → prompt string
            ↓
        BaseLLMService.generate(prompt)      → LLMResponse
            ↓
        RAGResponse(answer, sources, query, model)

    Responsibilities:
    - Passes the user's original question unchanged to Retriever.
    - Delegates prompt construction to app.prompts.templates.
    - Delegates LLM generation to the injected BaseLLMService.
    - Extracts source citations from retrieved chunk metadata.
    - Returns a controlled result when no relevant context is found.

    Does NOT:
    - Rewrite or transform the user's question.
    - Implement raw Redis networking or serialization (delegated to app.cache.redis_cache).
    - Implement streaming.
    - Implement conversation memory.
    - Implement reranking, BM25, or hybrid retrieval.
    """

    def __init__(
        self,
        retriever: Retriever,
        llm_service: BaseLLMService,
        cache: Optional[BaseQueryCache] = None,
    ) -> None:
        """Initializes the RAG pipeline with required dependencies and optional cache.

        Args:
            retriever: Phase 7 Retriever instance (handles embedding + ChromaDB search).
            llm_service: Phase 8 LLM service instance (handles text generation).
            cache: Optional Phase 10 BaseQueryCache instance (e.g. RedisQueryCache).
                If None, caching is bypassed and Phase 9 behavior is preserved.
        """
        self._retriever = retriever
        self._llm_service = llm_service
        self._cache = cache

        logger.info(
            "RAGPipeline initialized (caching=%s).",
            "enabled" if self._cache is not None else "disabled",
        )

    @property
    def cache(self) -> Optional[BaseQueryCache]:
        """Returns the configured query cache service, if any."""
        return self._cache

    def query(self, question: str) -> RAGResponse:
        """Executes the full RAG pipeline for a user question.

        Steps:
        1. Validate the question.
        1.5. Check Redis query cache (Phase 10). If HIT, return immediately.
        2. Retrieve relevant chunks via the Retriever.
        3. If no chunks found → return controlled "no info" response (LLM NOT called, NOT cached).
        4. Construct a grounded prompt via app.prompts.templates.
        5. Generate an answer via the LLM service.
        6. Assemble the RAGResponse with answer + source citations.
        7. Cache successful RAGResponse in Redis (Phase 10).

        Args:
            question: The user's original question string, passed unchanged
                through the entire pipeline.

        Returns:
            RAGResponse containing the answer, source citations, original query,
            model name, and context chunk count.

        Raises:
            RAGPipelineError: If retrieval or LLM generation fails.
        """
        # Step 1: Validate question
        if not question or not question.strip():
            raise RAGPipelineError("Question must not be empty or whitespace-only.")

        logger.info("RAG pipeline started: question_length=%d", len(question))

        # Step 1.5: Cache Lookup (Phase 10)
        cache_key: Optional[str] = None
        if self._cache is not None:
            model_name = self._resolve_model_name()
            top_k = self._resolve_top_k()
            cache_key = self._cache.build_key(query=question, model=model_name, top_k=top_k)
            cached_response = self._cache.get(cache_key)
            if cached_response is not None:
                logger.info("Serving response directly from cache for key=%s", cache_key)
                return cached_response

        # Step 2: Retrieve relevant chunks
        chunks = self._retrieve(question)

        # Step 3: Handle empty retrieval — do NOT call LLM and do NOT cache (Constraint 8)
        if not chunks:
            logger.info("No relevant chunks retrieved. Returning controlled response (not cached).")
            return RAGResponse(
                answer=NO_CONTEXT_ANSWER,
                sources=[],
                query=question,
                model="",
                context_chunks_used=0,
            )

        # Step 4: Construct prompt (delegated to app.prompts.templates)
        chunk_dicts = self._chunks_to_dicts(chunks)
        prompt = build_rag_prompt(question, chunk_dicts)

        # Step 5: Generate answer via LLM
        llm_response = self._generate(prompt)

        # Step 6: Assemble response
        sources = self._extract_sources(chunks)

        logger.info(
            "RAG pipeline completed: sources=%d, answer_length=%d, model='%s'",
            len(sources),
            len(llm_response.content),
            llm_response.model,
        )

        response = RAGResponse(
            answer=llm_response.content,
            sources=sources,
            query=question,
            model=llm_response.model,
            context_chunks_used=len(chunks),
        )

        # Step 7: Cache Write (Phase 10) — only for successful RAGResponse
        if self._cache is not None and cache_key is not None:
            self._cache.set(cache_key, response)

        return response

    # =================================================================
    # Internal Pipeline Steps
    # =================================================================

    def _retrieve(self, question: str) -> List[RetrievedChunk]:
        """Delegates retrieval to the Phase 7 Retriever.

        Args:
            question: The user's original question, passed unchanged.

        Returns:
            List of RetrievedChunk objects (may be empty).

        Raises:
            RAGPipelineError: If retrieval fails.
        """
        try:
            return self._retriever.retrieve(question)
        except RetrievalError as e:
            logger.error("Retrieval failed during RAG pipeline: %s", e)
            raise RAGPipelineError(
                f"Failed to retrieve relevant documents: {e}"
            ) from e

    def _generate(self, prompt: str) -> LLMResponse:
        """Delegates LLM generation to the Phase 8 LLM service.

        Args:
            prompt: The complete prompt constructed by app.prompts.templates.

        Returns:
            LLMResponse from the LLM service.

        Raises:
            RAGPipelineError: If LLM generation fails.
        """
        try:
            return self._llm_service.generate(prompt)
        except LLMError as e:
            logger.error("LLM generation failed during RAG pipeline: %s", e)
            raise RAGPipelineError(
                f"Failed to generate answer: {e}"
            ) from e

    @staticmethod
    def _chunks_to_dicts(chunks: List[RetrievedChunk]) -> List[Dict[str, Any]]:
        """Converts RetrievedChunk objects to plain dictionaries for prompt construction.

        The prompt module (app.prompts.templates) accepts dictionaries rather
        than RetrievedChunk dataclasses to avoid coupling between modules.

        Args:
            chunks: List of RetrievedChunk objects from the Retriever.

        Returns:
            List of dictionaries with 'content' and 'metadata' keys.
        """
        return [
            {"content": chunk.content, "metadata": chunk.metadata}
            for chunk in chunks
        ]

    @staticmethod
    def _extract_sources(chunks: List[RetrievedChunk]) -> List[SourceReference]:
        """Extracts deduplicated source citations from retrieved chunks.

        Deduplication is at the (source, page) level — multiple chunks
        from the same document page produce one SourceReference, but
        chunks from different pages of the same document produce
        separate SourceReference entries.

        Args:
            chunks: List of RetrievedChunk objects.

        Returns:
            Ordered list of unique SourceReference objects.
        """
        seen: set = set()
        sources: List[SourceReference] = []

        for chunk in chunks:
            metadata = chunk.metadata
            source = metadata.get("source", "unknown")
            page = metadata.get("page", 1)
            file_type = metadata.get("file_type", "")

            key = (source, page)
            if key not in seen:
                seen.add(key)
                sources.append(
                    SourceReference(
                        source=source,
                        file_type=file_type,
                        page=page,
                    )
                )

        return sources

    def _resolve_model_name(self) -> str:
        """Resolves the active model identifier for cache key generation.

        Inspects the LLM service instance, then configuration settings.
        """
        if hasattr(self._llm_service, "model") and self._llm_service.model:
            return str(self._llm_service.model)
        if hasattr(self._llm_service, "_settings") and hasattr(
            self._llm_service._settings, "llm_model"
        ):
            return str(self._llm_service._settings.llm_model)
        try:
            return get_settings().llm_model
        except Exception:
            return "unknown_model"

    def _resolve_top_k(self) -> int:
        """Resolves the retrieval top_k setting for cache key generation.

        Inspects the Retriever instance, then configuration settings.
        """
        if hasattr(self._retriever, "top_k") and self._retriever.top_k:
            return int(self._retriever.top_k)
        if hasattr(self._retriever, "_settings") and hasattr(
            self._retriever._settings, "top_k"
        ):
            return int(self._retriever._settings.top_k)
        try:
            return get_settings().top_k
        except Exception:
            return 4
