## Context

See `proposal.md` for motivation and `specs/initial-scoring/spec.md` for observable behavior. Current `main` exposes immutable Phase 6 result types for Market Demand, Competition, VOC, Supply Chain, Brand / Content, and Risk & Compliance; a deterministic `UnitEconomicsResult`; and the final `DimensionScore` / `DimensionScores` input accepted by `evaluate_scoring_decision(...)`.

The result contracts already preserve supported versus unknown outcomes, usable/supporting, adverse, and excluded Evidence IDs, nested `EvidenceAssessmentResult` values, Confidence, deterministic ordering, and coverage diagnostics. They deliberately do not contain numeric dimension scores. Conversely, `scoring_decision.py` validates only the shape and range of already-generated scores and deliberately does not read Phase 6 results or Evidence records.

Repository review found one current normalized quantitative signal suitable for a score mapping: Unit Economics Contribution Margin. No living spec or reference defines how that margin becomes `0..100`, and the existing economics policy intentionally keeps Minimum Viability and Dynamic Target thresholds caller-owned. No other Phase 6 result exposes a normalized metric with an authorized numeric rubric, so inventing additional deterministic formulas would exceed current repository facts.

## Goals / Non-Goals

**Goals:**

- Insert one deterministic validation/normalization boundary between structured analysis and the existing score executor.
- Keep Agent/LLM judgment outside `product_research/` while making its result explicit, typed, and independently verifiable.
- Reuse upstream supported-finding traceability rather than re-reading Evidence or rerunning assessment.
- Produce the existing final scorecard type even when every dimension is unresolved.
- Freeze the only v1 quantitative mapping completely, including boundaries, Decimal behavior, and unresolved cases.

**Non-Goals:**

- Define additional quantitative metrics or extract numbers from Phase 6 proposition text.
- Decide whether a proposition is favorable or adverse, or translate rationale text into a score.
- Add score history, provenance for revision events, Red Team behavior, weights, thresholds for GO, labels, or reporting.
- Change Phase 6 coverage, Evidence assessment, Risk aggregation, economics calculation, or scoring-decision behavior.

## Decisions

### 1. Add one sibling deterministic boundary and reuse the final score domain

Apply should add one focused module following the repository's flat `product_research/` convention. Its public evaluation boundary will accept explicit Phase 6 results, an existing Unit Economics result, and explicit qualitative judgments, then return the existing `DimensionScores` directly. Intermediate judgment/input values may be introduced only where needed to validate the boundary; they are not a second final score hierarchy.

This keeps dependency direction one-way:

```text
Phase 6 immutable results ─┐
Agent qualitative inputs ─┼─> deterministic Initial Scoring ─> DimensionScores
UnitEconomicsResult ──────┘                                  └─> scoring decision
```

Initial Scoring may import upstream result classes and the score value objects. Upstream analyzers and the scoring executor must not import Initial Scoring.

Alternatives considered:

- Extend `scoring_decision.py`: rejected because it would make the policy executor generate and validate semantic scoring judgments, contradicting its living spec.
- Add score fields to every Phase 6 result: rejected because analysis intentionally stops at structured findings and this would duplicate scoring policy across modules.
- Create a new final `InitialScorecard`: rejected because `DimensionScores` already expresses concrete and unresolved slots and is the downstream contract.

### 2. Agent judgment is data, not a runtime dependency

The Agent/caller produces one explicit qualitative judgment per dimension it can support. The deterministic boundary treats dimension, Decimal score, Confidence, Evidence IDs, and optional rationale as caller data. It never prompts a model, parses rationale, or infers score direction from proposition text. Apply may choose a small immutable judgment value or an equivalently strict aggregate that matches repository style; the externally required fields and validation behavior are fixed by the spec.

Malformed or duplicate judgments fail closed only for their affected dimension. A malformed judgment collection invalidates all seven qualitative slots, because selecting trustworthy members from an invalid aggregate would create an undocumented partial-input mode. Price & Profitability remains independently derivable from its economics input.

