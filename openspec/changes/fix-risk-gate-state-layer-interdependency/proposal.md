## Why

The domain-analysis module `risk_compliance.py` currently imports `RiskGateState` from the downstream decision engine (`scoring_decision.py`). This reverse dependency violates the architecture-boundary and dependency-direction rules in CLAUDE.md: `RiskGateState` is an upstream gate contract produced by Risk analysis and consumed by the decision engine, yet its canonical definition lives inside the decision module. Moving the definition to a neutral contract module restores the required dependency direction while preserving the supported public construction and value semantics and the existing `product_research.scoring_decision.RiskGateState` import path.

## What Changes

- **New capability**: `risk-gate` - neutral shared contract module for `RiskGateState` (canonical definition, closed vocabulary, immutable value semantics).
- **Modified capability**: `scoring-decision-engine` - `scoring_decision.py` re-exports the identical `RiskGateState` class object from the neutral contract for backward compatibility.
- **Modified capability**: `risk-compliance-analysis` - `risk_compliance.py` imports `RiskGateState` exclusively from the neutral contract and no longer imports from `scoring_decision`.

**BREAKING**: None for supported runtime/API usage. Canonical module ownership intentionally moves to `product_research.risk_gate`, so reflection metadata such as `RiskGateState.__module__` changes; the project has no persistence or serialization contract on this value, and no `__module__` or reflection compatibility hack is introduced.

## Capabilities

### New Capabilities

- **risk-gate**: Neutral domain contract for `RiskGateState` (`product_research/risk_gate.py`).

### Modified Capabilities

- **scoring-decision-engine**: `RiskGateState` is defined in the neutral contract and re-exported through the existing `product_research.scoring_decision` name.
- **risk-compliance-analysis**: `RiskGateState` is acquired exclusively from the neutral contract; the module no longer depends on `scoring_decision`.

## Impact

- Files: `product_research/risk_gate.py` (new), `product_research/scoring_decision.py`, `product_research/risk_compliance.py`, `tests/test_risk_gate.py` (new, including a producer-to-consumer boundary regression), `tests/test_risk_compliance.py`. Existing `tests/test_scoring_decision.py` must keep passing unchanged via the re-export and requires no modification.
- No external APIs, no vocabulary or behavior changes for supported usage, no new third-party dependencies.
- Internal architecture only; `SKILL.md` and `references/` do not pin the definition location and require no changes.
