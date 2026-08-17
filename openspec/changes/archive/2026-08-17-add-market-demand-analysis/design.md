## Context

See `proposal.md` for motivation and `specs/market-demand-analysis/spec.md` for observable behavior. The repository already has one immutable Evidence representation, deterministic Evidence Policy, and a generic Evidence Assessment that owns stance, policy eligibility, source independence, conflict, missing information, ordered traceability, and claim-level Confidence. Phase 5 orchestration and adapters end before analysis, while Phase 7 scoring consumes explicit normalized scores and deliberately does not generate them.

ECO-15 therefore needs one small domain layer. It must add only Market Demand meaning: explicit Search/Commerce/Social binding, independent cross-category confirmation, and explicit temporal interpretation. Current production code is standard-library-only and uses frozen dataclasses plus constrained string values; no package-wide export is required for sibling capability modules.

## Goals / Non-Goals

**Goals:**

- Make every semantic input explicit and immutable so equivalent inputs replay equivalently.
- Delegate generic policy and claim assessment to the existing public boundary, then derive only Market Demand fields from its result.
- Keep positive demand and non-Unknown temporal labels conservative and auditable through existing Evidence IDs.
- Return enough stable factors and preserved assessment state for later qualitative score generation without generating that score now.

**Non-Goals:**

- Create trend algorithms, growth thresholds, popularity weights, category inference, or provider mappings.
- Change Evidence, Policy, Assessment, orchestration, adapter, Unit Economics, or scoring semantics.
- Model negative demand as a new conclusion. Current requirements only establish a positive conclusion or Unknown; adverse Evidence remains represented by the existing conflicted assessment.
- Create generic analysis infrastructure for later Phase 6 dimensions.

## Decisions

### 1. Add one sibling module with a narrow public entry point

Add `product_research/market_demand.py` beside the existing capability modules. Use the repository's constrained-value pattern for these exact vocabularies:

```text
DemandSignalCategory: SEARCH | COMMERCE | SOCIAL
TemporalInterpretation: STABILITY_SUPPORT | SHORT_TERM_HYPE_SUPPORT | UNKNOWN
DemandConclusion: POSITIVE | UNKNOWN
TemporalDemandState: STABLE | SHORT_TERM_HYPE | UNKNOWN
DemandFactor: fixed ordered domain reasons
```

Expose one frozen binding value containing `EvidenceId`, `DemandSignalCategory`, and `TemporalInterpretation`, one frozen `MarketDemandResult`, and one `analyze_market_demand(...)` function. The function accepts an explicit participating `evidence_ids` collection, existing Evidence index, bindings, `EvidenceRelation`, `IndependenceAssignment`, `MissingInformation`, `ValidationContext`, and `EvidencePolicy` inputs.

Require the bindings to cover the participating IDs exactly once, with no missing, duplicate, or extra ID. Keeping the participating collection explicit matches the existing Assessment boundary and makes incomplete category/temporal classification observable rather than silently excluding an unbound record. The implementation also rejects duplicate participating IDs, unresolved IDs, incomplete Assessment assignments, or index identity mismatch. Deriving participation only from bindings was considered but rejected because a caller could accidentally omit an Evidence record without producing the required fail-closed signal. A separate temporal relation type was also considered, but combining category and temporal interpretation in one per-ID binding makes the “exactly one of each” invariant directly auditable without changing Evidence.

### 2. Invoke Evidence Assessment once with a fixed two-source minimum

Build the existing `AssessmentContext` from the caller's explicit `ValidationContext` and `minimum_independent_sources=2`, then invoke `assess_evidence` once with the participating IDs and the existing relation, independence, missing-information, index, and policy inputs. Preserve the returned `EvidenceAssessmentResult` unchanged inside `MarketDemandResult`.

The fixed minimum is a domain requirement, not a hidden configurable threshold: a strong cross-category conclusion must not treat one underlying source, duplicated across categories, as cross-validation. The Market Demand layer does not reproduce Policy or Assessment validation, Confidence ceilings, conflict detection, missing-information handling, or source counting. Allowing callers to lower the Assessment minimum was considered but rejected because it would weaken one invocation of the same Market Demand contract.

### 3. Qualify a positive conclusion through a cross-category, cross-source pair

Start only from `assessment.usable_ids`; these are already policy-usable supporting Evidence under the existing claim-support check. Compute supported categories in the fixed order `SEARCH`, `COMMERCE`, `SOCIAL`.

Return `POSITIVE` only if:

1. the existing assessment outcome is exactly `SUPPORTED`; and
2. at least one pair of usable supporting IDs has different demand categories; and
3. the same pair has non-null, different explicit independence group IDs.

Otherwise return `UNKNOWN`. This prevents record count, a duplicated ID, one category with many observations, two category labels on one underlying source, unknown independence, or a conflicted assessment from manufacturing a strong conclusion. The existing assessment remains authoritative for what is usable and for how independence affects generic Confidence; the pair check adds only the Market Demand cross-category meaning.

Counting two category names without independence was considered. It would satisfy a syntactic “two of three” test while allowing one provider publication repackaged across channels to appear independently confirmed, contrary to the existing independence boundary and the requested cross-validation test.

### 4. Temporal state is unanimous explicit interpretation over usable support

Evaluate temporal interpretations only for `assessment.usable_ids`, after a `POSITIVE` demand conclusion exists:

