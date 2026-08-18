# Gates

Run `Risk Gate` and `Unit Economics Gate` independently of the weighted score. Aggregate scoring cannot override either gate.

The deterministic decision boundary consumes only explicit upstream results: `product_research/scoring_decision.py` accepts one `RiskGateState` (`CLEAR`, `REVIEW_REQUIRED`, or `FATAL`) and an existing `UnitEconomicsResult`. It does not perform either research or calculation stage again.

## Risk Gate

Evaluate current authoritative evidence for applicable safety, product liability, customs, intellectual property, patent, trademark, certification, restricted-material, dangerous-goods, transport, and category-specific requirements. Children's products, batteries, liquids, food, cosmetics, medical claims, and similar categories require early gate attention.

### Fatal Risk

Examples include clear illegality, high-probability unavoidable infringement, inability to sell legally, or inability to transport/import normally.

Result: `NO-GO`.

### Material / Unresolved Risk

Examples include unresolved required certification, unconfirmed patent risk, or unconfirmed special regulatory or shipping requirements.

Result: `RISK REVIEW` until current authoritative evidence resolves the issue.

### Normal Risk

Non-critical risks proceed into ordinary analysis and the Risk & Compliance dimension. Do not label a risk fatal merely because evidence is missing; preserve the uncertainty and use `RISK REVIEW` when it is material.

The scoring decision executor receives the resulting decision-facing state directly. Missing or malformed state is fail-closed as `RISK REVIEW`; it does not inspect Evidence text or infer a state from scores.

The deterministic Risk analysis boundary is implemented in [product_research/risk_compliance.py](../product_research/risk_compliance.py): supply caller-declared Risk propositions over existing normalized Evidence plus the caller-owned required-area contract to `analyze_risk_compliance`. It reuses the Evidence Policy and Evidence Assessment boundaries, keeps original Evidence-ID traceability, treats unsupported propositions conservatively as `UNKNOWN`, and derives the decision-facing `RiskGateState` with fixed precedence: supported `FATAL`, then supported `REVIEWABLE`, then material or critical unresolved findings, unsafe inputs, or incomplete required coverage (`REVIEW_REQUIRED`), then `CLEAR`. Applicability stays caller-owned: Risk Areas absent from the required-area contract are not presumed to apply. The module does not acquire evidence, search regulations or IP registers, or infer legal conclusions, and it owns the exact aggregation behavior; do not restate it here.

## Unit Economics Gate

Build the model from traceable inputs:

```text
Selling Price
- Product Cost
- International Shipping
- Fulfillment
- Payment Fees
- Platform Cost
- CAC
- Returns / After-sales Loss
--------------------------------
= Contribution Profit
```

Classify every input as `Observed`, `Estimated`, `Calculated`, or `Unknown`, with source and confidence where feasible. Missing cost or logistics evidence must not become an assumed fact.

Use `基础生存线 + 动态目标值`:

- **基础生存线:** determine whether economics are clearly unsustainable independent of the aggregate score.
- **动态目标值:** assess attractiveness in context of price point, repeat purchase, returns, advertising dependency, shipping cost, risk, and support burden.

No concrete margin threshold is frozen in this phase. Do not invent one. Deterministic Unit Economics execution is implemented in [product_research/unit_economics.py](../product_research/unit_economics.py): supply the eight normalized inputs and an explicit policy with caller-supplied `minimum_viability_margin` and `dynamic_target_margin` to `evaluate_unit_economics`. If critical inputs or a frozen threshold are unavailable, state the gap, keep affected values `Unknown`, and withhold a definitive Unit Economics Gate pass. The module owns the exact arithmetic, Decimal, validation, and threshold-execution behavior; do not restate it here.

After that stage, pass the complete immutable `UnitEconomicsResult` to [product_research/scoring_decision.py](../product_research/scoring_decision.py). The scoring executor reads only its existing `EconomicsOutcome` and retains the result; it does not recalculate margins, rerun either economics gate, or generate economics thresholds.
