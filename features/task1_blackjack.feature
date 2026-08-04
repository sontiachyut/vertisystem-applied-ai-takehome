Feature: Multi-agent blackjack terminal demo
  The system demonstrates applied-AI orchestration with deterministic rules
  and dealer-only tool access.

  Background:
    Given a blackjack game with one dealer, three AI players, and one human player
    And the game uses the simplified Vertisystem rules

  Scenario: Terminal startup introduces all participants
    When the program starts
    Then the terminal should introduce the dealer
    And the terminal should introduce exactly three AI players
    And the terminal should introduce the human player

  Scenario: Dealer is the only actor allowed to draw cards
    Given an AI player decides to hit
    When the orchestrator processes the turn
    Then the card draw should be routed through the dealer
    And the AI player must not invoke the draw tool directly

  Scenario: Human natural language input is normalized to a hit action
    Given it is the human player's turn
    When the user types "deal me the next card"
    Then the command should normalize to a hit action
    And the dealer should handle the resulting card request

  Scenario: AI players return structured decisions
    Given an AI player has a current total of 11
    When the system asks the player for a turn decision
    Then the result should normalize to either "hit" or "stand"
    And the result should include a short reason

  Scenario: No participant may draw more than three cards
    Given a participant already has three cards
    When that participant requests another card
    Then the system should reject the request
    And the participant's hand should remain unchanged

  Scenario: Bust players cannot win
    Given one participant has a total greater than 21
    And another participant has the highest valid total under 21
    When the round is scored
    Then the busted participant should be excluded from winner selection
    And the valid participant should win

  Scenario: Ties are reported explicitly
    Given two participants share the same highest valid total under 21
    When the round is scored
    Then the system should report a tie
    And both winners should be listed

  Scenario: Malformed AI output falls back safely
    Given an AI player backend returns malformed output
    When the orchestrator validates the decision
    Then the system should apply the deterministic fallback policy
    And the game should continue without crashing

  Scenario: Seeded mode is repeatable
    Given two games are started with the same seed
    When all deterministic steps are replayed
    Then the card sequence should match between the runs
