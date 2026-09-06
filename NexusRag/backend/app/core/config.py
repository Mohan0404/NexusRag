from functools import lru_cache
import logging
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class RAGConfig(BaseModel):
    """Configuration for RAG chunking and retrieval parameters.

    Stored in config.yaml (non-secret).
    """

    chunk_size: int = Field(
        default=500, gt=0, description="Size of text chunks in characters or tokens"
    )
    chunk_overlap: int = Field(
        default=50, ge=0, description="Overlap between consecutive chunks"
    )
    top_k: int = Field(
        default=4, gt=0, description="Number of top relevant chunks to retrieve"
    )

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "RAGConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly less than chunk_size ({self.chunk_size})"
            )
        return self


class CacheConfig(BaseModel):
    """Configuration for application caching layers.

    Stored in config.yaml (non-secret).
    """

    cache_ttl: int = Field(
        default=3600, ge=0, description="Cache Time-To-Live in seconds"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM generation parameters.

    Stored in config.yaml (non-secret).
    Secrets (API keys) belong in .env, never here.
    """

    provider: str = Field(
        default="openrouter",
        description="LLM provider (currently 'openrouter')",
    )
    model: str = Field(
        default="google/gemini-2.5-flash",
        description="Model identifier on the selected provider",
    )
    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature for LLM generation"
    )
    max_tokens: int = Field(
        default=4096, gt=0, description="Maximum tokens in the generated response"
    )
    timeout: int = Field(
        default=60, gt=0, description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry attempts for transient failures"
    )


class IngestionConfig(BaseModel):
    """Configuration for document ingestion parameters.

    Stored in config.yaml (non-secret).
    """

    max_file_size_mb: int = Field(
        default=10, gt=0, description="Maximum allowed document size in megabytes"
    )
    allowed_extensions: List[str] = Field(
        default_factory=lambda: [".pdf", ".txt", ".md"],
        description="Allowed document file extensions",
    )


class EmbeddingsConfig(BaseModel):
    """Configuration for embedding models and batching."""

    model: str = Field(
        default="gemini-embedding-2",
        description="Google Gemini embedding model name",
    )

    batch_size: int = Field(
        default=100,
        gt=0,
        le=500,
        description="Maximum number of texts embedded per batch request",
    )

    output_dimension: int = Field(
        default=768,
        gt=0,
        description="Output dimensionality of embedding vectors",
    )


class VectorDBConfig(BaseModel):
    """Configuration for vector database storage.

    Stored in config.yaml (non-secret).
    The persist_directory is an infrastructure path managed via .env / Settings.CHROMA_PATH.
    """

    provider: str = Field(
        default="chroma",
        description="Vector database provider (currently only 'chroma' is supported)",
    )
    collection_name: str = Field(
        default="nexusrag_documents",
        description="Name of the ChromaDB collection for document vectors",
    )


class Settings(BaseSettings):
    """Centralized application settings combining environment variables and YAML config.

    Architecture:
    - .env / Environment Variables: Host/port, debug flags, secrets (API keys), provider names.
    - config.yaml: Non-secret algorithm hyperparameters (chunk size, overlap, top_k, TTL, temperature).
    - Application code: Injects get_settings() without calling raw os.getenv().
    """

    # Application & Environment
    PROJECT_NAME: str = "NexusRAG"
    APP_NAME: Optional[str] = None
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://10.13.252.112:5173"
    ]

    # LLM Provider & Model Selection (Non-secret environment variables)
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "google/gemini-2.5-flash"

    # Secrets (Managed strictly as SecretStr to prevent accidental logging/exposure)
    GEMINI_API_KEY: Optional[SecretStr] = None
    OPENROUTER_API_KEY: Optional[SecretStr] = None

    # Infrastructure Storage & Cache Locations
    CHROMA_PATH: str = "./data/chroma"
    CHROMA_PERSIST_DIRECTORY: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # Path to YAML configuration file
    CONFIG_YAML_PATH: str = "config.yaml"

    # Non-secret application configuration components
    rag: RAGConfig = Field(default_factory=RAGConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)

    # Convenience properties for direct access
    @property
    def chunk_size(self) -> int:
        return self.rag.chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self.rag.chunk_overlap

    @property
    def top_k(self) -> int:
        return self.rag.top_k

    @property
    def cache_ttl(self) -> int:
        return self.cache.cache_ttl

    @property
    def llm_temperature(self) -> float:
        return self.llm.temperature

    @property
    def llm_model(self) -> str:
        return self.llm.model

    @property
    def llm_provider(self) -> str:
        return self.llm.provider

    @property
    def llm_max_tokens(self) -> int:
        return self.llm.max_tokens

    @property
    def llm_timeout(self) -> int:
        return self.llm.timeout

    @property
    def llm_max_retries(self) -> int:
        return self.llm.max_retries

    @property
    def max_file_size_bytes(self) -> int:
        return self.ingestion.max_file_size_mb * 1024 * 1024

    @property
    def allowed_extensions(self) -> List[str]:
        return self.ingestion.allowed_extensions

    @property
    def embedding_model(self) -> str:
        return self.embeddings.model

    @property
    def embedding_batch_size(self) -> int:
        return self.embeddings.batch_size

    @property
    def embedding_output_dimension(self) -> int:
        return self.embeddings.output_dimension

    @property
    def vectordb_provider(self) -> str:
        return self.vectordb.provider

    @property
    def vectordb_collection_name(self) -> str:
        return self.vectordb.collection_name

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def model_post_init(self, __context) -> None:
        """Post-initialization lifecycle hook to normalize aliases and load YAML config."""
        # Synchronize APP_NAME and PROJECT_NAME aliases
        if self.APP_NAME and not self.PROJECT_NAME:
            self.PROJECT_NAME = self.APP_NAME
        elif self.PROJECT_NAME and not self.APP_NAME:
            self.APP_NAME = self.PROJECT_NAME

        # Synchronize CHROMA_PATH and CHROMA_PERSIST_DIRECTORY aliases
        if self.CHROMA_PERSIST_DIRECTORY and not self.CHROMA_PATH:
            self.CHROMA_PATH = self.CHROMA_PERSIST_DIRECTORY
        elif self.CHROMA_PATH and not self.CHROMA_PERSIST_DIRECTORY:
            self.CHROMA_PERSIST_DIRECTORY = self.CHROMA_PATH

        self._load_yaml_config()

    def _resolve_yaml_path(self) -> Optional[Path]:
        """Resolves the config.yaml path across various execution directories."""
        candidates = [
            Path(self.CONFIG_YAML_PATH),
            Path(__file__).resolve().parent.parent.parent / self.CONFIG_YAML_PATH,
            Path.cwd() / self.CONFIG_YAML_PATH,
            Path.cwd() / "backend" / self.CONFIG_YAML_PATH,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def _load_yaml_config(self) -> None:
        """Loads and validates non-secret configuration parameters from config.yaml."""
        yaml_path = self._resolve_yaml_path()
        if not yaml_path:
            return

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return

            # Security Guard: Prevent secrets from being defined in config.yaml
            prohibited_secret_keywords = (
                "api_key",
                "secret",
                "password",
                "token",
                "gemini_api_key",
                "openrouter_api_key",
            )
            for key in data.keys():
                if any(keyword in key.lower() for keyword in prohibited_secret_keywords):
                    raise ValueError(
                        f"Security Violation: Secret '{key}' found in {yaml_path}. "
                        "Secrets must be stored in .env, never in config.yaml."
                    )

            # Parse and merge submodels
            if "rag" in data and isinstance(data["rag"], dict):
                self.rag = RAGConfig(**data["rag"])
            elif any(k in data for k in ("chunk_size", "chunk_overlap", "top_k")):
                self.rag = RAGConfig(
                    chunk_size=data.get("chunk_size", self.rag.chunk_size),
                    chunk_overlap=data.get("chunk_overlap", self.rag.chunk_overlap),
                    top_k=data.get("top_k", self.rag.top_k),
                )

            if "cache" in data and isinstance(data["cache"], dict):
                self.cache = CacheConfig(**data["cache"])
            elif "cache_ttl" in data:
                self.cache = CacheConfig(cache_ttl=data["cache_ttl"])

            if "llm" in data and isinstance(data["llm"], dict):
                self.llm = LLMConfig(**data["llm"])
            elif "temperature" in data or "llm_temperature" in data:
                temp = data.get("temperature", data.get("llm_temperature"))
                self.llm = LLMConfig(temperature=temp)

            if "ingestion" in data and isinstance(data["ingestion"], dict):
                self.ingestion = IngestionConfig(**data["ingestion"])

            if "embeddings" in data and isinstance(data["embeddings"], dict):
                self.embeddings = EmbeddingsConfig(**data["embeddings"])

            if "vectordb" in data and isinstance(data["vectordb"], dict):
                self.vectordb = VectorDBConfig(**data["vectordb"])

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to load or parse configuration from {yaml_path}: {e}") from e


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton instance to avoid repeated filesystem or environment lookups."""
    return Settings()
