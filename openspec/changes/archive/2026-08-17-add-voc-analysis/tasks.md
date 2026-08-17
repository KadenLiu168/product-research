## 1. Reconfirm boundaries and establish RED

- [x] 1.1 Re-read this Change's proposal, delta spec, and design together with the current `evidence.py`, `evidence_policy.py`, `evidence_assessment.py`, `market_demand.py`, and `competition.py`; record the exact reusable public types/entry points and confirm no generic contract or adjacent module needs modification.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` before implementation and preserve the baseline result so any later regression is attributable to ECO-18.
- [x] 1.3 Create `tests/test_voc.py` with repository-style builders for explicit VOC Evidence, Policy, Assessment contexts, relations, independence assignments, missing information, propositions, Complaint characterization, and deterministic result assertions.
- [x] 1.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_voc.py' -v` and retain the expected RED import/API failure before adding `product_research/voc.py`.

## 2. Write focused RED domain-contract tests

- [x] 2.1 Add failing tests for the exact fixed category order `PURCHASE_MOTIVATION`, `PAIN_POINT`, `COMPLAINT`, `UNMET_NEED`, `USE_CASE`, `PURCHASE_BARRIER`, `CUSTOMER_LANGUAGE`, `SEGMENT`, and reject unsupported category values without inventing a finding.
- [x] 2.2 Add failing tests proving each of the eight categories can produce a structured supported finding with an exact proposition, existing Confidence, usable supporting Evidence IDs, and one complete existing Assessment result.
- [x] 2.3 Add failing frozen-value tests for proposition keys, proposition inputs, Complaint characterization, findings, and aggregate results; require tuple-based typed collections and preserve exact non-empty UTF-8 proposition text without trimming, case folding, or semantic normalization.
- [x] 2.4 Add failing constructor and public-boundary tests for malformed containers/types, duplicate IDs, invalid closed values, non-Complaint characterization, impossible Unknown-axis support IDs, and other incomplete structural inputs.
- [x] 2.5 Add failing absence tests proving Evidence/review/social text, `voc` policy kind, provider metadata, provenance, source family, or record count alone creates no proposition, category, theme, segment, stance, classification, or finding.

## 3. Write focused RED independent Assessment and traceability tests

- [x] 3.1 Add failing tests proving every unique proposition invokes and preserves its own existing Evidence Assessment and that two propositions in one category do not share Evidence, conflicts, missing information, Policy results, source independence, or Confidence.
- [x] 3.2 Add failing tests proving proposition-specific `AssessmentContext.minimum_independent_sources` values are honored independently, including one-source and two-source cases, with no hidden VOC-wide minimum.
- [x] 3.3 Add failing tests proving Assessment `SUPPORTED` plus non-empty usable support maps to VOC `SUPPORTED` with identical High/Medium/Low Confidence and no upgrade above Assessment or individual Evidence Confidence.
- [x] 3.4 Add failing tests proving policy-usable contradiction maps to `UNKNOWN`/Low while preserving the complete `CONFLICTED` Assessment and declared adverse IDs, and policy-excluded adverse Evidence remains traceable without becoming usable conflict or support.
- [x] 3.5 Add failing tests proving absent support, stale VOC Evidence, policy rejection, unresolved IDs, missing citations, incomplete relations/independence assignments, and other Assessment input errors map to `UNKNOWN`/Low with complete excluded IDs, Policy results, claim-support result, and ordered diagnostics.
- [x] 3.6 Add failing material and critical missing-information tests proving VOC preserves the exact existing Assessment outcome, missing-information values, factors, and Confidence restriction rather than inventing a stricter or more optimistic rule.
- [x] 3.7 Add one combined traceability test proving a finding retains lexically ordered usable supporting, declared adverse, and excluded Evidence IDs plus the unchanged complete existing Assessment.

## 4. Write focused RED category-coverage and duplicate tests

- [x] 4.1 Add failing tests proving `supported_categories`, `unknown_categories`, and `missing_categories` are fixed-order, mutually exclusive, exhaustive over all eight categories, and derived from supplied proposition keys and resulting findings.
- [x] 4.2 Add failing tests proving an unsupported-only category is Unknown, an absent category is missing without a placeholder finding, and a category with both supported and Unknown findings is supported while retaining both findings.
- [x] 4.3 Add failing permutation tests proving every exact duplicate `(category, proposition)` occurrence is excluded from assessment and output findings, its rejected key is reported once, its category remains Unknown unless another unique finding supports it, and no first-wins, last-wins, merge, or caller-order behavior occurs.
- [x] 4.4 Add failing isolation tests proving duplicate keys do not prevent other unique propositions from being assessed when shared Evidence/Policy input is safe.

## 5. Write focused RED Complaint-characterization tests

- [x] 5.1 Add failing tests for the exact prevalence vocabulary `COMMON`, `EDGE_CASE`, `UNKNOWN` and scope vocabulary `PRODUCT_SPECIFIC`, `CATEGORY_WIDE`, `UNKNOWN`, including independent axis preservation on a supported Complaint.
- [x] 5.2 Add failing tests proving each non-Unknown axis requires its own non-empty explicit axis Evidence-ID tuple wholly contained in the finding's policy-usable supporting IDs and exposes those IDs lexically.
- [x] 5.3 Add failing tests proving unresolved, excluded, adverse, non-participating, empty, or otherwise unusable axis Evidence downgrades only that axis to `UNKNOWN` with an empty axis-support tuple and stable axis diagnostic.
- [x] 5.4 Add failing tests proving an overall conflicted, insufficient, or invalid Complaint finding forces both axes to `UNKNOWN`, while an explicit input `UNKNOWN` stays Unknown regardless of Evidence text, metadata, provenance, source family, record count, or ordering.
- [x] 5.5 Add failing tests proving Complaint characterization cannot be attached to any other VOC category and no axis value is inferred from claim/Evidence text.

