from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union
from langchain_core.documents import Document

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# =====================================================================
# Data Structures
# =====================================================================


@dataclass
class EmbeddedChunk:
    """Encapsulates a document chunk paired with its dense vector embedding and metadata."""

    content: str
    embedding: List[float]
    metadata: Dict[str, Any]

    def to_document(self) -> Document:
        """Converts back to a LangChain Document with metadata preserved."""
        return Document(page_content=self.content, metadata=dict(self.metadata))


# =====================================================================
# Embedding Exceptions
# =====================================================================


class EmbeddingError(Exception):
    """Base exception for all embedding failures."""

    pass


class MissingAPIKeyError(EmbeddingError, ValueError):
    """Raised when Gemini API key is missing or empty."""

    pass


class EmbeddingConfigurationError(EmbeddingError, ValueError):
    """Raised when embedding configuration parameters are invalid."""

    pass


class EmbeddingProviderError(EmbeddingError):
    """Raised when external Gemini API call fails (rate limit, network, 5xx)."""

    pass


class EmptyEmbeddingInputError(EmbeddingError, ValueError):
    """Raised when attempting to embed empty or whitespace-only input."""

    pass


# =====================================================================
# Embedding Service Abstraction
# =====================================================================


class BaseEmbeddingService(ABC):
    """Abstract base class defining the embedding service interface."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates an embedding vector for a single document text string."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a search query string."""
        pass

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Batch-generates embedding vectors for multiple text strings."""
        pass

    @abstractmethod
    def embed_documents(self, documents: Sequence[Document]) -> List[EmbeddedChunk]:
        """Embeds a sequence of LangChain Documents, retaining all metadata."""
        pass


# =====================================================================
# Google Gemini Embedding 2 Service Implementation
# =====================================================================


class GeminiEmbeddingService(BaseEmbeddingService):
    """Production implementation of BaseEmbeddingService targeting the modern Google GenAI SDK (Gemini Embedding 2).

    Supports:
    - Dynamic model selection (default: gemini-embedding-2)
    - Matryoshka Representation Learning (MRL) via output_dimensionality (e.g. 768)
    - Asymmetric task types (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY)
    - Batching with rate-limit and error containment
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        batch_size: Optional[int] = None,
        output_dimension: Optional[int] = None,
    ) -> None:
        """Initializes the GeminiEmbeddingService with configuration or explicit overrides.

        Args:
            settings: Centralized application settings. Defaults to get_settings().
            api_key: Optional explicit API key string. If omitted, read from settings.
            model: Optional model name override. Defaults to settings.embedding_model.
            batch_size: Optional batch size override. Defaults to settings.embedding_batch_size.
            output_dimension: Optional MRL output dimensionality (e.g. 768). Defaults to settings.embedding_output_dimension.
        """
        self.settings = settings or get_settings()

        self._api_key = api_key
        self.model = model or self.settings.embedding_model
        self.batch_size = (
            batch_size if batch_size is not None else self.settings.embedding_batch_size
        )
        self.output_dimension = (
            output_dimension
            if output_dimension is not None
            else self.settings.embedding_output_dimension
        )

        if self.batch_size <= 0:
            raise EmbeddingConfigurationError(
                f"batch_size must be greater than 0, got {self.batch_size}."
            )
        if self.output_dimension <= 0:
            raise EmbeddingConfigurationError(
                f"output_dimension must be greater than 0, got {self.output_dimension}."
            )

        self._client = None

        logger.info(
            "GeminiEmbeddingService initialized with model='%s', batch_size=%d, output_dimension=%d",
            self.model,
            self.batch_size,
            self.output_dimension,
        )

    def _ensure_client(self):
        """Initializes the modern google.genai.Client instance on demand."""
        if self._client is not None:
            return self._client

        resolved_key: Optional[str] = None
        if self._api_key:
            resolved_key = self._api_key
        elif self.settings.GEMINI_API_KEY:
            resolved_key = self.settings.GEMINI_API_KEY.get_secret_value()

        if not resolved_key or not resolved_key.strip():
            logger.error("Gemini API key is missing. Cannot generate embeddings.")
            raise MissingAPIKeyError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env "
                "or pass it directly to the service."
            )

        try:
            from google import genai

            self._client = genai.Client(api_key=resolved_key)
            return self._client
        except Exception as e:
            logger.error("Failed to initialize google.genai Client: %s", e)
            raise EmbeddingConfigurationError(
                f"Failed to initialize google.genai Client: {e}"
            ) from e

    def _call_api(
        self, contents: Union[str, List[str]], task_type: str
    ) -> List[List[float]]:
        """Dispatches an embedding request using client.models.embed_content and returns vector lists."""
        client = self._ensure_client()
        from google.genai import types

        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self.output_dimension,
        )

        try:
            response = client.models.embed_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error("Gemini embedding API call failed: %s", error_msg)
            code = getattr(e, "code", None)
            if (
                code == 429
                or "quota" in error_msg.lower()
                or "429" in error_msg
                or "resourceexhausted" in error_msg.lower()
                or "rate limit" in error_msg.lower()
            ):
                raise EmbeddingProviderError(
                    f"Gemini API rate limit / quota exceeded: {error_msg}"
                ) from e
            raise EmbeddingProviderError(
                f"Gemini API embedding request failed: {error_msg}"
            ) from e

        if not response or getattr(response, "embeddings", None) is None:
            logger.error("Received empty or malformed response from Gemini embedding API.")
            raise EmbeddingProviderError(
                "Malformed response from Gemini embedding API: 'embeddings' field missing."
            )

        vectors: List[List[float]] = []
        for emb in response.embeddings:
            if hasattr(emb, "values") and emb.values is not None:
                vectors.append(list(emb.values))
            elif isinstance(emb, dict) and "values" in emb:
                vectors.append(list(emb["values"]))
            elif isinstance(emb, (list, tuple)):
                vectors.append(list(emb))
            else:
                raise EmbeddingProviderError(
                    "Unexpected embedding format received from Gemini embedding API."
                )

        return vectors

    def embed_text(self, text: str) -> List[float]:
        """Generates an embedding vector for a single document text string.

        Uses task_type='RETRIEVAL_DOCUMENT' for document chunks.
        """
        if not text or not text.strip():
            raise EmptyEmbeddingInputError("Cannot embed empty or whitespace-only text.")

        vectors = self._call_api(contents=text, task_type="RETRIEVAL_DOCUMENT")
        if not vectors:
            raise EmbeddingProviderError("No embedding returned for the input text.")
        return vectors[0]

    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a search query string.

        Uses task_type='RETRIEVAL_QUERY' to optimize vector projection for query-document similarity.
        """
        if not query or not query.strip():
            raise EmptyEmbeddingInputError("Cannot embed empty or whitespace-only query.")

        vectors = self._call_api(contents=query, task_type="RETRIEVAL_QUERY")
        if not vectors:
            raise EmbeddingProviderError("No embedding returned for the input query.")
        return vectors[0]

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Batch-generates embedding vectors for multiple text strings."""
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total_texts = len(texts)

        logger.info(
            "Batch-embedding %d texts using model='%s', dimension=%d, batch_size=%d",
            total_texts,
            self.model,
            self.output_dimension,
            self.batch_size,
        )

        for i in range(0, total_texts, self.batch_size):
            batch = list(texts[i : i + self.batch_size])
            # Replace empty entries in batch with whitespace placeholder to avoid API failure
            clean_batch = [t if t and t.strip() else " " for t in batch]

            vectors = self._call_api(
                contents=clean_batch, task_type="RETRIEVAL_DOCUMENT"
            )
            all_embeddings.extend(vectors)

        logger.info("Batch embedding completed: %d vectors generated", len(all_embeddings))
        return all_embeddings

    def embed_documents(self, documents: Sequence[Document]) -> List[EmbeddedChunk]:
        """Embeds a sequence of LangChain Documents produced by Phase 4.

        Preserves 100% of original chunk metadata (source, page, chunk_index, etc.)
        and returns structured EmbeddedChunk objects.
        """
        if not documents:
            logger.debug("embed_documents called with empty document collection.")
            return []

        logger.info("Embedding %d document chunks", len(documents))

        texts = [doc.page_content for doc in documents]
        embeddings = self.embed_texts(texts)

        embedded_chunks: List[EmbeddedChunk] = []
        for doc, vector in zip(documents, embeddings):
            embedded_chunks.append(
                EmbeddedChunk(
                    content=doc.page_content,
                    embedding=vector,
                    metadata=dict(doc.metadata),
                )
            )

        logger.info(
            "Successfully embedded %d document chunks with complete metadata association",
            len(embedded_chunks),
        )
        return embedded_chunks
