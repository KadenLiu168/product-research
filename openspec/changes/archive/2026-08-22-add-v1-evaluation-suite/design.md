## Context

See `proposal.md` for motivation and `specs/v1-evaluation-suite/spec.md` for observable requirements. The current repository already exposes all production owners needed by ECO-39: Evidence Policy and Assessment, domain analyses, Unit Economics, Initial Scoring, scoring/decision, Red Team revision, the fixed 16-stage workflow, a structured final state, and deterministic final-report rendering. Their focused contract tests prove individual behavior, but no single reusable scenario matrix makes the v1 cross-boundary acceptance baseline explicit.

The repository has two intentionally different evaluation mechanisms:

- standard-library `unittest` tests for deterministic code and public boundaries;
- `tests/scenarios.md` for fresh-context RED/GREEN evaluation of Agent behavior after loading the Skill.

The evaluation design must compose those mechanisms without moving test concerns into `product_research/`, duplicating runtime semantics, or treating natural-language output as deterministic data.

## Goals / Non-Goals

**Goals:**

- Make each required scenario family cheap to reconstruct from explicit, readable Python values.
- Give every ECO-39 dimension a named oracle and an authoritative test boundary.
- Use full workflow/report construction only where an invariant truly crosses stages.
- Make failures diagnostic by asserting retained authoritative state rather than a second evaluation status vocabulary.
- Preserve a stable v1 baseline that future changes can run with the full existing suite.

**Non-Goals:**

- Centralize all existing test builders or rewrite capability-level tests around ECO-39 fixtures.
- Add an evaluation runner, fixture serialization format, runtime API, metric collector, dashboard, persistence layer, or overall score.
- Judge the quality of Red Team reasoning or Agent prose subjectively.
- repair production behavior discovered to contradict an existing capability contract.

## Decisions

### 1. Keep reusable scenario construction in test support

Apply should add one small test-support module under `tests/` and one focused automated evaluation module. The support module should expose ordinary Python builders for the seven required scenario families plus the core-threshold variant. Builders may return existing production values or a small test-only bundle of explicit arguments needed to call an existing boundary; they must not introduce a public evaluation domain model.

The builders should be layered only where reuse is demonstrated:

- small Evidence, policy, score, Gate, and Red Team input constructors;
- scenario-family constructors composed from those values;
- a complete workflow input bundle only for scenarios that cross workflow/reporting.

Use fixed `Decimal` values, fixed Evidence IDs, fixed timezone-aware datetimes, deterministic in-memory research callbacks, tuples, and existing immutable production values. Prefer direct Python construction over JSON/YAML because the existing contracts are typed, Python construction is already the test convention, and serialization would add parsing/schema behavior unrelated to acceptance.

Exact helper names and file names remain Apply details so the implementation can match current test conventions. The required contract is reusable construction, not a new fixture API.

Alternatives considered:

- Put fixtures in `product_research/evaluation.py`: rejected because test data would become a production dependency and imply runtime evaluation ownership.
- Use JSON or YAML fixture files: rejected because no external interchange or non-Python consumer exists, while typed object construction and `Decimal`/datetime fidelity would become harder to inspect.
- Refactor all focused tests onto the new builders: rejected because it creates broad churn and couples capability tests to an integration suite.

### 2. Select the narrowest authoritative oracle per dimension

The focused evaluation module should name tests by scenario family and dimension while calling the owner that already defines the behavior. A single scenario may satisfy several dimensions, but every dimension needs at least one direct assertion rather than coverage inferred from execution alone.

