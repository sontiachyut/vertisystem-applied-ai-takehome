# Vertisystem Applied AI Task 1 Spec

- **Status:** v0.1
- **Date:** August 3, 2026
- **Owner:** Achyutaram Sonti
- **Type:** Living implementation spec

---

## 1. Goal

Build a terminal-based multi-agent blackjack demo that shows applied-AI engineering discipline, not just prompt usage.

The system must:

1. run as a local Python `3.12+` command-line application
2. include:
   - one AI dealer agent
   - at least three AI player agents
   - one human player
3. enforce that only the dealer can access the card-draw tool
4. allow AI players to make hit/stand decisions through an agent interface
5. allow the human player to interact naturally from the terminal
6. compute game state and winner selection deterministically in Python

This is a small applied-AI system with bounded scope.

---

## 2. Why This Exists

This task is not mainly about blackjack rules.

It is a compact test of whether the implementation can demonstrate:

1. role-based agent design
2. controlled tool access
3. structured AI decision-making
4. reliable orchestration between deterministic code and model-driven behavior
5. usable terminal experience

The submission should feel like a deliberate system, not a vibe-coded demo.

---

## 3. In Scope

### Functional Scope

1. One dealer agent that is the only actor permitted to draw cards
2. Exactly three AI player agents in V1, each deciding whether to hit or stand
3. One human player who can play through terminal input
4. A local card-draw function that returns an integer in the range `2..11`
5. Turn-by-turn game flow
6. Maximum of three cards per participant
7. Winner selection as highest total under `21`
8. Clear terminal transcript of:
   - turns
   - decisions
   - cards dealt
   - running totals
   - final outcome
9. A deterministic fallback path when agent output is malformed or unavailable
10. A seeded mode for repeatable demos and tests

### Engineering Scope

1. Clear separation between:
   - game engine
   - agent layer
   - dealer tool boundary
   - CLI layer
2. Structured action outputs for AI players
3. Basic automated coverage over game rules and tool-boundary behavior
4. README with local run instructions

---

## 4. Out of Scope

1. Full casino blackjack rules
2. Suits, face cards, or ace-as-1 logic
3. Betting, split, insurance, or double down
4. Hidden dealer cards
5. GUI or web interface
6. Persistent storage
7. Multiplayer networking
8. Framework-heavy orchestration that hides core logic

If a feature does not help demonstrate agent-tool orchestration or terminal usability, it is out of scope.

---

## 5. Product Principles

1. **Deterministic core first**
   - Game rules, totals, and winner selection live in ordinary Python logic.
2. **Bounded AI behavior**
   - Agents decide actions, but do not own authoritative game state.
3. **Dealer-only tool access**
   - The card tool is not callable by player agents.
4. **Structured outputs over free-form chat**
   - AI decisions must be parsed into narrow action objects.
5. **Failure-tolerant**
   - Bad model output should not crash or corrupt the game.
6. **Demoable**
   - The system should be understandable to an interviewer from one terminal run.

---

## 6. Actors

### Dealer Agent

Responsibilities:

1. receive card requests from players
2. call the card-draw tool
3. return the dealt card
4. announce or log dealing actions

Constraints:

1. only the dealer may invoke the card-draw tool
2. the dealer does not decide player strategy
3. the dealer is not a scoring participant in V1

### AI Player Agents

Responsibilities:

1. inspect the visible game context made available to them
2. decide whether to `hit` or `stand`
3. provide a short reason for the choice

Constraints:

1. cannot call the card-draw tool directly
2. cannot mutate shared game state directly
3. must return one supported action only

### Human Player

Responsibilities:

1. interact through the terminal
2. choose whether to hit or stand

Constraints:

1. must request cards through the dealer flow, not by direct tool invocation

### Game Orchestrator

Responsibilities:

1. initialize the game
2. manage turn order
3. route card requests to the dealer
4. validate actions
5. update authoritative game state
6. compute winner
7. render terminal output

---

## 7. Core Rules

