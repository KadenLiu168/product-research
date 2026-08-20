# Scoring Policy

Score only after evidence collection and both gate evaluations. Each dimension score must identify supporting evidence and confidence; unsupported intuitive scoring is invalid. Gates in [gates.md](gates.md) remain independent of the weighted score.

For explicit normalized inputs, [product_research/scoring_decision.py](../product_research/scoring_decision.py) owns score-shape validation, caller-supplied weight execution, aggregate calculation, core-threshold evaluation, explicit GO-policy evaluation, and the analytical labels. It does not generate qualitative scores, acquire or reassess Evidence, select Dynamic Weights, or justify a non-zero adjustment; those responsibilities remain upstream.

## Evidence-Grounded Initial Scoring

[product_research/initial_scoring.py](../product_research/initial_scoring.py) is the deterministic bridge from existing Phase 6 results, an existing `UnitEconomicsResult`, and explicit Agent/caller judgments to the existing eight-slot `DimensionScores`. It does not acquire Evidence, read Evidence text, rerun Policy/Assessment/analyzers, call a provider or LLM, calculate weights or aggregates, execute gate precedence, emit decision labels, or perform Red Team revision.

The seven qualitative dimensions have fixed ownership: Market Demand uses a `POSITIVE` Market Demand result; Competition uses `ADEQUATE` Competition findings declared `MARKET_STRUCTURE`; Pain Points & Differentiation uses VOC findings plus Competition findings declared `POSITIONING` or `DIFFERENTIATION`; Supply Chain & Fulfillment uses Supply Chain findings; Brand Potential and Content Potential use matching Brand / Content finding dimensions; Risk & Compliance uses Risk findings only when caller-owned required-area coverage is complete. A judgment is concrete only when every cited ID is in relevant supported or adverse IDs, at least one relevant source is cited, and nested assessment conflict, insufficiency, material/critical missing information, unsupported findings, and excluded IDs do not make the support unresolved. Unrelated uncited gaps do not contaminate another dimension.

The declared judgment Confidence must be at or below the weakest Confidence among all relevant cited sources; it is preserved rather than averaged or automatically downgraded. Invalid, duplicated, malformed, irrelevant, unsupported, or overconfident judgments use the canonical unresolved representation `DimensionScore(score=None, confidence=Low, evidence_ids=())`.

Price & Profitability uses no qualitative fallback. When the retained Contribution Margin and both retained gate thresholds are finite, both retained actual margins equal the Contribution Margin, the economics outcome is not `UNRESOLVED`, the Dynamic Target is strictly greater than Minimum Viability, and the non-empty result-level and Contribution Margin Evidence-ID tuples are equal and canonical, its raw score is:

```text
100 * (Contribution Margin - Minimum Viability)
    / (Dynamic Target - Minimum Viability)
```

The calculation uses a fresh 34-digit `ROUND_HALF_EVEN` Decimal context, clamps known out-of-band values to `0..100`, and applies no implicit quantization. Missing or incoherent values remain unresolved; a known margin mapping to `0` is not the same as unknown. Existing weights, core thresholds, Risk Gate precedence, Unit Economics Gate ownership, and downstream analytical decision policy remain unchanged.

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
