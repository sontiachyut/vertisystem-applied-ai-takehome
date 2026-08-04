# Vertisystem Applied AI Task 1

Terminal-based multi-agent blackjack demo built for an `Applied AI Engineer` take-home.

This project is intentionally small in scope, but engineered like a real applied-AI system:

- deterministic Python owns game truth
- AI agents only decide actions or interpret requests
- only the dealer can access the card-draw tool
- fake and real LLM backends share the same adapter interface
- core rules are covered by automated tests

## What This Demonstrates

The goal is not full blackjack. The goal is to show:

1. role-based agent design
2. controlled tool access
3. structured model outputs
4. deterministic orchestration around LLM behavior
5. a usable terminal demo instead of a one-off script

## Architecture

```text
CLI
  ->
Game Orchestrator
  ->
AI Player / Human Request
  ->
Dealer Agent
  ->
Card Draw Tool
  ->
Deterministic Game Engine
  ->
Terminal Transcript + Final Outcome
```

## Project Layout

```text
applied_ai_blackjack/
  cli.py
  dealer_agent.py
  game_engine.py
  llm_backend.py
  main.py
  models.py
  orchestrator.py
  player_agents.py
features/
  task1_blackjack.feature
tests/
  test_backend_factory.py
  test_cli_smoke.py
  test_fake_llm_backend.py
  test_game_engine.py
  test_orchestrator.py
spec.md
```

## Core Rules

- One dealer mediates all card draws.
- Three AI players and one human player compete.
- Each scoring player may hold at most `3` cards.
- Card values are random integers in the range `2..11`.
- Winner is the highest total under or equal to `21`.
- If multiple players share the highest valid total, the game reports a tie.
- If every scoring player busts, there is no winner.

## LLM Design

The LLM is used only for:

- AI player decisions: `hit` or `stand`
- dealer request interpretation: `deal_card`, `stand`, or `invalid`

The LLM is **not** used for:

- card generation
- score calculation
- rule enforcement
- turn limits
- winner selection

That split is deliberate. It keeps the system explainable, testable, and resilient.

## Backends

### 1. Fake backend

The default path is a deterministic `FakeLLMBackend`. It is useful for:

- local development
- repeatable demos
- fast regression tests

### 2. Gemini backend

A real Gemini-backed adapter is included behind the same interface. It is opt-in and uses environment variables so the API key does not live in source.

## Local Setup

From the project root:

```bash
python -m pytest tests
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5
```

That runs the app with the fake backend.

## Run With Gemini

```bash
export GEMINI_API_KEY=your_key_here
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Optional model override:

```bash
export GEMINI_MODEL=gemini-2.5-flash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Or pass the model directly:

```bash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini --gemini-model gemini-2.5-flash
```

## Example

```text
Welcome to Applied AI Blackjack.
Table: Dealer | AI Player 1 | AI Player 2 | AI Player 3 | Human
Rules: only the dealer can draw cards, each scoring player may hold up to 3 cards, and the highest total under 21 wins.

[AI Player 1]
Decision: hit
Reason: AI Player 1 has no cards yet, so opening with a draw is the only sensible move.
Dealer: AI Player 1, your next card is 11. Total is now 11.
Hand: [11] | Total: 11 | Status: active
```

## Testing

The test suite currently covers:

- deterministic card draws with seeding
- three-card limit enforcement
- bust exclusion from winner selection
- explicit tie handling
- dealer-only card routing
- malformed AI output fallback
- backend factory behavior
- CLI smoke run

Run all tests:

```bash
python -m pytest tests
```

## Design Notes

- `spec.md` is the implementation spec.
- `features/task1_blackjack.feature` contains BDD-style acceptance scenarios.
- The fake backend lets the system be built and verified before paying for or depending on live model calls.
- The real backend is intentionally thin so it can be swapped or extended later.

## Current Status

- deterministic engine implemented
- fake backend implemented
- Gemini backend implemented
- terminal transcript polished
- automated tests passing
