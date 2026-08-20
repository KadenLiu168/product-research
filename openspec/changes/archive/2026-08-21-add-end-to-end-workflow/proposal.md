## Why

The repository now has deterministic Research → Evidence, analysis, Gate, Initial Scoring, decision, and Red Team boundaries, but no authoritative coordinator connects them into one traceable result. ECO-37 is required now to freeze that integration contract after ECO-36 and provide the structured upstream boundary for ECO-38 without prematurely taking ownership of report generation.

## What Changes

- Add one thin deterministic end-to-end workflow capability with a fixed 16-stage order above the existing modules.
- Add immutable stage execution state that distinguishes `COMPLETE`, `UNRESOLVED`, `BLOCKED`, and `FAILED` while retaining the existing authoritative result objects and all earlier unresolved or failure information.
- Compose the real Research, Evidence, Risk, Unit Economics, Phase 6 analysis, Initial Scoring, scoring-decision, and Red Team revision boundaries without duplicating their business semantics, identifiers, thresholds, or result hierarchies.
- Reuse `evaluate_scoring_decision(...)` for both the initial and final decisions, and reuse the existing Red Team evaluator for explicit caller-owned, Evidence-backed revisions.
- Resolve Stage 16 from revised scores and accepted authoritative Risk / Unit Economics revisions, retain both initial and final `DecisionResult` values, and return one structured final workflow result.
- Align `SKILL.md` and relevant methodology documentation so Stage 16 terminates in the structured Final Result; human-readable report and Evidence Appendix generation remain a downstream ECO-38 responsibility.
- Add focused contract tests and Agent RED/GREEN scenarios for deterministic ordering, real composition, unresolved propagation, blocking, valid negative outcomes, revision resolution, and architectural boundaries.
- Exclude provider-backed acquisition, autonomous reasoning, proposition or judgment generation, policy changes, persistence, workflow-engine infrastructure, report rendering, and ECO-39 evaluation infrastructure.

## Capabilities

### New Capabilities

- `end-to-end-workflow`: Defines the canonical 16-stage deterministic coordinator, immutable execution trace, authoritative pre/post-Red-Team state resolution, and structured final analytical result.

### Modified Capabilities

None. Existing capability requirements and ownership remain unchanged; Skill and methodology wording is aligned to the new integration boundary without changing lower-level contracts.

## Impact

- Expected implementation area: one focused workflow module, one focused workflow contract-test module, Agent scenarios, and only the Skill/methodology wording needed to expose the ECO-37 → ECO-38 handoff.
- Public integration surface: a minimal explicit workflow input/coordinator contract plus immutable ordered stage records and one structured workflow result that references existing authoritative domain outputs directly.
- Existing lower-level modules remain dependency leaves relative to the workflow and require no imports from the new capability, migrations, external dependencies, network access, clock, randomness, persistence, or hidden policy.
