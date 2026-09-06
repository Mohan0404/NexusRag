import time
from typing import Optional

from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.llm.llm_service import (
    BaseLLMService,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMMissingAPIKeyError,
    LLMProviderError,
    LLMResponse,
    LLMResponseError,
)

logger = get_logger(__name__)

# OpenRouter API endpoint (OpenAI-compatible)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterLLMService(BaseLLMService):
    """Production implementation of BaseLLMService using OpenRouter as the LLM gateway.

    Architecture:
        Application
            ↓
        OpenRouterLLMService (this class)
            ↓
        LangChain ChatOpenAI (openai_api_base → OpenRouter)
            ↓
        OpenRouter API (OpenAI-compatible)
            ↓
        Gemini LLM (or any model available on OpenRouter)
            ↓
        Generated text

    Configuration:
        - Model name: Settings.llm.model (config.yaml)
        - Temperature: Settings.llm.temperature (config.yaml)
        - Max tokens: Settings.llm.max_tokens (config.yaml)
        - Timeout: Settings.llm.timeout (config.yaml)
        - Max retries: Settings.llm.max_retries (config.yaml)
        - API key: Settings.OPENROUTER_API_KEY (.env, SecretStr)

    Retry Strategy:
        - LangChain ChatOpenAI handles transient retries internally
          (429, 500, 502, 503, 504) using bounded exponential backoff.
        - max_retries is configurable (default: 3).
        - Permanent errors (401, 403, 404) are NOT retried.

    Does NOT:
        - Construct RAG prompts (Phase 9).
        - Manage conversation memory.
        - Implement streaming.
        - Cache results (Phase 10).
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Initializes the OpenRouterLLMService.

        Args:
            settings: Centralized application settings. Defaults to get_settings().
            api_key: Optional explicit API key override. If omitted, reads from
                Settings.OPENROUTER_API_KEY.

        Raises:
            LLMMissingAPIKeyError: If no API key is available.
        """
        self._settings = settings or get_settings()
        self._api_key = api_key
        self._llm = None

        logger.info(
            "OpenRouterLLMService configured: model='%s', temperature=%.2f, "
            "max_tokens=%d, timeout=%ds, max_retries=%d",
            self._settings.llm.model,
            self._settings.llm.temperature,
            self._settings.llm.max_tokens,
            self._settings.llm.timeout,
            self._settings.llm.max_retries,
        )

    def _resolve_api_key(self) -> str:
        """Resolves the OpenRouter API key from explicit override or Settings.

        Returns:
            The resolved API key string.

        Raises:
            LLMMissingAPIKeyError: If no API key is available.
        """
        if self._api_key:
            return self._api_key

        if self._settings.OPENROUTER_API_KEY:
            key = self._settings.OPENROUTER_API_KEY.get_secret_value()
            if key and key.strip():
                return key

        logger.error("OpenRouter API key is missing. Cannot generate LLM responses.")
        raise LLMMissingAPIKeyError(
            "OpenRouter API key is not configured. "
            "Please set OPENROUTER_API_KEY in your .env file."
        )

    def _ensure_llm(self):
        """Lazily initializes the LangChain ChatOpenAI instance configured for OpenRouter.

        Returns:
            The initialized ChatOpenAI instance.

        Raises:
            LLMMissingAPIKeyError: If the API key is not available.
            LLMConfigurationError: If ChatOpenAI initialization fails.
        """
        if self._llm is not None:
            return self._llm

        resolved_key = self._resolve_api_key()

        try:
            self._llm = ChatOpenAI(
                model=self._settings.llm.model,
                api_key=resolved_key,
                base_url=OPENROUTER_BASE_URL,
                temperature=self._settings.llm.temperature,
                max_tokens=self._settings.llm.max_tokens,
                timeout=self._settings.llm.timeout,
                max_retries=self._settings.llm.max_retries,
            )

            logger.info(
                "ChatOpenAI client initialized for OpenRouter: model='%s'",
                self._settings.llm.model,
            )
            return self._llm

        except Exception as e:
            logger.error("Failed to initialize ChatOpenAI client: %s", e)
            raise LLMConfigurationError(
                f"Failed to initialize LLM client: {e}"
            ) from e

    def generate(self, prompt: str) -> LLMResponse:
        """Generates text from the LLM given a prompt string.

        Pipeline:
        1. Validate input prompt.
        2. Ensure ChatOpenAI client is initialized.
        3. Invoke the LLM via ChatOpenAI.invoke().
        4. Extract and validate the response content.
        5. Return a clean LLMResponse.

        Args:
            prompt: The complete prompt text to send to the LLM.

        Returns:
            LLMResponse containing the generated text.

        Raises:
            LLMResponseError: If the prompt is empty.
            LLMMissingAPIKeyError: If the API key is not configured.
            LLMAuthenticationError: If OpenRouter rejects credentials.
            LLMProviderError: If OpenRouter encounters a transient failure.
            LLMResponseError: If the response is empty or malformed.
        """
        # Step 1: Validate prompt
        if not prompt or not prompt.strip():
            raise LLMResponseError("Cannot generate from an empty prompt.")

        start_time = time.time()
        model_name = self._settings.llm.model

        logger.info(
            "LLM generation started: model='%s', prompt_length=%d",
            model_name,
            len(prompt),
        )

        # Step 2: Ensure client
        llm = self._ensure_llm()

        # Step 3: Invoke LLM
        try:
            result = llm.invoke(prompt)
        except Exception as e:
            return self._handle_provider_error(e)

        # Step 4: Extract and validate response
        elapsed = time.time() - start_time
        return self._process_response(result, model_name, elapsed)

    def _handle_provider_error(self, error: Exception) -> LLMResponse:
        """Translates provider-specific exceptions into application-level exceptions.

        Args:
            error: The raw exception from LangChain/OpenAI SDK.

        Raises:
            LLMAuthenticationError: For 401/403 errors.
            LLMProviderError: For transient errors (429, 5xx, network, timeout).
        """
        error_msg = str(error)
        error_type = type(error).__name__
        logger.error("LLM provider error (%s): %s", error_type, error_msg)

        # Authentication errors (permanent — do not retry)
        if any(code in error_msg for code in ["401", "403", "Unauthorized", "Forbidden"]):
            raise LLMAuthenticationError(
                f"OpenRouter authentication failed: {error_msg}"
            ) from error

        # Invalid model / not found (permanent)
        if any(code in error_msg for code in ["404", "Not Found", "model_not_found"]):
            raise LLMConfigurationError(
                f"Invalid model or endpoint: {error_msg}"
            ) from error

        # Transient errors (429, 5xx, network, timeout)
        raise LLMProviderError(
            f"OpenRouter request failed: {error_msg}"
        ) from error

    def _process_response(
        self, result, model_name: str, elapsed: float
    ) -> LLMResponse:
        """Extracts content from the LangChain AIMessage and validates it.

        Args:
            result: The response object from ChatOpenAI.invoke().
            model_name: The configured model name.
            elapsed: Time taken for the API call in seconds.

        Returns:
            LLMResponse with the generated content.

        Raises:
            LLMResponseError: If the response is empty or malformed.
        """
        # Extract content from AIMessage
        content = None
        if hasattr(result, "content"):
            content = result.content
        elif isinstance(result, str):
            content = result
        elif isinstance(result, dict):
            content = result.get("content", "")

        if content is None or (isinstance(content, str) and not content.strip()):
            logger.error("LLM returned empty or missing content.")
            raise LLMResponseError(
                "LLM returned an empty response. The model may not have "
                "generated any content for the given prompt."
            )

        # Extract usage metadata if available
        usage = {}
        if hasattr(result, "usage_metadata") and result.usage_metadata:
            usage = dict(result.usage_metadata)
        elif hasattr(result, "response_metadata") and result.response_metadata:
            token_usage = result.response_metadata.get("token_usage", {})
            if token_usage:
                usage = dict(token_usage)

        # Resolve actual model name from response if available
        actual_model = model_name
        if hasattr(result, "response_metadata") and result.response_metadata:
            actual_model = result.response_metadata.get("model_name", model_name)

        logger.info(
            "LLM generation completed: model='%s', response_length=%d, "
            "elapsed=%.2fs",
            actual_model,
            len(content),
            elapsed,
        )

        return LLMResponse(
            content=content,
            model=actual_model,
            usage=usage,
        )