## 6. Write focused RED replay immutability and scope tests

- [x] 6.1 Add failing replay tests proving equivalent Evidence-index insertion order and permuted proposition, relation, independence, missing-information, and Complaint-axis ID order produce equal results with fixed category/factor order and lexical proposition/Evidence-ID tie-breakers.
- [x] 6.2 Add a failing immutability test proving analysis leaves every Evidence value and Confidence, Evidence index, proposition, relation, independence assignment, missing-information value, Assessment context, Complaint characterization, and Policy unchanged.
- [x] 6.3 Add failing shared-input tests proving malformed Evidence-index identity or Policy prevents every supported finding and returns stable `VOC_INPUT_ERROR`, while programmer-control `BaseException` values are not swallowed.
- [x] 6.4 Add a failing AST/import/static ownership audit proving the module defines no second Evidence schema, provider/network/browser/scraping/retry/cache/async/persistence/clock/random/environment/LLM/embedding/NLP path, research planning, `RawFinding`, `AcquisitionResult`, `run_research`, normalization, Evidence-ID allocation, automatic clustering, numeric score, threshold/weight, recommendation, Red Team, Brand/Content/Supply Chain/Risk analysis, reporting, or generic Structured Analysis framework.

## 7. Implement the minimal VOC boundary

- [x] 7.1 Add only `product_research/voc.py` with the closed constrained-value vocabularies, frozen proposition/Complaint inputs, frozen proposition-key/finding/aggregate results, deterministic exact-type validation, and no package export or third-party dependency.
- [x] 7.2 Implement `analyze_voc(...)` shared Evidence-index/Policy validation and exact duplicate-key multiplicity detection before assessment; reject every duplicate occurrence without selecting or merging one while retaining deterministic rejected keys and category coverage.
- [x] 7.3 Invoke existing `assess_evidence(...)` exactly once for every unique proposition, preserve the returned result unchanged, and map only Assessment `SUPPORTED` plus non-empty usable IDs to a supported VOC finding with identical Confidence.
- [x] 7.4 Map conflict, insufficiency, input error, unresolved/rejected Evidence, and absent usable support to `UNKNOWN`/Low with supporting/adverse/excluded Evidence-ID traceability and fixed-order VOC factors; do not duplicate Policy, freshness, independence, conflict, missing-information, or Confidence logic.
- [x] 7.5 Derive supported/Unknown/missing category coverage without placeholder findings and implement independent Complaint prevalence/scope gating solely from explicit axis declarations and the finding's usable supporting IDs.
- [x] 7.6 Implement narrow structured fail-closed handling so unsafe shared input blocks every supported finding, proposition-local Assessment failures affect only that finding, unsupported Complaint evidence affects only that axis, and no placeholder Evidence, proposition, classification, score, or recommendation is fabricated.
- [x] 7.7 Make `tests/test_voc.py` GREEN, then simplify only ECO-18 code and remove any new unused import/helper without refactoring Market Demand, Competition, or generic Evidence/Policy/Assessment modules.

## 8. Align capability routing narrowly

- [x] 8.1 Add concise VOC acceptance scenarios to `tests/scenarios.md` covering explicit propositions, all categories, independent assessment, traceability, coverage, Unknown behavior, Complaint axes, duplicate handling, replay, and absence of acquisition/clustering/scoring.
- [x] 8.2 Add `product_research/voc.py` to the `SKILL.md` routing table and implemented-capability statement while retaining concrete provider acquisition, automatic VOC clustering, qualitative score generation, later unavailable Phase 6 analysis, Red Team, persistence, reporting, and end-to-end workflow as unavailable.
- [x] 8.3 Update only directly stale current-boundary wording in `references/methodology.md` or `docs/product-research-skill-spec.md`; route normative behavior to the production module instead of duplicating the algorithm.
- [x] 8.4 Review all touched documentation together to ensure the sole path remains existing normalized Evidence plus explicit VOC inputs → existing Policy/Assessment → VOC result → later analysis/scoring, and ECO-13/ECO-14 ownership is unchanged.

## 9. Verify focused regression scope and OpenSpec gates

- [x] 9.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_voc.py' -v` and trace every ECO-18 delta scenario to fresh focused evidence.
- [x] 9.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove generic Evidence contracts remain unchanged.
- [x] 9.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` separately to prove acquisition, normalization, Evidence-ID, failure, and routing ownership remains unchanged.
- [x] 9.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_market_demand.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_competition.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove adjacent analysis and downstream scoring contracts remain unchanged.
- [x] 9.5 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the complete repository regression gate.
- [x] 9.6 Run `openspec validate add-voc-analysis --strict`, `openspec validate --all --strict`, and `openspec doctor`; record actual supported command output and do not claim an unavailable Verify artifact or command passed.
- [x] 9.7 Inspect the final diff and independently trace every requirement through implementation and tests for inferred category/theme/classification, duplicated Policy/Assessment behavior, hidden source thresholds, duplicate winner selection, Confidence upgrade, nondeterminism, acquisition/ID ownership leakage, clustering/NLP/LLM behavior, numeric scoring, recommendations, downstream analysis, adjacent refactors, or unrelated changes; resolve every in-scope finding and rerun affected focused and full gates.
