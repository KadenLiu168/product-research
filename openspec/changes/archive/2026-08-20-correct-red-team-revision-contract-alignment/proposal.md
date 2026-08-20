## Why

The archived ECO-36 implementation does not fully enforce the already-correct `red-team-score-revision` living contract: it can mistake non-state `UnitEconomicsResult` changes for a Gate revision, and forged immutable closed values can bypass parts of the Red Team boundary's structural validation. This corrective patch aligns implementation and tests with the existing contract before ECO-37 depends on the boundary.

## What Changes

- Determine an economics revision only from changes to the Minimum Viability Gate outcome, Dynamic Target Gate outcome, or `EconomicsOutcome`, while preserving the existing equal-threshold policy guard and complete before/after authoritative results.
- Strengthen the central canonical Evidence-ID check so exact-type `EvidenceId` instances with forged invalid payloads fail reconstruction before uniqueness, ordering, membership, or authorization checks.
- Strengthen structural authenticity checks for the closed values and Evidence-ID collections retained by authoritative Unit Economics and Risk results, reusing existing constructors and `__post_init__` validation without duplicating upstream business semantics.
- Add test-first contract coverage for state-preserving economics changes, each accepted authoritative state transition, threshold mutation, forged provenance and per-target Evidence IDs, forged nested economics and Risk values, and failure isolation.
- Preserve the existing Phase 8 architecture, score and Gate ownership, downstream `DimensionScores` compatibility, and all out-of-scope boundaries. Do not change the living spec or archived ECO-36 artifacts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The existing `red-team-score-revision` living specification already requires the target behavior, so this Change opts out of delta specs and corrects only implementation and test conformance.

## Impact

- Expected implementation files: `product_research/red_team_revision.py` and `tests/test_red_team_revision.py` only.
- No public API shape, score hierarchy, Gate state, formula, Risk aggregation rule, Initial Scoring rule, dependency, persistence format, provider, LLM, network, clock, randomness, reporting, or orchestration behavior is added.
- Existing `initial_scoring.py`, `scoring_decision.py`, authoritative Risk and Unit Economics owners, `openspec/specs/red-team-score-revision/spec.md`, and `openspec/changes/archive/2026-08-20-add-red-team-score-revision/` remain unchanged.
