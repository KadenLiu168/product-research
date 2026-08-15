## Context

See [proposal.md](proposal.md) for motivation. The repository has two implemented, archived boundaries:

- `product_research/evidence.py` owns immutable Evidence representation, constrained values, and deterministic serialization. It explicitly forbids confidence calculation and conflict or independence inference.
- `product_research/evidence_policy.py` owns exact Source/Tier, status/use, freshness, policy-metadata, citation, and temporal eligibility. Its public `validate_evidence_set`, `validate_evidence`, and `validate_claim_support` functions return immutable results with stable reason codes and fail-closed behavior.

The policy result has two orthogonal dimensions: `outcome` (`ACCEPT_CURRENT`, `CONTEXT_ONLY`, or `REJECT`) and `fact_eligible`. Assessment must preserve both. In particular, `CONTEXT_ONLY` can be fact eligible for a declared historical or context scope, while rejected current Evidence must remain visible even when it is adverse.

The implementation remains dependency-free Python using the repository's existing frozen dataclass and constrained-value style. The new module is a sibling layer, not an extension of either upstream module.

## Goals / Non-Goals

**Goals:**

- Provide one deterministic public assessment operation for a proposition and an explicitly selected Evidence collection.
- Keep eligibility owned by the existing policy functions while retaining record-level and claim-support diagnostics.
- Make every semantic stance, underlying-source grouping, minimum independence requirement, and missing-information severity caller-supplied.
- Produce immutable, directly inspectable results whose ordering never depends on input container order.
- Make `High` possible only when no applicable ceiling remains, without numeric scoring.

**Non-Goals:**

- Generalize the Evidence wire model or introduce serialization for assessment inputs/results.
- Infer semantic relationships, underlying sources, methodology quality, directness, reputation, or research completeness.
- Resolve conflicts, choose a winning source, or create a `RESOLVED` state.
- Implement acquisition, persistence, orchestration, analysis, scoring, gates, Red Team automation, reports, or commercial decisions.

## Decisions

### 1. Add a sibling `evidence_assessment.py` module

The module will import public Evidence and Evidence Policy values and functions but neither upstream module will import assessment. The dependency direction remains:

```text
evidence.py
    ↓
evidence_policy.py
    ↓
evidence_assessment.py
```

This avoids widening the stable Evidence wire schema or turning eligibility validation into an aggregation engine. Modifying `evidence.py` or `evidence_policy.py` is not planned; an Apply change may touch the latter only if a focused RED test proves that a very small reusable public API gap prevents correct reuse.

Alternative considered: add conflict fields to Evidence or extend policy results with assessment state. Rejected because both make a single record depend on collection context and violate the archived ownership boundaries.

### 2. Use small immutable explicit input values

The assessment module will define closed values for `Stance`, `MissingSeverity`, `AssessmentOutcome`, `ConflictState`, and `AssessmentFactor`, plus frozen values with strict construction:

```python
EvidenceRelation(evidence_id, stance)
IndependenceAssignment(evidence_id, group_id)  # group_id=None means explicitly unknown
MissingInformation(key, severity)
AssessmentContext(validation_context, minimum_independent_sources)
```

`minimum_independent_sources` is an explicit positive integer. Callers use `1` for a claim where one canonical authoritative source is sufficient and `2` where cross-validation is required. There is no hidden default and no claim-kind heuristic.

Every requested ID must have exactly one relation and one independence assignment. Extra, missing, duplicate, or unresolved assignments are input errors. An unknown group is a valid explicit state, not a missing assignment, and never contributes to the group count.

Alternative considered: derive stance from Evidence free text and independence from Source identity. Rejected because neither representation contains enough semantic provenance for deterministic inference.

### 3. Preserve policy evaluation at both record and claim-support levels

After strict input resolution, assessment will:

1. Call `validate_evidence_set` on the resolved requested Evidence values to retain the existing collection-integrity contract.
2. Call `validate_evidence` once per requested ID in lexical order and retain each `PolicyValidationResult` unchanged.
3. Identify individually fact-eligible supporting IDs, then call `validate_claim_support` on only that set. This preserves material-citation and critical Tier-4 restrictions without allowing an intentionally retained stale contradiction to reject otherwise eligible support.

`current_accepted_ids` comes from `ACCEPT_CURRENT`; `context_only_ids` comes from `CONTEXT_ONLY`; and individual `fact_eligible` controls whether a record can participate for the declared temporal scope. Supporting Evidence also must pass the claim-support check before it enters `usable_ids`. Individually eligible contradictions, neutral records, and unknown-stance records do not use the support-only citation gate, because they are not asserted as citations supporting the proposition.

The result retains:

```python
EvidenceAssessmentResult(
    outcome,
    confidence,
    conflict_state,
    source_count,
    independent_source_count,
    supporting_ids,
    contradicting_ids,
    neutral_ids,
    unknown_ids,
    current_accepted_ids,
    context_only_ids,
    usable_ids,
    excluded_ids,
    policy_results,
    claim_support_result,
    missing_information,
    factors,
)
```

The stance collections classify every safely resolved requested ID regardless of eligibility, so an ID may intentionally appear in both `contradicting_ids` and `excluded_ids`. `source_count` is the count of unique resolved requested records. `independent_source_count` counts distinct known groups among usable supporting Evidence only, because neutral, contrary, excluded, and unknown-group records cannot establish independent support for the proposition.

Alternative considered: call `validate_claim_support` once with every requested ID. Rejected because that function correctly assumes all supplied IDs are asserted citations; passing a stale adverse record would turn preservation of contradiction into rejection of fresh support.

### 4. Determine conflict and outcome from usable explicit stances

After policy processing:

