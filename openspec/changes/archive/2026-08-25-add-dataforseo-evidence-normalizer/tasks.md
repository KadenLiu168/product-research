## 1. Reconfirm scope, traceability, and baseline

- [x] 1.1 Re-read the ECO-45 proposal, design, both delta specs, `SKILL.md`, existing Evidence/Policy/orchestration contracts, all four DataForSEO finding builders, and ECO-42/ECO-43 fixtures; record a requirement-to-test trace before implementation edits.
- [x] 1.2 Confirm no conflicting active Change or repository guard has appeared, then run the existing research-orchestration, DataForSEO SEARCH, DataForSEO MARKETPLACE, and DataForSEO acquisition-runtime test modules as a fresh pre-change baseline; stop and report any in-scope pre-existing failure.
- [x] 1.3 Define a surgical ECO-45 Apply allowlist limited to the new external normalizer, its focused tests, the narrow `SKILL.md` wording update, and active Change task updates; confirm `product_research/`, provider modules, acquisition runtime, living specs, Linear, archive, commit, and push remain outside Apply edits.

## 2. Write RED construction, supported-operation, and Evidence contracts

- [x] 2.1 Add `tests/test_dataforseo_evidence_normalizer.py` with deterministic helpers that reuse committed ECO-42/ECO-43 fixtures or fixture-derived existing `RawFinding` values for all four supported operations and make no live/runtime transport call.
- [x] 2.2 Add failing construction tests requiring exactly one explicit existing `Tier` and base `Confidence` per exact supported operation; cover missing, extra, duplicate, wrong-type, forged, and caller-mutation cases and prove setup creates an immutable defensive assignment snapshot.
- [x] 2.3 Add failing tests for one-finding/one-existing-Evidence behavior across Google Ads Search Volume, Google Trends Explore, Amazon Bulk Search Volume, and Amazon Products, including exact preservation of the supplied `EvidenceId` and absence of any allocator/UUID/derived-ID surface.
- [x] 2.4 Add failing tests for exact `finding.source`, canonical `finding.observed_at`, `Status("Observed")`, and structural Evidence serialization for every supported operation.

## 3. Write RED factual claim, basis, and provenance contracts

- [x] 3.1 Add failing operation-specific claim tests for keyword metrics, Trends item/type/keywords, Amazon keyword search volume, and Amazon ASIN/listing title; add negative assertions for strong/weak demand, positive/declining trend, high/low competition, opportunity, product judgment, scores, gates, and GO/NO-GO conclusions.
- [x] 3.2 Add failing invariance tests proving changes only to `research_question` or `query_intent` cannot change claim, basis, EvidenceKind, Tier, or base Confidence.
- [x] 3.3 Add failing exact-basis tests proving `Evidence.evidence == RawFinding.content`, with no reserialization, aggregation, ranking interpretation, trend calculation, or semantic rewriting.
- [x] 3.4 Add failing null/missing-metric tests, including `search_volume = null`, proving values remain null/missing in both the exact basis and acquisition metadata and never become zero, estimates, Unknown Evidence, or conclusions.
- [x] 3.5 Add failing metadata tests for the exact `policy`, `research`, and `acquisition` namespace shape; prove task/finding identity and all existing SEARCH/MARKETPLACE provider, operation, endpoint, provider-task, request, result/item ordering, context, rank/reference, and observation provenance survive as JSON-equivalent data.
- [x] 3.6 Add failing nested-container tests proving mechanical frozen-to-ordinary JSON conversion changes no scalar/null/list/map value and creates no mutable alias capable of modifying the original `RawFinding`.

## 4. Write RED kind, temporal, recognition, and failure-boundary contracts