1. Each participant starts with zero cards.
2. A participant may hold at most three cards.
3. A card draw returns a random integer from `2` to `11`.
4. Only the human player and the three AI player agents take scoring turns.
5. On a scoring turn, a participant may:
   - request a card (`hit`)
   - end participation (`stand`)
6. A scoring participant with three cards cannot draw again.
7. A scoring participant with total over `21` is bust.
8. The winner is the scoring participant with the highest total that is `<= 21`.
9. If all scoring participants bust, the game ends with no winner.
10. Tie behavior must be deterministic and documented.

### Tie Rule for V1

If multiple scoring participants share the same highest valid score:

1. report a tie
2. list all tied winners in table turn order

---

## 8. System Architecture

```text
CLI
  ->
Game Orchestrator
  ->
Player / Human Action Request
  ->
Dealer Agent Tool Boundary
  ->
Card Draw Function
  ->
Game State Update
  ->
Terminal Transcript + Final Outcome
```

### 8.1 Game Engine

Owns:

1. participants
2. hands
3. totals
4. turn progression
5. max-card enforcement
6. bust detection
7. final scoring

This layer must be deterministic and testable without an LLM.

### 8.2 Agent Layer

Owns:

1. player decision policy
2. action reasoning text
3. parsing of model output into a narrow action schema

This layer must not own authoritative state transitions.

### 8.3 Dealer Tool Boundary

Owns:

1. the only path to `draw_card()`
2. request validation
3. tool invocation logging

This boundary is one of the core evaluation points of the task.

### 8.4 CLI Layer

Owns:

1. startup and help text
2. human input handling
3. turn transcript formatting
4. final score display

---

## 9. Action Contracts

### AI Player Decision Contract

Every AI player decision must normalize to:

```json
{
  "action": "hit" | "stand",
  "reason": "short explanation"
}
```

### Dealer Request Contract

Every card request routed to the dealer must normalize to:

```json
{
  "requesting_player_id": "string",
  "request_type": "deal_card"
}
```

### Human Input Contract

The CLI must accept simple natural variants such as:

1. `hit`
2. `stand`
3. `deal me a card`
4. `give me another card`

These must normalize to the same action contract as the AI players.

### CLI Utility Commands

The CLI may also support utility commands that do not count as turn actions:

1. `help`
2. `show scores`
3. `quit`

These commands must not bypass the turn system or the dealer-only tool boundary.

---

## 10. LLM Boundary

### Required

1. AI players must behave like agents making decisions
2. prompts must be narrow and role-specific
3. model output must be validated before use
4. the demo path must support an actual LLM-backed AI-player implementation

### Allowed

1. custom lightweight agent abstraction
2. optional use of frameworks such as:
   - LangChain
   - AutoGen
   - CrewAI
3. a provider-backed or mocked LLM interface

### Preferred

V1 should prefer a thin in-project abstraction over deep framework dependence.

Reason:

1. faster iteration
2. clearer control flow
3. easier testing
4. easier interview discussion

### Dealer Clarification

For V1, the dealer is treated as an agent role in the interaction model, but the dealer's tool use remains deterministic Python logic.

This means:

1. the dealer may speak or present itself as an agent
2. the dealer does not need model-driven reasoning to decide whether to draw
3. the dealer remains the only tool mediator for card draws

This preserves reliability while still demonstrating the required agent boundary.

---

## 11. Failure Handling

The system must handle these failures safely:

1. AI player returns malformed output
2. AI player returns unsupported action
3. human enters unrecognized command
4. player requests a fourth card
5. dealer request is malformed

### Fallback Rule

If AI output cannot be parsed after bounded recovery, the system must fall back to a deterministic policy:

1. if total is below `15`, `hit`
2. otherwise, `stand`

The fallback decision must be visible in the transcript.

---

## 12. Observability

The terminal run must make the system behavior inspectable.

Minimum transcript content:

1. player turn start
2. current total before decision
3. chosen action
4. short reason for AI decisions
5. dealt card values
6. running totals
7. bust or stand state
8. final scoreboard

Optional but useful:

1. `--seed` argument for deterministic demos
2. `--verbose` mode for agent reasoning details

### Agent Context Policy

For V1, each AI player receives only bounded visible context:

