## 1. Establish the ECO-16 baseline and traceability map

- [x] 1.1 Re-read all ECO-16 artifacts, living Evidence/Policy/Assessment, research orchestration/adapter, Market Demand, and scoring specs, current production modules, focused tests, `SKILL.md`, `references/methodology.md`, and current acceptance scenarios; map every Competition requirement and scenario to at least one focused test before production edits.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the pre-change baseline and record the exact result; stop and diagnose any existing failure that could invalidate ECO-16 verification.
- [x] 1.3 Inspect `git status --short` and all tracked Competition/Phase 6 references; confirm the implementation allowlist is limited to new `product_research/competition.py`, new `tests/test_competition.py`, and only necessary truth-alignment lines in `tests/scenarios.md`, `SKILL.md`, `references/methodology.md`, or `docs/product-research-skill-spec.md`; preserve unrelated work.
- [x] 1.4 Trace the current call chain proving ECO-13 alone normalizes `RawFinding` and allocates `EvidenceId`, ECO-14 stops at `AcquisitionResult` / `RawFinding`, Policy already supports `EvidenceKind("competition")`, and Assessment already owns generic eligibility/stance/independence/conflict/missing-information/Confidence behavior; if a genuine existing-contract defect would require a spec change, stop for scope review instead of silently editing an existing capability.

## 2. Write focused RED domain-input and sample-result contracts

- [x] 2.1 Add failing tests proving the exact immutable closed vocabularies include `HEAD` / `MIDDLE` / `NEW_ENTRANT` / `LOW_REVIEW`, `POSITIONING` / `DIFFERENTIATION` / `MARKET_STRUCTURE`, `ADEQUATE` / `LIMITED` / `UNKNOWN`, and `SUPPORTED` / `UNKNOWN`, while rejecting aliases, wrong casing, unsupported strings, and non-string values.
- [x] 2.2 Add failing tests proving `CompetitorSample` requires one exact non-empty identity, a non-empty unique tag tuple, one exact non-empty opaque price-band label, and a non-empty unique Evidence-ID tuple; accepted tags and IDs canonicalize deterministically without mutating or extending Evidence.
- [x] 2.3 Add failing tests proving Competition proposition inputs are frozen, preserve an exact dimension/proposition plus existing Evidence relations, independence assignments, missing information, and a material `AssessmentContext`, and do not infer any field from Evidence or source metadata.
- [x] 2.4 Add failing tests proving sample, sample-validation, finding, and aggregate result values are frozen, require tuple-based typed result collections, preserve nested existing Policy/Assessment results, expose the 10–15 sample target, and contain no numeric Competition score, score threshold, weight, or recommendation field.
- [x] 2.5 Add failing tests proving malformed containers/value types and unsupported or incomplete frozen input values reject construction or return structured fail-closed results without fabricated samples, strata, price bands, propositions, or Evidence.

## 3. Write focused RED sample validity and adequacy rules

- [x] 3.1 Add a failing 10–15 sample test proving unique policy-usable competitors spanning `HEAD`, `MIDDLE`, `NEW_ENTRANT`, optional `LOW_REVIEW`, and at least two explicit price bands produce `ADEQUATE` coverage with target minimum 10 and maximum 15.
- [x] 3.2 Add failing boundary tests proving 9 valid samples are retained with `SAMPLE_SIZE_LIMITATION`, 10 and 15 can be adequate, and more than 15 valid samples are all retained without random, first-N, or silent down-sampling.
- [x] 3.3 Add failing permutation tests proving every occurrence of an exact duplicate competitor identity is invalid with `DUPLICATE_COMPETITOR_IDENTITY`, no duplicate occurrence contributes to count/strata/bands, and no first-wins/last-wins behavior depends on caller order.
- [x] 3.4 Add failing tests proving covered and missing strata use fixed `HEAD`, `MIDDLE`, `NEW_ENTRANT`, `LOW_REVIEW` order; absence of any required stratum emits `MISSING_REQUIRED_STRATUM`, while absence of `LOW_REVIEW` alone does not limit an otherwise adequate sample.
- [x] 3.5 Add failing tests proving price bands remain exact opaque caller strings in lexical result order, one distinct valid band emits `INSUFFICIENT_PRICE_BAND_COVERAGE`, and the module applies no numeric or market-specific price boundary.
- [x] 3.6 Add failing tests proving each sample's complete required Evidence set is validated through existing material claim-support Policy: fresh fact-eligible Evidence validates, while stale, unsupported-source, tier/status-ineligible, context-ineligible, malformed, unresolved, or indeterminate Evidence invalidates only that sample and preserves the existing `PolicyValidationResult` and ordered issues.
- [x] 3.7 Add failing tests proving covered strata, covered price bands, valid count, and adequacy derive only from valid samples; policy-rejected or duplicated competitors never inflate any coverage field.

## 4. Write focused RED Competition-finding rules

- [x] 4.1 Add failing tests proving each Positioning, Differentiation, and Market Structure proposition invokes and preserves a separate existing Evidence Assessment, and multiple propositions in one dimension remain separate rather than sharing Evidence, conflicts, or missing-information state.
- [x] 4.2 Add failing tests proving an underlying `SUPPORTED` Assessment with usable IDs yields one `SUPPORTED` Competition finding with identical Confidence and supporting IDs, including High/Medium/Low cases without any Confidence upgrade.
- [x] 4.3 Add failing tests proving policy-eligible contradictory Evidence yields `UNKNOWN`/Low with the complete `CONFLICTED` Assessment and adverse IDs, while policy-excluded adverse Evidence remains traceable without becoming usable support.
- [x] 4.4 Add failing tests proving stale, unsupported, unresolved, missing-citation, claim-support-rejected, or otherwise insufficient Evidence yields `UNKNOWN`/Low and preserves excluded IDs, Policy results, claim-support result, Assessment factors, and declared missing information.
- [x] 4.5 Add failing tests proving incomplete or duplicate proposition relations/independence assignments fail only that proposition through `ASSESSMENT_INPUT_ERROR`, while separately valid propositions remain independently assessable.
- [x] 4.6 Add failing tests proving a duplicate exact `(dimension, proposition)` pair cannot duplicate support or select a caller-order winner and instead triggers the stable collection-level fail-closed behavior.
- [x] 4.7 Add a combined traceability test proving one material finding retains lexically ordered usable supporting, declared adverse, and excluded Evidence IDs plus its unchanged complete existing Assessment.

