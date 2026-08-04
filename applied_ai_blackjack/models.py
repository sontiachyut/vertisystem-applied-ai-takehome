from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TurnAction(str, Enum):
    HIT = "hit"
    STAND = "stand"


class DealerIntent(str, Enum):
    DEAL_CARD = "deal_card"
    STAND = "stand"
    INVALID = "invalid"


class PlayerDecision(BaseModel):
    action: Literal["hit", "stand"]
    reason: str = Field(min_length=1)


class DealerInterpretation(BaseModel):
    intent: Literal["deal_card", "stand", "invalid"]
    reply: str = Field(min_length=1)


class VisiblePlayerState(BaseModel):
    player_id: str
    display_name: str
    cards: list[int]
    total: int
    card_count: int
    is_bust: bool
    has_stood: bool


class PlayerDecisionContext(BaseModel):
    self_state: VisiblePlayerState
    other_players: list[VisiblePlayerState]
    max_cards: int = 3
    target_limit: int = 21


class DealerRequest(BaseModel):
    requesting_player_id: str
    request_type: Literal["deal_card"]

