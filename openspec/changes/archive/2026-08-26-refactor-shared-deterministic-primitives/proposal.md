## Why

The deterministic v1 core now contains several independently verified copies of the same private closed-value, Confidence-ordering, and strict structured-analysis canonicalization logic. Consolidating only proven-equivalent implementations after the core capability sequence reduces maintenance and divergence risk without changing any product capability or observable contract.

## What Changes

- Add one package-private low-level boundary for deterministic primitives that have at least two proven-equivalent consumers, initially the Scoring Decision and Unit Economics closed-value base plus the ordinal relation `Low < Medium < High` where callers use only ordering.
- Add one package-private structured-analysis support boundary for the strict Evidence-ID, relation, independence-assignment, missing-information, tuple, and exact-string behavior proven equivalent across Brand Content, Supply Chain, and Risk Compliance.
- Keep domain vocabularies, decisions, fallbacks, malformed-input behavior, duplicate handling, canonical ordering, immutable values, and fixed Decimal semantics unchanged.
- Preserve explicit negative boundaries: Evidence `_ConstrainedValue`, self-contained `risk_gate.py`, Competition, VOC, and any unproven Market Demand helper remain local.
- Re-confirm repository-wide `_score_is_valid` and `canonical_unresolved` usage during Apply, then remove the unused non-default Red Team branch only if no production or test caller depends on it.
- Add focused equivalence and boundary regressions, establish a pre-change baseline, and compare the complete post-refactor suite without weakening existing contract tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a behavior-preserving internal refactor, so the Change sets `skip_specs: true` rather than inventing a living-spec requirement for code organization.

## Impact

- Expected new private modules: `product_research/_deterministic_primitives.py` and `product_research/_analysis_support.py`.
- Expected migrated consumers: only `product_research/scoring_decision.py`, `product_research/unit_economics.py`, ordinal-only Confidence consumers proven equivalent during Apply, and the strict cluster in `product_research/brand_content.py`, `product_research/supply_chain.py`, and `product_research/risk_compliance.py`.
- Expected Red Team edit: `product_research/red_team_revision.py`, conditional on the required repository-wide no-usage check.
- Focused tests may be added to the existing touched-module suites or one narrow private-primitive test module where direct equivalence coverage is clearer.
- No public export, API, data model, vocabulary, capability, dependency, provider/configuration path, workflow, persistence, report, living spec, or Skill contract changes.
