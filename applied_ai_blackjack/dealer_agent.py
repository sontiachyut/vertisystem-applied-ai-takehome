from __future__ import annotations

from .llm_backend import LLMBackend
from .models import DealerInterpretation


class DealerAgent:
    def __init__(self, *, llm_backend: LLMBackend) -> None:
        self.llm_backend = llm_backend

    def interpret_request(self, raw_message: str) -> DealerInterpretation:
        system_prompt = (
            "You are an AI dealer for a simplified blackjack game. "
            "Classify the player's message as exactly one of: deal_card, stand, or invalid. "
            "Interpret natural language requests, but do not invent game actions beyond those three labels. "
            'Examples: "deal me the next card" -> deal_card, "hit me" -> deal_card, '
            '"another one" -> deal_card, "stay here" -> stand, "hold my total" -> stand. '
            "Anything unrelated, ambiguous, or not clearly a hit/stand request should map to invalid. "
            "Return only the allowed structured response."
        )
        user_prompt = f"Player message: {raw_message}"
        return self.llm_backend.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=DealerInterpretation,
        )
