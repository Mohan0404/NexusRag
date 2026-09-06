from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# =====================================================================
# LLM Response Data Structure
# =====================================================================


@dataclass
class LLMResponse:
    """Clean application-level representation of an LLM generation result.

    Attributes:
        content: The generated text response from the LLM.
        model: The model identifier that produced the response.
        usage: Optional token usage dictionary (prompt_tokens, completion_tokens, total_tokens).
    """

    content: str
    model: str = ""
    usage: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# LLM Exceptions
# =====================================================================


class LLMError(Exception):
    """Base exception for all LLM operations."""

    pass


class LLMMissingAPIKeyError(LLMError, ValueError):
    """Raised when the provider API key is missing or empty."""

    pass


class LLMConfigurationError(LLMError, ValueError):
    """Raised when LLM configuration parameters are invalid (model, timeout, etc.)."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when the provider rejects credentials (HTTP 401/403).

    This is a PERMANENT error — retrying with the same credentials will not help.
    """

    pass


class LLMProviderError(LLMError):
    """Raised when the provider encounters a transient failure (HTTP 429, 5xx, network, timeout).

    These errors may succeed on retry.
    """

    pass


class LLMResponseError(LLMError):
    """Raised when the provider returns an empty or malformed response."""

    pass


# =====================================================================
# LLM Service Abstraction
# =====================================================================


class BaseLLMService(ABC):
    """Provider-independent abstract interface for LLM text generation.

    The rest of the application interacts with this interface — it does not
    know or care whether the underlying provider is OpenRouter, Gemini, Claude,
    or any other LLM provider.

    Implementations must:
    - Accept a plain text prompt and return an LLMResponse.
    - Handle provider-specific errors and translate them into the
      application-level exception hierarchy defined above.
    - Never expose raw provider SDK objects to callers.
    """

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """Generates text from the LLM given a prompt string.

        Args:
            prompt: The complete prompt text to send to the LLM.

        Returns:
            LLMResponse containing the generated text, model name, and usage info.

        Raises:
            LLMMissingAPIKeyError: If the provider API key is not configured.
            LLMConfigurationError: If provider configuration is invalid.
            LLMAuthenticationError: If the provider rejects credentials (permanent).
            LLMProviderError: If the provider encounters a transient failure.
            LLMResponseError: If the provider returns empty or malformed content.
        """
        pass
