## 1. Setup

- [ ] 1.1 Create the self-contained neutral contract module `product_research/risk_gate.py`: a private immutable base plus the canonical `RiskGateState` with `_allowed = ("CLEAR", "REVIEW_REQUIRED", "FATAL")`; the module imports standard-library modules only and no other `product_research` module
- [ ] 1.2 Add `tests/test_risk_gate.py` as the home for the contract, boundary-regression, and static architecture tests below

## 2. Implementation

- [ ] 2.1 In `product_research/scoring_decision.py`: delete the local `RiskGateState` class definition and re-export it via `from .risk_gate import RiskGateState`; keep the existing `_ClosedValue` base and all other vocabularies unchanged; do not reassign `__module__` or apply any other reflection compatibility hack
- [ ] 2.2 In `product_research/risk_compliance.py`: replace `from .scoring_decision import RiskGateState` with `from .risk_gate import RiskGateState`; no other change

## 3. Contract tests (`tests/test_risk_gate.py`)

- [ ] 3.1 Verify the exact vocabulary: `RiskGateState._allowed == ("CLEAR", "REVIEW_REQUIRED", "FATAL")` and all three values are constructible
- [ ] 3.2 Verify typed construction failures without locking exception messages: non-string input raises `TypeError`; unsupported string raises `ValueError`
- [ ] 3.3 Verify `RiskGateState("CLEAR").value == "CLEAR"`
- [ ] 3.4 Verify `str(RiskGateState("CLEAR")) == "CLEAR"`
- [ ] 3.5 Verify `repr` retains the exact pre-move value-object format, e.g. `repr(RiskGateState("CLEAR")) == "RiskGateState('CLEAR')"` (not a dataclass or Enum default representation)
- [ ] 3.6 Verify exact-type equality: equal same-type values compare equal; different values compare unequal; a different-type object holding the same value does not compare equal
- [ ] 3.7 Verify hashing: equal values hash equal and values are usable as set / dict keys
- [ ] 3.8 Verify full immutability: assignment to `_value` or `value`, assignment of a new attribute, and deletion of `_value` all fail
- [ ] 3.9 Verify the re-export identity: `scoring_decision.RiskGateState is risk_gate.RiskGateState`

## 4. Boundary regression

- [ ] 4.1 Feed a real `analyze_risk_compliance(...)` result's `risk_gate` directly into `evaluate_scoring_decision(...)` (reusing existing test fixture patterns; no new integration framework) and verify: no `RISK_INPUT_ERROR` appears; a `CLEAR` gate is directly consumable; a `REVIEW_REQUIRED` gate retains `RISK REVIEW` precedence; a `FATAL` gate retains `NO-GO` precedence

## 5. Static architecture checks

- [ ] 5.1 Add a static test asserting `product_research/risk_gate.py` imports no `product_research` module
- [ ] 5.2 Update the `tests/test_risk_compliance.py` static import audit: remove `scoring_decision` from the allowed import set and add `risk_gate`, so `risk_compliance.py` can no longer import `scoring_decision`
- [ ] 5.3 Add an AST-based static test scanning the production package `product_research/` (not test files) asserting that `class RiskGateState` is defined exactly once, only in `risk_gate.py`

## 6. Verification

- [ ] 6.1 Run `python3 -m unittest tests.test_risk_gate`, `python3 -m unittest tests.test_risk_compliance`, `python3 -m unittest tests.test_scoring_decision`, then `python3 -m unittest discover -s tests`; all pass
