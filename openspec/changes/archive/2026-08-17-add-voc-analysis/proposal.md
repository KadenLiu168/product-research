## Why

The repository can acquire and normalize Evidence and can deterministically assess policy eligibility, support, conflict, missing information, and Confidence, but it has no structured boundary for traceable Voice of Customer (VOC) interpretation. ECO-18 is the next Phase 6 capability after Market Demand and Competition and is required before downstream Brand and Content analysis can consume VOC findings without inventing ad-hoc categories, support rules, or customer facts.

## What Changes

- Add a deterministic, immutable, read-only VOC analysis capability above the existing Evidence Policy and Evidence Assessment boundaries.
- Accept explicit material VOC propositions for the closed categories `PURCHASE_MOTIVATION`, `PAIN_POINT`, `COMPLAINT`, `UNMET_NEED`, `USE_CASE`, `PURCHASE_BARRIER`, `CUSTOMER_LANGUAGE`, and `SEGMENT`; do not infer category or proposition meaning from Evidence text or provenance.
- Assess every proposition independently through the existing `assess_evidence()` entry point using explicit Evidence IDs, relations, independence assignments, missing-information inputs, and `AssessmentContext`.
- Return immutable structured findings with `SUPPORTED` or `UNKNOWN`, existing `High` / `Medium` / `Low` Confidence, supporting/adverse/excluded Evidence IDs, the complete existing Assessment result, and stable VOC diagnostics.
- Expose deterministic supported, Unknown, and missing category coverage without fabricating findings for categories that have no proposition.
- Support explicit Complaint prevalence (`COMMON`, `EDGE_CASE`, `UNKNOWN`) and scope (`PRODUCT_SPECIFIC`, `CATEGORY_WIDE`, `UNKNOWN`) with Evidence-ID traceability; leave either axis Unknown unless explicit policy-usable support permits it, and never infer either value from text, metadata, source family, record count, or ordering.
- Reuse existing Policy and Assessment behavior for freshness, source/tier/status eligibility, stance, independence, conflicts, missing information, and Confidence. Stale, rejected, unresolved, malformed, conflicted, insufficient, or otherwise unsupported inputs fail closed to `UNKNOWN` with Low Confidence.
- Preserve the existing Evidence schema and ECO-13/ECO-14 ownership boundaries; exclude acquisition, normalization, automatic clustering, scoring, recommendations, downstream analysis, persistence, reporting, and internal LLM behavior.

## Capabilities

### New Capabilities

- `voc-analysis`: Defines explicit VOC propositions, independent Evidence Assessment, deterministic category coverage, Complaint characterization, complete Evidence-ID traceability, and structured fail-closed VOC findings.

### Modified Capabilities

None. `evidence-data-model`, `evidence-policy-validation`, `evidence-confidence-conflict`, `research-orchestration`, `research-source-adapters`, `market-demand-analysis`, `competition-analysis`, `scoring-decision-engine`, and other living capabilities retain their existing requirements and ownership boundaries.

## Impact

- Apply is expected to add `product_research/voc.py` and focused standard-library `unittest` coverage in `tests/test_voc.py`.
- Apply may make only minimal truth-alignment edits in `tests/scenarios.md`, `SKILL.md`, `references/methodology.md`, or `docs/product-research-skill-spec.md` so callers can discover the capability without implying provider-backed acquisition, automatic clustering, or score generation.
- The module will reuse `Evidence`, `EvidenceId`, and `Confidence`, together with existing Evidence Policy inputs/results and the public Evidence Assessment inputs/result and entry point.
- No existing Evidence or wire schema, generic Policy or Assessment rule, Phase 5 acquisition/normalization boundary, Market Demand or Competition behavior, scoring formula, dependency, provider integration, persistence boundary, or recommendation API is expected to change.
