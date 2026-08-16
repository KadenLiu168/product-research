## Context

See `proposal.md` for motivation and `specs/unit-economics-engine/spec.md` for observable behavior. Current `main` is a dependency-free Python repository with three production boundaries:

```text
product_research/evidence.py
        ↓
product_research/evidence_policy.py
        ↓
product_research/evidence_assessment.py
```

`evidence.py` owns immutable representation plus `EvidenceId`, `Status`, and `Confidence`; `evidence_policy.py` owns eligibility, freshness, Tier, status/use, and citation policy; `evidence_assessment.py` owns explicit collection stance, independence, conflict, missing information, and claim-level Confidence. The latter modules already establish frozen dataclasses, closed vocabularies, ordered tuples, explicit caller context/policy, and public exception-to-structured-result boundaries. `product_research/__init__.py` is empty, so current consumers import capability modules directly rather than through a package-level export surface.

The living `references/gates.md` defines the eight-input formula, Minimum Viability plus Dynamic Target, and the rule that missing inputs or unfrozen thresholds prevent a definitive pass. It explicitly says the calculator is not implemented and freezes no numeric thresholds. `references/scoring-policy.md` keeps gates independent from weighted scoring, while `references/report-contract.md` owns downstream final labels. Those are current repository facts; this design does not treat the requested architecture summary as authority where it would conflict with them.

## Goals / Non-Goals

**Goals:**

- Add one deterministic normalized-values-to-economics boundary without widening any Phase 3 owner.
- Keep mathematical calculation separate from caller-owned commercial thresholds even while both live in one capability module.
- Make incomplete knowledge, invalid data, and missing policy observable through one fail-closed result model.
- Give ECO-12 one immutable, replay-stable result rather than requiring callers to assemble calculation and gate stages themselves.
- Pin all ordering, confidence propagation, Decimal behavior, and equality boundaries in focused tests.

**Non-Goals:**

- Create acquisition, normalization-from-text, estimation, FX, fee-provider, persistence, serialization, generalized formula, Dynamic Target generation, Risk, scoring, Red Team, report, or decision capabilities.
- Revalidate Evidence or change `evidence.py`, `evidence_policy.py`, `evidence_assessment.py`, their living specs, or the empty package export surface.
- Define product/category-specific thresholds, accepted margin ranges, currency registries, or currency minor-unit quantization.

## Decisions

### 1. Add sibling `unit_economics.py` with one-way dependency on Evidence vocabulary

Apply will add `product_research/unit_economics.py`. It imports only the existing public `EvidenceId`, `Status`, and `Confidence` vocabulary from `evidence.py`; no existing module imports Unit Economics:

```text
evidence.py
    ↓
unit_economics.py
    ↓
future scoring/decision capability (ECO-12)
```

Unit Economics does not need Evidence Policy or Assessment objects because callers are responsible for producing eligible normalized numeric inputs. Importing those modules would tempt ECO-11 to repeat freshness, Source/Tier, conflict, or claim-level Confidence decisions.

No package-level exports are planned because the existing package surface is empty and every current capability is imported from its module. A focused RED test would have to demonstrate an unavoidable public API gap before any upstream file could be considered; repository inspection found none.

Alternative considered: add economics methods to `Evidence` or extend assessment results. Rejected because a single Evidence record is not an eight-input economics model, and policy/assessment ownership must not become downstream calculation ownership.

### 2. Keep calculator and policy values in one capability module

The module contains separate immutable types and pure helpers for normalized inputs, calculation, policy, gate results, and the final result. Calculation helpers receive no policy; gate helpers consume only a completed margin plus explicit policy. This is logical separation without a premature module lifecycle.

An independent `economics_policy.py` is deferred until policy gains its own consumers, versioning, or materially separate lifecycle. Today it would add a dependency edge and public surface for two optional Decimal values and one consistency invariant.

