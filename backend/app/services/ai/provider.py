"""Chat-completion adapter for SHREA AI.

Only this module knows about the provider's wire format. The advisor service
depends on ChatProvider, so a different provider is one new subclass plus one
branch in build_provider(). The key stays in this process: it is never put in
a prompt, a response or a log line.
"""

import logging
import re
import time
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Carries a safe, machine-readable code only - never provider bodies or headers."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ChatProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        """Return the assistant's reply text, or raise AIProviderError."""


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

# NVIDIA's hosted API intermittently answers HTTP 503. Only that status is retried,
# once, after this pause; every other status keeps its existing classification.
RETRY_STATUS = 503
RETRY_DELAY_SECONDS = 1.0


class NvidiaNimProvider(ChatProvider):
    """NVIDIA NIM's OpenAI-compatible chat-completions API."""

    name = "nvidia"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        max_output_tokens: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._timeout = timeout_seconds
        self._max_tokens = max_output_tokens
        self._transport = transport

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": self._max_tokens,
            "temperature": 0.2,
            "stream": False,
        }
        response = self._post(body)
        if response.status_code == RETRY_STATUS:
            logger.warning("AI provider returned HTTP %s on attempt 1; retrying once", response.status_code)
            time.sleep(RETRY_DELAY_SECONDS)
            response = self._post(body)
            logger.info("AI provider retry finished with HTTP %s", response.status_code)

        if response.status_code == 429:
            raise AIProviderError("rate_limited")
        if response.status_code in (401, 403):
            # Operator problem (bad or unauthorised key): log the status only.
            logger.error("AI provider rejected the configured credentials (HTTP %s)", response.status_code)
            raise AIProviderError("auth_failed")
        if response.status_code != 200:
            logger.warning("AI provider returned HTTP %s", response.status_code)
            raise AIProviderError("provider_error")

        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise AIProviderError("invalid_response") from None
        if not isinstance(text, str):
            raise AIProviderError("invalid_response")
        return _THINK_BLOCK.sub("", text)

    def _post(self, body: dict) -> httpx.Response:
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                return client.post(self._url, json=body, headers={"Authorization": f"Bearer {self._api_key}"})
        except httpx.TimeoutException:
            raise AIProviderError("timeout") from None
        except httpx.HTTPError:
            raise AIProviderError("network_error") from None


def build_provider(settings: Settings) -> ChatProvider | None:
    """None means "not configured": no key, or a provider this build has no adapter for."""
    if settings.ai_provider != "nvidia" or not settings.nvidia_api_key:
        return None
    return NvidiaNimProvider(
        api_key=settings.nvidia_api_key,
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout_seconds=settings.ai_timeout_seconds,
        max_output_tokens=settings.ai_max_output_tokens,
    )