## 5. Write focused RED replay, immutability, and ownership rules

- [x] 5.1 Add failing replay tests proving equivalent Evidence-index insertion order and permuted sample, proposition, relation, independence, and missing-information order produce equivalent result objects with fixed sample-tag/dimension/limitation/factor order and lexical identity/price-band/Evidence-ID order.
- [x] 5.2 Add a failing immutability test proving analysis leaves every existing Evidence value and Confidence, Evidence index, samples, propositions, relations, independence assignments, missing-information values, contexts, and policy unchanged.
- [x] 5.3 Add failing shared-input tests proving an Evidence-index identity mismatch or malformed shared Policy/context yields `UNKNOWN` sample adequacy, zero valid count, all required strata missing, and no supported finding, while programmer-control `BaseException` values are not swallowed.
- [x] 5.4 Add a failing AST/import/static ownership audit proving the module defines no second `Evidence` schema, provider/network/browser/scraping/retry/cache/async/persistence/clock/random/environment/LLM path, research planning, `RawFinding`, `AcquisitionResult`, `run_research`, normalization, Evidence-ID allocation, numeric Competition score, scoring threshold/weight, recommendation, Red Team, VOC, Supply Chain, Brand, Content, Risk, reporting, or unrelated Phase 6 behavior.

## 6. Implement the minimal Competition boundary

- [x] 6.1 Add only `product_research/competition.py` with the closed constrained-value types, frozen `CompetitorSample` and proposition inputs, frozen per-sample/per-finding/aggregate results, deterministic exact-type validation, and no package export or third-party dependency.
- [x] 6.2 Implement one `analyze_competition(...)` entry point that validates the shared Evidence index/context/policy, detects exact duplicate identities without first-wins behavior, invokes existing `validate_claim_support(...)` once per sample, and preserves each Policy result unchanged.
- [x] 6.3 Derive total/valid counts, the fixed 10–15 target, covered/missing strata, lexical price bands, adequacy, ordered sample limitations, and ordered sample results only from explicit valid sample inputs; retain every supplied sample above 15 and add no price inference or down-sampling.
- [x] 6.4 Invoke `assess_evidence(...)` exactly once per unique material proposition, preserve each returned Assessment unchanged, and map only `SUPPORTED` plus non-empty usable IDs to a supported Competition finding; map conflict, insufficiency, and input error to `UNKNOWN`/Low with stable diagnostics.
- [x] 6.5 Implement narrow structured fail-closed handling so unsafe shared inputs fail both pipelines, sample-local failures affect only sample coverage, proposition-local Assessment failures affect only that finding, and no placeholder Evidence, sample, proposition, score, or recommendation is fabricated.
- [x] 6.6 Make `tests/test_competition.py` GREEN, then simplify only ECO-16 code and remove any new unused import/helper without refactoring adjacent modules or changing generic Policy/Assessment behavior.

## 7. Align capability routing narrowly

- [x] 7.1 Add concise Competition acceptance scenarios to `tests/scenarios.md` covering explicit samples, exact duplicate handling, Policy-usable counting, 10–15 adequacy, required strata, explicit price bands, independent findings, traceability, Unknown behavior, replay, and absence of acquisition/scoring.
- [x] 7.2 Add `product_research/competition.py` to the `SKILL.md` routing table and current implemented-capability statement while retaining concrete provider acquisition, qualitative score generation, other unavailable Phase 6 analysis, Red Team, persistence, reporting, and end-to-end workflow as unavailable.
- [x] 7.3 Update only directly stale current-boundary wording in `references/methodology.md` or `docs/product-research-skill-spec.md`; keep broader sampling examples non-normative and route normative behavior to the production module instead of duplicating algorithms.
- [x] 7.4 Review all touched documentation together to ensure the sole path remains existing Evidence plus explicit Competition inputs → existing Policy/Assessment → Competition result → later score generation, and that ECO-13/ECO-14 ownership is unchanged.

## 8. Verify focused, regression, scope, and OpenSpec gates

- [x] 8.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_competition.py' -v` and trace every ECO-16 delta scenario to fresh focused evidence.
- [x] 8.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove Phase 3 contracts remain unchanged.
- [x] 8.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` separately to prove Phase 5 acquisition, normalization, ID, failure, and routing ownership remains unchanged.
- [x] 8.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_market_demand.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove adjacent deterministic analysis and downstream scoring contracts remain unchanged.
- [x] 8.5 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the complete repository regression gate.
- [x] 8.6 Run `openspec validate add-competition-analysis --strict`, `openspec validate --all --strict`, and `openspec doctor`; do not claim an unsupported Verify artifact or command passed.
- [x] 8.7 Inspect the final diff and independently trace every requirement through implementation and tests for hidden tag/price/dimension inference, duplicate Policy/Assessment logic, partial sample support, first-wins behavior, Confidence upgrade, nondeterminism, acquisition/ID ownership leakage, numeric scoring, recommendation behavior, adjacent refactors, or unrelated changes; resolve every in-scope finding and rerun affected focused and full gates.
