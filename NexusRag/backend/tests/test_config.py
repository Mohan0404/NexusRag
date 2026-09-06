import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError
import yaml

from app.core.config import RAGConfig, CacheConfig, LLMConfig, Settings, get_settings


def test_default_settings_instantiation() -> None:
    """Verify that Settings loads with appropriate defaults without external services."""
    settings = get_settings()
    assert settings.PROJECT_NAME in ("NexusRAG", "GenWorx RAG")
    assert settings.API_V1_STR == "/api/v1"
    assert settings.LLM_PROVIDER in ("gemini", "openrouter")
    assert settings.LLM_MODEL is not None
    assert settings.CHROMA_PATH == "./data/chroma"
    assert settings.REDIS_URL.startswith("redis://")


def test_yaml_config_parameters() -> None:
    """Verify that non-secret hyperparameters are loaded and accessible."""
    settings = get_settings()
    assert settings.chunk_size == 800
    assert settings.chunk_overlap == 100
    assert settings.top_k == 4
    assert settings.cache_ttl == 3600
    assert settings.llm_temperature == 0.2


def test_invalid_rag_overlap_validation() -> None:
    """Verify validation error when chunk_overlap is greater than or equal to chunk_size."""
    with pytest.raises(ValidationError):
        RAGConfig(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValidationError):
        RAGConfig(chunk_size=100, chunk_overlap=150)


def test_invalid_llm_temperature_validation() -> None:
    """Verify validation error when LLM temperature is outside the valid [0.0, 2.0] range."""
    with pytest.raises(ValidationError):
        LLMConfig(temperature=-0.5)

    with pytest.raises(ValidationError):
        LLMConfig(temperature=2.5)


def test_prohibited_secrets_in_yaml() -> None:
    """Ensure that storing API keys or secrets in config.yaml raises a security error."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        yaml.dump({"rag": {"chunk_size": 200}, "gemini_api_key": "leaked_secret"}, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Security Violation"):
            Settings(CONFIG_YAML_PATH=tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_secret_masking() -> None:
    """Verify that API keys wrapped in SecretStr are masked in string representations."""
    settings = Settings(GEMINI_API_KEY="AIzaSyTestSecretKey1234567890123")
    assert settings.GEMINI_API_KEY is not None
    # Plain str or repr must mask the secret value
    assert "AIzaSyTestSecretKey" not in str(settings.GEMINI_API_KEY)
    assert "AIzaSyTestSecretKey" not in repr(settings.GEMINI_API_KEY)
    # The true value is only accessible via explicit accessor
    assert (
        settings.GEMINI_API_KEY.get_secret_value()
        == "AIzaSyTestSecretKey1234567890123"
    )