Alternative considered: split policy immediately for symmetry with Evidence Policy. Rejected because Evidence Policy is a large independent eligibility capability, while ECO-11 policy is deliberately only explicit threshold data and comparison.

### 3. Use normalized explicit `EconomicInput`, never Evidence text

`EconomicInput` is a frozen value with:

```text
amount: Optional[Decimal]
currency: str
status: Status
confidence: Confidence
evidence_ids: Tuple[EvidenceId, ...]
```

Construction accepts only a tuple of `EvidenceId` values, rejects duplicates within the input, and stores them in lexical `EvidenceId.value` order. An empty tuple remains legal for an explicitly caller-owned value such as a not-applicable zero; ECO-11 records traceability but does not invent an Evidence eligibility requirement. The same Evidence ID may legitimately support multiple economic fields and is deduplicated only when producing the result-level union.

`Unknown` requires `amount=None`; `Observed`, `Estimated`, and `Calculated` require a finite exact `Decimal`. Numeric strings and binary floats are rejected, not parsed. ECO-11 never reads `Evidence.claim`, `Evidence.evidence`, metadata, provider, URL, or LLM output. Acquisition and normalization remain caller/future-work responsibilities.

Alternative considered: accept `Evidence` records and parse their text or metadata. Rejected because Phase 3 intentionally does not define an economic numeric schema, and semantic extraction would be nondeterministic and duplicate eligibility ownership.

### 4. Model exactly eight required inputs

`UnitEconomicsInputs` is a frozen aggregate with fields in formula order:

```text
selling_price
product_cost
international_shipping
fulfillment
payment_fees
platform_cost
cac
returns_after_sales_loss
```

There are no defaults. The evaluator verifies all fields even though normal construction is strict, so wrong aggregates or corrupted objects still fail closed. A not-applicable cost is a concrete `Decimal("0")`; absence or `Unknown` is not zero.

Selling Price is either `Unknown` or a strictly positive amount. Concrete costs are non-negative. Negative Contribution Profit is allowed because it is a mathematical result, not malformed input.

Alternative considered: mappings, optional fields, or a formula DSL. Rejected because they allow omission-to-zero ambiguity and create extensibility not required by the frozen gate formula.

### 5. Keep currency structural and conversion-free

Currency is exactly three uppercase ASCII letters (`^[A-Z]{3}$`). This catches blank, case-variant, and malformed codes without claiming that a code exists in an online ISO registry. Every concrete amount in one evaluation must match exactly. Unknown inputs still carry an explicit structurally valid currency, but only concrete monetary values participate in the mismatch check defined by the spec.

The engine performs no FX lookup or conversion. The derived profit carries the one resolved concrete currency when available; an unresolved profit has that currency only when it can be resolved unambiguously, otherwise no concrete currency is claimed. Contribution Margin is dimensionless.

Alternative considered: accept arbitrary non-empty currency strings. Rejected because aliases and case differences would make equality ambiguous. An external ISO registry was also rejected because it introduces network/version dependence and exceeds structural validation.

### 6. Use distinct immutable input and derived result shapes

Apply should use small frozen values rather than one generic dictionary:

- `EconomicInput` for normalized caller input.
- `UnitEconomicsInputs` for the fixed aggregate.
- a derived monetary value for Contribution Profit, including amount/currency/status/confidence/Evidence IDs.
- a derived margin value for Contribution Margin, including value/status/confidence/Evidence IDs but no currency.
- `UnitEconomicsPolicy` for the two optional thresholds.
- a gate result for outcome, actual margin, threshold, and reasons.
- `UnitEconomicsResult` for both derived values, both gates, economics outcome, unresolved input names, result-level Evidence IDs, and reasons.

Closed vocabularies cover gate outcome (`PASS`, `FAIL`, `UNRESOLVED`), economics outcome (`UNRESOLVED`, `UNVIABLE`, `BELOW_TARGET`, `MEETS_TARGET`), and reason code. Collections are immutable tuples. No JSON/wire format is added: current `main` has no Unit Economics persistence or downstream wire consumer, so serialization would be speculative.

