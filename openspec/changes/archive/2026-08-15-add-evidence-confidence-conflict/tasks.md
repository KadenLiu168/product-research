## 1. Establish RED assessment contracts

- [x] 1.1 Add the Evidence Assessment acceptance scenarios to `tests/scenarios.md`, covering explicit stance and independence, policy-result preservation, adverse exclusion, outcomes, missing information, Confidence ceilings, immutability, fail-closed inputs, and deterministic ordering.
- [x] 1.2 Create `tests/test_evidence_assessment.py` with failing tests for the closed vocabularies and immutable input/result values, including invalid stance, explicit unknown independence, duplicate or incomplete assignments, malformed missing information, and an explicit positive minimum-independent-source requirement; run the focused suite and record the expected RED result.
- [x] 1.3 Add failing integration tests for two independent agreeing sources, duplicate upstream groups, current and context-only eligibility, eligible contradiction, stale contradictory Evidence preserved with `STALE_EVIDENCE`, claim-support reuse, Tier-4-only support, no usable support, and separately ordered stance and eligibility collections; rerun and record RED.
- [x] 1.4 Add failing tests for every Confidence ceiling and stable factor, including material and critical missing information, insufficient and unknown independence, unknown stance, Low/Medium individual Evidence Confidence ceilings, strictest-cap behavior, factor deduplication, and a no-cap `High` case; rerun and record RED.
- [x] 1.5 Add failing replay and immutability tests using reordered equivalent inputs, repeated assessment, pre/post Evidence equality and serialization, invalid index or unresolved IDs, duplicate IDs, unexpected validation failure, and proof that provider, URL, domain, claim, and evidence text do not influence stance or independence; rerun and record RED.

## 2. Implement the minimal assessment boundary

- [x] 2.1 Add `product_research/evidence_assessment.py` with the closed assessment vocabularies and frozen `EvidenceRelation`, `IndependenceAssignment`, `MissingInformation`, `AssessmentContext`, and `EvidenceAssessmentResult` values; make the focused construction and immutability tests pass without adding dependencies or changing `evidence.py`.
- [x] 2.2 Implement strict collection, index, relation, independence, missing-information, context, and policy boundary validation plus the structured `ASSESSMENT_INPUT_ERROR` fallback; make malformed and indeterminate input tests pass without inference or repair.
- [x] 2.3 Integrate `validate_evidence_set` and ordered per-record `validate_evidence` results, then apply `validate_claim_support` only to individually eligible supporting IDs; preserve current, context-only, usable, excluded, stance, claim-support, and policy-reason outputs, including excluded adverse Evidence.
- [x] 2.4 Implement known independence-group counting, `NONE` / `PRESENT` conflict state, `SUPPORTED` / `CONFLICTED` / `INSUFFICIENT` outcomes, and lexical ID ordering without a conflict graph, majority vote, winner selection, or semantic comparison.
- [x] 2.5 Implement the fixed Confidence-cap table and factor priority, using the existing `High` / `Medium` / `Low` vocabulary and the strongest usable supporting Evidence Confidence as its ceiling; make all cap, strictest-rule, and no-cap tests pass without scores, weights, or averages.
- [x] 2.6 Normalize missing-information, factor, and policy-result ordering; make reordered-input replay and Evidence immutability tests pass, and remove only helpers or imports made unused by this Change.

## 3. Route living documentation narrowly

- [x] 3.1 Update `references/evidence-policy.md` to point source independence, conflict preservation, missing-information handling, and claim-level Confidence to the new assessment module while preserving the existing policy guidance and the distinction from individual `Evidence.confidence`.
- [x] 3.2 Update only the Evidence routing and implemented-capability statements needed in `SKILL.md`; do not claim research acquisition, semantic analysis, scoring, gates, Red Team automation, persistence, or report generation exists.
- [x] 3.3 Review the documentation diff to ensure rules remain single-owned, no Evidence wire field or existing policy requirement is redefined, and assessment remains upstream of future scoring and gates.

## 4. Verify requirements and scope

- [x] 4.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v`, then repeat deterministic and immutability cases to confirm identical outcomes, Confidence, ID collections, policy issues, missing-information order, and factor order.
- [x] 4.2 Run the unchanged upstream suites with `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, followed by `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v`.
- [x] 4.3 Trace every `evidence-confidence-conflict` requirement and scenario to implementation and focused test evidence, including excluded adverse traceability, explicit-input-only semantics, existing policy reuse, fail-closed behavior, Confidence ownership, and deterministic ordering.
- [x] 4.4 Run `openspec validate add-evidence-confidence-conflict --strict` and `openspec validate --all --strict`, then inspect the final diff for unauthorized changes to `evidence.py`, the Evidence wire schema, policy eligibility semantics, dependencies, acquisition, analysis, numerical scoring, gates, decisions, persistence, reports, or unrelated files.
- [x] 4.5 Obtain an independent acceptance review against proposal, design, delta spec, tasks, implementation, and fresh test output; resolve every in-scope finding and leave archive, commit, and push unperformed pending separate authorization.
