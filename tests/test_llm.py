"""
Tests for techpulse.llm.

We only test config/error-handling here — no real network calls, since
that would cost time and depend on external availability.
"""

import pytest

from techpulse.llm import OpenRouterClient


def test_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenRouterClient()


def test_uses_model_from_env_var_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key-for-testing")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")

    client = OpenRouterClient()

    assert client._model == "some/model:free"


def test_explicit_model_overrides_env_var(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key-for-testing")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")

    client = OpenRouterClient(model="different/model:free")

    assert client._model == "different/model:free"