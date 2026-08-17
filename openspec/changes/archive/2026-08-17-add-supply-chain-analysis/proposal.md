## Why

The repository can acquire and normalize Evidence and can deterministically assess policy eligibility, support, conflict, missing information, and Confidence, but it has no structured boundary for supply-chain feasibility and operational-risk facts. ECO-19 is a remaining Phase 6 capability and is now unblocked by the completed Phase 5 acquisition contracts, Unit Economics engine, and existing Market Demand, Competition, and VOC Evidence-consumer patterns.

## What Changes

- Add a deterministic, immutable, read-only Supply Chain analysis capability above the existing Evidence Policy and Evidence Assessment boundaries.
- Accept explicit material supply-chain propositions for the closed dimensions `SUPPLIER_LANDSCAPE`, `MOQ`, `SOURCING_COST`, `CUSTOMIZATION`, `QUALITY`, `WEIGHT_VOLUME`, `TRANSPORTATION`, and `RETURNS_AFTER_SALES`; do not extract, classify, cluster, or infer proposition meaning from Evidence text, metadata, provider, or source family.
- Assess every unique well-formed proposition independently through the existing `assess_evidence()` entry point using explicit Evidence IDs, relations, independence assignments, missing-information inputs, and `AssessmentContext`.
- Return immutable structured findings with `SUPPORTED` or `UNKNOWN`, existing `High` / `Medium` / `Low` Confidence, supporting/adverse/excluded Evidence IDs, the complete existing Assessment result, and stable Supply Chain diagnostics.
- Expose deterministic supported, Unknown, and missing dimension coverage without fabricating findings for dimensions that have no supplied proposition; reject every exact duplicate `(dimension, proposition)` occurrence without first-wins, last-wins, or merge behavior.
- Reuse existing Policy and Assessment behavior for source/tier/status/freshness eligibility, stance, independence, conflicts, missing information, and Confidence, including the existing 90-day `supplier_quotation` freshness rule. Rejected, unresolved, malformed, conflicted, insufficient, or otherwise unsupported inputs fail closed to `UNKNOWN` and cannot yield optimistic operational facts.
- Preserve the existing Evidence schema and Unit Economics ownership boundaries; exclude provider-backed acquisition, scraping, normalization, Evidence-ID allocation, numeric extraction, calculations, scoring, recommendations, final decisions, regulatory Risk classification, persistence, reporting, and internal LLM behavior.

## Capabilities

### New Capabilities

- `supply-chain-analysis`: Defines explicit Supply Chain propositions, independent Evidence Assessment, deterministic eight-dimension coverage, complete Evidence-ID traceability, and structured fail-closed findings over existing normalized Evidence.

### Modified Capabilities

None. `evidence-data-model`, `evidence-policy-validation`, `evidence-confidence-conflict`, `research-orchestration`, `research-source-adapters`, `unit-economics-engine`, `market-demand-analysis`, `competition-analysis`, `voc-analysis`, and downstream capabilities retain their existing requirements and ownership boundaries.

## Impact

- Apply is expected to add `product_research/supply_chain.py` and focused standard-library `unittest` coverage in `tests/test_supply_chain.py`.
- Apply may make only minimal truth-alignment edits in acceptance scenarios and routing/documentation so callers can discover the capability without implying provider-backed supplier acquisition, automatic extraction, calculations, scoring, or regulatory Risk behavior.
- The module will reuse `Evidence`, `EvidenceId`, and `Confidence`, together with existing Evidence Policy inputs/results and the public Evidence Assessment inputs/result and entry point.
- No existing Evidence or wire schema, Policy or Assessment rule, Phase 5 acquisition/normalization boundary, Unit Economics calculation or gate, other Phase 6 module, scoring formula, dependency, provider integration, persistence boundary, reporting contract, or recommendation API is expected to change.