- all are `STABILITY_SUPPORT` → `STABLE`;
- all are `SHORT_TERM_HYPE_SUPPORT` → `SHORT_TERM_HYPE`;
- any `UNKNOWN`, a mixture of the two non-Unknown values, or an `UNKNOWN` demand conclusion → `UNKNOWN`.

This intentionally has no dates, slopes, sample windows, trend weights, majority vote, or provider semantics. Requiring unanimity means additional usable contrary or unresolved temporal Evidence can only reduce what the system concludes. Majority voting was considered but rejected because no evidence-grounded weighting or conflict policy exists for overriding a minority temporal signal.

### 5. Preserve the assessment and add only domain trace fields

`MarketDemandResult` contains:

```text
conclusion
temporal_state
confidence
supported_categories
missing_categories
supporting_ids
adverse_ids
excluded_ids
assessment
factors
```

`supporting_ids` is the existing assessment's usable supporting IDs. `adverse_ids` preserves every explicitly contradicting ID, whether policy-usable or excluded, while the nested assessment retains exact policy eligibility and conflict details. `excluded_ids`, missing information, policy results, neutral/unknown relations, source counts, and existing factors remain available through the preserved assessment rather than being duplicated into a second parallel result model.

IDs sort lexically by `EvidenceId.value`; categories use the declared vocabulary order; domain factors use one fixed priority. `missing_categories` means categories absent from usable supporting Evidence, not missing providers or missing Phase 5 tasks.

Flattening all Assessment fields into the Market Demand result was considered but rejected because it would duplicate a living generic contract and create synchronization risk.

### 6. Confidence is the minimum of Assessment Confidence and a domain cap

Use a local ordinal only to choose the more conservative existing `Confidence` value; it is not a Market Demand score. The existing assessment Confidence is always the upper bound.

- malformed/unresolved domain input, assessment input error, assessment not `SUPPORTED`, or insufficient independent cross-category confirmation caps at `Low`;
- a positive conclusion with unknown or conflicting temporal interpretation caps at `Medium`;
- otherwise preserve the assessment Confidence.

The result exposes stable domain factors for these caps. It never alters individual `Evidence.confidence` values. A numeric confidence value or weighted demand score was considered and rejected because Phase 7 qualitative score generation is explicitly outside ECO-15.

### 7. Fail closed into the same result shape

Validate exact tuple/container and exact-type invariants at the public boundary, including exact one-to-one coverage between participating IDs and bindings. Domain validation failure returns `UNKNOWN`, temporal `UNKNOWN`, Low Confidence, no supported category, and the highest-priority input-error factor. When safe, retain the existing fail-closed assessment result; otherwise construct it only by invoking the public Assessment boundary with invalid/empty declared inputs rather than recreating an alternate Assessment model.

Ordinary malformed input is represented as a result, consistent with `assess_evidence`; programmer-control `BaseException` values are not swallowed. No placeholder Evidence or Unknown-status Evidence is created.

Raising domain exceptions was considered, but it would give callers a second public failure mode and make malformed inputs less traceable than existing assessment failures.

### 8. Verify scope through behavior and static ownership tests

Add focused tests for all category pairs, all-three ordering, one-category insufficiency, duplicate/conflicting bindings, rejected/stale/missing Evidence, Assessment conflict and independence behavior, temporal unanimity, Confidence caps, ordering replay, and immutability. Add an AST/import/static surface test that rejects provider/network/browser/LLM/acquisition, alternate Evidence definitions, numeric score fields, thresholds, recommendations, persistence, and unrelated analysis behavior in the new module.

Only after focused behavior is green should routing documentation add `market_demand.py` as the implemented analysis boundary and remove Market Demand from statements that imply all Phase 6 analysis is unavailable. Provider-backed research and qualitative score generation must remain explicitly unavailable.

## Risks / Trade-offs

- [Two categories can originate from one underlying source] → Require a qualifying cross-category pair with two distinct known independence groups and preserve existing independence diagnostics.
- [Unanimous temporal interpretation may return Unknown often] → Accept conservative Unknown until explicit Evidence resolves the disagreement; do not add weights or majority heuristics.
- [A preserved contradicting ID may be policy-rejected] → Keep `adverse_ids` as declared stance traceability and use the nested assessment to distinguish usable conflict from excluded Evidence.
- [The result contains a nested assessment object] → Prefer one authoritative generic model over duplicated fields; focused equality and immutability tests cover stable composition.
- [Documentation could imply that external demand research or score generation now works] → Limit edits to routing/current-capability statements and keep Phase 5 provider and Phase 7 score-generation gaps explicit.

## Migration Plan

1. Add focused RED tests for explicit bindings, pair coverage, temporal rules, result shape, fail-closed behavior, and scope ownership.
2. Add the minimal module using existing public Evidence Policy and Assessment contracts, then make focused tests green.
3. Update only the necessary Skill/reference/scenario routing statements and run all Phase 3, Phase 4, Phase 5, scoring, and full regression suites.
4. Run named and all-change strict OpenSpec validation plus doctor, then independently review requirement-to-test-to-code traceability.

Rollback removes `product_research/market_demand.py`, its focused tests, and its narrow routing additions. There is no persisted data, Evidence schema, provider, scoring, or wire migration to reverse.
