from __future__ import annotations

import pytest

from applied_ai_blackjack.llm_backend import FakeLLMBackend, GeminiLLMBackend, build_llm_backend


def test_build_llm_backend_returns_fake_backend_by_default() -> None:
    backend = build_llm_backend(backend_name="fake")
    assert isinstance(backend, FakeLLMBackend)


def test_build_llm_backend_requires_api_key_for_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        build_llm_backend(backend_name="gemini")


def test_build_llm_backend_uses_env_api_key_for_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    backend = build_llm_backend(backend_name="gemini")

    assert isinstance(backend, GeminiLLMBackend)
    assert backend.api_key == "test-key"
