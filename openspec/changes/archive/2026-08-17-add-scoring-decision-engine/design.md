## Context

See `proposal.md` for motivation and `specs/scoring-decision-engine/spec.md` for observable behavior. Current `main` is a dependency-free Python repository whose production capabilities are imported directly from sibling modules. Phase 3 owns Evidence representation, policy eligibility, and assessment; `product_research/unit_economics.py` owns normalized monetary validation, contribution arithmetic, its two gates, and the closed `EconomicsOutcome` values `UNRESOLVED`, `UNVIABLE`, `BELOW_TARGET`, and `MEETS_TARGET`.

The living documentation freezes eight scoring dimensions, Base Weights of `20/15/20/15/10/8/7/5`, Dynamic Weight limits of `±5` percentage points with a final `100%` total, four core thresholds, independent Risk and Unit Economics gates, and four final analytical labels. It does not freeze an aggregate GO threshold or an operational definition of a severe score-based `NO-GO`. This design therefore executes only caller-owned normalized scores, adjustments, upstream gate states, and decision policy.

## Goals / Non-Goals

**Goals:**

- Add one replay-stable policy executor that cannot acquire or generate any of its semantic inputs.
- Preserve the separation among dimension score validity, weighted aggregation, core thresholds, Risk, Unit Economics, and final label precedence.
- Make every non-GO condition visible through closed reasons and ordered traceability without allowing malformed or missing values to become passing values.
- Follow existing frozen-dataclass, closed-vocabulary, tuple-ordering, local-Decimal-context, and public exception-to-result patterns.

**Non-Goals:**

- Add research, Evidence parsing, eligibility or assessment logic, qualitative score generation, Dynamic Weight selection, Risk analysis, economics calculation, threshold generation, report generation, serialization, persistence, orchestration, or autonomous decisions.
- Change existing Evidence or Unit Economics types, their living specs, or the empty package-level export surface.
- Operationalize the documentary phrase “severe” into a new score-driven `NO-GO`, or invent an aggregate GO threshold.

## Decisions

### 1. Add one sibling `scoring_decision.py` policy executor

Apply will add `product_research/scoring_decision.py` with one-way dependencies on existing public vocabulary:

```text
evidence.py ───────────────┐
                          ├─→ scoring_decision.py
unit_economics.py ────────┘
```

The module imports `EvidenceId` and `Confidence` from `evidence.py`, plus `UnitEconomicsResult` and `EconomicsOutcome` from `unit_economics.py`. Neither upstream module imports scoring, and no upstream file needs a behavioral change.

Alternative considered: extend `unit_economics.py` with scoring and final labels. Rejected because its living spec explicitly stops before ECO-12 and because aggregate scoring must not own or override economics. A multi-module split into `scoring.py`, `decision_policy.py`, and `gates.py` was also considered; it adds lifecycle and API surface before any component has an independent consumer, so one internally separated module is simpler.

### 2. Use closed frozen values and fixed-field aggregates rather than mappings

The public surface should contain small immutable values in the existing style:

- `Dimension`, `CoreOutcome`, `RiskGateState`, `DecisionLabel`, and `DecisionReason` as closed vocabularies.
- `DimensionScore(score, confidence, evidence_ids)` for one normalized score.
- `DimensionScores` with exactly eight named fields in declared policy order.
- `WeightAdjustments` with exactly eight named Decimal fields and no defaults; an unchanged dimension is explicit `Decimal("0")`.
- `DecisionPolicy(go_threshold)` where `None` is the explicit policy-missing state.
- `DimensionWeight` and `CoreThresholdResult` for ordered machine-readable calculation details.
- `DecisionResult` for the label, valid input view, final weights, aggregate, core results, Risk and economics inputs when valid, diagnostics, failed/unresolved dimensions, and result-level Evidence IDs.

Fixed fields make omission and unsupported dimensions observable at construction and still allow the evaluator to defend against wrong or corrupted aggregates. Tuples preserve deterministic dimension order and immutability. `DimensionScore` sorts Evidence IDs lexically, rejects duplicates within one score, requires at least one ID for a concrete score, and permits an empty tuple for an unresolved score. Result-level IDs are a lexical deduplicated union across every valid score.