Alternative considered: let the deterministic boundary call an LLM with Phase 6 results. Rejected because it destroys replay stability, introduces provider/network behavior into the core, and makes an external model the hidden owner of score inputs.

### 3. Traceability is validated against a dimension-specific support index

The implementation should build an ephemeral read-only support index from the supplied immutable upstream results. For each qualitative dimension, the index contains only eligible traceable IDs, their source finding/result, and the source Confidence. Eligible traceable IDs are the union of `supporting_ids` and `adverse_ids` on a relevant supported finding/result; `excluded_ids` are never eligible.

The fixed routing is:

| Score dimension | Eligible upstream source |
|---|---|
| Market Demand | one positive `MarketDemandResult` |
| Competition | supported `CompetitionFinding` values from an adequate sample |
| Pain Points & Differentiation | supported `VOCFinding` values and supported Competition findings declared `POSITIONING` or `DIFFERENTIATION` |
| Supply Chain & Fulfillment | supported `SupplyChainFinding` values |
| Brand Potential | supported Brand / Content findings declared `BRAND_POTENTIAL` |
| Content Potential | supported Brand / Content findings declared `CONTENT_POTENTIAL` |
| Risk & Compliance | supported Risk findings from a result with complete required-area coverage |

Every judgment ID must resolve through this dimension-specific index. This is stronger than checking that an ID exists somewhere and prevents an unrelated or excluded record from satisfying the field shape. The implementation does not need an Evidence index because the Phase 6 result already records the assessment-owned identity relationship.

For a cited source, nested assessment conflict/insufficiency or material/critical missing information removes that source from eligibility even where an analyzer's older supported outcome did not enforce the same material-gap rule. This is a downstream scoring sufficiency rule, not a mutation or reassessment of the upstream finding. Uncited results outside the dimension route do not contaminate another score.

Alternative considered: accept any Evidence ID appearing anywhere in a Phase 6 run. Rejected because identity presence cannot prove dimension relevance or policy eligibility.

### 4. Confidence is a ceiling checked over the sources actually cited

For each judgment, resolve all relevant eligible source findings/results intersecting its cited IDs. The cap is the weakest source Confidence under the existing `Low < Medium < High` order. A declared Confidence at or below the cap is preserved exactly. A declared Confidence above it makes the score unresolved.

Rejecting rather than silently lowering is intentional: the Agent's Confidence is part of its explicit claim. Quietly rewriting it would hide that the submitted judgment overstated its support. The canonical unresolved score uses `None`, `Low`, and an empty ID tuple.

Alternative considered: average source Confidence or automatically downgrade the input. Rejected because averaging has no repository policy and automatic repair obscures invalid caller intent.

### 5. Freeze profitability normalization relative to existing policy anchors

The v1 quantitative rubric uses only values already retained by a valid `UnitEconomicsResult`:

```text
raw = 100 * (margin - minimum_threshold)
            / (dynamic_target_threshold - minimum_threshold)
score = min(100, max(0, raw))
```

This maps the caller's existing Minimum Viability boundary to `0` and its Dynamic Target boundary to `100`, with no additional business threshold or score anchor. It does not claim that `0` means unknown: it is the deterministic result for a known margin at or below the supplied minimum. Unknown or structurally unusable economics produce `score=None`.

Before calculation, validate the retained result shape and require: concrete finite calculated margin; both concrete finite thresholds; both retained gate actual margins equal to the Contribution Margin; `dynamic > minimum`; non-`UNRESOLVED` economics outcome; and one non-empty canonical Evidence-ID tuple shared exactly by the result and Contribution Margin. Use a fresh 34-digit `ROUND_HALF_EVEN` Decimal context and no display quantization. Confidence passes through from the Contribution Margin and the shared canonical IDs pass through unchanged.

This boundary does not compare margin to decide either gate outcome, reconstruct economics inputs, or change thresholds. Checking equality among already-retained values only ensures the metric and anchors belong to one coherent result.

