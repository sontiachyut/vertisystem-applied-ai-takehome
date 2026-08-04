from __future__ import annotations

from applied_ai_blackjack.cli import run_game
from applied_ai_blackjack.llm_backend import FakeLLMBackend


def test_cli_smoke_run_produces_final_scoreboard() -> None:
    outputs: list[str] = []
    scripted_inputs = iter(["stand"])

    def fake_input(prompt: str) -> str:
        outputs.append(prompt)
        return next(scripted_inputs)

    def fake_output(message: str) -> None:
        outputs.append(message)

    run_game(seed=5, input_fn=fake_input, output_fn=fake_output, llm_backend=FakeLLMBackend())

    assert any("Welcome to Applied AI Blackjack." in message for message in outputs)
    assert any("Final scoreboard:" in message for message in outputs)
    assert any("Winner:" in message or "It's a tie" in message or "No winner." in message for message in outputs)
