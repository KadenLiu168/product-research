## Context

See `proposal.md` for motivation and `specs/red-team-score-revision/spec.md` for observable behavior. Current `main` already exposes the exact immutable values this capability must compare and preserve:

- `EvidenceId` and `Confidence` in `product_research/evidence.py`;
- the closed eight-value `Dimension`, `DimensionScore`, and `DimensionScores` contracts in `product_research/scoring_decision.py`;
- authoritative `RiskComplianceResult` with the canonical `RiskGateState` in `product_research/risk_compliance.py`;
- authoritative `UnitEconomicsResult`, including both retained Gate results and their policy thresholds, in `product_research/unit_economics.py`;
- `evaluate_initial_scoring(...)` and `evaluate_scoring_decision(...)` on the two sides of the proposed Phase 8 boundary.

Those owners are frozen. `DimensionScore` validates the general score shape and canonicalizes its Evidence IDs, while Initial Scoring alone owns upstream dimension routing, nested uncertainty, Confidence ceilings, and the profitability rubric. The Red Team layer must therefore accept an already-normalized proposed score but add current-run authorization and history checks without treating successful construction as proof that a revision is allowed.

## Goals / Non-Goals

**Goals:**

- Express caller-generated findings and proposed changes as a small immutable input vocabulary.
- Separate whole-run validity, per-dimension acceptance, and optional authoritative Gate comparison so one local failure cannot contaminate unrelated valid dimensions.
- Make an actual state transition provable from the output alone: initial value, revised value, reason, and causal Evidence IDs remain together.
- Preserve direct compatibility with the existing score and authoritative result types instead of introducing adapters or copied domain models.

**Non-Goals:**

- Prove the semantic truth of a caller reason or decide whether cited Evidence actually entails it.
- Re-run any upstream capability or accept raw values that bypass an authoritative result.
- Add a diagnostic taxonomy, event log, identity, timestamp, storage format, or orchestration envelope not required by ECO-36.

## Decisions

### 1. Add one flat sibling module with a single pure evaluator

Apply should add `product_research/red_team_revision.py`, matching the repository's flat capability layout. It should expose one evaluator conceptually shaped as:

```text
initial DimensionScores
+ baseline Evidence IDs
+ current-run Red Team Evidence IDs
+ Red Team findings
+ per-dimension score revision proposals
+ optional authoritative Risk revision proposal
+ optional authoritative Unit Economics revision proposal
    -> immutable Red Team revision result
```

The exact public evaluator name should follow the existing `evaluate_<capability>(...)` convention; `evaluate_red_team_revision(...)` is the preferred minimal name. The module may introduce only the immutable input and record types needed to express findings, score proposals, authoritative-result proposals, and the combined result. It should import existing domain values rather than re-exporting or copying them.

Dependency direction remains:

```text
Agent / caller reasoning
        |
        v
existing analysis / Risk / Unit Economics / Initial Scoring
        |
        v
red_team_revision  ---> existing DimensionScores ---> scoring_decision
```

No upstream module and no scoring-decision code should import the Red Team module.

Alternatives considered:

- Add a mode to `initial_scoring.py`: rejected because Phase 7's ownership and output are frozen and initial values would no longer remain an independent boundary.
- Add revision behavior to `scoring_decision.py`: rejected because that module executes weights, thresholds, and Gate precedence over already-normalized inputs.
- Build a generic workflow/event framework: rejected because ECO-37 owns orchestration and ECO-36 needs no persistence or event identity.

### 2. Keep the public input vocabulary small and role-specific

The preferred minimal immutable values are:

- one finding value with non-empty text and causal Evidence IDs;
- one score proposal with `Dimension`, proposed `DimensionScore`, non-empty reason, and causal Evidence IDs;
- one Risk proposal containing initial and revised `RiskComplianceResult` values plus reason and causal IDs;
- one economics proposal containing initial and revised `UnitEconomicsResult` values plus reason and causal IDs;
- one result containing initial/revised scores, accepted findings, accepted score revision records, and optional accepted Risk/economics revision records.

Risk and economics use distinct proposal and record shapes because their authoritative result types and comparison rules differ. A generic `GateRevision[T]` abstraction would add typing machinery and obscure policy-threshold validation for a single use per owner. Raw `RiskGateState`, `GateOutcome`, or `EconomicsOutcome` parameters must not exist on the public evaluator.

The optional authoritative proposals represent claimed actual changes. If new Evidence produces no Gate/outcome change, the caller records a finding and supplies no Gate proposal. This avoids a second type for a no-op comparison and keeps “finding” distinct from “revision.”

