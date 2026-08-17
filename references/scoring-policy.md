# Scoring Policy

Score only after evidence collection and both gate evaluations. Each dimension score must identify supporting evidence and confidence; unsupported intuitive scoring is invalid. Gates in [gates.md](gates.md) remain independent of the weighted score.

For explicit normalized inputs, [product_research/scoring_decision.py](../product_research/scoring_decision.py) owns score-shape validation, caller-supplied weight execution, aggregate calculation, core-threshold evaluation, explicit GO-policy evaluation, and the analytical labels. It does not generate qualitative scores, acquire or reassess Evidence, select Dynamic Weights, or justify a non-zero adjustment; those responsibilities remain upstream.

## Base Weights

| Dimension | Weight |
|---|---:|
| Market Demand | 20% |
| Competition | 15% |
| Price & Profitability | 20% |
| Pain Points & Differentiation | 15% |
| Supply Chain & Fulfillment | 10% |
| Brand Potential | 8% |
| Content Potential | 7% |
| Risk & Compliance | 5% |
| **Total** | **100%** |

Use deterministic calculation for measurable inputs and weighted arithmetic when an implementation is available. Use evidence-based judgment for qualitative dimensions. Do not pretend a calculation engine exists; if inputs or deterministic calculation capability are unavailable, withhold the affected score or clearly mark it unresolved.

## Dynamic Weight

Each dimension may change by at most `±5 percentage points` when product characteristics justify it. After adjustment, `Total Weight = 100%`. Explain every change and do not adjust weights to manufacture a preferred result. The caller must provide the complete adjustment vector, including explicit zero values; the executor applies it but does not choose or explain it.

## Core Dimension Thresholds

| Core dimension | Minimum score |
|---|---:|
| Market Demand | 60 |
| Price & Profitability | 60 |
| Pain Points & Differentiation | 55 |
| Competition | 45 |

Check each threshold separately after scoring. Other high scores cannot average away a core shortfall. Explicitly surface any failure; the executor preserves a failed or unresolved core dimension and returns at most `CONDITIONAL GO` from that condition. No score-based severe-failure `NO-GO` threshold is defined here.

## Analytical Decision Policy

The aggregate GO threshold is optional but must be supplied explicitly by the caller when a `GO` classification is requested; the executor does not provide a default or derive one from the weights, Evidence, Confidence, or product category. Only complete scoring with passing core thresholds, `RiskGateState.CLEAR`, `EconomicsOutcome.MEETS_TARGET`, and an aggregate meeting that explicit threshold can return `GO`. `RISK REVIEW` and `NO-GO` retain the independent gate precedence described in [gates.md](gates.md). These labels are analytical classifications, not autonomous commercial decisions.

After the Red Team review, revise a score or confidence only when evidence warrants it. Record the initial value, changed value, reason, and evidence IDs.