- usable support and usable contradiction → `PRESENT`, `CONFLICTED`;
- usable support and no usable contradiction → `NONE`, `SUPPORTED`;
- no usable support → `NONE`, `INSUFFICIENT`.

Excluded contradictions remain adverse Evidence but do not create eligible conflict. A collection containing only contradictions is insufficient support for the assessed proposition rather than a new `CONTRADICTED` outcome; this keeps the first version to the requested three outcomes and does not pretend to prove the inverse proposition.

Alternative considered: implement a conflict graph or `RESOLVED` / `CONTRADICTED` outcomes. Rejected because choosing propositions, edges, or winners requires semantic analysis not present in the inputs.

### 5. Apply a fixed table of Confidence ceilings

The implementation starts from `Confidence("High")`, evaluates every rule, records every applicable factor, and returns the strictest cap using a fixed ordinal internal mapping only for `High > Medium > Low`. This mapping selects among the existing vocabulary; it is not a numeric score, weight, or business metric.

| Factor | Condition | Maximum Confidence |
|---|---|---|
| `ASSESSMENT_INPUT_ERROR` | Public input or evaluation is indeterminate | `Low` |
| `NO_USABLE_SUPPORT` | Outcome is `INSUFFICIENT` | `Low` |
| `CONFLICTING_EVIDENCE` | Usable support and contradiction coexist | `Low` |
| `CRITICAL_INFORMATION_MISSING` | Any explicit `CRITICAL` missing item | `Low` |
| `MATERIAL_INFORMATION_MISSING` | Any explicit `MATERIAL` missing item | `Low` |
| `ONLY_LOW_TIER_SUPPORT` | All usable support is `Tier 4` | `Low` |
| `LOW_BASE_CONFIDENCE` | Strongest usable supporting Evidence Confidence is `Low` | `Low` |
| `INDEPENDENCE_UNKNOWN` | Any usable support has unknown independence | `Medium` |
| `INSUFFICIENT_INDEPENDENT_SOURCES` | Known supporting groups are below the explicit minimum | `Medium` |
| `UNKNOWN_RELATIONSHIP` | Any policy-usable Evidence has stance `UNKNOWN` | `Medium` |
| `MEDIUM_BASE_CONFIDENCE` | No usable support is `High`, but at least one is `Medium` | `Medium` |

Factors are emitted in the table's fixed order with duplicates removed. Missing information remains fully present in key order even where multiple entries produce one factor. `NON_MATERIAL` entries are visible but impose no ceiling. `NEUTRAL` records are visible but do not satisfy support, create conflict, or impose an automatic ceiling.

Using the strongest supporting Evidence Confidence as a ceiling is deliberately narrow: it prevents a collection of only Medium or Low records from being upgraded, while not allowing one weak supplemental record to erase otherwise strong independent support. Conflict and missing-information rules still cap the complete assessment independently.

Alternative considered: points, averages, tier weights, or majority voting. Rejected because their thresholds would be arbitrary, could hide minority adverse Evidence, and would cross into later scoring.

### 6. Normalize output ordering, never semantic inputs

All ID collections and per-record results will be ordered by lexical `EvidenceId.value`; missing information by key; factors by their declared priority; and nested policy issues remain in the order produced by Evidence Policy. Input list or mapping order has no effect. Equal group strings establish equality only; group names are opaque and do not affect ordering or quality.

The public function shape is:

```python
assess_evidence(
    evidence_ids,
    evidence_index,
    relations,
    independence,
    missing_information,
    context,
    policy,
)
```

No system clock, network, random value, provider heuristic, or text comparison participates.

### 7. Return one minimal fail-closed result on invalid assessment input

Boundary validation rejects wrong types, duplicate requested IDs, index-key mismatch, unknown IDs, invalid assignment coverage, duplicate missing keys, invalid context/policy, and unexpected exceptions. The public function catches them and returns `INSUFFICIENT`, `Low`, and `ASSESSMENT_INPUT_ERROR`. It preserves safely completed per-record classifications and policy diagnostics when they exist, but never fabricates placeholders for unknown Evidence.

This follows the policy module's structured fail-closed style. It does not expose exceptions as a second public result mode and does not silently drop malformed inputs.

Alternative considered: raise construction or aggregation exceptions directly. Rejected because the acceptance contract requires indeterminate public assessment to fail closed rather than leave downstream callers free to treat absence of a result as confidence.

## Risks / Trade-offs

- [Explicit stance can be wrong] → Keep producer ownership visible; assessment guarantees deterministic handling, not semantic truth, and never claims to verify entailment.
- [Group identities can falsely imply independence] → Require explicit underlying-source groups, treat unknown as zero independent support, and document that provider/domain values are not substitutes.
- [Excluded contradiction does not set `PRESENT`] → Preserve it in both contradiction and exclusion outputs with policy reasons; reserve `PRESENT` for conflict relevant to the declared factual scope.
- [Strongest-support ceiling can overlook a weak supplemental source] → Conflict, missing, tier, independence, and unknown-relationship ceilings remain independent; methodology-weighted quality is deferred until structured inputs exist.
- [Fail-closed partial diagnostics may vary by failure point] → Validate container shape and assignment coverage before policy evaluation, then normalize any diagnostics retained after evaluation.

## Migration Plan

1. Add focused RED scenarios and unit tests for the complete assessment contract.
2. Add `product_research/evidence_assessment.py` without modifying Evidence serialization.
3. Narrowly route the Skill and Evidence policy reference to the new third layer.
4. Run focused assessment tests, the unchanged Evidence model and policy suites, the full test suite, and strict OpenSpec validation.

Rollback removes the new module, focused tests, scenario additions, narrow documentation routes, and this unarchived Change. No persisted data or Evidence wire migration exists.
