## 1. Setup

- [ ] 1.1 Create the self-contained neutral contract module `product_research/risk_gate.py`: a private immutable base plus the canonical `RiskGateState` with `_allowed = ("CLEAR", "REVIEW_REQUIRED", "FATAL")`; the module imports standard-library modules only and no other `product_research` module
- [ ] 1.2 Add `tests/test_risk_gate.py` covering the closed vocabulary, rejection of unsupported values, immutability, and a static audit that `risk_gate.py` imports no `product_research` module

## 2. Implementation

- [ ] 2.1 In `product_research/scoring_decision.py`: delete the local `RiskGateState` class definition and re-export it via `from .risk_gate import RiskGateState`; keep the existing `_ClosedValue` base and all other vocabularies unchanged
- [ ] 2.2 In `product_research/risk_compliance.py`: replace `from .scoring_decision import RiskGateState` with `from .risk_gate import RiskGateState`; no other change

## 3. Testing & Verification

- [ ] 3.1 Add a compatibility test asserting `scoring_decision.RiskGateState is risk_gate.RiskGateState` and that values constructed through either name are interchangeable
- [ ] 3.2 Update the `tests/test_risk_compliance.py` static import audit: remove `scoring_decision` from the allowed import set and add `risk_gate`, so the audit enforces the new dependency direction
- [ ] 3.3 Run the full test suite (`python3 -m unittest discover -s tests`); verify exactly one `RiskGateState` class definition exists (in `risk_gate.py`) and that both `scoring_decision.py` (re-export) and `risk_compliance.py` import it from `risk_gate`
