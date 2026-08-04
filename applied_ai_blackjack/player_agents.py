from __future__ import annotations

from .llm_backend import LLMBackend
from .models import PlayerDecision, PlayerDecisionContext


class AIPlayerAgent:
    def __init__(self, *, player_id: str, display_name: str, llm_backend: LLMBackend) -> None:
        self.player_id = player_id
        self.display_name = display_name
        self.llm_backend = llm_backend

    def decide_turn(self, context: PlayerDecisionContext) -> PlayerDecision:
        system_prompt = (
            "You are an AI blackjack player. "
            "Decide whether to hit or stand using the simplified game rules. "
            "Return only the allowed structured response."
        )
        user_prompt = (
            f"Player: {context.self_state.display_name}\n"
            f"Current cards: {context.self_state.cards}\n"
            f"Current total: {context.self_state.total}\n"
            f"Cards drawn: {context.self_state.card_count}\n"
            f"Max cards allowed: {context.max_cards}\n"
            f"Visible opponents: {[player.model_dump() for player in context.other_players]}\n"
            "Return action and a short reason."
        )
        return self.llm_backend.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=PlayerDecision,
        )