Alternative considered: a `dict[Dimension, Decimal]` API. Rejected because mappings create missing/extra/duplicate-key ambiguity and leak caller iteration order into diagnostics. A single generic dictionary result was rejected because it would weaken type and ordering guarantees.

### 3. Represent Unknown score as `None`, without adding or reusing Evidence Status

A dimension score is either a finite exact Decimal in `[0, 100]` or `None`. `None` is the sole unresolved numeric state and never enters arithmetic. Confidence and Evidence IDs remain attached without upgrading them, but the executor does not import `Status` because scoring status is not Evidence observation status and no new score-status lifecycle is required.

Value constructors reject float, string, bool, NaN, infinity, out-of-range score, wrong Confidence/ID types, duplicate IDs, and concrete score without traceability. The public evaluator additionally validates aggregates defensively and converts malformed calls into a structured result. Valid unresolved fields are listed in dimension order, suppress the aggregate, and make their core result unresolved when applicable.

Alternative considered: coerce missing scores to `Decimal("0")`. Rejected because it changes absence into negative evidence. Reusing Evidence `Status("Unknown")` was also considered, but it introduces redundant state combinations such as a concrete score marked Unknown.

### 4. Require a complete caller-supplied adjustment vector

`WeightAdjustments` has one Decimal percentage-point delta for every dimension, even when all deltas are zero. Validation occurs independently of score availability:

1. require exact standard-library finite Decimal values;
2. require every delta in inclusive `[-5, +5]`;
3. compute each final weight as frozen base plus delta in dimension order;
4. require the final sum to equal Decimal `100` exactly.

The engine returns no final-weight tuple and calculates no aggregate when the vector is missing or invalid. It does not infer a zero vector, choose adjustments, or inspect caller rationale. Existing documentation continues to require callers to explain non-zero Dynamic Weights; explanation generation and semantic justification validation remain outside this numerical executor.

Alternative considered: make adjustments optional and silently use Base Weights. Rejected because that makes the evaluator create an adjustment policy that the contract says is caller-owned. A sparse adjustment map was rejected because omitted entries would introduce an implicit zero convention.

### 5. Freeze arithmetic locally and keep threshold stages independent

All score, weight, aggregate, and policy comparisons use standard-library `Decimal`. Like Unit Economics, the module creates a fresh local context with precision `34` and `ROUND_HALF_EVEN`; it does not mutate or inherit the ambient context. In declared dimension order:

```text
weighted contribution = score × final_weight / 100
aggregate = Σ(score × final_weight) / 100
```

No display quantization is part of the domain result. Arithmetic errors become `CALCULATION_ERROR` and suppress the aggregate.

Core thresholds run from validated dimension scores even if weight validation or another non-core score fails. Each core result carries dimension, actual score when valid, frozen threshold, and `PASS` / `FAIL` / `UNRESOLVED`. This allows a caller to see core truth without treating it as part of aggregate arithmetic.

Alternative considered: calculate a partial aggregate over resolved dimensions or renormalize their weights. Rejected because both manufacture a different scoring policy and allow missing inputs to disappear.

### 6. Consume three-state Risk and the complete existing economics result

`RiskGateState` contains only `CLEAR`, `REVIEW_REQUIRED`, and `FATAL`, which are the minimum states required by documented precedence. It contains no Evidence or scan result and the executor never derives it. Missing or malformed Risk becomes `RISK_INPUT_ERROR` and follows the review-required precedence branch.

The evaluator accepts a concrete existing `UnitEconomicsResult`, retains it in the decision result, and reads only its validated `EconomicsOutcome`. It does not call `evaluate_unit_economics`, compare margins, or flatten away upstream gate/reason detail. A wrong or corrupted economics value becomes `ECONOMICS_INPUT_ERROR` and behaves as unresolved; a valid outcome maps only to the matching decision reason when it constrains the label.

Alternative considered: accept only an `EconomicsOutcome`. Rejected because the user explicitly requires reuse of the existing result/outcome and retaining the full result preserves upstream traceability without duplication. Accepting raw margins was rejected because it would reimplement ECO-11 policy.

### 7. Keep aggregate GO policy explicit and minimal

`DecisionPolicy` contains only `go_threshold: Optional[Decimal]`. A supplied threshold must be finite, exact Decimal in `[0, 100]`; equality passes. `None` produces `GO_THRESHOLD_MISSING`. The evaluator contains no default and no category-specific policy.

