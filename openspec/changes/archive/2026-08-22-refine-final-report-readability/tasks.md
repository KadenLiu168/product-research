## 1. Establish RED presentation contracts

- [x] 1.1 Run the existing focused final-report tests before edits and add characterization assertions for the exact 15-section order, canonical eight-dimension Scorecard values/order, Key Evidence membership, complete lossless Appendix, fail-closed foreign/dangling Evidence, incomplete-result reportability, deterministic bytes, and one-way no-upstream-execution boundary.
- [x] 1.2 Add focused Executive Summary tests proving a fully complete workflow emits one clear completion status without its 16 successful stage records, while retaining subject, `FINAL`/`LATEST-KNOWN`/`INITIAL` source, final label, aggregate, Risk, Economics, core state, accepted Red Team state, and Key Decision Evidence IDs when authoritative.
- [x] 1.3 Add focused incomplete-summary tests proving only `UNRESOLVED`, `BLOCKED`, and `FAILED` stages are listed in canonical order and that failure kind and all blocking dependencies remain visible.
- [x] 1.4 Add analytical and Risk tests proving fixed reader-facing labels replace raw `snake_case`, closed domain values are unchanged, every retained finding remains in input order, and all applicable proposition/text, outcome, dimension/category/area/aspect, Confidence, supporting/adverse/excluded Evidence IDs, factors, and diagnostics remain represented in a compact layout.
- [x] 1.5 Add Key Uncertainties tests proving the existing uncertainty sources and canonical structural order remain unchanged while known field names use fixed reader-facing labels, with no ranking, selection, inference, or arbitrary attribute humanization.
- [x] 1.6 Add Red Team tests proving Score revisions retain dimension, score and available Confidence transitions, reason, and causal Evidence IDs; Risk revisions show only the authoritative Risk Gate transition; and Unit Economics revisions show outcome and applicable Minimum Viability/Dynamic Target Gate transitions without full-object representations or generic diff behavior.
- [x] 1.7 Add a static coupling regression proving reporting no longer reads `scoring_decision._FIELD_NAMES` while canonical dimension ordering and equivalent-input Key Evidence membership remain unchanged.
- [x] 1.8 Run the focused final-report modules and record the expected RED failures as presentation-contract failures rather than fixture, import, or unrelated semantic failures.

## 2. Implement the minimal presentation refinement

- [x] 2.1 Replace report-internal field-name output with explicit ordered `(attribute, reader label)` registries shared only where analytical and uncertainty presentation require the same label; do not add reflection or dynamic humanization.
- [x] 2.2 Refactor general domain findings and specialized Risk findings into compact deterministic rows or shallow field groups that retain every existing non-empty authoritative value and Evidence reference exactly once in canonical input order.
- [x] 2.3 Replace the Executive Summary stage dump with a conditional renderer that emits one complete-status line or only non-complete stage records with retained failure and blocking detail, leaving all other summary facts unchanged.
- [x] 2.4 Replace Red Team Risk and Unit Economics full-object rendering with narrow type-specific closed-state transitions and add Score Confidence transitions without changing accepted-history membership, order, reasons, or causal Evidence IDs.
- [x] 2.5 Apply fixed labels to Key Uncertainties without changing its source membership, workflow/dimension traversal order, closed values, finding indices, or unresolved-state behavior.
- [x] 2.6 Iterate score and Evidence collection through reporting's existing canonical dimension registry instead of `scoring_decision._FIELD_NAMES`; preserve the scoring module and the existing Decimal context/arithmetic path unchanged.
- [x] 2.7 Run the focused final-report generation and documentation tests and make them GREEN using only scoped reporting presentation, test, and report-contract changes.

## 3. Align the canonical report documentation

- [x] 3.1 Update `references/report-contract.md` to document the conditional workflow summary, explicit fixed reader-facing labels, compact but complete finding projection, type-specific Red Team transitions, and unchanged complete Appendix semantics.
- [x] 3.2 Update focused documentation assertions so the reference contract and delta spec agree on the refined body while continuing to declare exactly 15 sections, eight dimensions, non-ranked Key Evidence, explicit uncertainties, and no overall-report Confidence or ECO-39 evaluation behavior.
- [x] 3.3 Search routed reporting documentation for directly conflicting debug-oriented wording and change only statements required for consistency; do not introduce another report format or broaden unrelated Skill/methodology documentation.

## 4. Verify unchanged ECO-38 semantics and scope

- [x] 4.1 Run `python3 -m unittest tests.test_final_report_generation tests.test_final_report_documentation` and confirm all focused presentation and invariant tests pass.
- [x] 4.2 Run `python3 -m unittest tests.test_end_to_end_workflow tests.test_scoring_decision tests.test_red_team_revision tests.test_evidence_data_model tests.test_evidence_policy tests.test_evidence_assessment tests.test_risk_compliance tests.test_risk_gate tests.test_unit_economics` and resolve only regressions attributable to this Change.
- [x] 4.3 Run `python3 -m unittest discover -s tests` and confirm the full repository suite passes without ECO-39 fixtures or infrastructure.
- [x] 4.4 Run `openspec validate refine-final-report-readability --strict` and `openspec validate --all --strict`.
- [x] 4.5 Run `git diff --check`, inspect `git status --short`, and review the complete diff to confirm every changed line traces to the readability contract and no workflow, Evidence, domain, Risk, Unit Economics, scoring, decision, Red Team, Linear, archive, commit, or push state changed during Apply.

## 5. Independent acceptance and completion synchronization

- [x] 5.1 In a separately authorized independent verification stage, trace every delta requirement and acceptance criterion through design, implementation, focused regression evidence, and full verification; do not treat completed checkboxes or a green suite alone as acceptance.
- [x] 5.2 After independent acceptance and explicit sync/archive authorization, synchronize the delta into the existing `final-report-generation` living spec and verify it is consistent with `references/report-contract.md`; do not create a second capability.
- [x] 5.3 After the accepted Change is synchronized to the repository under the authorized delivery workflow, read and de-duplicate Linear state, then update existing ECO-38 from `Backlog` to `Done` only; create no issue, preserve ECO-37 → ECO-38 → ECO-39 dependency history, verify ECO-39 is no longer operationally blocked by incomplete ECO-38, and leave ECO-39 status unchanged.
