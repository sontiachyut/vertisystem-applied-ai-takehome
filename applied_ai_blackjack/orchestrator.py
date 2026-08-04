from __future__ import annotations

from dataclasses import dataclass
import re

from .dealer_agent import DealerAgent
from .game_engine import GameEngine, GameRuleViolation
from .models import DealerIntent, DealerRequest, PlayerDecisionContext, TurnAction
from .player_agents import AIPlayerAgent


DEFAULT_FALLBACK_HIT_THRESHOLD = 15


@dataclass(frozen=True)
class TurnResult:
    player_id: str
    action: str
    reason: str
    used_fallback: bool
    dealer_intent: str
    dealer_reply: str
    card_dealt: int | None
    player_total_after: int
    player_card_count_after: int
    player_is_bust: bool
    player_has_stood: bool
    player_is_done: bool


class GameOrchestrator:
    def __init__(
        self,
        *,
        engine: GameEngine,
        dealer_agent: DealerAgent,
        ai_players: dict[str, AIPlayerAgent],
        human_player_id: str,
        fallback_hit_threshold: int = DEFAULT_FALLBACK_HIT_THRESHOLD,
    ) -> None:
        self.engine = engine
        self.dealer_agent = dealer_agent
        self.ai_players = ai_players
        self.human_player_id = human_player_id
        self.fallback_hit_threshold = fallback_hit_threshold

    def process_ai_turn(self, player_id: str) -> TurnResult:
        participant = self.engine.get_participant(player_id)
        if self.engine.is_player_done(player_id):
            return TurnResult(
                player_id=player_id,
                action="stand",
                reason="Player is already done for the round.",
                used_fallback=False,
                dealer_intent=DealerIntent.STAND.value,
                dealer_reply=f"{participant.display_name} is already done.",
                card_dealt=None,
                player_total_after=participant.total,
                player_card_count_after=participant.card_count,
                player_is_bust=participant.is_bust,
                player_has_stood=participant.has_stood,
                player_is_done=self.engine.is_player_done(player_id),
            )

        used_fallback = False
        try:
            decision = self.ai_players[player_id].decide_turn(self._build_player_context(player_id))
            action = TurnAction(decision.action)
            reason = decision.reason
        except Exception:
            used_fallback = True
            action, reason = self._fallback_decision_for(player_id)

        if action is TurnAction.HIT:
            dealer_request = DealerRequest(requesting_player_id=player_id, request_type="deal_card")
            card_dealt = self._process_dealer_request(dealer_request)
            participant = self.engine.get_participant(player_id)
            return TurnResult(
                player_id=player_id,
                action=action.value,
                reason=reason,
                used_fallback=used_fallback,
                dealer_intent=DealerIntent.DEAL_CARD.value,
                dealer_reply=self._dealer_card_reply(participant.display_name, card_dealt, participant.total, participant),
                card_dealt=card_dealt,
                player_total_after=participant.total,
                player_card_count_after=participant.card_count,
                player_is_bust=participant.is_bust,
                player_has_stood=participant.has_stood,
                player_is_done=self.engine.is_player_done(player_id),
            )

        self.engine.stand(player_id)
        participant = self.engine.get_participant(player_id)
        return TurnResult(
            player_id=player_id,
            action=action.value,
            reason=reason,
            used_fallback=used_fallback,
            dealer_intent=DealerIntent.STAND.value,
            dealer_reply=f"{participant.display_name} will stand on {participant.total}.",
            card_dealt=None,
            player_total_after=participant.total,
            player_card_count_after=participant.card_count,
            player_is_bust=participant.is_bust,
            player_has_stood=participant.has_stood,
            player_is_done=self.engine.is_player_done(player_id),
        )

    def process_human_turn(self, raw_message: str) -> TurnResult:
        participant = self.engine.get_participant(self.human_player_id)
        try:
            interpretation = self.dealer_agent.interpret_request(raw_message)
            dealer_intent = DealerIntent(interpretation.intent)
            dealer_reply = interpretation.reply
        except Exception:
            dealer_intent, dealer_reply = self._fallback_human_intent(raw_message)

        if dealer_intent is DealerIntent.DEAL_CARD:
            card_dealt = self._process_dealer_request(
                DealerRequest(requesting_player_id=self.human_player_id, request_type="deal_card")
            )
            participant = self.engine.get_participant(self.human_player_id)
            return TurnResult(
                player_id=self.human_player_id,
                action=TurnAction.HIT.value,
                reason="Human requested another card.",
                used_fallback=False,
                dealer_intent=dealer_intent.value,
                dealer_reply=self._dealer_card_reply(participant.display_name, card_dealt, participant.total, participant, prefix=dealer_reply),
                card_dealt=card_dealt,
                player_total_after=participant.total,
                player_card_count_after=participant.card_count,
                player_is_bust=participant.is_bust,
                player_has_stood=participant.has_stood,
                player_is_done=self.engine.is_player_done(self.human_player_id),
            )

        if dealer_intent is DealerIntent.STAND:
            self.engine.stand(self.human_player_id)
            participant = self.engine.get_participant(self.human_player_id)
            return TurnResult(
                player_id=self.human_player_id,
                action=TurnAction.STAND.value,
                reason="Human chose to stand.",
                used_fallback=False,
                dealer_intent=dealer_intent.value,
                dealer_reply=dealer_reply,
                card_dealt=None,
                player_total_after=participant.total,
                player_card_count_after=participant.card_count,
                player_is_bust=participant.is_bust,
                player_has_stood=participant.has_stood,
                player_is_done=self.engine.is_player_done(self.human_player_id),
            )

        return TurnResult(
            player_id=self.human_player_id,
            action="invalid",
            reason="Human request could not be mapped to a valid turn action.",
            used_fallback=False,
            dealer_intent=dealer_intent.value,
            dealer_reply=dealer_reply,
            card_dealt=None,
            player_total_after=participant.total,
            player_card_count_after=participant.card_count,
            player_is_bust=participant.is_bust,
            player_has_stood=participant.has_stood,
            player_is_done=self.engine.is_player_done(self.human_player_id),
        )

    def _build_player_context(self, player_id: str) -> PlayerDecisionContext:
        return PlayerDecisionContext(
            self_state=self.engine.visible_state_for(player_id),
            other_players=self.engine.visible_states(exclude_player_id=player_id),
            max_cards=self.engine.max_cards,
        )

    def _fallback_decision_for(self, player_id: str) -> tuple[TurnAction, str]:
        participant = self.engine.get_participant(player_id)
        if participant.total < self.fallback_hit_threshold and participant.card_count < self.engine.max_cards:
            return (
                TurnAction.HIT,
                f"Fallback policy selected hit because total {participant.total} is below {self.fallback_hit_threshold}.",
            )
        return (
            TurnAction.STAND,
            f"Fallback policy selected stand because total {participant.total} is at least {self.fallback_hit_threshold}.",
        )

    def _process_dealer_request(self, dealer_request: DealerRequest) -> int:
        if dealer_request.request_type != "deal_card":
            raise GameRuleViolation(f"Unsupported dealer request type: {dealer_request.request_type}")
        return self.engine.deal_card_to(dealer_request.requesting_player_id)

    def _fallback_human_intent(self, raw_message: str) -> tuple[DealerIntent, str]:
        lowered = raw_message.strip().lower()
        if re.search(r"\b(stand|stay|hold)\b", lowered):
            return DealerIntent.STAND, "Understood. I will hold your current total."
        if re.search(r"\b(hit|deal|card|another)\b", lowered):
            return DealerIntent.DEAL_CARD, "All right. I will deal the next card to your hand."
        return DealerIntent.INVALID, "I can help with hit or stand requests, but I did not understand that one."

    def _dealer_card_reply(
        self,
        player_name: str,
        card_dealt: int,
        total_after: int,
        participant,
        *,
        prefix: str | None = None,
    ) -> str:
        lead = f"{prefix} " if prefix else ""
        if participant.is_bust:
            return f"{lead}{player_name}, your next card is {card_dealt}. That busts the hand at {total_after}."
        if participant.card_count >= self.engine.max_cards:
            return (
                f"{lead}{player_name}, your next card is {card_dealt}. "
                f"That brings the hand to {total_after} and completes the three-card limit."
            )
        return f"{lead}{player_name}, your next card is {card_dealt}. Total is now {total_after}."
