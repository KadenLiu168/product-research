## Context

See `proposal.md` for motivation. Stage 3 already retains the immutable `ResearchRunResult` with validated required-task coverage, while Stages 13 and 16 call the same `evaluate_scoring_decision(...)` boundary. `DecisionResult` is the authoritative decision state consumed by final reporting, and the report can separately reach the retained Stage 3 research result. ECO-60 intentionally keeps provider execution and caller-owned semantic sufficiency separate; this design must combine them without moving either ownership boundary.

## Goals / Non-Goals

**Goals:**

- Add exactly one caller judgment, one workflow derivation, and one decision prerequisite.
- Preserve a structured fail-closed result when readiness is omitted or malformed.
- Reuse the same derived value and label executor at Stages 13 and 16.
- Let reporting join authoritative decision readiness with existing Stage 3 detail without duplicating research state.

**Non-Goals:**

- A readiness class, engine, hierarchy, registry, score, or semantic inference algorithm.
- Any change to `ResearchRunResult`, provider-first/fallback policy, Evidence semantics, provider execution, or the 16-stage sequence.
- Report-owned decision or readiness policy, a new report section, or provider-specific reporting state.

## Decisions

### 1. Use exact booleans and `None` as the existing fail-closed absence representation

The workflow keyword input will be named `required_research_semantically_satisfied`; the decision input will be named `required_research_ready`. Both accept only exact `bool` values as valid. Their Python boundary default will be `None`, which is not a positive default: omission and any other non-boolean value remain invalid and produce `RESEARCH_READINESS_INPUT_ERROR` at the decision boundary. This preserves the existing structured-result error mode and lets unchanged callers fail closed instead of escaping with a signature `TypeError`.

`DecisionResult.required_research_ready` will be `True` or `False` for a valid input and `None` for an invalid input. Valid `False` adds `RESEARCH_READINESS_INCOMPLETE`; invalid input adds only `RESEARCH_READINESS_INPUT_ERROR`. Both reasons join the existing set-based, declared-priority normalization, so output stays duplicate-free and replay-stable.

Alternative considered: make the new argument syntactically required. Rejected because an omitted argument would raise before the public executor could return the required structured input diagnostic. A custom sentinel was also rejected because `None` already represents invalid/missing decision inputs in this module.

### 2. Derive readiness once from the retained Stage 3 result

After the workflow has retained Stage 3, one private local helper will validate only the existing `ResearchRunResult` contract and compute:

```text
execution_ready =
    valid ResearchRunResult
    and status == COMPLETE
    and missing_required_task_ids == ()

required_research_ready =
    execution_ready
    and required_research_semantically_satisfied
```

For an exact caller boolean this yields an exact boolean. `true` cannot override incomplete execution; `false` remains false even for complete execution. If the caller input is missing or malformed, the helper returns `None` so the authoritative executor emits the distinct input diagnostic. The helper does not inspect task content, provider identity, Evidence text, acquisition metadata, or fallback state and does not mutate or wrap `ResearchRunResult`.

Alternative considered: add a `ResearchReadiness` value object or extend `ResearchRunResult`. Rejected because the composed value has one consumer contract and research orchestration must retain its existing execution-only semantics.

### 3. Add readiness only to the existing GO predicate

The scoring executor will validate readiness alongside its current inputs, retain the normalized value, and add the applicable reason. The `hard_failure` and `risk_review` predicates remain unchanged. Exact readiness `True` is added only to the existing complete-GO predicate; therefore readiness cannot weaken `NO-GO` or `RISK REVIEW`, and false/invalid readiness makes an otherwise eligible result `CONDITIONAL GO`.

Alternative considered: post-process a `GO` label after evaluation. Rejected because it would create a second label policy and could lose lower-precedence diagnostics.

### 4. Pass the same derived object value to both decision calls

The workflow computes readiness once and passes that exact value to the existing Stage 13 and Stage 16 calls. Red Team input and revision contracts receive no readiness field and cannot override it. `WorkflowFinalState` continues to expose final readiness through its existing authoritative `DecisionResult`; no duplicate workflow-final field is added.

Alternative considered: recompute at each decision stage. Rejected because a single local derivation is smaller and makes identical semantics directly testable through the two captured calls.

### 5. Report by joining existing authoritative owners

Executive Summary will add fixed labels for the final decision's normalized readiness, retained Stage 3 run status, and missing required task IDs. Key Uncertainties will include false/invalid readiness and, for existing missing required tasks, the matching structured `ResearchTask`/`TaskResult` values already available: task ID, source family, query intent, task status, and existing failure reasons. The report will not parse free text or arbitrary metadata and will not emit provider operation, provider task ID, fallback state, credentials, or configuration values unless a future authoritative structured contract separately adds them.

The Final Analysis Label continues to copy `DecisionResult.label` and reasons exactly. The Evidence Appendix remains untouched.

Alternative considered: copy missing-task details into `DecisionResult` or add a Research Readiness section. Rejected because either duplicates ownership or changes the canonical 15-section contract.

### 6. Migrate every repository caller explicitly

Existing direct decision fixtures that intentionally model a fully ready run will pass `required_research_ready=True`; new fail-closed tests will pass `False`, `None`, and malformed values. Existing workflow fixtures will pass the semantic judgment explicitly, extending the current partial-research fixture for override tests. No live provider path is needed.

Documentation updates are limited to `SKILL.md`, `references/scoring-policy.md`, and `references/report-contract.md`. `references/provider-first-acquisition-policy.md`, the research-orchestration spec, and provider documentation remain authoritative and unchanged.

## Risks / Trade-offs

- [An old caller omits the new input and its former `GO` becomes `CONDITIONAL GO`] → Treat this as the intentional fail-closed migration and update every repository caller explicitly.
- [A Python truthy value such as `1` could masquerade as ready] → Accept only `type(value) is bool`; do not coerce.
- [Malformed retained Stage 3 state could be treated as complete] → Reuse the existing `ResearchRunResult` validation contract before evaluating its status and missing IDs; any failure is not execution-ready.
- [Reporting could drift into acquisition-policy interpretation] → Render only fixed fields on existing structured objects and cover absent provider/fallback fields with negative tests.
- [Readiness reasons could reorder existing diagnostics] → Append the two new codes at one declared position and test duplicate-free equivalent replay.

## Migration Plan

1. Add RED contract tests for the decision input/result, precedence, workflow derivation/reuse, and report projection.
2. Add the minimal readiness field and decision predicate, then update all direct executor callers with explicit intent.
3. Add the workflow input and single derivation, update all workflow callers, and pass the value to both decision calls.
4. Add fixed report projections and synchronize only the three runtime-facing documents.
5. Run focused modules, the full offline `unittest` suite, OpenSpec strict validation, the repository quality gate, and diff checks.

Rollback is a single coordinated revert of the new parameters, result field, report lines, tests, and documentation; no persisted data or external migration exists.