No score-based `NO-GO` threshold is added. Current policy gives exact core minima but no operational severity boundary, so a core failure constrains the result to `CONDITIONAL GO` unless Risk or economics independently triggers `NO-GO`.

Alternative considered: freeze `70` or another common aggregate threshold. Rejected because no normative project rule supports it. Deriving a threshold from weights, Confidence, or Evidence was rejected because ECO-12 is an executor rather than an analysis engine.

### 8. Evaluate all safe diagnostics, then apply one precedence table

The evaluator validates independent branches and accumulates every safely knowable reason before choosing a label. It does not early-return after finding a hard failure:

| Priority | Condition | Label |
|---|---|---|
| 1 | Risk `FATAL` or economics `UNVIABLE` | `NO-GO` |
| 2 | Risk `REVIEW_REQUIRED`, missing, or malformed | `RISK REVIEW` |
| 3 | Any other unresolved/invalid input or policy, economics `BELOW_TARGET` / `UNRESOLVED`, core failure/unresolved, absent aggregate, or aggregate below GO threshold | `CONDITIONAL GO` |
| 4 | Every prerequisite valid and passing | `GO` |

Thus economics `UNVIABLE` plus Risk review returns `NO-GO` while retaining both reasons. A fatal Risk with malformed scoring still returns `NO-GO` and reports the scoring problem. High aggregate never changes a higher-priority gate outcome.

Reasons use the exact spec order as their stable priority. Failed core and unresolved dimension tuples use declared dimension order. Upstream economics reasons remain available inside the retained `UnitEconomicsResult`; the decision layer adds only the mapped decision-facing reason rather than duplicating the economics reason vocabulary.

Alternative considered: short-circuit on the first decisive gate. Rejected because it loses machine-readable unresolved and failure information needed for remediation and replay comparison.

### 9. Keep one fail-closed public entry point

The public function will be:

```text
evaluate_scoring_decision(
    scores,
    weight_adjustments,
    risk_gate,
    unit_economics,
    policy,
) -> DecisionResult
```

Strict constructors remain useful for normalized callers, while the evaluator defensively handles wrong aggregate types, corrupted instances, and ordinary arithmetic exceptions. It always returns one immutable `DecisionResult`; programmer-control exceptions such as `KeyboardInterrupt` and `SystemExit` are not swallowed.

No serialization contract is added because the repository has no ECO-12 wire or persistence consumer. “Machine-readable” is satisfied by closed values, frozen records, and ordered tuples rather than speculative JSON.

## Risks / Trade-offs

- [Requiring eight explicit zero adjustments is verbose] → It makes adjustment ownership and completeness unambiguous and prevents hidden defaults; small test helpers can construct the vector without widening production APIs.
- [A concrete score with at least one Evidence ID does not prove eligibility] → Phase 3 remains responsible for eligibility and assessment; ECO-12 preserves IDs and Confidence but intentionally does not revalidate them.
- [A core failure maps to `CONDITIONAL GO`, not score-based `NO-GO`] → This is conservative relative to the only executable policy available; a future Change can add a new explicit severe-failure rule once a normative threshold exists.
- [Malformed input still yields an analytical label] → Closed reasons, missing aggregates, and preserved unresolved details make the fail-closed nature explicit; only the four existing labels are permitted.
- [The full Unit Economics result couples ECO-12 to its exact public type] → That coupling is intentional reuse; focused integration tests will catch contract drift without copying economics logic.
- [Documentation spans four routing files] → Apply changes only stale capability/routing statements and keeps numerical truth in the living spec and production module rather than duplicating algorithms broadly.

## Migration Plan

1. Add focused RED tests for value contracts, arithmetic, thresholds, precedence, traceability, purity, and malformed public-boundary inputs.
2. Add the isolated module and make the focused suite pass without changing upstream capability behavior.
3. Narrowly update routing documentation to point deterministic scoring and decision execution to the new module while retaining future-stage limitations.
4. Run focused, Phase 3, Unit Economics, full-suite, strict OpenSpec, and scope-diff gates. No data migration, persistence migration, package dependency, or runtime rollout is required.

Rollback consists of removing the new module, focused tests, and its narrow routing/documentation changes; no stored data or existing public contract needs conversion.