Alternative considered: reuse one generic value/result dictionary. Rejected because it would permit currency on a dimensionless margin, invalid spellings, mutable collections, and ad hoc downstream interpretation.

### 7. Freeze the Decimal arithmetic contract

The module defines one private immutable configuration used to create a fresh local standard-library Decimal context for every evaluation:

```text
precision = 34 significant digits
rounding = ROUND_HALF_EVEN
Emin = -999999
Emax = 999999
clamp = 0
traps = InvalidOperation, DivisionByZero, Overflow
```

`Inexact` and `Rounded` are not trapped because non-terminating margins are valid and must be rounded predictably. Every subtraction, division, and threshold comparison runs inside `localcontext` created from that fixed configuration. The module never calls `getcontext()` to derive behavior and never mutates the process-global context. Ordinary Decimal failures are converted to `CALCULATION_ERROR`.

Contribution Margin is the dimensionless fraction `profit / selling_price`; `0.20` means 20%. No hidden percentage scaling or minor-unit quantization is applied. Gate comparison uses the calculated margin value returned by this fixed context, so replay and comparison share one numeric truth.

34 digits matches the standard decimal128 significant-digit precision while remaining available in Python's standard library. It provides a generous deterministic domain without adding a financial dependency.

Alternative considered: Python's ambient default context. Rejected because callers can mutate it. Fixed two-decimal money and four-decimal margin quantization were rejected because the living rules freeze no such rounding policy and quantization would discard supplied precision.

### 8. Calculate mathematical truth before applying policy

With complete valid input, calculation performs the frozen subtraction in formula order and then divides by positive Selling Price. Formula order is explicit even though subtraction of the summed costs is mathematically equivalent; pinning the sequence removes implementation variation under finite precision.

Both derived statuses are `Status("Calculated")`. Their Confidence is the weakest of all eight input Confidence values under `High > Medium > Low`. There is no average, weight, tier adjustment, Evidence Assessment call, or LLM judgment.

Calculation is independent from policy. If inputs calculate successfully but policy is missing or invalid, the derived profit and margin remain valid mathematical facts while gate results fail closed. This preserves the central ownership rule: policy failure must not erase calculation truth, and calculation success must not invent viability policy.

Alternative considered: stop before calculation when policy is incomplete. Rejected because it couples mathematical truth to a commercial configuration and deprives ECO-12 of valid traceable economics.

### 9. Propagate Unknown completely and conservatively

The evaluator scans all eight fields before calculation. Every `Unknown` field is recorded once in formula order. One or more Unknown inputs produce Unknown profit and margin, both with no numeric value, `Status("Unknown")`, `Confidence("Low")`, and the safely resolved result-level Evidence ID union. The engine does not perform partial subtraction or emit a provisional margin.

Both gates are `UNRESOLVED`; valid supplied thresholds may remain visible, but no actual margin exists. Reasons include `UNKNOWN_REQUIRED_INPUT` once, plus any independently missing threshold reasons in fixed priority. This makes missing calculation inputs and missing business policy separately machine-readable.

Alternative considered: calculate a range or substitute zero. Rejected because no bound contract exists and either behavior would fabricate information.

### 10. Normalize Confidence and Evidence ID propagation

For a completed calculation, both derived values use the weakest of the eight input Confidence values. For unresolved calculation, they use `Low`; this is a conservative evaluation confidence and never modifies any upstream Evidence or claim-level assessment Confidence.

The result-level and both derived ID collections are the lexical union of every input's already-normalized IDs. Duplicate IDs across fields are expected and deduplicated. Input order and repetition of the evaluation cannot affect output ordering.

Alternative considered: average Confidence or let only cost IDs flow to profit. Rejected because every formula input contributes to both profit and margin, while numerical Confidence aggregation has no frozen semantics.

