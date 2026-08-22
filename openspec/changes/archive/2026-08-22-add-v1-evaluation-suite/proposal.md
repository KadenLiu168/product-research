## Why

The v1 runtime path now reaches a deterministic structured workflow result and downstream final report, but the repository has no unified Phase 9 acceptance baseline that proves the integrated contracts remain traceable, fail closed, and replay-stable. ECO-39 adds that persistent regression contract now that its structured blockers, ECO-37 and ECO-38, are present on `main`.

## What Changes

- Add reusable test-only deterministic fixture builders for the required normal, missing, conflicting, expired, high-risk, economic-failure, and Evidence-based score-revision scenario families, plus a focused core-threshold failure variant.
- Add one focused standard-library `unittest` acceptance suite that maps all ten ECO-39 dimensions to explicit pass/fail oracles at the narrowest existing authoritative boundary.
- Exercise selected integration scenarios across the complete workflow → structured final state → final report path, including byte-identical report replay and current-run Evidence traceability.
- Assert existing fail-closed Evidence, scoring, Gate, Red Team, workflow, and reporting behavior without reimplementing their semantics or producing an aggregate evaluation-quality score.
- Inventory and map the existing `tests/scenarios.md` fresh-context RED/GREEN scenarios to Agent-owned acceptance behavior; add a scenario only if an observable Hallucination Resistance, Estimate Discipline, Evidence/citation discipline, or unresolved-risk behavior remains uncovered.
- Keep the suite offline, explicit-input driven, independent of wall-clock time and randomness, and free of live providers, browsers, scrapers, LLM judging, persistence, or third-party test dependencies.

## Capabilities

### New Capabilities

- `v1-evaluation-suite`: Defines the reusable scenario matrix, ten acceptance-dimension oracles, deterministic automated acceptance boundaries, Agent behavior protocol reuse, and persistent v1 regression baseline.

### Modified Capabilities

None. Existing production capability requirements and ownership remain unchanged.

## Impact

- Expected implementation area: reusable test support under `tests/`, one focused v1 evaluation test module, and only demonstrably necessary additions to `tests/scenarios.md`.
- Existing public production APIs are consumed unchanged, including Evidence Policy / Assessment, scoring and decision, Red Team revision, `run_end_to_end_workflow(...)`, `EndToEndWorkflowResult`, and `render_final_report(...)`.
- No new `product_research/` module, runtime dependency, production policy, test framework, third-party package, external service, or data persistence is introduced.
- Full acceptance remains `python3 -m unittest discover -s tests` plus the existing manual fresh-context RED/GREEN Agent protocol.
