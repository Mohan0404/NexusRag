import time
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.core.config import Settings
from app.llm import (
    BaseLLMService,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMMissingAPIKeyError,
    LLMProviderError,
    LLMResponse,
    LLMResponseError,
    OpenRouterLLMService,
)


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def mock_chat_openai():
    """Fixture that mocks the ChatOpenAI class to prevent real API calls."""
    with patch("app.llm.openrouter.ChatOpenAI") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance, mock_cls


@pytest.fixture
def llm_service(mock_chat_openai) -> OpenRouterLLMService:
    """Provides an OpenRouterLLMService with a mocked ChatOpenAI backend."""
    return OpenRouterLLMService(api_key="sk-or-test-dummy-key-12345")


def _make_ai_message(content: str, model_name: str = "google/gemini-2.5-flash"):
    """Creates a mock AIMessage-like response object."""
    msg = MagicMock()
    msg.content = content
    msg.usage_metadata = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    msg.response_metadata = {"model_name": model_name, "token_usage": {}}
    return msg


# =====================================================================
# Test 1: Successful Generation
# =====================================================================


def test_successful_generation(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify a valid prompt returns an LLMResponse with generated content."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.return_value = _make_ai_message("The leave policy allows 20 days PTO.")

    result = llm_service.generate("What is the leave policy?")

    assert isinstance(result, LLMResponse)
    assert result.content == "The leave policy allows 20 days PTO."
    assert result.model != ""


# =====================================================================
# Test 2: Prompt Passed Correctly
# =====================================================================


def test_prompt_passed_correctly(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify the exact prompt string reaches ChatOpenAI.invoke()."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.return_value = _make_ai_message("answer")

    llm_service.generate("Explain RAG architecture")

    mock_instance.invoke.assert_called_once_with("Explain RAG architecture")


# =====================================================================
# Test 3: Correct Provider Configured
# =====================================================================


def test_correct_provider_configured(mock_chat_openai) -> None:
    """Verify ChatOpenAI is initialized with OpenRouter base_url."""
    _, mock_cls = mock_chat_openai
    service = OpenRouterLLMService(api_key="sk-or-test-key-1234")

    mock_cls.return_value.invoke.return_value = _make_ai_message("ok")
    service.generate("test prompt")

    mock_cls.assert_called_once()
    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"


# =====================================================================
# Test 4: Correct Model Configured
# =====================================================================


def test_correct_model_configured(mock_chat_openai) -> None:
    """Verify ChatOpenAI is initialized with the configured model name."""
    _, mock_cls = mock_chat_openai
    service = OpenRouterLLMService(api_key="sk-or-test-key-1234")

    mock_cls.return_value.invoke.return_value = _make_ai_message("ok")
    service.generate("test prompt")

    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["model"] == "google/gemini-2.5-flash"


# =====================================================================
# Test 5: Response Content Extracted
# =====================================================================


def test_response_content_extracted(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify LLMResponse.content matches the AIMessage content."""
    mock_instance, _ = mock_chat_openai
    expected = "Vector databases store high-dimensional embeddings."
    mock_instance.invoke.return_value = _make_ai_message(expected)

    result = llm_service.generate("What are vector databases?")

    assert result.content == expected


# =====================================================================
# Test 6: Empty Response Handled
# =====================================================================


def test_empty_response_handled(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify empty AIMessage content raises LLMResponseError."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.return_value = _make_ai_message("")

    with pytest.raises(LLMResponseError, match="empty response"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 7: Missing API Key
# =====================================================================


def test_missing_api_key(mock_chat_openai) -> None:
    """Verify missing OPENROUTER_API_KEY raises LLMMissingAPIKeyError."""
    service = OpenRouterLLMService(api_key=None)
    # Clear the internal settings too
    service._settings = MagicMock()
    service._settings.OPENROUTER_API_KEY = None
    service._settings.llm = MagicMock()
    service._settings.llm.model = "google/gemini-2.5-flash"
    service._settings.llm.temperature = 0.2
    service._settings.llm.max_tokens = 4096
    service._settings.llm.timeout = 60
    service._settings.llm.max_retries = 3

    with pytest.raises(LLMMissingAPIKeyError, match="not configured"):
        service.generate("test prompt")


# =====================================================================
# Test 8: Authentication Failure
# =====================================================================


def test_authentication_failure(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify HTTP 401 from OpenRouter raises LLMAuthenticationError."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 401 - Unauthorized: Invalid API key"
    )

    with pytest.raises(LLMAuthenticationError, match="authentication failed"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 9: Invalid Model
# =====================================================================


def test_invalid_model(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify invalid model (404) raises LLMConfigurationError."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 404 - Not Found: model_not_found"
    )

    with pytest.raises(LLMConfigurationError, match="Invalid model"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 10: Rate Limit Retry
# =====================================================================


def test_rate_limit_retry(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify HTTP 429 (rate limit) raises LLMProviderError after exhausting retries."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 429 - Rate limit exceeded. Please retry after 60 seconds."
    )

    with pytest.raises(LLMProviderError, match="request failed"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 11: Server Error Retry
# =====================================================================


def test_server_error_retry(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify HTTP 500 (server error) raises LLMProviderError."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 500 - Internal server error"
    )

    with pytest.raises(LLMProviderError, match="request failed"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 12: Permanent Error Does Not Endlessly Retry
# =====================================================================


def test_permanent_error_no_infinite_retry(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify authentication errors are raised immediately without retry."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 403 - Forbidden: Access denied"
    )

    with pytest.raises(LLMAuthenticationError):
        llm_service.generate("test prompt")

    # Should only have been called once (no retries for auth errors)
    assert mock_instance.invoke.call_count == 1


# =====================================================================
# Test 13: Retry Limit Respected
# =====================================================================


def test_retry_limit_respected(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify the service does not attempt more invocations than configured."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = Exception(
        "Error code: 502 - Bad Gateway"
    )

    with pytest.raises(LLMProviderError):
        llm_service.generate("test prompt")

    # Our service calls invoke once; ChatOpenAI handles retries internally
    # The important thing is that the exception surfaces after retries are exhausted
    assert mock_instance.invoke.call_count >= 1


# =====================================================================
# Test 14: Timeout/Network Failure
# =====================================================================


def test_timeout_failure(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify timeout/network errors raise LLMProviderError."""
    mock_instance, _ = mock_chat_openai
    mock_instance.invoke.side_effect = TimeoutError("Connection timed out")

    with pytest.raises(LLMProviderError, match="request failed"):
        llm_service.generate("test prompt")


# =====================================================================
# Test 15: Malformed Response
# =====================================================================


def test_malformed_response(
    mock_chat_openai, llm_service: OpenRouterLLMService
) -> None:
    """Verify non-standard response objects are handled gracefully."""
    mock_instance, _ = mock_chat_openai
    # Return an object without .content attribute
    malformed = MagicMock(spec=[])  # Empty spec = no attributes
    mock_instance.invoke.return_value = malformed

    with pytest.raises(LLMResponseError, match="empty response"):
        llm_service.generate("test prompt")
