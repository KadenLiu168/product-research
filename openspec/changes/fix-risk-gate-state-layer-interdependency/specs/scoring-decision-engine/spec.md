## ADDED Requirements

### Requirement: RiskGateState is re-exported from the neutral contract

`product_research/scoring_decision.py` SHALL import `RiskGateState` from the neutral contract `product_research/risk_gate.py` and expose it under the existing `scoring_decision.RiskGateState` name such that both names refer to the identical class object. The re-export SHALL NOT alter the closed vocabulary, the value semantics, or the supported public API of the scoring and decision capability.

#### Scenario: Legacy access stays identical

- **WHEN** code imports `RiskGateState` from `product_research.scoring_decision`
- **THEN** `scoring_decision.RiskGateState` is the identical class object as `risk_gate.RiskGateState`, and values constructed through either name are interchangeable
