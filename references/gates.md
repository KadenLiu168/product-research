# Gates

Run `Risk Gate` and `Unit Economics Gate` independently of the weighted score. Aggregate scoring cannot override either gate.

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

