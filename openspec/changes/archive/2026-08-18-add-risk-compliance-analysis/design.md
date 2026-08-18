## Context

See `proposal.md` for motivation. The repository already has three relevant boundaries:

- `evidence_policy.py` decides whether a normalized `Evidence` record is eligible for a declared use. Its regulatory branch already requires an official/authoritative registered Source, Tier 1, `effective_from`, and bounded `verified_current_at` for current use.
- `evidence_assessment.py` accepts caller-declared Evidence IDs, stances, independence groups, missing information, and an `AssessmentContext`; it owns policy reuse, conflicts, source sufficiency, and claim-level Confidence.
- Phase 6 modules such as `supply_chain.py` and `brand_content.py` are frozen-dataclass, standard-library-only consumers that create one Assessment per explicit proposition, preserve the full Assessment result, canonicalize output ordering, and fail closed with stable factors.

`scoring_decision.py` already defines the decision-facing `RiskGateState` values and precedence. Risk analysis must produce that existing value, not modify the scoring executor or introduce another gate contract. Phase 5 exposes an injected `REGULATORY_IP` adapter slot but no provider implementation, so this design begins only after normalized Evidence already exists.

## Goals / Non-Goals

**Goals:**

- Add a dedicated Phase 6 Risk / Compliance consumer whose public inputs, findings, coverage, diagnostics, and gate aggregation are immutable and deterministic.
- Reuse Policy and Assessment as the only owners of evidence eligibility and claim assessment while adding only the Risk-specific interpretation of a supported proposed classification.
- Preserve enough structure to audit every finding and every fail-closed gate transition back to original Evidence IDs and the complete Assessment result.
- Represent official patent/trademark records truthfully through one minimal Evidence Policy kind.

**Non-Goals:**

- No generic Phase 6 framework or refactor of existing consumer modules.
- No acquisition, provider integration, source discovery, legal inference, applicability inference, semantic text interpretation, score generation, recommendation, persistence, reporting, Red Team, or workflow orchestration.
- No change to `RiskGateState`, scoring-decision logic, Supply Chain behavior, or the shared `Evidence` / `Confidence` representations.

## Decisions

### 1. Add one dedicated `risk_compliance.py` module

The module will follow the existing Phase 6 shape and expose closed constrained values plus frozen dataclasses:

- `RiskArea`: `REGULATION`, `CERTIFICATION`, `IP`, `PRODUCT_LIABILITY`, `DANGEROUS_GOODS`, `TRANSPORT_RESTRICTION`.
- `RiskClassification`: `NORMAL`, `REVIEWABLE`, `FATAL`.
- `RiskFindingOutcome`: `SUPPORTED`, `UNKNOWN`.
- `RiskAnalysisDiagnostic`: the ordered vocabulary specified by the delta spec.
- `RiskPropositionInput`: `area`, exact `proposition`, proposed `classification`, canonical Evidence-ID tuple, canonical relation/independence/missing-information tuples, and `assessment_context`.
- `RiskPropositionKey`: `(area, exact proposition)`; classification is deliberately excluded so conflicting proposed classifications cannot evade duplicate detection.
- `RiskFinding`: proposition identity, outcome, optional supported classification, Confidence, usable supporting IDs, adverse IDs, excluded IDs, full `EvidenceAssessmentResult`, and ordered diagnostics.
- `RiskComplianceResult`: required-area coverage, ordered findings, ordered duplicate keys, existing `RiskGateState`, and ordered result diagnostics.

The entry point will be `analyze_risk_compliance(propositions, required_areas, evidence_index, policy)`. Proposition inputs and result values are immutable; the top-level function accepts a tuple of propositions and a tuple of required areas, validates both without repair, and canonicalizes only semantically order-insensitive content.

Alternative considered: extend `scoring_decision.py`. Rejected because scoring consumes a gate and must not acquire or assess Evidence. Alternative considered: create a generic structured-analysis engine. Rejected because current Phase 6 modules intentionally keep domain vocabularies and conservative rules explicit, and ECO-22 does not justify a cross-module abstraction.