Exact dataclass names may be adjusted during Apply to match local readability, but their roles and fields must not be merged in ways that weaken the spec.

### 3. Validate run provenance before any revision authorization

`baseline_evidence_ids` and `red_team_evidence_ids` should be exact tuples. Validation should require exact `EvidenceId` members, lexical order by `.value`, uniqueness within each tuple, and disjointness across tuples. Unlike `DimensionScore`, this boundary must reject non-canonical provenance rather than normalize it, because silently sorting or deduplicating caller-owned run identity would conceal a malformed authorization contract.

If the initial scorecard has the wrong exact type, the evaluator cannot preserve a trustworthy initial state and should reject the call with the repository's ordinary constructor/input exception style; it must not create a parallel optional scorecard result. If the initial scorecard is valid but either provenance tuple or a top-level findings/proposals collection is malformed, return a conservative result with `revised_scores == initial_scores`, no accepted revisions, and no accepted Gate trace. Invalid ordinary members of valid tuples are handled locally as described below.

This two-level behavior makes “fail closed” concrete:

```text
invalid initial scorecard       -> no result can be constructed
invalid run aggregate/provenance -> valid initial retained, no changes authorized
invalid member/target           -> that member/target rejected, independent targets continue
```

Alternative considered: always raise on any malformed input. Rejected because a single bad dimension would erase independently valid revision work and contradict the per-target acceptance contract.

### 4. Revalidate immutable inputs at the evaluator boundary

New frozen dataclasses should validate exact types, non-empty strings, exact tuples, unique and lexically ordered Evidence IDs, and their own local structural invariants at construction. The evaluator should still re-run or equivalently reproduce those checks so forged frozen values cannot bypass the public boundary, following the existing repository pattern.

The evaluator must also revalidate relevant existing values where their constructor contract is looser than ECO-36:

- an unresolved proposed `DimensionScore` is accepted only when it is exactly `None`, `Low`, and `()`;
- a concrete proposed score must contain a causal current-run ID in its own existing score trace;
- a same-score/same-Confidence proposal is a no-op even if Evidence IDs differ, so the initial value is retained rather than replacing it for enrichment.

The deterministic layer validates identity relationships and explicit state equality only. It does not validate dimension ownership or recompute an upstream Confidence ceiling; producing a semantically supported proposal remains the caller's responsibility through the existing owner and Initial Scoring flow.

### 5. Group score proposals by target before validating a winner

For a valid proposal tuple, first identify every exact valid `Dimension` target and count proposals by target. Any target appearing more than once is marked ineligible before proposal validity, direction, score, Confidence, reason, or ordering is considered. This ensures two identical proposals and two conflicting proposals fail the same way and prevents an invalid first/valid second ordering loophole.

Then visit the fixed existing dimension order. For a target with exactly one proposal:

1. validate the proposal's typed fields and causal IDs against the declared universe;
2. require at least one causal current-run ID;
3. compare only score and Confidence to determine whether an actual revision exists;
4. validate canonical unresolved or concrete current-run grounding as applicable;
5. create the revision record and replace that target only if all checks pass.

Start from the eight values extracted from `initial_scores`, then build a new `DimensionScores` once from the accepted replacements. Never mutate a score and never fold over caller proposal order.

Malformed members whose target cannot be safely identified are discarded as members; they cannot create or collide with a target. A forged or otherwise invalid member with a safely validated target makes that target ineligible. This distinction prevents malformed input from authorizing a value while preserving failure isolation.

Alternative considered: validate proposals sequentially and keep the first valid value. Rejected because order would become a hidden winner-selection policy.

### 6. Findings have no authority over state

A finding should carry non-empty text and a canonical non-empty Evidence-ID tuple. Accept it only when every ID is in the run universe and the tuple intersects `red_team_evidence_ids`. Findings should be ordered deterministically by text and then Evidence-ID values; exact duplicate findings should not be silently deduplicated into one claim. The simplest conservative treatment is to reject every exact duplicate occurrence while retaining other independently valid findings.

Findings never participate in score or Gate acceptance. A caller that wants a state change must submit the corresponding explicit proposal with its own reason and causal IDs. This deliberate duplication of trace at the call boundary prevents a proposal from relying on positional or implicit association with a finding.

Alternative considered: link revisions to generated finding IDs. Rejected because runtime identifiers and persistence are out of scope, and the revision record already contains the required self-contained causal trace.

### 7. Gate records compare authoritative result values only

Risk validation requires exact `RiskComplianceResult` values and compares only their existing `risk_gate` values to decide whether a Gate transition occurred. Accepted output retains both complete authoritative results, the reason, and causal IDs. It must not reconstruct a Risk result, inspect proposition text, or execute gate precedence.

