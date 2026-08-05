from __future__ import annotations

from pydantic import BaseModel

from applied_ai_blackjack.dealer_agent import DealerAgent
from applied_ai_blackjack.llm_backend import _parse_json_response_text
from applied_ai_blackjack.models import DealerInterpretation, PlayerDecision, PlayerDecisionContext, VisiblePlayerState
from applied_ai_blackjack.player_agents import AIPlayerAgent


class CapturingBackend:
    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, type[BaseModel]]] = []

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        self.calls.append((system_prompt, user_prompt, response_model))
        return response_model.model_validate(self.payload)


def test_ai_player_prompt_includes_style_and_tool_boundary() -> None:
    backend = CapturingBackend({"action": "stand", "reason": "Holding."})
    agent = AIPlayerAgent(player_id="ai-1", display_name="AI Player 1", llm_backend=backend)

    context = PlayerDecisionContext(
        self_state=VisiblePlayerState(
            player_id="ai-1",
            display_name="AI Player 1",
            cards=[7, 5],
            total=12,
            card_count=2,
            is_bust=False,
            has_stood=False,
        ),
        other_players=[
            VisiblePlayerState(
                player_id="human",
                display_name="Human",
                cards=[10],
                total=10,
                card_count=1,
                is_bust=False,
                has_stood=False,
            )
        ],
        max_cards=3,
        target_limit=21,
    )

    agent.decide_turn(context)

    system_prompt, user_prompt, response_model = backend.calls[0]

    assert response_model is PlayerDecision
    assert "Style profile: cautious" in system_prompt
    assert "Suggested stop line: stand on 16 or higher" in system_prompt
    assert "You cannot draw cards yourself" in system_prompt
    assert "exactly one lowercase value: hit or stand" in system_prompt
    assert "Target limit before bust: 21" in user_prompt
    assert "Visible opponents:" in user_prompt


def test_dealer_prompt_includes_normalization_examples() -> None:
    backend = CapturingBackend({"intent": "stand", "reply": "Understood. I will hold your current total."})
    agent = DealerAgent(llm_backend=backend)

    agent.interpret_request("I think I'll stay here.")

    system_prompt, user_prompt, response_model = backend.calls[0]

    assert response_model is DealerInterpretation
    assert "deal_card" in system_prompt
    assert "stand" in system_prompt
    assert "invalid" in system_prompt
    assert '"another one" -> deal_card' in system_prompt
    assert '"stay here" -> stand' in system_prompt
    assert user_prompt == "Player message: I think I'll stay here."


def test_parse_json_response_text_accepts_code_fenced_json() -> None:
    payload = _parse_json_response_text(
        """```json
{"action":"hit","reason":"Need one more card."}
```"""
    )

    assert payload == {"action": "hit", "reason": "Need one more card."}


def test_parse_json_response_text_extracts_json_from_surrounding_text() -> None:
    payload = _parse_json_response_text(
        'Here is the structured response:\n{"intent":"stand","reply":"Holding at 18."}\nThanks.'
    )

    assert payload == {"intent": "stand", "reply": "Holding at 18."}