### 2. Treat `required_areas` as the sole applicability contract

`required_areas` means “the Risk Areas the caller has determined apply and must be resolved for this run.” It is a duplicate-free tuple of `RiskArea`, canonicalized to the declared vocabulary order. Areas absent from this tuple are not presumed applicable and do not create missing coverage. Supplied findings for a non-required area remain visible and still participate in Fatal/Reviewable precedence because ignoring known supported Risk would be unsafe.

Coverage is calculated only over required areas:

- `supported_required_areas`: at least one non-duplicate proposition in the area has a `SUPPORTED` finding.
- `unresolved_required_areas`: at least one valid unique proposition was supplied, but none is supported.
- `missing_required_areas`: no valid unique proposition was supplied.

These collections are disjoint, exhaustive over `required_areas`, and emitted in `RiskArea` order. A supported area can still contain an additional material Unknown; coverage remains supported, but the separate Unknown gate rule blocks `CLEAR`.

Alternative considered: maintain separate “applicable” and “required” sets. Rejected because ECO-22 defines incomplete applicable coverage as review-blocking; two overlapping sets would introduce an unspecified state with no requested behavior.

### 3. Delegate one Assessment per unique proposition

For every non-duplicate key, call `assess_evidence` exactly once with the proposition's values and the shared Evidence index/Policy. Do not pre-filter Evidence or reproduce Policy logic. If the Assessment call raises or returns an invalid value, substitute the same conservative empty `EvidenceAssessmentResult` pattern used by existing Phase 6 modules, tagged with `ASSESSMENT_INPUT_ERROR`.

A finding is supported only when all are true:

1. Assessment outcome is `SUPPORTED`.
2. `assessment.usable_ids` is non-empty.
3. No `ASSESSMENT_INPUT_ERROR` exists.
4. Neither Assessment factors nor returned missing-information entries identify `MATERIAL` or `CRITICAL` information as missing.

For a supported finding, copy the proposed classification and Assessment Confidence. Otherwise emit `UNKNOWN`, set supported classification to `None`, and use `Confidence("Low")`; retain the full Assessment and trace collections. `supporting_ids` comes from `assessment.usable_ids`, `adverse_ids` from `assessment.contradicting_ids`, and `excluded_ids` from `assessment.excluded_ids`.

Alternative considered: let `AssessmentOutcome("SUPPORTED")` alone publish a classification. Rejected because ECO-22 explicitly requires material/critical missing information to remain Unknown even if other support exists.

### 4. Aggregate directly to the existing `RiskGateState`

After findings and coverage are complete, derive one `RiskGateState` in this order:

1. Any supported `FATAL` → `FATAL`.
2. Else any supported `REVIEWABLE` → `REVIEW_REQUIRED`.
3. Else any unsafe top-level/shared input, duplicate key, Assessment input error, material/critical Unknown proposition, material/critical missing information, missing required area, or unresolved required area → `REVIEW_REQUIRED`.
4. Else → `CLEAR`.

`NORMAL` has meaning only on a supported finding and cannot cancel another condition. An Unknown proposed as Fatal remains Unknown; the absent evidence can require review but cannot produce Fatal. Empty `required_areas` is valid: it means the caller declares no mandatory coverage, but any supplied supported Fatal/Reviewable or material Unknown still controls the gate.

Alternative considered: create a Risk-local gate enum and translate later. Rejected because it creates two decision vocabularies and risks precedence drift.

### 5. Fail closed without first-wins/last-wins behavior

Validate proposition tuples, required-area tuples, shared Evidence index identity, and exact `EvidencePolicy` type before assessment. Malformed shared inputs produce no supported findings and return `REVIEW_REQUIRED` with `RISK_ANALYSIS_INPUT_ERROR`. Duplicate keys are collected and sorted by Risk Area then proposition; every occurrence of that key is omitted from findings, while unrelated unique propositions may still be assessed. The duplicate itself forces review even when a unique Fatal also exists; gate precedence still returns Fatal while retaining the duplicate diagnostic.

