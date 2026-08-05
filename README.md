# Vertisystem Applied AI Take-Home

This repository contains both take-home tasks:

1. Task 1: terminal-based multi-agent blackjack demo
2. Task 2: FastAPI abacus microservice with cross-node consistency

The code is organized so each task can be reviewed independently:

- `applied_ai_blackjack/` for Task 1
- `applied_ai_abacus/` for Task 2
- `spec.md` for the Task 1 implementation spec
- `task2_spec.md` for the Task 2 implementation spec
- `features/` for BDD-style acceptance criteria
- `tests/` for automated regression coverage

## Reviewer Quick Start

If you only want the shortest path to verifying the submission:

1. Create and activate a Python 3.12 virtual environment.
2. Install the project with dev dependencies.
3. Run the test suite.
4. Run Task 1.
5. Run Task 2.

Commands:

```bash
cd /Users/achyutaramsonti/Projects/vertisystem-applied-ai-task1
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest tests
```

Expected result:

- the full suite should pass
- current passing status is `43 passed`

## Requirements

- Python `3.12+`
- `docker compose` only if you want the PostgreSQL-backed Task 2 two-node demo
- Gemini API key only if you want the live-LLM Task 1 demo instead of the fake backend

## Project Layout

```text
applied_ai_blackjack/
applied_ai_abacus/
features/
  task1_blackjack.feature
  task2_abacus.feature
tests/
spec.md
task2_spec.md
docker-compose.task2.yml
```

## Task 1

Task 1 is a simplified blackjack-style terminal demo with:

- 1 AI dealer
- 3 AI player agents
- 1 human player

### Task 1 Design Boundary

The LLM is only used for:

- AI player decisions: `hit` or `stand`
- dealer interpretation of human input: `deal_card`, `stand`, or `invalid`

Deterministic Python owns:

- card drawing
- game state
- score calculation
- bust detection
- 3-card limit enforcement
- winner selection
- final scoreboard rendering

That split is deliberate. The model proposes actions; Python decides what is actually allowed to happen.

### Task 1: Fastest Demo Path

Run the deterministic fake backend:

```bash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5
```

What to expect:

1. the 3 AI players act first
2. the human is prompted in plain language
3. the dealer is the only actor who announces dealt cards
4. a final scoreboard prints at the end

Useful human inputs:

- `deal me the next card`
- `hit`
- `another one`
- `hold my total`
- `stand`

Invalid input such as `tell me a joke` should be rejected without changing the hand.

### Task 1: Live Gemini Demo

Set your key in the shell:

```bash
export GEMINI_API_KEY='your_key_here'
export GEMINI_MODEL='gemini-2.5-flash'
```

Run the game:

```bash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Recommended manual test:

1. type `tell me a joke`
2. confirm the dealer rejects it cleanly
3. type `deal me the next card`
4. type `hit`
5. type `s tan d`
6. confirm the game recovers that spaced-out stand request and ends normally

Important note about Gemini:

- the code now handles Gemini retry windows for `429` responses
- if you are on a tight free-tier quota, you may still see pauses or fallback notes during AI turns
- this does not affect deterministic game correctness

### Task 1 Files

- `spec.md`
- `features/task1_blackjack.feature`
- `applied_ai_blackjack/`

## Task 2

Task 2 is a FastAPI microservice with these APIs:

- `POST /abacus/number` with `{"number": N}`
- `GET /abacus/sum`
- `DELETE /abacus/sum`

### Task 2 Design Boundary

V1 uses:

- stateless FastAPI service nodes
- a shared authoritative database
- one authoritative `abacus_state` row
- atomic increment/reset operations
- strict integer validation
- no node-local fallback state

The response shape is intentionally minimal:

```json
{"sum": 18}
```

### Task 2: Fastest Verification Path

Run the tests:

```bash
python -m pytest tests
```

The automated tests cover:

- endpoint behavior
- strict validation
- overflow rejection
- reset behavior
- shared-state visibility across two nodes
- concurrent update correctness

Note:

- automated tests use temporary SQLite databases for fast local verification
- the live two-node demo target remains PostgreSQL, matching `task2_spec.md`

### Task 2: Two-Node Local Demo

Start PostgreSQL:

```bash
docker compose -f docker-compose.task2.yml up -d
```

Start Node A in one terminal:

```bash
cd /Users/achyutaramsonti/Projects/vertisystem-applied-ai-task1
source .venv312/bin/activate
PYTHONPATH=. python -m applied_ai_abacus.main --port 8001
```

Start Node B in another terminal:

```bash
cd /Users/achyutaramsonti/Projects/vertisystem-applied-ai-task1
source .venv312/bin/activate
PYTHONPATH=. python -m applied_ai_abacus.main --port 8002
```

Default database URL:

```text
postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

Optional override:

```bash
export ABACUS_DATABASE_URL=postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

### Task 2: Manual Terminal Demo

Initial read from Node A:

```bash
curl -s http://127.0.0.1:8001/abacus/sum
```

Write through Node A:

```bash
curl -s -X POST http://127.0.0.1:8001/abacus/number \
  -H 'Content-Type: application/json' \
  -d '{"number": 5}'
```

Read through Node B:

```bash
curl -s http://127.0.0.1:8002/abacus/sum
```

Reset through Node B:

```bash
curl -s -X DELETE http://127.0.0.1:8002/abacus/sum
```

Read through Node A again:

```bash
curl -s http://127.0.0.1:8001/abacus/sum
```

Expected result:

- a write to Node A is visible from Node B
- a reset on Node B is visible from Node A

### Task 2: Concurrent Smoke Check

This shell loop should end at `{"sum":100}`:

```bash
for i in $(seq 1 50); do
  curl -s -X POST http://127.0.0.1:8001/abacus/number -H 'Content-Type: application/json' -d '{"number":1}' >/dev/null &
  curl -s -X POST http://127.0.0.1:8002/abacus/number -H 'Content-Type: application/json' -d '{"number":1}' >/dev/null &
done
wait
curl -s http://127.0.0.1:8001/abacus/sum
```

### Task 2 Files

- `task2_spec.md`
- `features/task2_abacus.feature`
- `applied_ai_abacus/`

## Running Everything

From the project root:

```bash
source .venv312/bin/activate
python -m pytest tests
```

## Known Notes

- Task 1 with Gemini can show temporary pauses or fallback notes if the API key is rate-limited.
- Task 2’s automated tests intentionally use SQLite for speed, but the live two-node demo target is PostgreSQL.
- The repo is designed so the deterministic core remains testable even when live LLM behavior is noisy.

## Screenshots / Demo Artifacts

If you want to add screenshots to the repo, a good minimum set is:

1. Task 1 terminal transcript showing AI turns, invalid human input rejection, and final scoreboard
2. Task 2 terminal transcript showing Node A write and Node B read of the same sum
