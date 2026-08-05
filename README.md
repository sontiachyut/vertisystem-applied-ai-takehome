# Vertisystem Applied AI Take-Home

This repo now contains both screening tasks:

1. Task 1: terminal-based multi-agent blackjack demo
2. Task 2: FastAPI abacus microservice with shared-sum consistency

The two implementations are kept separate:

- `applied_ai_blackjack/` for Task 1
- `applied_ai_abacus/` for Task 2

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

## Setup

From the project root:

```bash
python -m pip install -e .
python -m pytest tests
```

## Task 1

Task 1 is a deterministic-rule blackjack demo where the LLM is only used for:

- AI player decisions: `hit` / `stand`
- dealer request interpretation: `deal_card` / `stand` / `invalid`

The LLM is not trusted with game truth. Python owns:

- game state
- score calculation
- bust detection
- max-3-card enforcement
- winner selection

### Run Task 1

Default fake backend:

```bash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5
```

Gemini backend:

```bash
export GEMINI_API_KEY=your_key_here
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Optional Gemini model override:

```bash
export GEMINI_MODEL=gemini-2.5-flash
PYTHONPATH=. python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Specs:

- `spec.md`
- `features/task1_blackjack.feature`

## Task 2

Task 2 is a FastAPI microservice with three endpoints:

- `POST /abacus/number` with `{"number": N}`
- `GET /abacus/sum`
- `DELETE /abacus/sum`

V1 design choices:

- stateless FastAPI nodes
- shared authoritative PostgreSQL store for the live demo path
- one authoritative `abacus_state` row
- atomic increment/reset operations
- strict integer validation
- no node-local fallback state

The API response shape is intentionally minimal:

```json
{"sum": 18}
```

### Run Task 2 Tests

```bash
python -m pytest tests
```

Note:

- automated tests use temporary SQLite databases for fast local verification
- the live two-node demo target remains PostgreSQL, matching `task2_spec.md`

### Run Task 2 Locally With Two Nodes

Start PostgreSQL:

```bash
docker compose -f docker-compose.task2.yml up -d
```

Start Node A in one terminal:

```bash
PYTHONPATH=. python -m applied_ai_abacus.main --port 8001
```

Start Node B in another terminal:

```bash
PYTHONPATH=. python -m applied_ai_abacus.main --port 8002
```

The default database URL used by the service is:

```text
postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

If you want to override it:

```bash
export ABACUS_DATABASE_URL=postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

### Demo Task 2 From The Terminal

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

### Concurrent Smoke Check

This simple shell loop should end at `{"sum":100}`:

```bash
for i in $(seq 1 50); do
  curl -s -X POST http://127.0.0.1:8001/abacus/number -H 'Content-Type: application/json' -d '{"number":1}' >/dev/null &
  curl -s -X POST http://127.0.0.1:8002/abacus/number -H 'Content-Type: application/json' -d '{"number":1}' >/dev/null &
done
wait
curl -s http://127.0.0.1:8001/abacus/sum
```

Specs:

- `task2_spec.md`
- `features/task2_abacus.feature`

## Test Coverage

Current tests cover:

- Task 1 deterministic game rules and orchestration
- Task 1 LLM prompt/parsing hardening
- Task 2 API behavior
- Task 2 strict validation
- Task 2 cross-node shared-state visibility
- Task 2 concurrent update correctness

Run everything:

```bash
python -m pytest tests
```
