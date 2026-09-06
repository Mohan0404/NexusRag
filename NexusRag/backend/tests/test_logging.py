import io
import logging
import pytest

from app.core.logging import SensitiveDataFilter, get_logger, setup_logging


def test_sensitive_data_filter_redaction() -> None:
    """Verify SensitiveDataFilter redacts various sensitive token formats."""
    redact = SensitiveDataFilter.redact

    # Google Gemini API key
    gemini_key = "AIzaSyD4e8F123456789012345678901234"
    assert "AIzaSy" not in redact(f"Failed with key {gemini_key}")
    assert "[REDACTED]" in redact(f"Failed with key {gemini_key}")

    # OpenRouter API key
    openrouter_key = "sk-or-v1-1234567890abcdef1234567890"
    assert "sk-or" not in redact(f"Using OpenRouter {openrouter_key}")
    assert "[REDACTED]" in redact(f"Using OpenRouter {openrouter_key}")

    # Bearer Token
    bearer = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    assert "eyJhbGci" not in redact(f"Auth header: {bearer}")
    assert "Bearer [REDACTED]" in redact(f"Auth header: {bearer}")

    # Key=Value pairs
    kv = "User login with password=SuperSecretPassword123"
    assert "SuperSecretPassword123" not in redact(kv)
    assert "password=[REDACTED]" in redact(kv)


def test_sensitive_data_filter_preserves_normal_messages() -> None:
    """Ensure standard operational logs are preserved without modification."""
    normal_msg = "Successfully ingested document report.pdf with 42 chunks."
    assert SensitiveDataFilter.redact(normal_msg) == normal_msg


def test_logging_level_configuration() -> None:
    """Verify logging setup properly configures log levels."""
    logger = setup_logging(log_level="DEBUG")
    assert logger.level == logging.DEBUG

    logger = setup_logging(log_level="WARNING")
    assert logger.level == logging.WARNING


def test_logger_redaction_stream() -> None:
    """Verify that records passing through a StreamHandler have secrets redacted."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(logging.Formatter("%(message)s"))

    test_logger = logging.getLogger("test_redaction_stream")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    secret_key = "AIzaSyTestApiKeyForLogging012345678"
    test_logger.info("Attempting connection with key: %s", secret_key)

    output = stream.getvalue()
    assert secret_key not in output
    assert "[REDACTED]" in output
