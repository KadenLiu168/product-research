## ADDED Requirements

### Requirement: Risk Gate state is acquired from the neutral contract

The Risk / Compliance analysis module SHALL acquire `RiskGateState` exclusively from the neutral contract `product_research/risk_gate.py` and SHALL NOT import from `product_research.scoring_decision`. The gate aggregation behavior, gate vocabulary, and gate precedence SHALL remain unchanged.

#### Scenario: Dependency direction

- **WHEN** `product_research/risk_compliance.py` is inspected statically
- **THEN** it imports `RiskGateState` from `risk_gate` and contains no import from `scoring_decision`
