# risk-gate Specification

## Purpose

This capability defines the neutral shared contract for the decision-facing Risk Gate state, so that upstream Risk analysis and the downstream scoring / decision engine depend on the same canonical `RiskGateState` definition without depending on each other.

## Requirements

### Requirement: RiskGateState is defined in the neutral contract module

The system SHALL provide `RiskGateState` as the canonical definition in the neutral contract module `product_research/risk_gate.py`. The module SHALL be self-contained, importing only standard-library modules and no other `product_research` module, and the production package SHALL contain exactly one `RiskGateState` class definition at that location.

#### Scenario: Canonical definition location

- **WHEN** the system is queried for the `RiskGateState` definition location
- **THEN** the canonical definition SHALL be found at `product_research/risk_gate.py`

#### Scenario: Neutral contract has no engine dependency

- **WHEN** `product_research/risk_gate.py` is inspected statically
- **THEN** it contains no import of any other `product_research` module

#### Scenario: Single production definition

- **WHEN** the `product_research` production package is scanned statically for `RiskGateState` class definitions
- **THEN** exactly one definition exists and it is located in `product_research/risk_gate.py`

### Requirement: RiskGateState vocabulary and value semantics are unchanged

The neutral contract SHALL define `RiskGateState` with exactly the closed vocabulary `CLEAR`, `REVIEW_REQUIRED`, and `FATAL`, preserving the existing value-object semantics unchanged: a non-string input is rejected as a type error, an unsupported string is rejected as a value error, the raw value is exposed via `.value`, string conversion returns the raw value, the representation retains the existing value-object style rather than a dataclass or Enum default, equality is exact-type equality, hashing is consistent with equality, and constructed values cannot be mutated, extended with new attributes, or deleted from.

#### Scenario: Closed vocabulary is preserved

- **WHEN** `RiskGateState` values are constructed in the neutral contract
- **THEN** exactly `CLEAR`, `REVIEW_REQUIRED`, and `FATAL` are accepted; a non-string input fails with a type error and any other string fails with a value error

#### Scenario: Value semantics are preserved

- **WHEN** a `RiskGateState` value is constructed and inspected
- **THEN** `.value`, `str()`, `repr()`, equality with an equal same-type value, inequality with a different value or with a different-type object holding the same value, hash stability, and usability as a set or dict key all behave identically to the pre-move definition

#### Scenario: Values remain immutable

- **WHEN** a constructed `RiskGateState` value is mutated after creation
- **THEN** assignment to `_value` or `value`, assignment of a new attribute, and deletion of `_value` are all rejected rather than silently applied

### Requirement: The neutral contract keeps Risk producer and decision consumer interchangeable

The gate value produced by the Risk / Compliance analyzer and the Risk state consumed by the scoring decision engine SHALL be the identical `RiskGateState` type from the neutral contract, so analyzer output is directly consumable by the decision engine without conversion or input errors and with unchanged gate precedence.

#### Scenario: Analyzer output is consumed directly by the decision engine

- **WHEN** a real `analyze_risk_compliance` result's `risk_gate` is passed directly as the Risk input of `evaluate_scoring_decision`
- **THEN** the engine accepts it without `RISK_INPUT_ERROR`: `CLEAR` remains directly consumable, `REVIEW_REQUIRED` retains the existing `RISK REVIEW` precedence, and `FATAL` retains the existing `NO-GO` precedence