| ECO-39 dimension | Primary authoritative boundary | Required observable assertions |
|---|---|---|
| Evidence Coverage | Evidence Policy / Assessment and authoritative domain results | support IDs resolve; missing required support remains missing/unresolved; no synthesized Evidence |
| Citation Accuracy | Evidence Policy claim support and report reference validation | current eligibility; unknown/duplicate/stale/foreign references fail closed; report IDs stay run-local |
| Hallucination Resistance | fail-closed narrow owners plus workflow state; Agent protocol | invalid/unsupported inputs never become successful state; Agent does not invent research, facts, values, scores, Gates, or conclusions |
| Estimate Discipline | Evidence status/use policy; Agent protocol | `Estimated` is not `Observed`; `Unknown` remains unknown; unsupported estimates are not facts |
| Repeatability | narrow results, complete workflow result, and report renderer | equal structured replay and ordered traces; byte-identical Markdown; explicit time only |
| Scoring Stability | Initial Scoring where applicable and scoring/decision | exact scores, weights, aggregate, core state, reason codes, and label under existing `Decimal` semantics |
| Gate Correctness | scoring/decision, exercised from integrated fixtures where useful | `FATAL` Risk and `UNVIABLE` economics each defeat a favorable aggregate |
| Core Threshold Enforcement | scoring/decision | favorable aggregate cannot override a failed core dimension; diagnostic stays explicit |
| Red Team Effectiveness | Red Team revision, workflow final state, and report | new-Evidence authorization, target isolation, duplicate/conflict fail-closed behavior, before/after/reason/causal trace, revised final decision |
| Report Traceability | final-report renderer over workflow results | current-run resolution, complete appendix, adverse Evidence, incomplete state, and revision trace; invalid references fail closed |

Tests must not restate a threshold, precedence chain, Evidence-eligibility rule, or Red Team authorization algorithm to calculate an expected result. They should provide inputs chosen to trigger the existing owner, then assert its public result and reason state. Literal expected labels, IDs, fixed ordering, and exact values are appropriate contract assertions; locally reproducing how those values are derived is not.

Alternative considered: route every dimension through the 16-stage workflow. Rejected because narrow Evidence and policy failures would require large unrelated fixtures, obscure the actual owner, and make failures harder to diagnose.

### 3. Reserve complete workflow-to-report runs for integration invariants

At minimum, the normal, missing, and Evidence-based score-revision scenarios should cross:

```text
explicit deterministic fixture
    → existing 16-stage workflow
    → EndToEndWorkflowResult / final structured state
    → existing final-report renderer
```

The normal scenario proves the fully reportable happy path and whole-path replay. The missing scenario proves that unresolved/blocked/failed state remains visible and no report value is manufactured. The Evidence-based revision scenario proves baseline score → authorized revision → revised authoritative score → final decision → report causal trace. High-risk and economic-failure fixtures should execute at least through the existing decision boundary and may reuse the complete workflow input bundle when doing so provides the clearest precedence proof. The core-threshold variant should use the scoring owner directly unless an existing complete fixture makes the workflow assertion comparably small.

Conflicting and expired scenarios should first target Evidence Assessment and Evidence Policy directly. A report-level assertion should reuse an integrated fixture containing adverse or ineligible Evidence rather than forcing every narrow policy case through all 16 stages.

Equivalent replay means rebuilding semantically equivalent inputs rather than only rendering the same object instance twice. Workflow equality includes the exact canonical stage order and accepted Red Team history. Report equality compares the complete Markdown strings.

Alternatives considered:

- Keep ECO-39 as isolated boundary tests only: rejected because it would not prove the Phase 9 integration and report handoff.
- Make all seven families full workflow fixtures: rejected because it inflates setup and weakens ownership-local diagnostics without adding acceptance value.

### 4. Treat fixture families as input compositions, not new expected-state authorities

Each named family describes the decisive variation from a common valid baseline:

- `normal`: complete current Evidence, valid explicit analyses/judgments, determinate Gates and decision, no unauthorized revision;
- `missing`: required Evidence or input absent, retaining authoritative incomplete stage and report state;
- `conflicting`: existing assessment relations/groups encode opposed Evidence and preserve adverse support;
- `expired`: fixed dated Evidence plus explicit timezone-aware `as_of` makes current use ineligible under existing policy;
- `high-risk`: explicit valid Risk result reaches `FATAL` while scoring inputs remain favorable;
- `economic-failure`: explicit valid Unit Economics result reaches `UNVIABLE` while scoring inputs remain favorable;
- `evidence-based-score-revision`: baseline Evidence and distinct current-run new Evidence authorize an otherwise valid proposal and retain causal history;
- core variant: the aggregate meets the existing GO threshold but one core dimension is below its existing requirement.

Variants should replace only the values needed to produce the named condition. They should not hide required inputs behind defaults that make the test's business premise difficult to inspect. Builders may reduce boilerplate but the decisive Evidence IDs, dates, statuses, scores, Gate states, and causal IDs should remain visible at the call site or in the named scenario constructor.

