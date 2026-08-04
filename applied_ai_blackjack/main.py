from __future__ import annotations

import argparse

from .cli import run_game


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Applied AI blackjack terminal demo.")
    parser.add_argument("--seed", type=int, default=None, help="Seed the card draw RNG for repeatable runs.")
    parser.add_argument(
        "--llm-backend",
        choices=("fake", "gemini"),
        default="fake",
        help="LLM backend to use for agent reasoning. Defaults to fake for local deterministic runs.",
    )
    parser.add_argument(
        "--gemini-model",
        default=None,
        help="Optional Gemini model override when --llm-backend gemini is selected.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_game(
        seed=args.seed,
        backend_name=args.llm_backend,
        gemini_model=args.gemini_model,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
