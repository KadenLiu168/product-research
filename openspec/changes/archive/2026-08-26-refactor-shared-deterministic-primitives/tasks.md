## 1. Establish the baseline and equivalence gates

- [x] 1.1 Record `git status --short`, active OpenSpec changes, `python3 --version`, and the attributable ECO-53 file allowlist before edits; preserve unrelated dirty work and confirm no implementation, living-spec, Skill, provider/configuration, archive, Linear, commit, or push action is in scope.
- [x] 1.2 Run and record the pre-refactor focused baseline for Scoring Decision, Unit Economics, Evidence Assessment, Initial Scoring, Market Demand, Brand Content, Supply Chain, Risk Compliance, Competition, VOC, Evidence data model, Risk Gate, and Red Team; run `python3 -m unittest tests.test_v1_evaluation_suite` and `python3 -m unittest discover -s tests` as the complete baseline.
- [x] 1.3 Build a closed-value equivalence matrix for the two `_ClosedValue` implementations covering accepted/unsupported/non-string inputs, immutability, deletion, exact-type equality, hash, `repr`, and `str`; confirm Evidence UTF-8 behavior and Risk Gate isolation make them explicit non-consumers.
- [x] 1.4 Build a Confidence-use inventory for every `_CONFIDENCE_RANK` caller and compare all nine `Low`/`Medium`/`High` ordered pairs, caller authenticity checks, invalid-value handling, selection direction, and fallback behavior; identify at least two purely ordinal consumers before authorizing a shared comparator and leave Market Demand local unless its individual contract is independently equivalent.
- [x] 1.5 Build a side-by-side Brand Content/Supply Chain/Risk Compliance matrix for exact strings, tuples, Evidence IDs, relations, independence assignments, missing information, and ordered IDs, including valid, malformed, duplicate, lexical-order, return-type, and exception behavior; separately record the Competition and VOC semantic differences that prohibit cluster migration.
- [x] 1.6 Search the complete repository for `_score_is_valid` and `canonical_unresolved`, record every production and test call site, and confirm the current non-default Red Team branch has no dependent caller before planning its removal.

## 2. Add pre-refactor characterization coverage

- [x] 2.1 Add the minimum focused closed-value equivalence tests against Scoring Decision and Unit Economics subclasses for valid values, unsupported values, non-string values, assignment/deletion immutability, exact-type equality, hash, `repr`, and `str`.
- [x] 2.2 Add exhaustive Confidence-ordering coverage for all nine pairs plus unchanged Unit Economics weakest-confidence, Evidence Assessment ceiling/selection, and Initial Scoring ceiling results for every consumer approved by task 1.4; assert caller-specific invalid/fallback behavior remains local.
- [x] 2.3 Add strict structured-analysis characterization for lexical Evidence-ID canonicalization, duplicate Evidence IDs, relations, independence assignments, missing-information keys, malformed member/container types, exact UTF-8 strings, and immutable tuple ordering across Brand Content, Supply Chain, and Risk Compliance.
- [x] 2.4 Add negative-boundary regressions proving Competition and VOC retain their special duplicate behavior, Evidence `_ConstrainedValue` retains UTF-8 encodability validation, `risk_gate.py` remains package-internal-import-free, and no new private primitive is exported from `product_research.__init__`.
- [x] 2.5 Add Red Team coverage proving canonical unresolved scores remain accepted, noncanonical unresolved proposal shapes remain rejected, and public revision behavior does not rely on the non-default private branch.
- [x] 2.6 Run the new and existing focused tests before production edits; require the consumer-level characterization to pass against the duplicated baseline, and fix only fixture/test defects if a case does not describe current authoritative behavior.

## 3. Consolidate low-level deterministic primitives

