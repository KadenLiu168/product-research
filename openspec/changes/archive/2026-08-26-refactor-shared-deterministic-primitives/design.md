## Context

See `proposal.md` for motivation. The current repository has four relevant duplication groups:

- `scoring_decision.py` and `unit_economics.py` define behavior-equivalent private `_ClosedValue` bases.
- `evidence_assessment.py`, `unit_economics.py`, `initial_scoring.py`, and `market_demand.py` encode the same ordinal Confidence relation with incidental integer maps that differ in numeric values.
- `brand_content.py`, `supply_chain.py`, and `risk_compliance.py` repeat a strict canonicalization cluster; Competition and VOC contain superficially similar helpers with different duplicate semantics.
- `red_team_revision._score_is_valid(..., canonical_unresolved=...)` has a non-default branch with no current repository caller found during proposal investigation, but removal requires a fresh Apply-time repository-wide check.

The living specs already define the authoritative capability behavior. This Change therefore uses `skip_specs: true`; implementation and new characterization coverage must converge on the existing contracts rather than changing them.

The intended dependency direction is:

```text
_deterministic_primitives.py (stdlib only)
  -> scoring_decision.py
  -> unit_economics.py
  -> only other proven ordinal-only consumers

evidence.py + evidence_assessment.py
  -> _analysis_support.py
       -> brand_content.py
       -> supply_chain.py
       -> risk_compliance.py

risk_gate.py (remains isolated; no package-internal imports)
```

## Goals / Non-Goals

**Goals:**

- Make each extracted implementation canonical only after valid, malformed, duplicate, ordering, immutability, and exception behavior are proven equivalent.
- Keep shared code private, narrow, deterministic, and dependency-safe.
- Retain domain vocabularies and policy at their current owners.
- Preserve byte-for-byte Decimal configuration and the current arithmetic call paths.
- Leave focused tests that detect a future divergence at each shared boundary and negative boundary.

**Non-Goals:**

- Unify all validation helpers, introduce a framework, or make domain differences configurable through flags.
- Move public types, exports, constructors, policies, formulas, outcomes, fallbacks, or ownership.
- Make Evidence inherit from the shared closed-value base or make `risk_gate.py` consume package code.
- Normalize Competition, VOC, or Market Demand merely because a helper name or body looks similar.
- Change acquisition, provider, DataForSEO, configuration, orchestration, report, persistence, Skill, or living-spec behavior.

## Decisions

### 1. Require a written equivalence inventory before each extraction

Apply begins by recording every candidate consumer and comparing: accepted inputs, exact-type versus `isinstance` checks, malformed types, invalid payloads, duplicate policy, canonical ordering, exception type/message where observable, return type, mutation behavior, and caller fallback. An implementation is extracted only when at least two current consumers match across all relevant dimensions.

The inventory is a gate, not a request to generalize differences. A candidate that fails one dimension stays local. No flag such as `reject_duplicates=` may be added to disguise different domain contracts.

Alternative considered: extract identical-looking bodies first and rely on the full suite. Rejected because existing suites may not cover malformed or duplicate permutations, and name/body similarity is weaker evidence than caller behavior.

### 2. Use two private support layers with one-way dependencies

Create `product_research/_deterministic_primitives.py` for primitives that can remain independent of Evidence Assessment and structured-analysis modules. It may use only the standard library. Create `product_research/_analysis_support.py` for the strict analysis cluster because those helpers require `EvidenceId`, `EvidenceRelation`, `IndependenceAssignment`, and `MissingInformation`.

Neither module is exported from `product_research.__init__`. `_analysis_support.py` may import Evidence and Evidence Assessment types; `evidence.py` and `evidence_assessment.py` must not import `_analysis_support.py`. This avoids a reverse dependency and keeps the Evidence representation boundary authoritative.

Alternative considered: one catch-all `_shared.py`. Rejected because it would mix low-level immutable values with analysis-specific policy types and invite circular dependencies and unrelated reuse.

### 3. Share the closed-value base only between Scoring Decision and Unit Economics

Move the exact common `_ClosedValue` implementation into `_deterministic_primitives.py`; keep each subclass and `_allowed` vocabulary in its current module. Preserve string-only construction, closed membership, single-assignment immutability, deletion rejection, exact-type equality, type-sensitive hashing, and current `repr`/`str` output.

Do not migrate `evidence._ConstrainedValue`: it additionally validates UTF-8 encodability and owns the Evidence representation contract. Do not migrate `risk_gate.py`: its self-contained stdlib-only architecture is intentional even though its private value implementation is similar.

Alternative considered: make Evidence or Risk Gate use the base to remove more lines. Rejected because that either drops Evidence-specific validation or breaks the Risk Gate dependency boundary.

### 4. Share only a private Confidence comparator, never a rank contract

Represent `Low < Medium < High` through a private comparison/selection primitive whose interface expresses relative order, not numeric rank, weight, or score. The incidental current mappings (`0..2` and `1..3`) are implementation details and must disappear only from migrated callers; no mapping or ordinal number is exported.

