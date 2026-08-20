## 1. RED Research Failure Retention Tests

- [x] 1.1 Add a planner-exception RED test using the existing Research boundary's valid `ResearchRunResult(plan=None, status=FAILED, failures=(PLANNER_EXCEPTION, ...))`; assert Stage 2 is `UNRESOLVED` with `output is None` and `failure_kind is None`, Stage 3 is `UNRESOLVED`, and Stage 3 output is the exact returned object.
- [x] 1.2 In the planner-exception test, assert `result.research_run` is the same Stage 3 object, its lower-level status remains `FAILED`, the exact `PLANNER_EXCEPTION` remains inspectable, and no workflow replacement failure object or duplicated Stage 2 failure payload exists.
- [x] 1.3 Add an invalid-plan RED test using the existing Research boundary's valid `ResearchRunResult(plan=None, status=FAILED, failures=(INVALID_PLAN, ...))`; assert Stage 2 and Stage 3 are `UNRESOLVED`, the complete exact run result is retained, and the exact `INVALID_PLAN` remains inspectable.

## 2. RED Dependency and Execution-Failure Regressions

- [x] 2.1 For a planner-failed run with no Evidence, add RED call-spy assertions that Risk, Market Demand, Competition, VOC, Supply Chain, Brand Potential, and Content Potential analyzers are not invoked and their stages remain `BLOCKED` without placeholder Evidence or synthetic Evidence IDs.
- [x] 2.2 In the same no-Evidence planner-failure path, assert Unit Economics still executes and retains its existing result when its own explicit inputs are valid, proving there is no whole-workflow early return.
- [x] 2.3 Add RED regressions for `run_research(...)` raising an unexpected ordinary exception and returning an invalid type; assert Stage 2 is `FAILED` with `EXECUTION_ERROR`, Stage 3 is `BLOCKED` by Stage 2, and no Research run is fabricated.

## 3. RED Existing Research Semantics Regressions

- [x] 3.1 Assert a valid `COMPLETE` Research run with a plan remains Stage 2 `COMPLETE` and Stage 3 `COMPLETE`, with the exact plan and full run result retained.
- [x] 3.2 Assert a valid `PARTIAL` Research run with a plan remains Stage 2 `COMPLETE` and Stage 3 `UNRESOLVED`, with the complete exact run result retained.
- [x] 3.3 Assert a valid `FAILED` Research run with a plan but no Evidence remains Stage 2 `COMPLETE` and Stage 3 `UNRESOLVED`, with the complete exact run result retained and Evidence-dependent stages blocked.

## 4. Minimal Composition-Layer Correction

- [x] 4.1 Update only the Stage 2/3 valid-result branch in `product_research/end_to_end_workflow.py`: Stage 2 is `COMPLETE` when the exact plan exists and otherwise `UNRESOLVED`; Stage 3 always retains the exact valid `ResearchRunResult` and is `COMPLETE` only for lower-level `COMPLETE`, otherwise `UNRESOLVED`.
- [x] 4.2 Preserve the existing invalid-result branch so failure to obtain a valid `ResearchRunResult` remains Stage 2 `FAILED` with `EXECUTION_ERROR` and Stage 3 `BLOCKED`; do not inspect or reinterpret `research_run.failures` to classify workflow state.
- [x] 4.3 Preserve existing Evidence-dependent blocking and independent Unit Economics execution without adding early return, placeholder Evidence, fabricated IDs, provider behavior, persistence, reporting, retry, or ECO-38 behavior.

## 5. Architecture and Verification Gates

- [x] 5.1 Add or strengthen focused architecture regressions proving `run_research(...)` remains the only Research-to-Evidence boundary used by the workflow and the coordinator introduces no second Research model, Research status, failure taxonomy, planner validator, or Evidence allocator.
- [x] 5.2 Review the scoped Apply diff and confirm `product_research/research_orchestration.py` is unchanged and every production-code change is limited to the ECO-37 Stage 2/3 composition correction.
- [x] 5.3 Run `python3 -m unittest tests.test_end_to_end_workflow` and require all focused workflow tests to pass.
- [x] 5.4 Run `python3 -m unittest discover -s tests` and require the complete suite to pass.
- [x] 5.5 Run `openspec validate preserve-research-run-failure-trace --strict` and `openspec validate --all --strict` and require both validations to pass before verification handoff.
