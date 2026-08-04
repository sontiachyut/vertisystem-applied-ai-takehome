from __future__ import annotations

from applied_ai_blackjack.llm_backend import FakeLLMBackend
from applied_ai_blackjack.models import PlayerDecision


def test_fake_llm_backend_uses_distinct_ai_player_thresholds() -> None:
    backend = FakeLLMBackend()

    player_one = backend.generate_structured(
        system_prompt="x",
        user_prompt=(
            "Player: AI Player 1\n"
            "Current cards: [9, 7]\n"
            "Current total: 16\n"
            "Cards drawn: 2\n"
        ),
        response_model=PlayerDecision,
    )
    player_three = backend.generate_structured(
        system_prompt="x",
        user_prompt=(
            "Player: AI Player 3\n"
            "Current cards: [9, 7]\n"
            "Current total: 16\n"
            "Cards drawn: 2\n"
        ),
        response_model=PlayerDecision,
    )

    assert player_one.action == "stand"
    assert player_three.action == "hit"
