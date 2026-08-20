## Context

See `proposal.md` for motivation. The current `red_team_revision.py` already has the correct sibling-capability shape and preserves authoritative before/after results, but two boundary checks are incomplete:

- `_accepted_economics_revision(...)` compares complete `GateResult` objects, so a changed `actual_margin` or `reasons` value can create a revision even when both Gate outcomes and `EconomicsOutcome` are unchanged.
- structural validation often checks exact Python type and accesses `.value`, but not every retained closed value is reconstructed through its real constructor. An object forged with `object.__new__` / `object.__setattr__` can therefore retain the expected Python type while carrying an invalid closed-vocabulary or Evidence-ID payload.

The living `red-team-score-revision` spec already defines the correct externally observable behavior. This Change therefore has `skip_specs: true`; implementation must move toward the living spec without editing it or the archived ECO-36 artifacts.

## Goals / Non-Goals

**Goals:**

- Separate economics revision detection from complete authoritative result retention.
- Fail closed when Red Team-retained Evidence IDs or closed values are forged, without leaking validation exceptions.
- Preserve whole-run invalidity for malformed provenance and per-target isolation for locally invalid findings, score proposals, Risk proposals, or economics proposals.
- Reuse domain constructors and `__post_init__` methods as structural validators while keeping business semantics in their existing owners.

**Non-Goals:**

- Recalculate Unit Economics, reclassify Risk, rerun Evidence Policy or Assessment, or execute Initial Scoring or scoring-decision policy.
- Add a generic validation framework, registry, serialization layer, Gate abstraction, diagnostic taxonomy, event log, persistence, runtime identity, or ECO-37 orchestration.
- Change any public input/output shape, authoritative owner, threshold/formula, Risk aggregation rule, living spec, archived Change, Agent documentation, or unrelated code.

## Decisions

### 1. Compare only the three authoritative economics state values

After exact authoritative-result validation and the existing threshold-equality guard, compute revision existence from:

```text
initial.minimum_viability_gate.outcome != revised.minimum_viability_gate.outcome
OR initial.dynamic_target_gate.outcome != revised.dynamic_target_gate.outcome
OR initial.outcome != revised.outcome
```

If all three are unchanged, return no economics revision even when contribution profit, contribution margin, Gate `actual_margin`, or reasons differ. If one changes and all authorization checks pass, retain the complete initial and revised `UnitEconomicsResult` values in the existing `EconomicsGateRevisionRecord`.

Alternative considered: compare complete `GateResult` or `UnitEconomicsResult` values. Rejected because those values include findings and measurements that are not authoritative Gate/outcome state. Alternative considered: retain only the three compared fields. Rejected because the existing history contract requires complete authoritative before/after results.

### 2. Keep threshold equality as an earlier independent policy guard

Compare both corresponding retained thresholds before accepting any state transition. A mismatch in either Minimum Viability or Dynamic Target threshold rejects the complete economics proposal, even when a Gate outcome or `EconomicsOutcome` also changes. Equal `None` values remain equal.

Alternative considered: accept the transition for the unchanged-threshold Gate only. Rejected because an economics proposal is one complete authoritative comparison, and partial acceptance would conceal policy mutation.

### 3. Harden the central Evidence-ID validator by reconstruction

Extend the existing canonical tuple validator rather than adding checks at each call site. For every tuple member:

1. require `type(evidence_id) is EvidenceId`;
2. read `evidence_id.value`;
3. require `EvidenceId(evidence_id.value)` to construct successfully;
4. then perform uniqueness and lexical-order checks.

All existing callers inherit this validation: top-level baseline/current-run provenance, findings, proposal causal IDs, revised concrete score traces, economics result traces, and the Risk result Evidence-ID collections explicitly traversed by the Red Team boundary.

Reconstruction must happen before set membership or hashing can authorize a forged value. The existing catch-and-reject flow converts constructor, attribute, equality, or hashing failures into the correct whole-run or local fail-closed outcome.

Alternative considered: duplicate a regular expression or inspect `EvidenceId._pattern`. Rejected because the domain constructor is the canonical contract and avoids policy drift.

### 4. Use one minimal private helper for closed-value authenticity

Where it reduces repetition, add a private helper equivalent to:

```text
type(value) is expected_type
AND expected_type(value.value) constructs successfully
```

Use it only for explicit closed value classes already imported by `red_team_revision.py`. Do not add reflection, a type registry, recursive serialization, or generic domain traversal.

Alternative considered: rely only on parent dataclass `__post_init__`. Rejected because several current domain validators assert nested exact types but do not reconstruct every nested `.value`, which is the forged-value gap this patch closes.

### 5. Explicitly traverse retained Unit Economics closed values and IDs

`_economics_result_is_valid(...)` continues to call the existing `UnitEconomicsResult`, `ContributionProfit`, `ContributionMargin`, and both `GateResult` `__post_init__` methods. It additionally authenticates:

- `Status`, `Confidence`, and Evidence IDs in Contribution Profit;
- `Status`, `Confidence`, and Evidence IDs in Contribution Margin;
- `GateOutcome` and every nested `ReasonCode` in both Gate results;
- result-level `EconomicsOutcome`, every result-level `ReasonCode`, and result-level Evidence IDs.

The boundary validates only retained structure and closed vocabulary. It does not derive amounts, margins, thresholds, Gate outcomes, reasons, or the aggregate economics outcome.

### 6. Explicitly traverse retained Risk closed values and IDs

`_risk_result_is_valid(...)` continues to call `RiskComplianceResult.__post_init__` and the existing nested `RiskFinding` / `RiskPropositionKey` validators. It additionally authenticates the closed values and Evidence IDs on paths the revision history retains or relies upon:

- all required, supported, unresolved, and missing `RiskArea` values;
- result `RiskGateState` and result diagnostics;
- each duplicate proposition key's `RiskArea`;
- each finding's `RiskArea`, `RiskFindingOutcome`, optional `RiskClassification`, `Confidence`, diagnostics, and supporting/adverse/excluded Evidence IDs.

This is deliberately not a recursive validation of `EvidenceAssessmentResult` business semantics. Existing nested domain validation remains authoritative; the Red Team boundary only prevents forged directly retained identity and closed-vocabulary values from entering revision history.

### 7. Preserve failure granularity and public behavior

The shared provenance validator remains whole-run: a forged baseline or current-run Evidence ID returns unchanged scores and no accepted findings or revisions. A forged member confined to one finding or proposal rejects only that member/target; independent valid score targets continue. A forged authoritative economics result rejects only `economics_revision`, and a forged authoritative Risk result rejects only `risk_revision`; independent score revisions remain eligible.

No new rejection output is added. Absence of the affected record and preservation of the relevant initial state remain the observable fail-closed behavior.

## Risks / Trade-offs

- [Calling existing `__post_init__` methods on forged frozen values can raise from nested access, hashing, or ordering] → Keep validation inside narrow exception-to-`False` boundaries and add no catch outside the expected structural exception family unless a test proves a real leak.
- [A helper could drift into a generic validation engine] → Limit it to exact type plus constructor reconstruction and keep explicit traversal at the two authoritative-result validators.
- [Risk nested objects contain deeper Evidence Assessment values] → Validate the closed values and Evidence-ID collections directly retained by Risk revision history, reuse existing nested validators, and do not reproduce Evidence Assessment semantics.
- [Test fixtures built through normal constructors cannot express forged states] → Forge only the targeted immutable member, rebuild the minimum containing object with `object.__new__` / `object.__setattr__`, and keep all unrelated fixture fields valid so each test isolates one boundary.
- [A broad cleanup could obscure this corrective patch] → Restrict production edits to the existing validation helpers and economics acceptance predicate; restrict tests to focused contract cases.

## Migration Plan

1. Add RED tests for economics state-change semantics and forged structural values, including whole-run and per-target isolation.
2. Make the minimum changes in `product_research/red_team_revision.py` to satisfy those tests.
3. Run the focused Red Team suite, named Phase 7/Gate/decision regressions, full suite, and `openspec validate --all --strict`.
4. Inspect the final diff for scope containment and unchanged downstream `evaluate_scoring_decision(...)` compatibility.

There is no stored-data or API migration. Rollback consists of reverting the two implementation/test files from the future Apply; the planning artifacts and historical ECO-36 archive do not participate in runtime behavior.
