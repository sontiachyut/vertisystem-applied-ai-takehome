from __future__ import annotations

import json
import os
import re
import time
from typing import Protocol, TypeVar
from urllib import error, request

from pydantic import BaseModel

from .models import DealerInterpretation, PlayerDecision


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LLMBackend(Protocol):
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        """Return a validated structured response from a model backend."""


class GeminiLLMBackend:
    """Gemini-backed structured generation adapter."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key.strip()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        prompt = f"{system_prompt}\n\n{user_prompt}".strip()
        payload = self._generate_structured_payload(
            prompt=prompt,
            schema=_clean_schema(response_model.model_json_schema()),
        )
        return response_model.model_validate(payload)

    def _generate_structured_payload(self, *, prompt: str, schema: dict) -> dict:
        request_payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.2,
            },
        }
        encoded_payload = json.dumps(request_payload).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                http_request = request.Request(
                    self.endpoint,
                    data=encoded_payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                    method="POST",
                )
                with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                break
            except error.HTTPError as exc:
                last_error = exc
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {429, 500, 503} or attempt == self.max_retries:
                    raise ValueError(f"Gemini request failed with HTTP {exc.code}: {body}") from exc
                time.sleep(1.5 * (attempt + 1))
            except error.URLError as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise ValueError(f"Gemini request failed: {exc.reason}") from exc
                time.sleep(1.5 * (attempt + 1))
        else:  # pragma: no cover - defensive
            raise ValueError(f"Gemini request failed: {last_error}")

        parts = response_payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            return {}
        text = parts[0].get("text", "").strip()
        if not text:
            return {}
        return json.loads(text)


class FakeLLMBackend:
    """Deterministic local backend used for early development and tests."""

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        if response_model is PlayerDecision:
            player_name_match = re.search(r"player:\s*(.+)", user_prompt, re.IGNORECASE)
            total_match = re.search(r"current total:\s*(\d+)", user_prompt, re.IGNORECASE)
            cards_drawn_match = re.search(r"cards drawn:\s*(\d+)", user_prompt, re.IGNORECASE)
            current_total = int(total_match.group(1)) if total_match else 0
            cards_drawn = int(cards_drawn_match.group(1)) if cards_drawn_match else 0
            player_name = player_name_match.group(1).strip() if player_name_match else "AI Player"
            threshold, style = self._player_profile(player_name)
            payload = self._player_decision_payload(
                player_name=player_name,
                style=style,
                current_total=current_total,
                cards_drawn=cards_drawn,
                threshold=threshold,
            )
            return response_model.model_validate(payload)
        if response_model is DealerInterpretation:
            lowered = user_prompt.lower()
            if "stand" in lowered:
                payload = {"intent": "stand", "reply": "Understood. I will hold your current total."}
            elif "deal" in lowered or "card" in lowered or "hit" in lowered:
                payload = {"intent": "deal_card", "reply": "All right. I will deal the next card to your hand."}
            else:
                payload = {
                    "intent": "invalid",
                    "reply": "I can help with hit or stand requests, but I did not understand that one.",
                }
            return response_model.model_validate(payload)
        raise ValueError(f"Unsupported response model for FakeLLMBackend: {response_model.__name__}")

    def _player_profile(self, player_name: str) -> tuple[int, str]:
        normalized = player_name.lower()
        if "1" in normalized:
            return 16, "cautious"
        if "2" in normalized:
            return 17, "balanced"
        if "3" in normalized:
            return 18, "aggressive"
        return 17, "balanced"

    def _player_decision_payload(
        self,
        *,
        player_name: str,
        style: str,
        current_total: int,
        cards_drawn: int,
        threshold: int,
    ) -> dict[str, str]:
        if current_total >= threshold:
            reason = {
                "cautious": (
                    f"{player_name} is playing carefully and will stand on {current_total} "
                    "rather than risk a late bust."
                ),
                "balanced": f"{player_name} has enough value at {current_total} and will protect the hand.",
                "aggressive": (
                    f"{player_name} has reached the aggressive stop line at {current_total} "
                    "and will stand now."
                ),
            }[style]
            return {"action": "stand", "reason": reason}

        if cards_drawn == 0:
            reason = f"{player_name} has no cards yet, so opening with a draw is the only sensible move."
        elif style == "cautious":
            reason = f"{player_name} is still below the cautious stand threshold of {threshold}, so one more card is justified."
        elif style == "aggressive":
            reason = f"{player_name} is pressing for a stronger hand and will keep drawing until reaching {threshold} or the card limit."
        else:
            reason = f"{player_name} is below the balanced stop line of {threshold}, so drawing again is reasonable."
        return {"action": "hit", "reason": reason}


def build_llm_backend(*, backend_name: str, gemini_api_key: str | None = None, gemini_model: str | None = None) -> LLMBackend:
    normalized_name = backend_name.strip().lower()
    if normalized_name == "fake":
        return FakeLLMBackend()
    if normalized_name == "gemini":
        api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when --llm-backend gemini is selected.")
        model = (gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip() or "gemini-2.5-flash"
        return GeminiLLMBackend(api_key=api_key, model=model)
    raise ValueError(f"Unsupported llm backend: {backend_name}")


def _clean_schema(value):
    if isinstance(value, dict):
        cleaned: dict = {}
        for key, child in value.items():
            if key in {"title", "default", "$schema", "examples"}:
                continue
            cleaned[key] = _clean_schema(child)
        return cleaned
    if isinstance(value, list):
        return [_clean_schema(item) for item in value]
    return value
