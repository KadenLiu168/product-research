## 1. Reconfirm Scope and Write Focused RED Regressions

- [x] 1.1 Re-read this Change, the current `dataforseo-evidence-normalizer` and `dataforseo-marketplace-provider` living specs, the ECO-43/ECO-45 implementations and focused tests, and active Change status; confirm the mismatch still exists and keep the Apply edit allowlist to `dataforseo_evidence_normalizer.py`, `tests/test_dataforseo_evidence_normalizer.py`, and this task checklist.
- [x] 1.2 Add an offline provider-to-normalizer regression using the existing Amazon Products fixture with `rank_absolute = None`; assert ECO-43 successfully produces matching null `observation.rank_absolute` and `metadata.provider_rank`, then assert normalization succeeds with exact factual content, both acquisition nulls, and existing `Status("Observed")`.
- [x] 1.3 Retain explicit coverage that the existing provider-produced integer rank normalizes unchanged and add fail-closed cases for at least one contradictory pair, missing `metadata.provider_rank`, and missing `metadata.observation.rank_absolute`; keep canonical content consistent with each intentionally mutated observation so each test reaches the intended rank boundary.
- [x] 1.4 Add a narrow ownership regression proving matching rank provenance is not subjected to a normalizer-owned integer/type schema rule, while retaining and rerunning ECO-43 provider coverage that rejects provider-produced invalid `rank_absolute` types before `RawFinding` construction.
- [x] 1.5 Run `python3 -m unittest -v tests.test_dataforseo_evidence_normalizer`, retain the expected RED failure caused by the current integer-only normalizer check, and do not edit implementation before the RED is observed.

## 2. Implement the Minimum Rank-Provenance Repair

- [x] 2.1 In `dataforseo_evidence_normalizer.py`, replace only the marketplace rank type/value lookup check with explicit key-presence checks for both duplicated rank representations followed by exact type-and-value equality; add no rank coercion, default, inference, provider-schema validation, abstraction, or new failure vocabulary.
- [x] 2.2 Run `python3 -m unittest -v tests.test_dataforseo_evidence_normalizer` and make the focused regressions GREEN with no changes to Evidence construction, status, metadata projection, classification, policy, IDs, SEARCH behavior, providers, runtime, or `product_research/`.

## 3. Verify Compatibility and Repository Contracts

- [x] 3.1 Run `python3 -m unittest -v tests.test_research_orchestration tests.test_dataforseo_search_provider tests.test_dataforseo_marketplace_provider tests.test_dataforseo_acquisition_runtime` and confirm orchestration failure semantics, SEARCH/provider/runtime contracts, integer rank behavior, and offline fake transport remain unchanged.
- [x] 3.2 Run `python3 -m unittest discover -s tests` and confirm the complete default suite is deterministic, credential-independent, browser-free, network-free, and unable to incur DataForSEO charges.
- [x] 3.3 Run `openspec validate fix-dataforseo-nullable-marketplace-rank-normalization --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve only findings attributable to this Change and rerun affected gates.

## 4. Audit the Final Change Boundary

- [x] 4.1 Trace every modified requirement scenario and acceptance criterion to the final implementation and focused regression evidence, including null preservation, integer compatibility, both missing-key cases, contradiction failure, provider-owned type validation, `Observed`, and existing `NORMALIZATION_EXCEPTION` behavior.
- [x] 4.2 Inspect the final diff and reject scope expansion: no edits to provider/runtime/core/public APIs, `RawFinding`, `ResearchTask`, `Evidence`, IDs, Tier/Confidence, Policy/Assessment, SEARCH normalization, downstream analysis, Linear, archive state, commits, pushes, or unrelated work; changes outside the intended two implementation/test files and this Change's task progress require explicit justification.
