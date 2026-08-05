from __future__ import annotations

from .llm_backend import LLMBackend
from .models import PlayerDecision, PlayerDecisionContext


PLAYER_STYLE_PROFILES = {
    "ai-1": ("cautious", "stand on 16 or higher"),
    "ai-2": ("balanced", "stand on 17 or higher"),
    "ai-3": ("aggressive", "stand on 18 or higher"),
}


class AIPlayerAgent:
    def __init__(self, *, player_id: str, display_name: str, llm_backend: LLMBackend) -> None:
        self.player_id = player_id
        self.display_name = display_name
        self.llm_backend = llm_backend

    def decide_turn(self, context: PlayerDecisionContext) -> PlayerDecision:
        style_name, stop_line = PLAYER_STYLE_PROFILES.get(self.player_id, ("balanced", "stand on 17 or higher"))
        system_prompt = (
            f"You are {self.display_name}, an AI blackjack player in a simplified terminal game. "
            "Decide only whether to hit or stand. "
            "You cannot draw cards yourself; only the dealer can execute a card draw, so you are only proposing an action. "
            "Respect the simplified rules: each scoring player can hold at most 3 cards, totals above 21 are bust, and the highest valid total wins. "
            f"Style profile: {style_name}. Suggested stop line: {stop_line}. "
            "Return only the allowed structured response with a short reason."
        )
        user_prompt = (
            f"Player: {context.self_state.display_name}\n"
            f"Current cards: {context.self_state.cards}\n"
            f"Current total: {context.self_state.total}\n"
            f"Cards drawn: {context.self_state.card_count}\n"
            f"Max cards allowed: {context.max_cards}\n"
            f"Target limit before bust: {context.target_limit}\n"
            f"Visible opponents: {[player.model_dump() for player in context.other_players]}\n"
            "Return action and a short reason."
        )
        return self.llm_backend.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=PlayerDecision,
        )
