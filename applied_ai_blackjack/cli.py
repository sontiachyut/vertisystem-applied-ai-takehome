from __future__ import annotations

from collections.abc import Callable

from .dealer_agent import DealerAgent
from .game_engine import GameEngine, ParticipantRole
from .llm_backend import FakeLLMBackend, LLMBackend, build_llm_backend
from .orchestrator import GameOrchestrator, TurnResult
from .player_agents import AIPlayerAgent


def build_default_orchestrator(
    *,
    seed: int | None = None,
    llm_backend: LLMBackend | None = None,
    backend_name: str = "fake",
    gemini_api_key: str | None = None,
    gemini_model: str | None = None,
) -> GameOrchestrator:
    backend = llm_backend or build_llm_backend(
        backend_name=backend_name,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )
    engine = GameEngine(seed=seed)
    engine.add_participant(player_id="dealer", display_name="Dealer", role=ParticipantRole.DEALER)
    engine.add_participant(player_id="ai-1", display_name="AI Player 1", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-2", display_name="AI Player 2", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="ai-3", display_name="AI Player 3", role=ParticipantRole.AI_PLAYER)
    engine.add_participant(player_id="human", display_name="Human", role=ParticipantRole.HUMAN_PLAYER)

    ai_players = {
        player_id: AIPlayerAgent(
            player_id=player_id,
            display_name=engine.get_participant(player_id).display_name,
            llm_backend=backend,
        )
        for player_id in ("ai-1", "ai-2", "ai-3")
    }
    dealer_agent = DealerAgent(llm_backend=backend)
    return GameOrchestrator(
        engine=engine,
        dealer_agent=dealer_agent,
        ai_players=ai_players,
        human_player_id="human",
    )


def run_game(
    *,
    seed: int | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    llm_backend: LLMBackend | None = None,
    backend_name: str = "fake",
    gemini_api_key: str | None = None,
    gemini_model: str | None = None,
) -> None:
    orchestrator = build_default_orchestrator(
        seed=seed,
        llm_backend=llm_backend,
        backend_name=backend_name,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )
    _print_intro(output_fn)

    for player_id in orchestrator.engine.scoring_player_ids():
        participant = orchestrator.engine.get_participant(player_id)
        while not orchestrator.engine.is_player_done(player_id):
            if participant.role is ParticipantRole.HUMAN_PLAYER:
                result = _run_human_turn(orchestrator, input_fn=input_fn, output_fn=output_fn)
                if result.action == "invalid":
                    output_fn(f"Dealer: {result.dealer_reply}")
                    output_fn("")
                    continue
            else:
                result = orchestrator.process_ai_turn(player_id)
            _render_turn_result(orchestrator, result=result, output_fn=output_fn)

    _render_final_outcome(orchestrator, output_fn=output_fn)


def _run_human_turn(
    orchestrator: GameOrchestrator,
    *,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> TurnResult:
    human_state = orchestrator.engine.get_participant(orchestrator.human_player_id)
    prompt = (
        f"Your turn. Hand={human_state.cards} Total={human_state.total}. "
        "Type hit/stand or say something like 'deal me the next card': "
    )
    try:
        raw_message = input_fn(prompt)
    except EOFError:
        output_fn("Dealer: No input received. Standing for the human player.")
        return orchestrator.process_human_turn("stand")
    except KeyboardInterrupt:
        output_fn("Dealer: Input interrupted. Standing for the human player.")
        return orchestrator.process_human_turn("stand")
    return orchestrator.process_human_turn(raw_message)


def _print_intro(output_fn: Callable[[str], None]) -> None:
    output_fn("Welcome to Applied AI Blackjack.")
    output_fn("Table: Dealer | AI Player 1 | AI Player 2 | AI Player 3 | Human")
    output_fn("Rules: only the dealer can draw cards, each scoring player may hold up to 3 cards, and the highest total under 21 wins.")
    output_fn("")


def _render_turn_result(
    orchestrator: GameOrchestrator,
    *,
    result: TurnResult,
    output_fn: Callable[[str], None],
) -> None:
    participant = orchestrator.engine.get_participant(result.player_id)
    output_fn(f"[{participant.display_name}]")
    output_fn(f"Decision: {result.action}")
    output_fn(f"Reason: {result.reason}")
    output_fn(f"Dealer: {result.dealer_reply}")
    output_fn(
        f"Hand: {participant.cards} | Total: {result.player_total_after} | "
        f"Status: {_describe_hand_status(orchestrator, result)}"
    )
    if result.used_fallback:
        output_fn("Note: deterministic fallback policy was used for this decision.")
    output_fn("")


def _render_final_outcome(orchestrator: GameOrchestrator, *, output_fn: Callable[[str], None]) -> None:
    outcome = orchestrator.engine.score_round()
    output_fn("Final scoreboard:")
    for score in outcome.scoreboard:
        output_fn(
            f"- {score.display_name}: cards={list(score.cards)} | total={score.total} | "
            f"status={_describe_score_status(orchestrator, score.card_count, score.is_bust, score.has_stood)}"
        )
    if not outcome.winners:
        output_fn("No winner. All scoring players busted.")
        return
    if outcome.is_tie:
        winner_names = ", ".join(winner.display_name for winner in outcome.winners)
        output_fn(f"It's a tie between: {winner_names}")
        return
    output_fn(f"Winner: {outcome.winners[0].display_name}")


def _describe_hand_status(orchestrator: GameOrchestrator, result: TurnResult) -> str:
    return _describe_score_status(
        orchestrator,
        result.player_card_count_after,
        result.player_is_bust,
        result.player_has_stood,
    )


def _describe_score_status(
    orchestrator: GameOrchestrator,
    card_count: int,
    is_bust: bool,
    has_stood: bool,
) -> str:
    if is_bust:
        return "bust"
    if has_stood:
        return "standing"
    if card_count >= orchestrator.engine.max_cards:
        return "complete (max cards reached)"
    return "active"