Result diagnostics are the ordered de-duplicated union of top-level conditions and finding diagnostics. `ASSESSMENT_NOT_SUPPORTED` alone does not block a non-required, non-material proposition; blocking uses explicit materiality, required coverage, or unsafe-input rules. This keeps diagnostics observable without silently turning every low-impact Unknown into review.

Alternative considered: reject the entire batch on one duplicate. Rejected because it would discard independent traceable findings, including a supported Fatal. Omitting only the ambiguous duplicate key preserves safe information without selecting a winner.

### 6. Add one authoritative IP Evidence kind by reusing the regulatory temporal branch

Add `ip_authoritative_record` to `EvidenceKind._allowed` and to the internal set that currently applies authoritative Tier-1/current-verification validation to regulation, certification, and tariff kinds. Keep the existing `effective_from` and `verified_current_at` metadata shape to make the change minimal and deterministic. For this kind, `effective_from` means the caller-selected authoritative applicable start date for the cited record (for example filing, publication, issue, or registration date); it does not infer legal status or applicability.

This change extends Policy eligibility only. Risk propositions still explicitly declare what the record supports, and Evidence Assessment still owns stance, independence, conflict, and sufficiency.

Alternative considered: reuse `regulation`. Rejected because patent and trademark records are not regulations. Alternative considered: add separate patent and trademark kinds or new per-Risk-area kinds. Rejected as unnecessary for the current policy distinction and contrary to the requested minimal shared-policy change.

### 7. Update routing documentation only after the executable boundary exists

After tests pass, route Risk / Compliance analysis from `SKILL.md` to `product_research/risk_compliance.py`, remove only the now-stale “risk scanning unavailable” claim, and preserve the unavailability of provider-backed research and automatic risk scanning. Update `references/methodology.md`, `references/evidence-policy.md`, and `references/gates.md` to distinguish the deterministic consumer from acquisition and from the scoring executor.

The documentation must say that the module evaluates caller-declared propositions over existing Evidence; it must not claim that the skill searches regulations, patents, trademarks, or automatically infers applicability.

## Risks / Trade-offs

- [A supported Normal proposition could be mistaken for proof that an entire area is universally safe] → Define area coverage as evidence that at least one required proposition resolved, retain every other finding, and let material Unknown propositions independently block `CLEAR`; documentation must state that callers own proposition completeness and applicability.
- [Using `effective_from` for multiple authoritative IP record types is semantically broad] → Document it as an explicit caller-selected authoritative start date, retain exact proposition semantics, and avoid inventing legal-status fields or conclusions.
- [A malformed or forged frozen value could bypass constructor checks] → Revalidate exact public types and invariants at the analysis boundary and return structured review-required diagnostics.
- [Duplicate propositions with different classifications are ambiguous] → Exclude all occurrences of the duplicated key, report it once in deterministic order, and force review rather than choosing a classification.
- [Policy or Assessment behavior may evolve] → Consume only their public result contracts and test reuse/traceability rather than copying their algorithms.
- [Documentation could overstate Phase 5 capability] → Keep provider-backed regulatory/IP acquisition and automatic searches explicitly unavailable after adding the deterministic consumer.

## Migration Plan

1. Add RED tests for the new IP kind and Risk / Compliance public contract.
2. Extend the Evidence Policy kind set and current-authoritative branch, then rerun focused Policy tests.
3. Add `risk_compliance.py` with immutable types, Assessment delegation, finding construction, coverage, and gate aggregation; make focused Risk tests pass.
4. Run existing scoring-decision and adjacent Evidence/Assessment/Supply Chain suites to confirm boundary compatibility.
5. Update routing and references, run static ownership checks, the full repository suite, and strict OpenSpec validation.

Rollback is code-only and additive: remove the new module/tests/docs routing and remove `ip_authoritative_record` from the Policy vocabulary/authoritative set. There is no persistence, migration, provider configuration, or stored-data rewrite.
