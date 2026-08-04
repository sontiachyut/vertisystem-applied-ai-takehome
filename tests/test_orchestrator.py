from __future__ import annotations

from pydantic import BaseModel

from applied_ai_blackjack.dealer_agent import DealerAgent
from applied_ai_blackjack.game_engine import GameEngine, ParticipantRole
from applied_ai_blackjack.llm_backend import FakeLLMBackend, LLMBackend
from applied_ai_blackjack.models import DealerInterpretation, PlayerDecision
from applied_ai_blackjack.orchestrator import GameOrchestrator
from applied_ai_blackjack.player_agents import AIPlayerAgent


class BrokenBackend:
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        raise ValueError("malformed output")


def _build_engine(*, seed: int = 13) -> GameEngine:
    engine = GameEngine(seed=seed)
    engine.add_participant(player_id="dealer", display_name="Dealer", role=ParticipantRole.DEALER)
    engine.add_participant(player_id="ai-1", display_name="AI Player 1", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-2", display_name="AI Player 2", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-3", display_name="AI Player 3", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="human", display_name="Human", role=ParticipantRole.HUMAN_PLAYER)
    return engine


def _build_orchestrator(*, player_backend: LLMBackend, dealer_backend: LLMBackend) -> GameOrchestrator:
    engine = _build_engine()
    ai_players = {
        player_id: AIPlayerAgent(
            player_id=player_id,
            display_name=engine.get_participant(player_id).display_name,
            llm_backend=player_backend,
        )
        for player_id in ("ai-1", "ai-2", "ai-3")
    }
    dealer_agent = DealerAgent(llm_backend=dealer_backend)
    return GameOrchestrator(
        engine=engine,
        dealer_agent=dealer_agent,
        ai_players=ai_players,
        human_player_id="human",
    )


def test_ai_turn_hit_routes_card_draw_through_dealer_boundary() -> None:
    orchestrator = _build_orchestrator(player_backend=FakeLLMBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("ai-1").cards = [4, 5]

    result = orchestrator.process_ai_turn("ai-1")

    assert result.action == "hit"
    assert result.dealer_intent == "deal_card"
    assert result.card_dealt is not None
    assert orchestrator.engine.get_participant("ai-1").card_count == 3


def test_human_natural_language_request_normalizes_to_hit() -> None:
    orchestrator = _build_orchestrator(player_backend=FakeLLMBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("human").cards = [6]

    result = orchestrator.process_human_turn("deal me the next card")

    assert result.action == "hit"
    assert result.dealer_intent == "deal_card"
    assert result.card_dealt is not None
    assert orchestrator.engine.get_participant("human").card_count == 2


def test_malformed_ai_output_uses_fallback_policy_for_low_total() -> None:
    orchestrator = _build_orchestrator(player_backend=BrokenBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("ai-1").cards = [5, 6]

    result = orchestrator.process_ai_turn("ai-1")

    assert result.used_fallback is True
    assert result.action == "hit"
    assert "below 15" in result.reason
    assert result.card_dealt is not None


def test_malformed_ai_output_uses_fallback_policy_for_high_total() -> None:
    orchestrator = _build_orchestrator(player_backend=BrokenBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("ai-1").cards = [10, 7]

    result = orchestrator.process_ai_turn("ai-1")

    assert result.used_fallback is True
    assert result.action == "stand"
    assert "at least 15" in result.reason
    assert result.card_dealt is None
    assert orchestrator.engine.get_participant("ai-1").has_stood is True


def test_invalid_human_request_does_not_mutate_state() -> None:
    orchestrator = _build_orchestrator(player_backend=FakeLLMBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("human").cards = [8, 2]

    result = orchestrator.process_human_turn("tell me a joke")

    assert result.action == "invalid"
    assert result.dealer_intent == DealerInterpretation(intent="invalid", reply="x").intent
    assert orchestrator.engine.get_participant("human").cards == [8, 2]


def test_three_card_completion_is_called_out_in_dealer_reply() -> None:
    orchestrator = _build_orchestrator(player_backend=FakeLLMBackend(), dealer_backend=FakeLLMBackend())
    orchestrator.engine.get_participant("ai-3").cards = [2, 2]

    result = orchestrator.process_ai_turn("ai-3")

    assert result.action == "hit"
    assert result.player_card_count_after == 3
    assert result.player_is_done is True
    assert "completes the three-card limit" in result.dealer_reply
