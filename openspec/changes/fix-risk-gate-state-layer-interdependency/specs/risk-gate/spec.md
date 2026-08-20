## Purpose

This capability defines the neutral shared contract for the decision-facing Risk Gate state, so that upstream Risk analysis and the downstream scoring / decision engine depend on the same canonical `RiskGateState` definition without depending on each other.

## ADDED Requirements

### Requirement: RiskGateState is defined in the neutral contract module

The system SHALL provide `RiskGateState` as the canonical definition in the neutral contract module `product_research/risk_gate.py`. The module SHALL be self-contained, importing only standard-library modules and no other `product_research` module.

#### Scenario: Canonical definition location

- **WHEN** the system is queried for the `RiskGateState` definition location
- **THEN** the canonical definition SHALL be found at `product_research/risk_gate.py`

#### Scenario: Neutral contract has no engine dependency

- **WHEN** `product_research/risk_gate.py` is inspected statically
- **THEN** it contains no import of any other `product_research` module

### Requirement: RiskGateState vocabulary and value semantics are unchanged

The neutral contract SHALL define `RiskGateState` with exactly the closed vocabulary `CLEAR`, `REVIEW_REQUIRED`, and `FATAL`, using the existing immutable value-object semantics: values validate at construction, reject unsupported values, and cannot be mutated after creation.

#### Scenario: Closed vocabulary is preserved

- **WHEN** `RiskGateState` values are constructed in the neutral contract
- **THEN** exactly `CLEAR`, `REVIEW_REQUIRED`, and `FATAL` are accepted and every other value fails construction

#### Scenario: Values remain immutable

- **WHEN** a constructed `RiskGateState` value is mutated after creation
- **THEN** mutation is rejected rather than silently applied
