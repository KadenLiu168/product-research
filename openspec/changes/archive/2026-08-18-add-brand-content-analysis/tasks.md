## 1. Establish baseline and RED boundary

- [x] 1.1 Re-read `proposal.md`, `design.md`, and `specs/brand-content-analysis/spec.md`; inspect current `evidence.py`, `evidence_policy.py`, `evidence_assessment.py`, `voc.py`, `supply_chain.py`, `scoring_decision.py`, and adjacent tests before editing, and record any contract drift that would require planning review rather than silent adaptation.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` before implementation and retain the baseline result so later regressions are attributable to ECO-21.
- [x] 1.3 Create only `tests/test_brand_content.py` for focused behavior; do not create production code, export changes, generic test frameworks, or adjacent refactors during the RED step.
- [x] 1.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_brand_content.py' -v` and retain the expected RED import/API failure before adding `product_research/brand_content.py`.

## 2. Specify frozen vocabulary and input behavior with tests

- [x] 2.1 Add failing tests for the exact dimension order `BRAND_POTENTIAL`, `CONTENT_POTENTIAL` and exact aspect order `BRAND_PREMIUM`, `STORYTELLING`, `VISUAL_EXPRESSION`, `DEMO_POTENTIAL`, `UGC_PROPAGATION`, including rejection of aliases, wrong case, whitespace variants, and unsupported values.
- [x] 2.2 Add failing tests proving every aspect is representable under explicit caller semantics and that Brand Potential and Content Potential remain distinct typed fields even when exact proposition text and Evidence IDs match.
- [x] 2.3 Add failing frozen-value tests for proposition inputs, full proposition keys, findings, and aggregate results; require exact tuple collections and preserve exact non-empty UTF-8 proposition text without trimming, case folding, parsing, semantic normalization, or dimension/aspect inference.
- [x] 2.4 Add failing constructor and public-boundary tests for malformed containers/types, duplicate Evidence IDs, duplicate relations/independence assignments, invalid closed values, invalid UTF-8 text, and non-material or malformed Assessment contexts.
- [x] 2.5 Add failing tests proving no dimension/aspect compatibility matrix is inferred and the same aspect can remain explicitly associated with either dimension.

## 3. Specify independent Assessment mapping and traceability with tests

- [x] 3.1 Add failing call-count and isolation tests proving `assess_evidence(...)` is invoked exactly once for each unique well-formed `(dimension, aspect, proposition)` and propositions never share Evidence, relations, missing information, independence state, Policy results, context, conflicts, or Confidence.
- [x] 3.2 Add failing supported-path tests proving only Assessment `SUPPORTED` with non-empty policy-usable IDs yields a `SUPPORTED` finding, with Confidence exactly equal to Assessment Confidence and supporting IDs exactly equal to `usable_ids`.
- [x] 3.3 Add failing conflict tests proving policy-usable contradiction yields `UNKNOWN`/Low while preserving the complete `CONFLICTED` Assessment and adverse/contradicting IDs.
- [x] 3.4 Add failing insufficiency tests proving absent support, stale or status-ineligible Evidence, policy rejection, unresolved IDs, incomplete relations/independence assignments, absent usable support, and Assessment input errors yield `UNKNOWN`/Low with complete Policy, claim-support, exclusion, missing-information, and diagnostic traceability.
- [x] 3.5 Add failing tests proving Brand / Content neither relaxes nor tightens existing missing-information behavior: it follows the existing Assessment outcome and Confidence without a domain-specific missing-information gate.
- [x] 3.6 Add failing tests proving a finding retains exact dimension, aspect, proposition, supporting/adverse/excluded IDs, complete unchanged Assessment, and fixed-order Brand / Content diagnostics.

## 4. Specify coverage duplicate replay and immutability with tests

- [x] 4.1 Add failing tests proving `supported_aspects`, `unknown_aspects`, and `missing_aspects` are fixed-order, mutually exclusive, exhaustive over all five aspects, and derived from supplied full keys plus resulting findings without placeholder findings.
- [x] 4.2 Add failing tests for wholly missing, unsupported-only, fully supported, and mixed supported/Unknown aspects, including findings from both dimensions while every finding retains its dimension.
- [x] 4.3 Add failing permutation tests proving every exact duplicate `(dimension, aspect, proposition)` occurrence receives zero Assessment calls, creates no finding, is reported once, keeps the aspect supplied/Unknown unless another unique finding supports it, and never uses first-wins, last-wins, merge, or caller-order behavior.
- [x] 4.4 Add failing tests proving identical proposition text under a different dimension or aspect remains a distinct full key and is independently assessed, while human-paraphrase similarity triggers no semantic deduplication.
- [x] 4.5 Add failing permutation/replay tests over proposition, Evidence-index, relation, independence, and missing-information order; require equivalent ordered coverage, findings, keys, IDs, factors, Confidence, and nested Assessment results.
- [x] 4.6 Add failing deep immutability and input-snapshot tests proving all public values and tuple collections are frozen and supplied Evidence, Policy, contexts, relations, independence assignments, and missing-information entries remain unchanged.

