"""
llm_backend.py
--------------

Interchangeable ways to call an LLM: Claude API or any other model on OpenRouter.

Both backends expose the same `complete(system, user) -> str` method for swapping between different
models without code change and instead through config
"""

from __future__ import annotations

import os

import requests

ANTHROPIC_MODEL = "claude-sonnet-5"
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
OPENROUTER_URL = "https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b:free"

class OpenRouterBackend:
    def __init__(self, model: str = OPENROUTER_MODEL, session: requests.Session | None = None) -> None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

        self._api_key = api_key
        self._model = model
        self._session = session or requests.Session()

    def complete(self, system: str, user: str) -> str:
        response = self._session.post(
            OPENROUTER_URL,
            headers= {"Authorization": f"Bearer {self._api_key}"},
            json= {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 200,
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class AnthropicBackend:
    pass #TBD


def build_backend_from_env():
    """Pick a backedn based on the LLM_PROVIDER environment variable."""
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider == "anthropic":
        return AnthropicBackend()
    if provider == "openrouter":
        return OpenRouterBackend()

    raise ValueError(f"Unknown LLM PROVIDER: {provider!r}. Use 'anthropic' or 'openrouter'.")