- [x] 4.1 Add failing tests proving `metadata.policy.kind` always equals the exact `task.evidence_kind.value` and is never inferred from operation, URL, title, keyword, ASIN, metrics, finding content, or free-form task text.
- [x] 4.2 Add failing table-driven tests proving `market`, `competition`, `marketplace_price`, `supplier_quotation`, and `voc` receive `source_date` equal to the canonical `observed_at` date.
- [x] 4.3 Add failing tests proving `regulation`, `certification`, `tariff`, `ip_authoritative_record`, and `long_term_industry` fail closed without fabricated `effective_from`, `verified_current_at`, `source_year`, or continuing-relevance justification.
- [x] 4.4 Add failing recognition tests for unsupported operation, non-DataForSEO provider, Source/metadata/content operation contradiction, SEARCH/MARKETPLACE task-family mismatch, finding ownership mismatch, and missing/malformed endpoint, provider-task, request, ordering, or observation provenance.
- [x] 4.5 Add narrowly mutated findings proving duplicated operation and observation representations must agree while unrelated provider-validated metric details are not revalidated by a second response-schema engine.
- [x] 4.6 Add a real `run_research` integration test with deterministic fake acquisition and the real normalizer; prove finding order, orchestration-owned `E001...` allocation, a failed attempted position gap, later-ID preservation, `NORMALIZATION_EXCEPTION`, and independent success retention.
- [x] 4.7 Retain and rerun existing orchestration tests proving structurally invalid normalizer output remains `INVALID_EVIDENCE`; add no new failure reason or conversion path.
- [x] 4.8 Add architecture/static-call tests proving the normalizer is outside `product_research/`, no core module imports it, providers/runtime still stop at RawFinding, and normalizer source neither imports nor invokes Evidence Policy, Evidence Assessment, structured analysis, scoring, gates, Red Team, reporting, persistence, or workflow execution.
- [x] 4.9 Add a network/billing tripwire or equivalent deterministic assertion proving focused and full default tests cannot contact DataForSEO even when credential-like environment variables are present, then run the focused module and retain expected RED evidence before creating the normalizer implementation.

## 5. Implement the minimum external normalizer

- [x] 5.1 Add one root-level `dataforseo_evidence_normalizer.py` module with a minimal factory returning the existing three-argument normalization callable; add no package split, class hierarchy, provider registry, new operation type, Evidence subtype, ID allocator, or runtime bundling.
- [x] 5.2 Validate and defensively freeze the exact four-operation Tier/base-Confidence assignment at construction using only existing `Tier` and `Confidence` contracts.
- [x] 5.3 Implement narrow finding recognition and duplicated-provenance consistency checks for exact provider, operation, Source type, task family/ownership, canonical content observation, provider task, endpoint, request, and operation-specific ordering; leave full response/metric validation in ECO-42/ECO-43.
- [x] 5.4 Implement four closed neutral claim templates over provider-validated observation identity fields and preserve `RawFinding.content` unchanged as the Evidence basis.
- [x] 5.5 Implement mechanical recursive thawing into one acquisition subtree plus exact research identities, exact task-declared policy kind, truthful acquisition-date `source_date`, and fail-closed unsupported temporal declarations.
- [x] 5.6 Construct exactly one existing `Evidence` with the supplied ID, existing Source/time, explicit Tier/base Confidence, and existing `Observed` status; make every focused normalizer and real-orchestration integration test GREEN with the smallest implementation.

## 6. Align documentation and verify the complete contract

- [x] 6.1 Update only the relevant DataForSEO sections of `SKILL.md` to state that configured SEARCH/MARKETPLACE acquisition remains provider-owned and stops at RawFinding, while the separate ECO-45 normalizer can be injected to produce existing Evidence; retain caller-controlled Policy/Assessment/analysis and no automatic provider-backed 16-stage workflow.
- [x] 6.2 Re-read proposal, design, delta specs, implementation, tests, and `SKILL.md`; trace every requirement/scenario to code and independent test evidence and confirm no provider/core/public contract or existing assertion was changed to make ECO-45 pass.
- [x] 6.3 Run `python3 -m unittest -v tests.test_dataforseo_evidence_normalizer` and retain the focused result.
- [x] 6.4 Run `python3 -m unittest -v tests.test_research_orchestration tests.test_dataforseo_search_provider tests.test_dataforseo_marketplace_provider tests.test_dataforseo_acquisition_runtime` and retain scoped compatibility results.
- [x] 6.5 Run `python3 -m unittest discover -s tests` with live access disabled and confirm the complete deterministic default suite passes without credentials, network, browser, or billable provider access.
- [x] 6.6 Run `openspec validate add-dataforseo-evidence-normalizer --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every in-scope finding and rerun affected gates.
- [x] 6.7 Inspect the final diff and requirement-to-implementation-to-test trace for reverse imports, edits under `product_research/`, provider/runtime/schema/API changes, duplicate validation/classification/Evidence/ID frameworks, free-form or payload heuristics, null coercion, fabricated policy facts, analytical conclusions, downstream execution, live-test risk, unrelated edits, or unauthorized Linear/archive/commit/push activity.
