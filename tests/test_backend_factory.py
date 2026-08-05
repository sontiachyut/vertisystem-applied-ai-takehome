from __future__ import annotations

import pytest

from applied_ai_blackjack.llm_backend import (
    FakeLLMBackend,
    GeminiLLMBackend,
    _retry_delay_seconds_for_http_error,
    _retry_delay_seconds_from_error_body,
    build_llm_backend,
)


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


def test_retry_delay_is_parsed_from_retry_info_payload() -> None:
    body = """
    {
      "error": {
        "details": [
          {
            "@type": "type.googleapis.com/google.rpc.RetryInfo",
            "retryDelay": "54s"
          }
        ]
      }
    }
    """

    assert _retry_delay_seconds_from_error_body(body) == 54.0


def test_retry_delay_falls_back_to_message_text_when_payload_is_not_json() -> None:
    body = "Quota exceeded. Please retry in 12.75s."

    assert _retry_delay_seconds_from_error_body(body) == 12.75


def test_retry_delay_for_http_error_prefers_server_retry_delay_for_429() -> None:
    body = '{"error":{"details":[{"retryDelay":"30s"}]}}'

    assert _retry_delay_seconds_for_http_error(status_code=429, body=body, attempt=0) == 30.0


def test_retry_delay_for_http_error_uses_backoff_for_non_429() -> None:
    assert _retry_delay_seconds_for_http_error(status_code=503, body="", attempt=1) == 3.0