## 5. Specify fail-closed and negative ownership behavior with tests

- [x] 5.1 Add failing public-boundary tests for malformed proposition collections/members, Evidence-index identity mismatch, malformed Policy, unresolved Evidence IDs, incomplete Assessment assignments, unexpected ordinary Assessment errors, and wrong Assessment return types; require structured fail-closed results and no fabricated support.
- [x] 5.2 Add failing tests proving proposition-local Assessment failure affects only that unique finding when shared inputs remain safe, while malformed shared index or Policy prevents every affected proposition from becoming supported.
- [x] 5.3 Add failing tests proving programmer-control `BaseException` signals are not swallowed and the narrow internal fallback is always empty, `INSUFFICIENT`, Low, and marked `ASSESSMENT_INPUT_ERROR`.
- [x] 5.4 Add failing behavioral and type tests proving Evidence text alone creates no proposition/finding and `VOCResult` or `VOCFinding` is rejected as substitute Evidence or an inherited Confidence source.
- [x] 5.5 Add failing AST/import/static tests proving the module defines no alternate Evidence/RawFinding or generic Structured Analysis framework; imports/calls no VOC, sibling analysis, Unit Economics, or scoring engine; and contains no provider/network/browser/scraper/acquisition/normalization/ID-allocation/NLP/embedding/clustering/internal-LLM path.
- [x] 5.6 Add failing output/static tests proving no numeric score, weight, threshold, scorecard, analytical label, recommendation, Risk / Compliance, Red Team, persistence, reporting, hidden clock, randomness, environment dependency, or mutable global state is introduced.

## 6. Implement the narrow Brand Content module

- [x] 6.1 Add only `product_research/brand_content.py` with exact constrained vocabularies, canonical tuple validation, frozen proposition/key/finding/result values, and the single public `analyze_brand_content(...)` entry point; keep the implementation standard-library-only and avoid package-export or sibling refactors.
- [x] 6.2 Implement full-key multiplicity detection before Assessment, exclude every duplicate occurrence without selection or merge, and retain deterministic rejected keys plus supplied-aspect coverage.
- [x] 6.3 Invoke existing `assess_evidence(...)` exactly once for every unique well-formed proposition and preserve the returned `EvidenceAssessmentResult` unchanged; add only the narrow empty fail-closed fallback for unexpected ordinary execution failure.
- [x] 6.4 Map only Assessment `SUPPORTED` with non-empty usable IDs to `SUPPORTED` with identical Confidence; map all other Assessment states to `UNKNOWN`/Low with supporting/adverse/excluded Evidence-ID traceability and fixed Brand / Content factors.
- [x] 6.5 Derive supported/Unknown/missing aspect coverage without synthetic findings and implement fixed dimension, aspect, factor, key, finding, and lexical Evidence-ID ordering independent of caller order.
- [x] 6.6 Implement narrow shared/local input handling so unsafe shared input cannot support any finding, valid proposition-local failures remain traceable, and no Evidence, VOC-derived layer, proposition, relation, independence assignment, score, label, or recommendation is fabricated.
- [x] 6.7 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_brand_content.py' -v` until every focused RED test is GREEN, simplifying any implementation that exceeds the sibling-module contract.

## 7. Align scenarios and verify all ownership boundaries

- [x] 7.1 Add concise Brand / Content acceptance scenarios to `tests/scenarios.md` covering explicit dimensions/aspects, original Evidence reuse after VOC guidance, independent Assessment, traceability, coverage, Unknown behavior, duplicate rejection, replay, and absence of acquisition/inference/scoring/Risk behavior; do not rewrite unrelated scenarios.
- [x] 7.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_brand_content.py' -v` and trace every ECO-21 delta scenario to fresh focused evidence.
- [x] 7.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove the Evidence, Policy, Assessment, freshness, missing-information, conflict, and Confidence contracts remain unchanged.
- [x] 7.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` separately to prove acquisition, normalization, Evidence-ID allocation, and source-adapter ownership remain unchanged.
- [x] 7.5 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_market_demand.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_competition.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_voc.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_supply_chain.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove sibling analysis, VOC, economics, and downstream scoring ownership remains unchanged.
- [x] 7.6 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the complete repository regression gate.
- [x] 7.7 Run `openspec validate add-brand-content-analysis --strict`, `openspec validate --all --strict`, and `openspec doctor`; record actual supported command output and do not claim an unavailable Verify artifact or command passed.
- [x] 7.8 Inspect the final diff and independently trace every requirement through implementation and tests for inferred dimension/aspect semantics, duplicate winner selection, duplicated Policy/Assessment behavior, Confidence upgrade, VOC confidence inheritance, nondeterminism, acquisition/ID ownership leakage, NLP/embedding/clustering/LLM behavior, numeric scoring/scorecard/recommendation labels, Risk/Red Team behavior, persistence/reporting, generic frameworks, adjacent refactors, or unrelated changes; repair every in-scope finding and rerun affected focused and full gates.