Alternative considered: one giant configurable fixture builder. Rejected because dozens of optional switches would form an untyped test DSL and obscure why a scenario passes.

### 5. Reuse the current Agent scenarios unless the Apply-time audit proves a gap

The current fresh-context rubrics already map as follows:

- Scenario 1 covers Evidence use for material claims, research before conclusions, Evidence status vocabulary, and no model-knowledge viability verdict.
- Scenario 2 covers non-fabrication of missing numeric inputs, `Unknown`, evidence-supported `Estimated`, and estimates not presented as facts.
- Scenario 3 covers current authoritative regulatory Evidence, Risk Gate priority, and withholding positive conclusions while material risk is unresolved.

Together these rubrics cover the Agent-owned portions of Evidence Coverage, Citation Accuracy, Hallucination Resistance, Estimate Discipline, and unresolved-risk behavior requested by ECO-39. Apply should re-read the current file and record the mapping in the focused suite's test documentation or other test-local documentation without changing the scenario protocol. If the file remains substantively as inventoried, no new Agent scenario is needed and `tests/scenarios.md` should remain unchanged. A new scenario is permitted only when the live audit identifies a specific uncovered observable behavior; it must use the same fresh-context RED/GREEN procedure and fixed `PASS`/`FAIL` items.

Historical RED/GREEN result prose is evidence from its stated run date, not proof that a future Agent still passes. ECO-39 preserves the repeatable protocol; it does not claim byte-stable Agent output or automatically rerun an LLM during `unittest`.

Alternatives considered:

- Add seven Agent scenarios matching the deterministic fixture names: rejected because most dimensions belong to deterministic owners and duplication would add cost without a distinct oracle.
- Add an LLM judge or prose similarity test: rejected because it is non-deterministic, subjective, and outside the existing protocol.

### 6. Make acceptance failures local and preserve unrelated production defects

Evaluation tests should assert public values and reason/diagnostic state sufficiently to identify the broken owner. A negative scenario passes only when the expected fail-closed authoritative state is present; merely raising an arbitrary exception is not acceptance unless the existing boundary explicitly defines that exception.

If a fresh evaluation reveals production behavior that contradicts a living production spec, Apply should keep the reproducing fixture/test evidence and stop short of repairing the production owner. The contradiction should be proposed as a separate Change unless ECO-39 cannot construct or execute its own test-only contract without the correction. This prevents an evaluation task from silently changing Evidence, Gate, scoring, Red Team, workflow, or report semantics.

Alternative considered: repair any discovered defect inside ECO-39 to reach green. Rejected because it would erase scope ownership and make the evaluation baseline redefine the system it is intended to observe.

## Risks / Trade-offs

- [Large workflow fixtures become difficult to maintain] → Keep complete fixtures limited to genuinely cross-stage invariants and compose them from small explicit test-only builders.
- [A helper accidentally duplicates policy] → Builders construct inputs only; assertions call and inspect existing owners, and architecture tests can verify no production evaluation module appears.
- [Dimension coverage becomes nominal rather than behavioral] → Require at least one direct named oracle assertion for every dimension and maintain a clear dimension-to-test mapping in the focused module.
- [Shared fixtures couple unrelated tests] → Do not migrate existing focused tests; expose only scenario values with demonstrated ECO-39 reuse.
- [Agent behavior evidence becomes stale] → Preserve the fresh-context protocol and dated results, avoid claiming historical prose is current execution, and add no byte-comparison oracle.
- [Full suite runtime grows] → Keep inputs in-memory and deterministic, avoid parameter explosions, and reuse constructed bundles only inside the focused suite.

## Migration Plan

This is an additive test-only change with no runtime or data migration.

1. Add reusable test support and the focused automated evaluation module.
2. Audit the live Agent scenarios; retain them unchanged when the current mapping remains sufficient.
3. Run the focused evaluation module, then the complete standard-library test suite.
4. Validate the OpenSpec Change strictly.

Rollback consists of removing only the ECO-39 test support, focused tests, and any demonstrably required Agent scenario additions. No production state or schema rollback is needed.
