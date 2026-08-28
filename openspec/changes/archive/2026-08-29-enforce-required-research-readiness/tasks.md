## 1. Scoring Decision Contract

- [x] 1.1 Add RED `tests/test_scoring_decision.py` cases for readiness `True` preserving `GO`, readiness `False` producing `CONDITIONAL GO`, exact-boolean validation, missing/malformed input diagnostics, Risk/Unit Economics precedence, deterministic duplicate-free reasons, and equivalent replay.
- [x] 1.2 Add the two readiness reason codes, normalized optional readiness field, exact-boolean validation, and the single readiness check in the existing GO predicate in `product_research/scoring_decision.py`; keep hard-failure and Risk-review predicates unchanged.
- [x] 1.3 Inventory every `evaluate_scoring_decision(...)` caller with `rg`, pass explicit readiness intent through all repository fixtures/callers, and verify `python3 -m unittest tests.test_scoring_decision tests.test_risk_gate tests.test_initial_scoring tests.test_risk_compliance tests.test_red_team_revision tests.test_v1_evaluation_suite`.

## 2. Workflow Derivation and Reuse

- [x] 2.1 Extend the existing workflow fixtures and partial-research fixture with RED cases for complete/partial/failed execution crossed with semantic `True`/`False`, malformed/omitted semantic input, approved-fallback semantic insufficiency, and the unchanged 16-stage vocabulary.
- [x] 2.2 Add `required_research_semantically_satisfied` and one private Stage 3 readiness derivation in `product_research/end_to_end_workflow.py`, using only the existing validated `ResearchRunResult.status` and `missing_required_task_ids` contract.
- [x] 2.3 Pass the one derived value unchanged to both existing Stage 13 and Stage 16 executor calls, forbid any Red Team/readiness override, and assert both captured calls receive identical readiness semantics.
- [x] 2.4 Update every `run_end_to_end_workflow(...)` caller with explicit semantic-sufficiency intent and verify `python3 -m unittest tests.test_end_to_end_workflow` without modifying `product_research/research_orchestration.py` or its spec.

## 3. Final Report Projection

- [x] 3.1 Add RED `tests/test_final_report_generation.py` cases for Executive Summary/Key Uncertainties readiness visibility, deterministic missing-task/failure projection, semantic insufficiency with Stage 3 `COMPLETE`, exact authoritative label retention, unchanged 15-section order, and unchanged Evidence Appendix.
- [x] 3.2 Add fixed-label projection of authoritative readiness, research-run status, missing required task IDs, and matching existing structured task status/failure details in `product_research/final_report_generation.py`; do not parse free text/metadata or fabricate provider/fallback fields.
- [x] 3.3 Add negative report tests proving scoring policy is not re-executed, credentials/configuration are not read or rendered, absent provider operation/fallback state is not invented, and equivalent inputs render byte-identically; verify `python3 -m unittest tests.test_final_report_generation tests.test_final_report_documentation`.

## 4. Runtime Documentation and Contract Scenarios

- [x] 4.1 Update `tests/scenarios.md` with provider-neutral ECO-61 behavior for execution-plus-semantic derivation, decision precedence, Stage 13/16 reuse, report-only projection, non-Amazon/non-DataForSEO compatibility, and offline/no-charge execution.
- [x] 4.2 Update only `SKILL.md`, `references/scoring-policy.md`, and `references/report-contract.md` to require the explicit caller judgment, document effective readiness and precedence, and preserve ECO-60, research-orchestration, Evidence, workflow-stage, and report-section ownership.
- [x] 4.3 Verify documentation/runtime agreement with `python3 -m unittest tests.test_final_report_documentation` and confirm no credential, provider-specific readiness, new label, new stage, or new report-section vocabulary was introduced.

## 5. Full Verification

- [x] 5.1 Run the full offline deterministic suite with `python3 -m unittest discover -s tests` and confirm no live or billable provider transport is invoked.
- [x] 5.2 Run `openspec validate enforce-required-research-readiness --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every applicable error without changing out-of-scope contracts.
- [x] 5.3 Run `git diff --check`, inspect the final scoped diff and caller inventory, and confirm `ResearchRunResult`, provider/Evidence contracts, four decision labels, 16 workflow stages, and 15 report sections remain unchanged except for the planned readiness integration.