### 11. Represent policy as explicit optional thresholds

`UnitEconomicsPolicy` has two independently optional values:

```text
minimum_viability_margin: Optional[Decimal]
dynamic_target_margin: Optional[Decimal]
```

`None` is the intentional “not supplied” state and is legal. Supplied values must be finite exact Decimals; float/string coercion is forbidden. No hidden range such as zero-to-one is imposed because current policy freezes no business-valid margin range, and negative or above-100% thresholds can be structurally meaningful in some commercial contexts. When both are present, `dynamic_target_margin >= minimum_viability_margin` is the sole consistency rule.

There are no constants such as `DEFAULT_MINIMUM_MARGIN` or `DEFAULT_TARGET_MARGIN`. Dynamic Target is executed exactly as supplied. Price point, repeat purchase, returns, ad dependency, shipping burden, risk, and support burden remain upstream considerations for a future explicit target-generation policy, not ECO-11 heuristics.

Alternative considered: choose conservative defaults or adjustment rules. Rejected because the living gate document explicitly freezes no numbers or algorithms.

### 12. Evaluate each gate independently with an equality-inclusive boundary

Each gate returns actual calculated margin when available, its own valid supplied threshold, an outcome, and ordered reasons:

- missing/invalid calculation or missing threshold → `UNRESOLVED`;
- actual margin greater than or equal to threshold → `PASS`;
- actual margin below threshold → `FAIL`.

Minimum Viability and Dynamic Target are evaluated separately whenever safe. Thus Minimum may remain `PASS` when Dynamic Target is missing, and Dynamic Target may preserve its own evaluation even when Minimum is missing. An inconsistent policy invalidates both because the policy object cannot be interpreted safely.

Alternative considered: a single boolean gate. Rejected because it loses partial policy state, actual-versus-threshold trace, and unresolved reasons.

### 13. Derive one closed economics outcome without ECO-12 labels

Top-level precedence is:

1. calculation unresolved, invalid policy, or Minimum unresolved → `UNRESOLVED`;
2. Minimum `FAIL` → `UNVIABLE`, regardless of whether Dynamic Target exists;
3. Minimum `PASS` plus Dynamic unresolved → `UNRESOLVED`;
4. Minimum `PASS` plus Dynamic `FAIL` → `BELOW_TARGET`;
5. both `PASS` → `MEETS_TARGET`.

`UNVIABLE` is a Unit Economics state, not a final commercial `NO-GO`. ECO-12 may later combine this stable result with independent scoring and other gates, but ECO-11 never emits `GO`, `CONDITIONAL GO`, `RISK REVIEW`, or `NO-GO`.

Alternative considered: emit final decision labels now. Rejected because `references/report-contract.md` owns those downstream labels and the aggregate decision engine does not yet exist.

### 14. Use one closed reason vocabulary and deterministic priority

Reason values and priority are fixed in this order:

1. `ECONOMICS_INPUT_ERROR`
2. `UNKNOWN_REQUIRED_INPUT`
3. `INVALID_AMOUNT`
4. `INVALID_SELLING_PRICE`
5. `CURRENCY_MISMATCH`
6. `CALCULATION_ERROR`
7. `MINIMUM_POLICY_MISSING`
8. `DYNAMIC_TARGET_POLICY_MISSING`
9. `INVALID_POLICY`

Reasons are deduplicated and sorted by this priority. Unresolved input names use formula order. Evidence IDs use lexical ID order. Gate reasons are the applicable subset of the same vocabulary; the top result carries their deterministic union plus calculation-level reasons.

The distinction is narrow: wrong aggregate shape or field type is `ECONOMICS_INPUT_ERROR`; a non-finite/unsupported/sign-invalid cost amount is `INVALID_AMOUNT`; zero/negative concrete Selling Price is `INVALID_SELLING_PRICE`; an ordinary arithmetic exception is `CALCULATION_ERROR`; missing thresholds are legal business states; malformed or inconsistent thresholds are `INVALID_POLICY`.

