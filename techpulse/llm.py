"""
llm.py
------

Simple integration with OpenRouter via openai-compatible sdk.
model is controlled by the OPENROUTER_MODEL environment variable. easy swap
"""

from __future__ import annotations

import logging
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# DEFAULT_MODEL = "z-ai/glm-5.2:free"
# DEFAULT_MODEL = "thinkingmachines/inkling:free"
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL") or "nvidia/nemotron-3-ultra-550b-a55b:free"
DEFAULT_MAX_TOKENS = 500
DEFAULT_MAX_RETRIES = 3

class OpenRouterClient:
    """A wrapper around OpenRouter's chat completions endpoint."""

    def __init__(self, model: str | None = None, max_retries: int = DEFAULT_MAX_RETRIES):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

        self._client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self._model: str = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        self._max_retries = max_retries

    def complete(self, system: str, user: str) -> str:
        """
        Send a system+user prompt, return the model's raw text reply.
        
        Retries with expontial backoff (1s, 2s, 4s,...) on transient failures like rate limits,
        since these are common and expected when using shred free-tier model pools.
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model = self._model,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                if not response.choices:
                    raise ValueError(f"Empty response from model (no choices): {response!r}")
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError(f"Model returned no text content: {response!r}")
                return content
            except Exception as exc:  # noqa: BLE001 - retry on any transient failure
                last_error = exc
                wait_seconds = 2**attempt
                logger.warning(
                    "OpenRouter call failed (attempt %d/%d) using model=%s: %s. Retrying in %ds...",
                    attempt + 1,
                    self._max_retries,
                    self._model,
                    exc,
                    wait_seconds,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(wait_seconds)

        raise RuntimeError(f"OpenRouter call failed after {self._max_retries} attempts") from last_error