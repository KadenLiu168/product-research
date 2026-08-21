## 1. Establish RED reporting contracts

- [x] 1.1 Add focused complete-result fixtures and failing contract tests for the exact 15-section order, exactly eight canonical analytical dimensions, final post-Red-Team scores, authoritative base/final weights, per-dimension Confidence and Evidence IDs, core-threshold results, aggregate, final Risk and Unit Economics state, accepted revisions, and exact Final Analysis Label.
- [x] 1.2 Add failing contract tests for presentation-only weighted contributions using exact repository `Decimal` semantics, consistency with an available authoritative aggregate, and no aggregate reconstruction when the authoritative value is absent.
- [x] 1.3 Add failing Evidence tests proving every report reference resolves inside the current Stage 3 universe, Key Evidence is a deterministic non-ranked membership projection, the appendix includes every normalized record exactly once in Evidence-ID order, content/provenance and adverse Evidence are preserved, and dangling or foreign-run IDs fail closed.
- [x] 1.4 Add failing incomplete-result tests for `UNRESOLVED`, `BLOCKED`, and `FAILED` stages, latest-known versus final-state labeling, missing scores, empty Evidence, absent Stage 16 decision, absent overall Confidence, and no unknown-to-zero or fabricated positive conclusion.
- [x] 1.5 Add failing determinism and architecture-boundary tests proving equivalent inputs produce byte-identical output, no provider/network/clock/randomness/persistence/LLM/asynchronous behavior or upstream policy executor is called, lower-level modules do not import reporting, and `end_to_end_workflow.py` remains report-free.
- [x] 1.6 Run the focused report test module and record the expected RED failures as caused by the missing ECO-38 reporting capability rather than unrelated fixture or import errors.

## 2. Implement the downstream authoritative projection

- [x] 2.1 Add the minimal dedicated reporting component that accepts only a well-formed `EndToEndWorkflowResult`, keeps all presentation helpers private, and introduces no generic template framework or new authoritative Evidence, analysis, score, Gate, Red Team, or decision model.
- [x] 2.2 Implement explicit state selection: Stage 16 owns final scores, Risk, Economics, weights, aggregate, core results, and label; accepted Stage 15 revisions or initial Stage 12/4/5 values may be shown only as clearly labeled latest-known state when Stage 16 is unavailable; Stage 13 never substitutes for the final decision.
- [x] 2.3 Implement fixed canonical section and dimension registries, stable unavailable markers, deterministic value formatting/escaping, and explicit preservation of workflow stage status and reasons.
- [x] 2.4 Implement explicit current-run Evidence collectors and validation for selected scores, domain findings, Risk, Unit Economics, accepted Red Team history, and final decision; reject dangling or foreign IDs without reflection, silent omission, renumbering, cloning, or fabrication.
- [x] 2.5 Run the focused projection, incomplete-state, determinism, and architecture tests and make them GREEN with only reporting-layer changes.

## 3. Implement canonical report rendering

- [x] 3.1 Render Executive Summary from available subject, final decision, aggregate, Risk, Unit Economics, core state, workflow incompleteness, key decision Evidence references, and material accepted revisions without overall Confidence, unsupported ranking, recommendation, or severity inference.
- [x] 3.2 Render the eight analytical sections from their retained authoritative results, preserving available conclusions/outcomes, Confidence, supporting and adverse Evidence IDs, missing/unknown state, diagnostics, factors, coverage, and findings without interpreting Evidence text.
- [x] 3.3 Render the Scorecard with exactly eight ordered rows, final or explicitly latest-known scores, authoritative base/final weights, Confidence, Evidence IDs, authoritative core and aggregate state, plus only the permitted Decimal-exact weighted contribution with aggregate-consistency validation.
- [x] 3.4 Render final Risk, Unit Economics, Final Analysis Label, accepted Red Team findings, and accepted score/Risk/Economics before-after history directly from authoritative objects, retaining reasons and causal Evidence IDs and never reinterpreting rejected proposals.
- [x] 3.5 Render Key Evidence as the deterministic Evidence-ID-ordered union of material authoritative references and Key Uncertainties from explicit workflow/domain state in canonical structural order, with no Evidence-strength or cross-domain severity ranking.
- [x] 3.6 Render the complete Evidence Appendix exactly once over the Stage 3 Evidence universe, preserving ID, claim, evidence, source, observed timestamp, tier, status, and Confidence including multiline, Unicode, control-character-sensitive, and adverse content.
- [x] 3.7 Run all focused report contract tests and make the canonical complete and incomplete reports GREEN.

## 4. Align Skill, reference, methodology, and Agent scenarios

- [x] 4.1 Update `references/report-contract.md` to be the precise implemented 15-section runtime contract, replace unsupported "strongest evidence" and overall-report Confidence requirements with key decision Evidence and per-dimension Confidence, and document deterministic incomplete-state and appendix semantics.
- [x] 4.2 Update `SKILL.md` routing and capability statements so final-report generation and Evidence Appendix rendering route to the implemented downstream boundary while provider-backed research, autonomous judgment, persistence, and other still-unavailable capabilities remain unchanged.
- [x] 4.3 Align `references/methodology.md` and `docs/product-research-skill-spec.md` to the same 15 sections, final-state ownership, non-ranking uncertainty/evidence rules, and ECO-37/ECO-38 boundary; remove the competing 17-section runtime layout and stale reporting-unavailable statements.
- [x] 4.4 Add relevant `tests/scenarios.md` RED/GREEN cases for Skill routing, complete and incomplete reports, traceability, no fabrication, no hidden upstream execution, and absence of ECO-39 evaluation behavior.
- [x] 4.5 Add focused documentation assertions or searches proving all routed documents name one canonical structure and no longer claim implemented reporting is unavailable.

## 5. Verify the complete Change

- [x] 5.1 Run the focused final-report contract tests and relevant existing workflow, scoring-decision, Red Team, Evidence, Risk, and Unit Economics boundary tests.
- [x] 5.2 Run `python3 -m unittest discover -s tests` and resolve only regressions attributable to ECO-38.
- [x] 5.3 Run `openspec validate add-final-report-generation --strict` and `openspec validate --all --strict`, then inspect the Change against every requirement and acceptance criterion without adding ECO-39 infrastructure.
- [x] 5.4 Inspect `git diff --check`, `git status --short`, and the final diff to confirm changes remain limited to the ECO-38 reporting capability, focused tests/scenarios, and required Skill/reference/methodology/docs alignment.