Economics validation requires exact `UnitEconomicsResult` values and compares:

- `minimum_viability_gate`;
- `dynamic_target_gate`;
- `outcome`.

Before accepting any change, compare the retained `threshold` on each corresponding Gate. Both threshold pairs must be equal, including equal `None` values. This is an equality guard, not policy execution. If either threshold differs, reject the complete economics revision trace; do not accept only the Gate whose threshold happened to remain equal. Accepted output retains both complete results so later orchestration can inspect all other changed economics values without Red Team taking calculation ownership.

Both Gate proposal types independently require a non-empty reason, causal IDs entirely within the run universe, and at least one current-run causal ID. No Gate/outcome difference means no record. New Evidence with unchanged Gate state belongs in findings.

Alternatives considered:

- Accept raw before/after Gate values: rejected because callers could bypass the authoritative owner.
- Re-run Risk or economics logic inside Red Team: rejected because it duplicates frozen precedence and calculation semantics.
- Permit threshold changes when they have Evidence IDs: rejected because thresholds are caller policy, not observed Evidence.

### 8. Canonical output ordering follows existing closed vocabularies

Ordering should be explicit and independent of input order:

- revised score slots: existing `DimensionScores` field order;
- score revision records: existing `Dimension` order;
- findings: finding text, then lexical Evidence-ID tuple;
- Evidence IDs inside new values: lexical `.value` order;
- optional authoritative records: fixed Risk field followed by economics field in the result shape, not a heterogeneous collection.

Frozen dataclasses and tuples provide immutability and equality-based replay checks. Do not add timestamps, UUIDs, counters, hashes as identity, or `__dict__`-backed mutable collections.

### 9. Documentation and tests prove boundaries rather than implementation detail

Apply should add focused `unittest` coverage in `tests/test_red_team_revision.py` using real existing domain constructors. Tests should exercise public values and evaluator behavior, include AST/source-boundary checks consistent with existing architecture tests, and pass revised scores directly into `evaluate_scoring_decision(...)`.

`tests/scenarios.md` should add the requested Agent RED/GREEN cases. `SKILL.md`, `references/methodology.md`, `references/scoring-policy.md`, `references/gates.md`, `references/report-contract.md`, and `docs/product-research-skill-spec.md` should be inspected, but edited only where their current statements would contradict the shipped boundary. Documentation must continue to say the deterministic core cannot generate objections, acquire or interpret Evidence, or make a final decision.

## Risks / Trade-offs

- [A normalized `DimensionScore` proves shape but not that the caller reran the correct upstream route] → Require new-Evidence intersection in every revised concrete score and keep ownership explicit in Skill/scenarios; do not duplicate Initial Scoring in Phase 8.
- [A malformed top-level aggregate could contain useful members] → Preserve the initial scorecard and authorize nothing, because recovering selected values would create an undocumented repair policy.
- [Per-target failure can make the revised scorecard partially changed] → Preserve complete accepted revision records and exact unchanged slots; partial validity is intentional and matches existing fail-closed-by-ownership behavior.
- [Rejecting duplicate findings can lose a repeated observation] → Findings are value records, not occurrence logs; callers can express distinct findings with distinct text/causal trace, while persistence and frequency tracking remain out of scope.
- [Risk results do not expose one result-level Evidence-ID tuple] → Keep causal IDs as explicit revision provenance without inventing a Risk trace index or reinterpreting Risk findings.
- [Equal economics thresholds do not prove every upstream policy input is identical] → ECO-36 freezes only the two Gate policy anchors named by the contract; broader policy versioning would require a future authoritative policy identity contract.
- [No rejection diagnostic vocabulary makes invalid proposals visible only through unchanged output and absent records] → Keep v1 narrow and test every rejection behavior; add diagnostics only through a future explicit contract if orchestration requires them.

## Migration Plan

1. Add RED public-contract tests and Agent scenarios for run provenance, no-new-Evidence authorization, score transitions, no-op findings, conflict isolation, authoritative Gate ownership, determinism, immutability, and downstream compatibility.
2. Add the focused module and minimum immutable input/output types; make the RED tests pass without modifying existing scoring, Risk, or economics behavior.
3. Align only the Skill and reference statements needed to route Phase 8 through the new caller-to-deterministic boundary.
4. Run focused Red Team tests, the named Phase 7/Risk/economics/scoring regressions, the full suite, and strict OpenSpec validation; inspect static dependency boundaries and the final diff.

The change is additive and has no stored-data migration. Rollback removes the new module, tests, and documentation routing; all pre-existing APIs and results remain unchanged.
