"""LLMRouter: Ollama default, cloud fallback.

Provides a single async interface for LLM completions with automatic
fallback from local Ollama to cloud Groq when Ollama is unavailable or slow.
"""

import re
import time
import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.settings import settings

logger = structlog.get_logger(__name__)


class LLMUnavailableError(Exception):
    """Raised when both Ollama and fallback LLM providers fail."""
    pass


class RetryableLLMError(LLMUnavailableError):
    """Raised when a transient network error should trigger a retry."""
    pass


def _log_retry_attempt(retry_state) -> None:
    next_action = retry_state.next_action
    wait_seconds = next_action.sleep if next_action else None
    logger.warning(
        "llm_retry_scheduled",
        attempt=retry_state.attempt_number,
        wait_seconds=wait_seconds,
        error=str(retry_state.outcome.exception()) if retry_state.outcome else None,
    )


class LLMRouter:
    """Routes LLM calls to Ollama (default) with Groq fallback."""

    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS
        self.fallback_provider = settings.LLM_FALLBACK_PROVIDER
        self.fallback_api_key = settings.LLM_FALLBACK_API_KEY

    @retry(
        retry=retry_if_exception_type(RetryableLLMError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )
    async def complete(self, prompt: str, expect_json: bool = False, force_json_object: bool = False) -> str:
        """Send a prompt to the LLM and return the response text.

        Args:
            prompt: The prompt string to send.
            expect_json: If True, strip markdown code fences from response.
            force_json_object: If True, use Ollama's native format='json' (forces {})

        Returns:
            The LLM response text.

        Raises:
            LLMUnavailableError: If both Ollama and fallback fail.
        """
        retryable_error = False
        ollama_error: Exception | None = None

        # Try Ollama first
        try:
            result = await self._call_ollama(prompt, force_json_object)
            if expect_json:
                result = self._strip_code_fences(result)
            return result
        except Exception as e:
            ollama_error = e
            retryable_error = self._is_retryable_error(e)
            logger.warning(
                "ollama_failed",
                error=str(e),
                model=self.ollama_model,
                fallback_triggered=True,
                retryable=retryable_error,
            )

        # Try fallback
        if self.fallback_provider == "groq" and self.fallback_api_key:
            try:
                result = await self._call_groq(prompt)
                if expect_json:
                    result = self._strip_code_fences(result)
                return result
            except Exception as e:
                retryable_fallback_error = self._is_retryable_error(e)
                logger.error(
                    "groq_fallback_failed",
                    error=str(e),
                    fallback_triggered=True,
                    retryable=retryable_fallback_error,
                )
                if retryable_fallback_error:
                    raise RetryableLLMError(
                        "Transient fallback LLM network error. Retrying request."
                    ) from e

        if retryable_error:
            raise RetryableLLMError(
                "Transient Ollama network error. Retrying request."
            ) from ollama_error

        raise LLMUnavailableError(
            "Both Ollama and fallback LLM providers failed. "
            "Check that Ollama is running and the model is pulled, "
            "or provide a valid LLM_FALLBACK_API_KEY."
        )

    async def _call_ollama(self, prompt: str, force_json_object: bool = False) -> str:
        """Call Ollama's generate API."""
        start = time.monotonic()
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        if force_json_object:
            payload["format"] = "json"
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.monotonic() - start) * 1000)
        result = data.get("response", "")

        logger.info(
            "llm_call_complete",
            model=self.ollama_model,
            latency_ms=latency_ms,
            fallback_triggered=False,
            provider="ollama",
        )
        return result

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq as a fallback provider."""
        from groq import AsyncGroq

        start = time.monotonic()
        client = AsyncGroq(api_key=self.fallback_api_key)
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        result = chat_completion.choices[0].message.content or ""

        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "llm_call_complete",
            model="llama-3.1-8b-instant",
            latency_ms=latency_ms,
            fallback_triggered=True,
            provider="groq",
        )
        return result

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove markdown code fences and conversational filler from LLM responses."""
        text = text.strip()
        
        # Find the first { or [ and the last } or ]
        first_brace = text.find('{')
        first_bracket = text.find('[')
        
        start_idx = -1
        if first_brace != -1 and first_bracket != -1:
            start_idx = min(first_brace, first_bracket)
        elif first_brace != -1:
            start_idx = first_brace
        elif first_bracket != -1:
            start_idx = first_bracket
            
        last_brace = text.rfind('}')
        last_bracket = text.rfind(']')
        
        end_idx = -1
        if last_brace != -1 and last_bracket != -1:
            end_idx = max(last_brace, last_bracket)
        elif last_brace != -1:
            end_idx = last_brace
        elif last_bracket != -1:
            end_idx = last_bracket
            
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            return text[start_idx:end_idx + 1]
            
        return text

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        retryable_httpx_errors = (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.ReadError,
            httpx.WriteError,
            httpx.RemoteProtocolError,
        )
        if isinstance(error, retryable_httpx_errors):
            return True

        return error.__class__.__name__ in {"APIConnectionError", "APITimeoutError"}
