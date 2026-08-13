# Scoring Policy

Score only after evidence collection and both gate evaluations. Each dimension score must identify supporting evidence and confidence; unsupported intuitive scoring is invalid. Gates in [gates.md](gates.md) remain independent of the weighted score.

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

Each dimension may change by at most `±5 percentage points` when product characteristics justify it. After adjustment, `Total Weight = 100%`. Explain every change and do not adjust weights to manufacture a preferred result.

## Core Dimension Thresholds

| Core dimension | Minimum score |
|---|---:|
| Market Demand | 60 |
| Price & Profitability | 60 |
| Pain Points & Differentiation | 55 |
| Competition | 45 |

Check each threshold separately after scoring. Other high scores cannot average away a core shortfall. Explicitly surface any failure; a severe failure prevents an unqualified positive conclusion.

After the Red Team review, revise a score or confidence only when evidence warrants it. Record the initial value, changed value, reason, and evidence IDs.

