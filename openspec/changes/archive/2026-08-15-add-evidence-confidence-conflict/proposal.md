## Why

The shared Evidence model and Evidence Policy validator define representation and factual eligibility, but they deliberately do not assess whether a policy-valid collection is independent, internally consistent, materially incomplete, or strong enough for a claim-level Confidence. A deterministic assessment boundary is now required so later analysis cannot manufacture confidence from duplicated sources, omit adverse Evidence, or collapse conflict and insufficiency into an unexplained `Low` value.

## What Changes

- Add a separate, read-only Evidence Assessment capability above `evidence-data-model` and `evidence-policy-validation`, without changing either existing contract or the Evidence wire schema.
- Require explicit per-Evidence proposition stance (`SUPPORTS`, `CONTRADICTS`, `NEUTRAL`, or `UNKNOWN`) and explicit source-independence identity; do not infer either from claim text, provider, URL, domain, or LLM output.
- Reuse existing Evidence Policy validation for collection integrity and per-record eligibility, while preserving every requested Evidence ID, validation outcome, policy reason code, and adverse record in the assessment result.
- Separate policy-eligible, context-only, and rejected Evidence while retaining supporting, contradicting, neutral, and unknown relationships independently of eligibility.
- Return closed claim-level outcomes (`SUPPORTED`, `CONFLICTED`, or `INSUFFICIENT`), claim-level `High` / `Medium` / `Low` Confidence, conflict state, deterministic source counts, missing-information details, and ordered machine-readable factors.
- Apply explainable Confidence ceilings rather than numeric weights: no usable support, eligible conflict, Tier-4-only usable Evidence, material or critical missing information, insufficient or unknown independence, and uniformly Low supporting Evidence deterministically restrict Confidence.
- Fail closed on malformed, duplicate, unresolved, incomplete, or indeterminate assessment inputs without mutating Evidence or overwriting `Evidence.confidence`.

## Capabilities

### New Capabilities

- `evidence-confidence-conflict`: Defines deterministic multi-source consistency, explicit independence, missing-information, conflict-preservation, claim outcome, and claim-level Confidence assessment for Evidence evaluated through the existing policy boundary.

### Modified Capabilities

None. `evidence-data-model` remains representation-only, and `evidence-policy-validation` remains eligibility-only.

## Impact

- Adds a sibling assessment module expected at `product_research/evidence_assessment.py` and focused standard-library unit tests at `tests/test_evidence_assessment.py`.
- Narrowly updates `tests/scenarios.md`, `references/evidence-policy.md`, and `SKILL.md` to route consumers through the new assessment boundary without duplicating its rules.
- Reuses public values and entry points from `product_research/evidence.py` and `product_research/evidence_policy.py`; no existing API, Evidence field, serialization format, dependency, persistence layer, scoring formula, gate, or commercial decision rule changes.