Each caller retains its own authenticity checks, fallback behavior, and construction of `Confidence` results. Apply may migrate a caller only when its numeric use is purely ordinal. At minimum two consumers must pass the exhaustive three-by-three ordering matrix or the shared primitive is not created. Market Demand remains local unless its individual use independently passes the same equivalence inventory; its inclusion is not required for ECO-53.

Alternative considered: add ordering methods to public `Confidence` or expose a rank constant. Rejected because either changes the public model or turns incidental integers into a contract.

### 5. Extract only the strict Brand/Supply/Risk canonicalization cluster

After a side-by-side call-site and exception audit, `_analysis_support.py` may own only the proven-equivalent strict helpers used by all three modules:

- exact non-empty UTF-8 string validation and exact tuple validation;
- duplicate-rejecting Evidence-ID canonicalization with lexical ordering;
- duplicate-rejecting relation and independence-assignment canonicalization keyed by Evidence ID;
- duplicate-rejecting missing-information canonicalization keyed by entry key;
- validation of already ordered, duplicate-free Evidence-ID tuples.

The helpers must retain exact type checks, field-specific errors, tuple return values, lexical keys, and immutable stored ordering. Domain-specific dimension/aspect/area/factor ordering, proposition keys, diagnostics, aggregation, findings, and duplicate-proposition behavior remain in their current modules.

Competition and VOC are explicit negative consumers. Their duplicate-accepting/rejecting choices stay untouched; no configurable shared helper is introduced for them.

Alternative considered: share all similarly named analysis helpers. Rejected because Competition and VOC demonstrate that those names do not imply equivalent contracts.

### 6. Remove the Red Team branch only after a fresh no-usage proof

Immediately before editing `red_team_revision.py`, search the full repository, including tests, for `_score_is_valid` and `canonical_unresolved`. If every call still uses the default canonical-unresolved behavior and no private-helper test depends on the non-default mode, remove the parameter and alternate branch while retaining the canonical condition: unresolved scores require `score is None`, `Confidence("Low")`, and empty Evidence IDs.

If any dependent caller exists at Apply time, stop this task and report the scope conflict instead of preserving a compatibility flag or changing that caller.

Alternative considered: remove the branch based on proposal-time evidence. Rejected because repository usage may change before Apply.

### 7. Characterize behavior before moving code and compare full baselines

Before production edits, run every focused touched-module suite, the v1 evaluation suite, and the complete discovery suite. Add focused characterization/equivalence cases before extraction; because this is behavior-preserving, these tests should pass against the pre-refactor implementation except tests that directly require the new private location.

After each narrow migration, rerun its focused suites. Finish with the v1 evaluation suite, the complete discovery suite, strict OpenSpec validation, and `git diff --check`. Existing contract assertions must not be weakened, rewritten, or deleted merely to fit the refactor.

## Risks / Trade-offs

- [A shared helper subtly changes malformed-input or exception behavior] → Compare each call site and add focused malformed/duplicate/order cases before extraction; leave uncertain duplication local.
- [The low-level module creates a reverse or circular dependency] → Keep it stdlib-only and verify the import graph plus `risk_gate.py` source/import boundary tests.
- [Confidence consolidation accidentally publishes numeric semantics] → Expose only a private comparator/selection operation and test all nine ordered pairs through caller results.
- [Structured-analysis consolidation tightens or relaxes Competition/VOC] → Do not edit those modules; retain explicit negative-boundary regressions.
- [Moving `_ClosedValue` changes identity-sensitive behavior] → Test exact-type equality, hash, `repr`, `str`, and immutability on subclasses from both consuming modules.
- [A broad mechanical cleanup obscures behavior drift] → Migrate one primitive cluster at a time, remove only imports/helpers made unused by ECO-53, and inspect an explicit file allowlist.
- [The full baseline is already failing] → Record exact failures before edits and require post-refactor results to introduce no new failure; do not repair unrelated failures in ECO-53.

## Migration Plan

1. Record clean/dirty workspace state, current active changes, Python version, focused baseline results, v1 evaluation result, full-suite result, and current Red Team usage inventory.
2. Add focused equivalence and negative-boundary characterization coverage without changing production code.
3. Add `_deterministic_primitives.py`; migrate the closed-value pair, then only proven ordinal-only Confidence consumers, with focused verification after each step.
4. Add `_analysis_support.py`; migrate Brand Content, Supply Chain, and Risk Compliance only after the strict equivalence matrix passes, then rerun all three suites plus Competition/VOC negative regressions.
5. Re-run the Red Team repository-wide usage check and conditionally remove the dead parameter/branch; verify public revision behavior.
6. Run every touched suite, the v1 evaluation suite, full discovery, OpenSpec strict validation, import/source boundary checks, and diff containment checks.

There is no stored-data, deployment, or API migration. Rollback is the future Apply diff for the two private modules, migrated imports/helpers, and focused tests; existing living specs and public contracts remain unchanged.