1. its own current cards and total
2. the number of cards already drawn by that player
3. the public current totals or visible status of other participants
4. the simplified rules of the game

AI players must not receive:

1. direct access to the card tool
2. hidden internal engine state
3. authority to mutate shared state directly

---

## 13. Deliverables

The submission should include:

1. runnable Python application
2. README with setup and run steps
3. source organized by responsibility
4. tests for deterministic game logic
5. tests or checks for dealer-only tool access

---

## 14. Acceptance Criteria

### AC1: Terminal Startup

Given the project is installed locally  
When the user launches the program from the terminal  
Then the game starts successfully and introduces the dealer, AI players, and human player

### AC2: Dealer-Only Tool Access

Given a player wants another card  
When the player takes a `hit` action  
Then the request is routed through the dealer  
And only the dealer calls the card-draw function

### AC3: AI Agent Decision-Making

Given an AI player has a valid turn  
When the orchestrator asks for the player decision  
Then the player returns a normalized action of `hit` or `stand`  
And the transcript includes a short reason

### AC4: Human Natural Input

Given it is the human player’s turn  
When the user types `deal me a card` or `hit`  
Then the input is normalized to a `hit` action  
And the dealer performs the draw

### AC5: Max Three Cards

Given a participant already has three cards  
When that participant attempts another draw  
Then the system rejects the draw  
And the participant’s state remains unchanged

### AC6: Winner Calculation

Given all players have completed their turns  
When final scoring runs  
Then the winner is the highest score under `21`  
And ties are reported deterministically

### AC7: Bust Handling

Given a participant’s total exceeds `21`  
When the score is updated  
Then the participant is marked bust  
And cannot win the round

### AC8: Agent Failure Tolerance

Given an AI player returns malformed or invalid output  
When the system validates the response  
Then the system falls back to a deterministic decision policy  
And continues the game without crashing

### AC9: Repeatable Demo Mode

Given the program is started with a seed argument  
When the game is run multiple times with the same seed  
Then the card sequence and deterministic behaviors are repeatable

---

## 15. BDD Test Targets

The first automated test set should cover:

1. dealer-only card draw enforcement
2. winner selection with valid and bust players
3. three-card limit
4. tie handling
5. malformed AI output fallback
6. human input normalization

---

## 16. Open Decisions Resolved for V1

1. **Should the human player be restricted to the same game actions as AI players?**
   - Yes for turn actions. The only normalized turn actions are `hit` and `stand`.
   - Utility commands like `help`, `show scores`, and `quit` are allowed, but they do not count as game actions.
2. **How many AI players should V1 implement?**
   - Exactly three. The prompt says at least three, and V1 fixes the count to three to keep the demo compact and deterministic.
3. **Is the dealer also a scoring player?**
   - No. The dealer is a tool-mediating agent and is not included in winner selection for V1.
4. **Should the LLM own game state?**
   - No. Game state remains deterministic Python state.
5. **Must the dealer itself use LLM reasoning?**
   - No. The dealer is an agent role in the interaction model, but card dealing stays deterministic and tool-mediated in Python.
6. **Must the project use a real LLM at all?**
   - Yes in the demo path for AI-player decisions, with deterministic fakes or mocks allowed for tests and fallback required for runtime failures.
7. **What context should AI players receive?**
   - Only bounded visible context: their own state, public status of others, and game rules.
8. **What exact fallback threshold should V1 use for malformed AI output?**
   - `15`. If a player's total is below `15`, fallback chooses `hit`; otherwise it chooses `stand`.
9. **Should the game begin with an automatic initial deal?**
   - No. V1 begins from zero cards and proceeds through explicit hit/stand turns for all participants.
10. **Should a framework be mandatory?**
   - No. Framework use is optional.
11. **Should full blackjack rules be implemented?**
   - No. Only the simplified task rules are implemented.
12. **Should tie behavior be implicit?**
   - No. V1 explicitly reports ties.

---

## 17. Next Step

Translate this spec into:

1. file/module layout
2. BDD scenarios
3. deterministic game-engine tests
4. implementation skeleton
