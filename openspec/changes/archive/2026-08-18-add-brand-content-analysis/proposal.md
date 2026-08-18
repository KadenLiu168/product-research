## Why

Phase 6 currently has no evidence-grounded boundary for evaluating Brand Potential and Content Potential, so ECO-21's five closed analysis aspects cannot produce traceable findings without leaking qualitative interpretation into VOC or scoring. VOC is now complete and can guide callers toward propositions and underlying Evidence IDs, making this the next dependency before Phase 7 initial scoring while preserving `Evidence` as the sole normalized evidence contract.

## What Changes

- Add one deterministic, immutable, read-only Brand / Content analysis capability over caller-supplied material propositions and existing normalized `Evidence`.
- Preserve `BRAND_POTENTIAL` and `CONTENT_POTENTIAL` as explicit dimensions and support exactly `BRAND_PREMIUM`, `STORYTELLING`, `VISUAL_EXPRESSION`, `DEMO_POTENTIAL`, and `UGC_PROPAGATION` as ECO-21 aspects.
- Assess each unique well-formed proposition independently through the existing Evidence Policy and `assess_evidence()` contracts, retaining the complete Assessment, Evidence-ID traceability, and Confidence.
- Map only policy-usable supported Assessments to `SUPPORTED`; map conflict, insufficiency, rejection, staleness, unresolved IDs, malformed Assessment inputs, and all other unsupported states to `UNKNOWN` without optimistic inference.
- Expose deterministic supported, Unknown, and missing aspect coverage without synthetic findings, and reject every occurrence of an exact duplicate proposition key without caller-order winner selection or merge behavior.
- Add focused tests plus the minimum package routing, documentation, and acceptance-scenario alignment required to expose the capability.
- Keep acquisition, Evidence/VOC schema changes, automated proposition generation or text interpretation, numeric scoring, scorecards, recommendations, Risk/Compliance, Red Team, persistence, and generic Structured Analysis abstractions out of scope.

## Capabilities

### New Capabilities

- `brand-content-analysis`: Explicit Brand / Content proposition vocabulary, independent Evidence Assessment mapping, immutable traceable findings, deterministic aspect coverage, duplicate rejection, replay behavior, and fail-closed ownership boundaries.

### Modified Capabilities

None.

## Impact

- Adds a sibling domain module such as `product_research/brand_content.py` and its focused tests.
- Reuses, without changing, `Evidence`, `EvidenceId`, Evidence Policy, `AssessmentContext`, `assess_evidence()`, and `EvidenceAssessmentResult`.
- May minimally update `product_research/__init__.py`, `README.md`, and `tests/scenarios.md` where current project conventions require public routing and capability truth alignment.
- Adds no runtime dependency, provider/network/browser behavior, persistence, scoring behavior, or change to existing Market Demand, Competition, VOC, Supply Chain, Unit Economics, or Scoring contracts.
