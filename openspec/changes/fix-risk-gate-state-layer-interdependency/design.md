## Context

Current dependency direction:

```
risk_compliance -> scoring_decision (only to obtain RiskGateState)
```

`RiskGateState` is a decision-facing gate contract: `risk_compliance` (domain analysis) produces it and `scoring_decision` (decision engine) consumes it. The canonical definition lives in `scoring_decision.py`, forcing the upstream analysis module to import from the downstream decision engine. This is a reverse dependency, not a literal import cycle (`scoring_decision` does not import `risk_compliance`), but it violates the dependency-direction rule for the analysis / decision boundary in CLAUDE.md and couples the Risk analysis module to the full decision module.

## Goals / Non-Goals

**Goals:**

- Move the canonical definition of `RiskGateState` to a neutral contract module (`risk_gate.py`)
- Ensure `risk_compliance` depends only on the neutral contract
- Ensure `scoring_decision` re-exports the identical class object for backward compatibility
- Preserve the supported public construction and value semantics and the existing `product_research.scoring_decision.RiskGateState` import path (canonical module ownership intentionally moves to `risk_gate`; reflection metadata such as `__module__` changes)

**Non-Goals:**

- Any vocabulary or behavior change to `RiskGateState`
- Any `__module__` reassignment or other reflection / serialization compatibility hack
- Creation of `shared_contracts.py` or other generalization modules
- Modification of `scoring_decision.py` beyond the `RiskGateState` re-export (its own `_ClosedValue` base and other vocabularies stay in place)
- Any change to `risk_compliance.py` except the import
- Unifying the private immutable base classes across the package

## Decisions

1. **Neutral contract module** - `product_research/risk_gate.py` is the sole canonical location. This breaks the reverse dependency without introducing a generalization layer.

2. **Self-contained contract module** - `risk_gate.py` imports standard-library modules only and SHALL NOT import from any `product_research` module; it defines its own private immutable base for `RiskGateState`. This structurally prevents a real import cycle: importing `_ClosedValue` from `scoring_decision` would create one, because `scoring_decision` imports `RiskGateState` from `risk_gate`. `scoring_decision.py` keeps its own `_ClosedValue` for its remaining vocabularies. The duplicated private base is an accepted trade-off consistent with the existing per-cluster bases (`evidence._ConstrainedValue`, `scoring_decision._ClosedValue`).

3. **Re-export pattern** - `scoring_decision.py` re-exports via a plain `from .risk_gate import RiskGateState` import; the import itself guarantees both names refer to the identical class object. Identity is enforced by tests (this repository uses no production asserts) and by the preserved vocabulary tests that access the class through `scoring_decision`.

4. **No Enum** - Retained the existing immutable value-object pattern (private closed-vocabulary base with `_allowed`, not a `str` subclass and not an `Enum`) to avoid any API or behavior difference.

5. **Spec ownership distribution** - The `risk-gate` capability owns the contract itself (canonical location, closed vocabulary, immutable value semantics, single production definition, producer/consumer interchangeability). The re-export identity requirement lives in `scoring-decision-engine` (the capability owning `scoring_decision.py`'s public surface), and the import-direction requirement lives in `risk-compliance-analysis` (the capability owning `risk_compliance.py`), so each living spec records the obligation that governs its own module.

6. **Verification strategy** - Three layers of automated protection replace manual grep acceptance: (a) contract tests in `tests/test_risk_gate.py` pin the exact value semantics (vocabulary, typed construction failures, `.value`, `str`, `repr`, exact-type equality, hashing, full immutability) at the new canonical location; (b) a boundary regression feeds a real `analyze_risk_compliance` result's `risk_gate` directly into `evaluate_scoring_decision` to prove producer-to-consumer compatibility across `CLEAR` / `REVIEW_REQUIRED` / `FATAL` with unchanged precedence; (c) static architecture checks (AST) enforce that `risk_gate.py` imports no `product_research` module, that `risk_compliance.py` imports no `scoring_decision`, and that exactly one `RiskGateState` class definition exists in the production package.

## Risks / Trade-offs

[Reliability] -> Mitigation: All existing tests that construct or inspect `RiskGateState` through `scoring_decision` continue to pass unchanged against the re-exported class; an explicit identity test prevents future drift.

[Base-class duplication] -> Mitigation: `risk_gate.py`'s private base is a small self-contained copy following the existing per-cluster pattern; unifying the bases across the package is deliberately out of scope.

[Future coupling] -> Mitigation: The neutral contract is intentionally minimal and self-contained (standard library only).

## Migration Plan

The canonical definition of `RiskGateState` moves from `product_research.scoring_decision` to `product_research.risk_gate`, so reflection metadata such as `RiskGateState.__module__` changes. The supported import path `product_research.scoring_decision.RiskGateState` remains available through the re-export, the project has no persistence or serialization contract on this value, and no migration action or compatibility hack is required.

## Open Questions

None.
