## Why

The shared Evidence model guarantees representational validity but deliberately does not decide whether structurally valid Evidence may support a factual claim. A deterministic, fail-closed policy boundary is now required so stale, unsupported, mis-tiered, status-incompatible, unresolved, or incompletely cited Evidence cannot flow into later confidence, analysis, scoring, gate, or reporting capabilities as factual support.

## What Changes

- Add an Evidence Policy Validation capability above the existing `evidence-data-model`, without changing or duplicating the core Evidence schema.
- Validate registered Source classifications against their allowed Evidence tiers; unknown classifications and tier mismatches fail closed without URL heuristics, LLM inference, or mutation.
- Validate Evidence status against an explicit claim-use context so `Observed`, `Estimated`, `Calculated`, and `Unknown` retain distinct eligibility semantics.
- Validate freshness using explicit `as_of`, Evidence-kind-specific temporal metadata, and deterministic thresholds, distinguishing `ACCEPT_CURRENT`, `CONTEXT_ONLY`, and `REJECT`.
- Validate policy-required metadata, future observations, unsupported Evidence kinds, collection-level ID uniqueness, citation resolution and completeness, referenced Evidence eligibility, and critical-claim Tier 4 restrictions.
- Return structured, machine-readable validation results and stable reason codes rather than booleans or message parsing.
- Keep validation read-only and fail closed on unknown inputs, indeterminate policy results, and validation exceptions.

## Capabilities

### New Capabilities

- `evidence-policy-validation`: Defines deterministic Source/Tier, status/use, freshness, policy-metadata, collection-integrity, citation-completeness, and critical-claim eligibility rules for structurally valid Evidence.

### Modified Capabilities

None. `evidence-data-model` remains policy-neutral and its requirements do not change.

## Scope and Non-goals

This Change determines whether structurally valid Evidence is eligible for a declared use at a declared `as_of`; it does not determine whether source content semantically entails claim text. It excludes research acquisition and adapters, source-independence detection, multi-source conflict resolution, confidence inference or aggregation, research orchestration, analysis, scoring, Risk or Unit Economics Gate decisions, Red Team logic, report generation, persistence, databases, ORM, and LLM-based source classification.

The Change introduces only the smallest contexts and policy values required by `validate_evidence`, `validate_evidence_set`, and `validate_claim_support`. It does not introduce complete Finding, Score, Gate, or Report domain models.

## Impact

- Adds a policy module alongside `product_research/evidence.py`, expected as `product_research/evidence_policy.py`, plus focused standard-library `unittest` coverage.
- Establishes a required upstream eligibility boundary for later confidence/conflict handling, acquisition consumers, analysis, scoring, gates, and reports.
- Uses the existing Evidence `metadata` extension for policy temporal data and does not alter Evidence JSON fields or dependencies.
- Adds new public validation entry points, policy/context types, structured outcomes, and machine-readable reason codes; no existing Evidence API is removed or reinterpreted.
