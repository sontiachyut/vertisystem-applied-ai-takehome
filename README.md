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

macOS / Linux:

```bash
cd /path/to/vertisystem-applied-ai-task1
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest tests
```

Windows PowerShell:

```powershell
cd C:\path\to\vertisystem-applied-ai-task1
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest tests
```

Expected result:

- the full suite should pass
- current passing status is `44 passed`

## Requirements

- Python `3.12+`
- `docker compose` only if you want the PostgreSQL-backed Task 2 two-node demo
- Gemini API key only if you want the live-LLM Task 1 demo instead of the fake backend
- compatible with macOS, Linux, and Windows

## Windows Notes

The code is ordinary Python and is intended to run on Windows as well.

The main differences on Windows are:

1. use `py -3.12` instead of `python3.12`
2. activate the virtual environment with `.\.venv312\Scripts\Activate.ps1`
3. set environment variables with `$env:NAME="value"` in PowerShell

Everything else is the same idea as macOS/Linux.

If PowerShell blocks activation, run this once in that terminal and then try again:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

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

### Task 1 Q&A

**Q: How is AI actually used in Task 1?**

A: AI is used for decision-making and interpretation, not for authoritative state changes. Each AI player looks at the visible game context and proposes `hit` or `stand`. The dealer model interprets human language like `deal me the next card` or `hold my total` and maps it to a narrow intent.

**Q: Does the AI decide the actual game outcome?**

A: No. Deterministic Python still owns the real game logic. Python draws the cards, updates the hands, calculates totals, detects busts, enforces the 3-card rule, and selects the winner. The AI proposes actions; Python executes or rejects them.

### Task 1: Fastest Demo Path

Run the deterministic fake backend:

```bash
python -m applied_ai_blackjack.main --seed 5
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

The repo does **not** include a Gemini API key.

If the reviewer wants to run the live Gemini path, they must provide their own API key in their terminal session first.

Step 1: activate the Python 3.12 environment.

macOS / Linux:

```bash
cd /path/to/vertisystem-applied-ai-task1
source .venv312/bin/activate
```

Windows PowerShell:

```powershell
cd C:\path\to\vertisystem-applied-ai-task1
.\.venv312\Scripts\Activate.ps1
```

Step 2: set the Gemini API key.

Use your own Gemini key here. The repository does not contain one.

macOS / Linux:

```bash
export GEMINI_API_KEY='your_key_here'
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY='your_key_here'
```

Optional: if you want to override the default Gemini model, also set `GEMINI_MODEL`.

macOS / Linux:

```bash
export GEMINI_MODEL='gemini-2.5-flash'
```

Windows PowerShell:

```powershell
$env:GEMINI_MODEL='gemini-2.5-flash'
```

Step 3: run the game.

macOS / Linux or Windows:

```bash
python -m applied_ai_blackjack.main --seed 5 --llm-backend gemini
```

Step 4: when the human turn appears, try these exact inputs:

1. `tell me a joke`
2. `deal me the next card`
3. `hit`
4. `I want to stand`

Recommended manual test:

1. confirm unrelated input is rejected cleanly
2. confirm natural language for another card is interpreted correctly
3. confirm the dealer is still the one who announces the dealt card
4. confirm the final scoreboard prints at the end

Important note about Gemini:

- the code now handles Gemini retry windows for `429` responses
- if you are on a tight free-tier quota, you may still see pauses or fallback notes during AI turns
- this does not affect deterministic game correctness
- if `GEMINI_API_KEY` is missing, the live Gemini path will not start
- the fake backend remains available for deterministic local testing, but the live Gemini path is the reviewer-facing AI demo

### Task 1 Screenshots

These are real screenshots from a live terminal run of Task 1 with Gemini enabled:

- [AI rounds](screenshots/task1/task1-ai-rounds.png)
- [Human turn](screenshots/task1/task1-human-turn.png)
- [Final scoreboard](screenshots/task1/task1-final-scoreboard.png)

AI rounds:

![Task 1 AI rounds](screenshots/task1/task1-ai-rounds.png)

Human turn:

![Task 1 human turn](screenshots/task1/task1-human-turn.png)

Final scoreboard:

![Task 1 final scoreboard](screenshots/task1/task1-final-scoreboard.png)

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

This is the simplest reviewer flow:

1. start PostgreSQL
2. start Node A on port `8001`
3. start Node B on port `8002`
4. send a write to one node
5. confirm the other node sees the same sum
6. reset on one node and confirm the reset is visible from the other

Start PostgreSQL:

```bash
docker compose -f docker-compose.task2.yml up -d
```

Start Node A in one terminal:

```bash
cd /path/to/vertisystem-applied-ai-task1
source .venv312/bin/activate
python -m applied_ai_abacus.main --port 8001
```

Start Node B in another terminal:

```bash
cd /path/to/vertisystem-applied-ai-task1
source .venv312/bin/activate
python -m applied_ai_abacus.main --port 8002
```

Windows PowerShell equivalents:

```powershell
cd C:\path\to\vertisystem-applied-ai-task1
.\.venv312\Scripts\Activate.ps1
python -m applied_ai_abacus.main --port 8001
```

```powershell
cd C:\path\to\vertisystem-applied-ai-task1
.\.venv312\Scripts\Activate.ps1
python -m applied_ai_abacus.main --port 8002
```

Default database URL:

```text
postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

Optional override:

```bash
export ABACUS_DATABASE_URL=postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus
```

Windows PowerShell override:

```powershell
$env:ABACUS_DATABASE_URL='postgresql+psycopg://abacus:abacus@127.0.0.1:5432/abacus'
```

### Task 2: Manual Terminal Demo

macOS / Linux examples:

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

Windows PowerShell examples:

Initial read from Node A:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8001/abacus/sum
```

Write through Node A:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/abacus/number -ContentType "application/json" -Body '{"number":5}'
```

Read through Node B:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8002/abacus/sum
```

Reset through Node B:

```powershell
Invoke-RestMethod -Method Delete -Uri http://127.0.0.1:8002/abacus/sum
```

Read through Node A again:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8001/abacus/sum
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

Windows PowerShell version:

```powershell
1..50 | ForEach-Object {
    Start-Job { Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/abacus/number -ContentType "application/json" -Body '{"number":1}' } | Out-Null
    Start-Job { Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8002/abacus/number -ContentType "application/json" -Body '{"number":1}' } | Out-Null
}
Get-Job | Wait-Job | Out-Null
Get-Job | Remove-Job
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8001/abacus/sum
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

Windows PowerShell:

```powershell
.\.venv312\Scripts\Activate.ps1
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
