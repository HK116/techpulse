"""
Tests for techpulse.llm_backends.

We don't test actual network calls here (that would cost money / need a
key) — just the backend-selection logic and missing-key error handling.
"""

import pytest

from techpulse.llm_backend import build_backend_from_env


def test_build_backend_raises_for_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(ValueError, match="Unknown LLM PROVIDER"):
        build_backend_from_env()


def test_openrouter_backend_raises_without_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        build_backend_from_env()


# def test_anthropic_backend_raises_without_api_key(monkeypatch):
#     monkeypatch.setenv("LLM_PROVIDER", "anthropic")
#     monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

#     with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
#         build_backend_from_env()