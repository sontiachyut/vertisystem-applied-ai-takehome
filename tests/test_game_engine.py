from __future__ import annotations

import pytest

from applied_ai_blackjack.game_engine import (
    GameEngine,
    GameRuleViolation,
    ParticipantRole,
)
from applied_ai_blackjack.models import TurnAction


def _build_engine(*, seed: int = 7) -> GameEngine:
    engine = GameEngine(seed=seed)
    engine.add_participant(player_id="dealer", display_name="Dealer", role=ParticipantRole.DEALER)
    engine.add_participant(player_id="ai-1", display_name="AI Player 1", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-2", display_name="AI Player 2", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-3", display_name="AI Player 3", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="human", display_name="Human", role=ParticipantRole.HUMAN_PLAYER)
    return engine


def test_seeded_draws_are_repeatable() -> None:
    engine_a = _build_engine(seed=41)
    engine_b = _build_engine(seed=41)

    draws_a = [
        engine_a.deal_card_to("human"),
        engine_a.deal_card_to("ai-1"),
        engine_a.deal_card_to("ai-2"),
    ]
    draws_b = [
        engine_b.deal_card_to("human"),
        engine_b.deal_card_to("ai-1"),
        engine_b.deal_card_to("ai-2"),
    ]

    assert draws_a == draws_b


def test_participant_may_not_draw_more_than_three_cards() -> None:
    engine = _build_engine()

    assert engine.deal_card_to("human") >= 2
    assert engine.deal_card_to("human") >= 2
    assert engine.deal_card_to("human") >= 2

    with pytest.raises(GameRuleViolation, match="maximum of 3 cards"):
        engine.deal_card_to("human")


def test_standing_prevents_future_draws() -> None:
    engine = _build_engine()

    engine.stand("human")

    with pytest.raises(GameRuleViolation, match="already stood"):
        engine.deal_card_to("human")


def test_bust_players_are_excluded_from_winner_selection() -> None:
    engine = _build_engine()
    engine.get_participant("human").cards = [10, 9, 5]
    engine.get_participant("ai-1").cards = [10, 8]
    engine.get_participant("ai-2").cards = [9, 7]
    engine.get_participant("ai-3").cards = [6, 6]
    engine.get_participant("dealer").cards = [10, 7]

    outcome = engine.score_round()

    assert [winner.player_id for winner in outcome.winners] == ["ai-1"]
    assert outcome.highest_valid_total == 18
    assert outcome.is_tie is False


def test_ties_are_reported_explicitly() -> None:
    engine = _build_engine()
    engine.get_participant("human").cards = [10, 8]
    engine.get_participant("ai-1").cards = [9, 9]
    engine.get_participant("ai-2").cards = [10, 7]
    engine.get_participant("ai-3").cards = [8, 8]
    engine.get_participant("dealer").cards = [7, 7]

    outcome = engine.score_round()

    assert outcome.highest_valid_total == 18
    assert outcome.is_tie is True
    assert [winner.player_id for winner in outcome.winners] == ["ai-1", "human"]


def test_round_completion_requires_all_participants_to_be_done() -> None:
    engine = _build_engine()

    for player_id in engine.scoring_player_ids():
        engine.apply_turn_action(player_id, TurnAction.STAND)

    assert engine.is_round_complete() is True


def test_visible_state_reflects_updated_totals() -> None:
    engine = _build_engine()

    engine.get_participant("human").cards = [7, 8]
    state = engine.visible_state_for("human")

    assert state.total == 15
    assert state.card_count == 2
    assert state.is_bust is False


def test_dealer_is_not_included_in_winner_selection() -> None:
    engine = _build_engine()
    engine.get_participant("dealer").cards = [11, 10]
    engine.get_participant("human").cards = [10, 8]
    engine.get_participant("ai-1").cards = [9, 7]
    engine.get_participant("ai-2").cards = [8, 8]
    engine.get_participant("ai-3").cards = [7, 7]

    outcome = engine.score_round()

    assert outcome.highest_valid_total == 18
    assert [winner.player_id for winner in outcome.winners] == ["human"]
    assert all(score.player_id != "dealer" for score in outcome.scoreboard)