Alternatives considered:

- Map `margin * 100` directly: rejected because that would make the existing core threshold of `60` implicitly require a 60% contribution margin and would ignore caller-owned viability policy.
- Add fixed score bands such as 40/60/80: rejected because the repository provides no evidence or policy basis for those constants.
- Score only from `EconomicsOutcome`: rejected because four labels do not preserve metric distance and a gate label alone is insufficient numeric evidence.
- Defer all quantitative scoring: rejected because the current result does provide one reliable metric and explicit policy anchors; the relative mapping can be fully frozen without inventing a new business threshold.

### 6. Partial output is fail-closed by ownership

The evaluator always constructs all eight slots. Each slot is validated independently from its owned inputs. Invalid Market Demand does not erase valid Brand support; invalid Risk does not erase valid economics; a malformed shared Brand / Content result makes only Brand and Content unresolved. This maximizes valid conclusions without converting missing information into assumptions.

All unresolved slots use one canonical representation:

```text
score = None
confidence = Low
evidence_ids = ()
```

This loses invalid-input IDs intentionally: they did not validly support a score. The existing scoring executor will then expose its established incomplete-score behavior.

### 7. Documentation and tests remain aligned with capability ownership

Apply must update `SKILL.md` so Stage 12 routes explicit Agent judgments and quantitative normalization through Initial Scoring, while preserving the statement that the deterministic core cannot generate qualitative judgments or call providers. `references/methodology.md` and `references/scoring-policy.md` should describe the new bridge and its exact quantitative rubric without duplicating lower-level implementation details. `references/gates.md` needs change only if required to clarify that neither dimension score alters gate ownership; no gate semantics change.

Contract-style `unittest` should exercise public values and architecture boundaries. `tests/scenarios.md` should add Agent RED/GREEN cases covering relevant Evidence selection, explicit unresolved withholding, and the Agent-to-deterministic handoff. No new framework or dependency is needed.

## Risks / Trade-offs

- [The relative profitability score is policy-relative, so two callers with different valid economics thresholds can assign different scores to the same margin] → Preserve the thresholds in the supplied Unit Economics result, document the mapping, and treat the score as relative to explicit caller policy rather than a universal market benchmark.
- [A strict `dynamic > minimum` rule leaves equal-threshold economics unscored even though Unit Economics permits equality] → Keep the score unresolved because a zero-width normalization interval has no deterministic position; the economics gates remain valid and unchanged.
- [Requiring adequate Competition sampling can withhold a score when useful findings exist] → Prefer fail-closed core-dimension scoring; callers can improve the existing structured sample rather than bypass its limitation.
- [Source IDs may support several findings with different Confidence values] → Cap by the weakest relevant cited source finding so overlap cannot inflate Confidence.
- [A valid supported finding can still contain material missing information in analyzers that do not currently block it] → Apply the scoring-specific sufficiency check without rewriting upstream outcomes.
- [Returning only `DimensionScores` does not expose detailed rejection diagnostics] → Keep v1 final compatibility minimal and assert deterministic unresolved behavior in tests; Agent-facing rationale remains input-only. Adding a diagnostic wrapper later would be a separate contract change if operationally necessary.

## Migration Plan

1. Add RED contract and Agent scenarios for output shape, routing, traceability, Confidence, rubric boundaries, unresolved behavior, architecture, and downstream compatibility.
2. Add the narrow Initial Scoring module and minimum immutable input boundary needed by those tests, reusing existing domain values.
3. Update Skill and references to route Stage 12 through the new capability while preserving all upstream/downstream ownership.
4. Run focused Initial Scoring and integration tests, relevant upstream regression modules, the full suite, and strict OpenSpec validation.

The change is additive and has no persisted data migration. Rollback removes the new module/tests/documentation routing; existing Phase 6, Unit Economics, and scoring-decision APIs remain unchanged throughout.