- [x] 3.1 Add only `product_research/_deterministic_primitives.py` with the exact shared closed-value base and, only if task 1.4 proved at least two equivalent consumers, one private Confidence comparison/selection primitive expressing `Low < Medium < High` without exposing numeric rank, weight, score, mutable state, or non-stdlib dependencies.
- [x] 3.2 Replace the duplicate `_ClosedValue` definitions in `product_research/scoring_decision.py` and `product_research/unit_economics.py` with the private shared base while leaving all subclasses, vocabularies, imports, public locations, and Decimal constants/call paths unchanged.
- [x] 3.3 Migrate only the ordinal-only Confidence consumers approved by task 1.4; retain each caller's validation, constructor, return values, and fail-closed fallback locally, and leave every unproven caller unchanged.
- [x] 3.4 Run the primitive, Scoring Decision, Unit Economics, Evidence Assessment, Initial Scoring, and any other actually migrated Confidence-consumer suites; verify all nine pair results and closed-value observations are identical to baseline.
- [x] 3.5 Inspect imports and `product_research.__init__` to confirm the new module is private, stdlib-only, unexported, and introduces no dependency from Evidence, Risk Gate, or a lower layer back to a consumer.

## 4. Consolidate strict structured-analysis support

- [x] 4.1 Add only `product_research/_analysis_support.py` with the helpers that passed task 1.5, importing only the minimum existing Evidence/Evidence Assessment types needed for exact validation, canonical sorting, and duplicate rejection.
- [x] 4.2 Migrate the proven-equivalent helper call sites in `product_research/brand_content.py`, `product_research/supply_chain.py`, and `product_research/risk_compliance.py`; keep domain-specific ordering, proposition keys, findings, diagnostics, aggregation, and policies local.
- [x] 4.3 Do not edit Competition or VOC and do not add configurable flags to encode their differences; leave any candidate helper local if migration would alter valid, malformed, duplicate, ordering, or exception behavior in one consumer.
- [x] 4.4 Run `python3 -m unittest tests.test_brand_content tests.test_supply_chain tests.test_risk_compliance tests.test_competition tests.test_voc`; verify strict-cluster outputs and negative-boundary duplicate semantics match baseline.
- [x] 4.5 Confirm `evidence.py` and `evidence_assessment.py` do not import `_analysis_support`, no cycle/reverse dependency exists, stored results remain tuples in canonical order, and only imports/helpers made unused by ECO-53 were removed.

## 5. Remove the Red Team dead branch conditionally

- [x] 5.1 Immediately before editing, repeat the full repository-wide `_score_is_valid` and `canonical_unresolved` search; if any non-default or direct private-helper dependency now exists, stop and surface the scope conflict without changing that caller or adding compatibility machinery.
- [x] 5.2 If task 5.1 confirms no dependency, remove only the `canonical_unresolved` parameter and non-default branch from `_score_is_valid`, retaining canonical unresolved validation requiring `score is None`, Low Confidence, and empty Evidence IDs.
- [x] 5.3 Run `python3 -m unittest tests.test_red_team_revision` and confirm canonical unresolved scores, noncanonical unresolved rejection, accepted revisions, authorization, history, and failure isolation remain unchanged.

## 6. Verify complete behavior preservation and scope

- [x] 6.1 Run the focused suites for every touched module plus Evidence data model, Risk Gate, Competition, and VOC negative boundaries; compare results with the recorded baseline and investigate any changed output, exception, ordering, hash, or immutability behavior before proceeding.
- [x] 6.2 Run `python3 -m unittest tests.test_v1_evaluation_suite` and record the result.
- [x] 6.3 Run `python3 -m unittest discover -s tests` under Python 3.11+ and require no new failure relative to baseline.
- [x] 6.4 Run `openspec doctor`, `openspec validate refactor-shared-deterministic-primitives --strict`, `openspec validate --all --strict`, and `git diff --check`; record the actual results.
- [x] 6.5 Inspect the final dependency graph, public imports, and diff to confirm Evidence UTF-8 semantics, Risk Gate self-containment, Confidence ordinal-only semantics, Decimal configuration/arithmetic, public APIs/vocabularies, strict Brand/Supply/Risk behavior, Competition/VOC behavior, and acquisition/provider/DataForSEO/config/workflow/report/persistence boundaries are unchanged.
- [x] 6.6 Inspect `git status --short` and an explicit ECO-53 diff allowlist; verify every changed line traces to this Change, unrelated work is preserved, and no living spec, Skill, archive, Linear, commit, or push action occurred.
