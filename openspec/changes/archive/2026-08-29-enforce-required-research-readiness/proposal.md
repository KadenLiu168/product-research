## Why

The workflow already retains deterministic required-task execution coverage, but the authoritative scoring/decision executor does not consume it, so otherwise-qualified inputs can still produce `GO` while required research is incomplete or semantically insufficient. ECO-60 is complete and deliberately left this decision-readiness consequence to ECO-61, so the gap can now be closed at the single existing decision boundary without changing provider, Evidence, or research-orchestration semantics.

## What Changes

- **BREAKING**: require callers of `evaluate_scoring_decision(...)` to provide one explicit provider-neutral effective required-research readiness input; missing or malformed input fails closed and cannot produce `GO`.
- **BREAKING**: require the 16-stage workflow caller to provide an explicit semantic-sufficiency judgment with no positive default, then combine it with the retained Stage 3 `ResearchRunResult` execution coverage.
- Preserve decision precedence: fatal Risk or unviable Unit Economics remains `NO-GO`, Risk review remains `RISK REVIEW`, and incomplete readiness only caps an otherwise eligible result at `CONDITIONAL GO`.
- Pass the same derived readiness value to the existing Stage 13 and Stage 16 decision calls, retaining one label engine and the fixed stage sequence.
- Project authoritative readiness, research status, missing required task IDs, and existing structured task failure context through Executive Summary and/or Key Uncertainties without report-level decision logic or a new report section.
- Synchronize the runtime-facing Skill, scoring policy, and report contract documentation while leaving ECO-60 and research-orchestration contracts unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `scoring-decision-engine`: add explicit fail-closed required-research readiness input, diagnostics, result traceability, and precedence behavior.
- `end-to-end-workflow`: accept caller-owned semantic sufficiency, derive effective readiness from Stage 3 execution coverage, and reuse it at Stages 13 and 16.
- `final-report-generation`: project retained readiness and existing research incompleteness state without changing the authoritative decision or canonical report structure.

## Impact

- Public APIs: `product_research.scoring_decision.evaluate_scoring_decision(...)` and `product_research.end_to_end_workflow.run_end_to_end_workflow(...)` gain required explicit inputs; all repository callers and deterministic fixtures must be updated.
- Result contracts: `DecisionResult` retains only the normalized effective readiness value needed for traceability; missing task and acquisition details remain in `ResearchRunResult` and workflow state.
- Runtime and tests: `product_research/scoring_decision.py`, `product_research/end_to_end_workflow.py`, `product_research/final_report_generation.py`, and their existing `unittest` suites and contract scenarios.
- Documentation: `SKILL.md`, `references/scoring-policy.md`, and `references/report-contract.md`.
- No new dependency, provider integration, workflow stage, decision label, report section, or live/billable test path.
