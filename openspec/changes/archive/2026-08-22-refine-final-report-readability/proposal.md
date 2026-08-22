## Why

ECO-38's final-report capability is functionally complete and evidence-traceable, but parts of its main body still expose verbose workflow traces, internal field vocabulary, and full authoritative object representations that read more like an audit/debug projection than a concise research report. This refinement closes that known readability gap before ECO-39 evaluates Report Traceability, without changing any authoritative model, workflow, analytical, scoring, Gate, Red Team, decision, or Evidence semantics.

## What Changes

- Compact the Executive Summary so complete workflows report completion once, while incomplete workflows expose only `UNRESOLVED`, `BLOCKED`, and `FAILED` stages with retained failure kinds and blocking dependencies.
- Use explicit fixed reader-facing labels in analytical sections and Key Uncertainties instead of user-visible internal `snake_case` field names.
- Render every required authoritative finding in a compact deterministic layout that preserves outcomes, Confidence, diagnostics/factors, and supporting, adverse, and excluded Evidence IDs without ranking, omission, or semantic summarization.
- Present accepted Score, Risk, and Unit Economics Red Team revisions as concise authoritative state transitions rather than full result-object representations.
- Preserve the existing 15-section structure, Scorecard semantics, Key Evidence membership, incomplete-state behavior, deterministic rendering, fail-closed traceability, and complete lossless Evidence Appendix.
- Align `references/report-contract.md` with the refined presentation contract and remove reporting's unnecessary dependency on the private `scoring_decision._FIELD_NAMES` registry without changing scoring arithmetic or APIs.
- Keep Linear synchronization as a post-implementation completion action: do not create another ECO, change ECO-38/ECO-39 state, or encode Linear state in runtime requirements during this Change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `final-report-generation`: Refine the existing downstream Markdown presentation requirements for concise workflow status, fixed reader-facing labels, compact lossless findings, and material Red Team transitions while preserving all authoritative and traceability guarantees.

## Impact

- Affected implementation is limited to the existing reporting module and its private presentation helpers; the public reporting boundary remains unchanged unless implementation evidence demonstrates a correctness need.
- Focused final-report tests, documentation assertions, and `references/report-contract.md` will be aligned during Apply; the existing `final-report-generation` living specification will be aligned only through the later separately authorized sync/archive workflow after implementation and independent acceptance.
- Existing workflow, Evidence, domain analysis, Unit Economics, Risk, scoring, decision, and Red Team models and policies remain unchanged. ECO-39 evaluation fixtures and infrastructure remain out of scope.