Alternative considered: free-text messages or one generic failure. Rejected because downstream code would need string parsing and could not distinguish resolvable missing policy from invalid data.

### 15. Keep strict constructors and one fail-closed evaluation entry point

Following existing modules, value constructors reject invalid direct construction with `TypeError` or `ValueError`; they do not coerce. The single capability entry point is:

```python
evaluate_unit_economics(inputs, policy)
```

It performs strict aggregate resolution, input validation, deterministic calculation, propagation, both policy comparisons, and result assembly. It catches ordinary exceptions and returns a structured result rather than exposing a second public evaluation mode. It preserves only safely resolved diagnostics and traceability; it never fabricates placeholder amounts or IDs.

Downstream callers consume `UnitEconomicsResult` directly and do not assemble intermediate helpers with potentially different gate precedence.

Alternative considered: expose public calculator and gate functions that callers must compose. Rejected because it invites divergent Unknown handling, policy precedence, and economics outcomes. Pure helpers may remain private and testable through the public contract.

### 16. Preserve purity and ownership through tests and documentation routing

Focused tests will vary ambient Decimal context, input/Evidence-ID order, repeat evaluation, and each Unknown field. An import/source audit will assert the new module has no clock, network, random, LLM, or third-party dependency. Existing Phase 3 suites run unchanged.

After implementation, `references/gates.md` retains high-level ownership and routes algorithm execution to `unit_economics.py`; it no longer says the calculator is absent. `SKILL.md` names Unit Economics as implemented while preserving research adapters, scoring, Risk automation, Red Team, persistence, and report generation as unavailable. `tests/scenarios.md` gains acceptance routing. Algorithm, Decimal, and threshold-execution truth remain single-owned by the capability/spec rather than duplicated across Markdown.

Alternative considered: duplicate the complete algorithm and threshold semantics in every routed document. Rejected because those copies would drift.

## Risks / Trade-offs

- [A fixed 34-digit context can round extreme high-precision inputs] → Make the precision observable, test non-terminating and boundary values, and fail closed on trapped overflow rather than depend on ambient settings.
- [Three-letter structural currency codes do not prove real-world currency validity] → Treat them only as stable equality tokens; upstream normalization owns semantic validity.
- [Caller-supplied `Estimated` numbers or Confidence may be poor] → Preserve explicit status/Confidence and Evidence IDs; ECO-11 guarantees deterministic math, not upstream truth.
- [Allowing negative or above-one policy thresholds may look permissive] → Current repository freezes no valid business range; require finite Decimal and cross-threshold consistency only, leaving future policy constraints to a separate Change.
- [Minimum failure can produce `UNVIABLE` while Dynamic Target is missing] → Preserve Dynamic Target `UNRESOLVED` and its reason, but retain the already decisive independent Minimum result as specified.
- [Strict construction still raises before evaluation if callers build invalid values directly] → Document constructors as value-validation boundaries and keep `evaluate_unit_economics` fail closed for aggregate/evaluation failures, matching current Phase 3 style.

## Migration Plan

1. Add scenario-first RED acceptance text and focused `unittest` contracts for the complete delta spec.
2. Add `product_research/unit_economics.py` only; do not modify Phase 3 modules or package exports unless a focused RED test proves the documented unavoidable gap.
3. Implement the minimum immutable values, local Decimal calculation, propagation, explicit policy execution, and fail-closed public result needed to turn focused tests green.
4. Narrowly update `references/gates.md`, `SKILL.md`, and `tests/scenarios.md`, preserving single ownership and current capability-gap honesty.
5. Run focused, unchanged Phase 3, full-suite, strict OpenSpec, purity, determinism, and independent acceptance gates.

Rollback removes the new module, focused tests, scenario additions, narrow documentation routes, and this Change. No persisted data, Evidence wire schema, existing API, or dependency migration exists.
