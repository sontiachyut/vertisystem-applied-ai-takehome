from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random

from .models import TurnAction, VisiblePlayerState


TARGET_LIMIT = 21


class GameRuleViolation(ValueError):
    """Raised when a requested action violates the simplified game rules."""


class UnknownParticipantError(KeyError):
    """Raised when a requested participant is not registered in the game."""


class ParticipantRole(str, Enum):
    DEALER = "dealer"
    AI_PLAYER = "ai_player"
    HUMAN_PLAYER = "human_player"


@dataclass
class ParticipantState:
    player_id: str
    display_name: str
    role: ParticipantRole
    cards: list[int] = field(default_factory=list)
    has_stood: bool = False

    @property
    def total(self) -> int:
        return sum(self.cards)

    @property
    def is_bust(self) -> bool:
        return self.total > TARGET_LIMIT

    @property
    def card_count(self) -> int:
        return len(self.cards)

    @property
    def can_draw(self) -> bool:
        return not self.has_stood and not self.is_bust


@dataclass(frozen=True)
class PlayerScore:
    player_id: str
    display_name: str
    total: int
    cards: tuple[int, ...]
    is_bust: bool
    has_stood: bool
    card_count: int


@dataclass(frozen=True)
class RoundOutcome:
    winners: tuple[PlayerScore, ...]
    scoreboard: tuple[PlayerScore, ...]
    highest_valid_total: int | None
    is_tie: bool


class GameEngine:
    def __init__(self, *, seed: int | None = None, max_cards: int = 3) -> None:
        self._random = random.Random(seed)
        self.max_cards = max_cards
        self._participants: dict[str, ParticipantState] = {}
        self._turn_order: list[str] = []

    def add_participant(self, *, player_id: str, display_name: str, role: ParticipantRole) -> ParticipantState:
        normalized_player_id = player_id.strip()
        if not normalized_player_id:
            raise ValueError("player_id must not be empty.")
        if normalized_player_id in self._participants:
            raise ValueError(f"Participant '{normalized_player_id}' is already registered.")
        participant = ParticipantState(
            player_id=normalized_player_id,
            display_name=display_name.strip() or normalized_player_id,
            role=role,
        )
        self._participants[normalized_player_id] = participant
        self._turn_order.append(normalized_player_id)
        return participant

    def participant_ids(self) -> tuple[str, ...]:
        return tuple(self._turn_order)

    def scoring_player_ids(self) -> tuple[str, ...]:
        return tuple(
            player_id
            for player_id in self._turn_order
            if self._participants[player_id].role is not ParticipantRole.DEALER
        )

    def get_participant(self, player_id: str) -> ParticipantState:
        try:
            return self._participants[player_id]
        except KeyError as exc:  # pragma: no cover - trivial guard
            raise UnknownParticipantError(player_id) from exc

    def visible_state_for(self, player_id: str) -> VisiblePlayerState:
        participant = self.get_participant(player_id)
        return VisiblePlayerState(
            player_id=participant.player_id,
            display_name=participant.display_name,
            cards=list(participant.cards),
            total=participant.total,
            card_count=participant.card_count,
            is_bust=participant.is_bust,
            has_stood=participant.has_stood,
        )

    def visible_states(self, *, exclude_player_id: str | None = None) -> list[VisiblePlayerState]:
        return [
            self.visible_state_for(player_id)
            for player_id in self._turn_order
            if player_id != exclude_player_id
        ]

    def deal_card_to(self, player_id: str) -> int:
        participant = self.get_participant(player_id)
        self._assert_player_can_draw(participant)
        card = self._draw_card()
        participant.cards.append(card)
        return card

    def stand(self, player_id: str) -> None:
        participant = self.get_participant(player_id)
        if participant.is_bust:
            raise GameRuleViolation(f"{participant.display_name} is already bust and cannot stand.")
        participant.has_stood = True

    def apply_turn_action(self, player_id: str, action: TurnAction | str) -> int | None:
        normalized_action = TurnAction(action)
        if normalized_action is TurnAction.HIT:
            return self.deal_card_to(player_id)
        if normalized_action is TurnAction.STAND:
            self.stand(player_id)
            return None
        raise GameRuleViolation(f"Unsupported action: {action}")

    def is_player_done(self, player_id: str) -> bool:
        participant = self.get_participant(player_id)
        return participant.has_stood or participant.is_bust or participant.card_count >= self.max_cards

    def is_round_complete(self) -> bool:
        scoring_ids = self.scoring_player_ids()
        if not scoring_ids:
            return False
        return all(self.is_player_done(player_id) for player_id in scoring_ids)

    def score_round(self) -> RoundOutcome:
        scoreboard = tuple(self._score_for(player_id) for player_id in self.scoring_player_ids())
        eligible_scores = [score for score in scoreboard if not score.is_bust]
        if not eligible_scores:
            return RoundOutcome(
                winners=(),
                scoreboard=scoreboard,
                highest_valid_total=None,
                is_tie=False,
            )

        highest_valid_total = max(score.total for score in eligible_scores)
        winners = tuple(score for score in eligible_scores if score.total == highest_valid_total)
        return RoundOutcome(
            winners=winners,
            scoreboard=scoreboard,
            highest_valid_total=highest_valid_total,
            is_tie=len(winners) > 1,
        )

    def _score_for(self, player_id: str) -> PlayerScore:
        participant = self.get_participant(player_id)
        return PlayerScore(
            player_id=participant.player_id,
            display_name=participant.display_name,
            total=participant.total,
            cards=tuple(participant.cards),
            is_bust=participant.is_bust,
            has_stood=participant.has_stood,
            card_count=participant.card_count,
        )

    def _assert_player_can_draw(self, participant: ParticipantState) -> None:
        if participant.has_stood:
            raise GameRuleViolation(f"{participant.display_name} has already stood.")
        if participant.is_bust:
            raise GameRuleViolation(f"{participant.display_name} is already bust.")
        if participant.card_count >= self.max_cards:
            raise GameRuleViolation(
                f"{participant.display_name} already has the maximum of {self.max_cards} cards."
            )

    def _draw_card(self) -> int:
        return self._random.randint(2, 11)
