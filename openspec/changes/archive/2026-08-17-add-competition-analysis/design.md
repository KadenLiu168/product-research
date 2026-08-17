## Context

See `proposal.md` for motivation and `specs/competition-analysis/spec.md` for observable behavior.

The current repository already has three boundaries that constrain this design:

- `Evidence` / `EvidenceId` are the sole normalized durable evidence representation.
- Evidence Policy owns source/tier/status/freshness eligibility and claim-support validation for an explicit `ValidationContext`; Evidence Assessment owns stance, source independence, conflicts, missing information, usable IDs, and claim-level Confidence for an explicit `AssessmentContext`.
- ECO-13's `run_research()` owns `RawFinding` validation, normalization, and run-local Evidence-ID allocation. ECO-14's fixed five-family composition stops at `AcquisitionResult` / `RawFinding`.

`market_demand.py` is the architectural precedent: a standard-library-only domain module reads existing Evidence, requires explicit domain meaning, composes existing Policy/Assessment results, and emits frozen deterministic values. Competition differs because it has two related but separable outputs: competitor-sample adequacy and zero or more independently assessed material propositions.

## Goals / Non-Goals

**Goals:**

- Add one small read-only Competition module with explicit frozen inputs and outputs.
- Make valid-sample counting, required-stratum coverage, price-band coverage, and the 10–15 default target deterministic and auditable.
- Preserve existing Policy results per sample and existing Assessment results per material proposition rather than reproducing either rule set.
- Keep malformed or unavailable information explicit at the narrowest safe level while allowing unrelated valid samples or propositions to remain useful.
- Produce stable equality and ordering for replay from equivalent explicit inputs.

**Non-Goals:**

- No competitor discovery, provider adapters, scraping, acquisition orchestration, normalization, or Evidence-ID allocation.
- No inferred competitor identity, sample tag, price band, dimension, proposition, stance, or independence.
- No universal price boundaries, ranking, numeric Competition score, scoring threshold, weight, recommendation, Red Team, persistence, or report model.
- No change to the Evidence, Policy, Assessment, research orchestration, adapter, or scoring contracts.

## Decisions

### 1. Use one domain module with two explicit input families

Add `product_research/competition.py` without changing package exports. Its public constrained vocabularies and frozen values should be conceptually:

```text
SampleTag: HEAD | MIDDLE | NEW_ENTRANT | LOW_REVIEW
CompetitionDimension: POSITIONING | DIFFERENTIATION | MARKET_STRUCTURE
SampleAdequacy: ADEQUATE | LIMITED | UNKNOWN
CompetitionFindingOutcome: SUPPORTED | UNKNOWN

CompetitorSample
  competitor_identity
  tags
  price_band
  evidence_ids

CompetitionPropositionInput
  dimension
  proposition
  evidence_ids
  relations
  independence
  missing_information
  assessment_context
```

Expose one entry point conceptually shaped as:

```text
analyze_competition(
    samples,
    propositions,
    evidence_index,
    sample_validation_context,
    policy,
) -> CompetitionResult
```

The sample validation context must be an existing material `ValidationContext`. Each proposition carries its own existing material `AssessmentContext`, so its declared use and independent-source minimum are explicit rather than hidden globally. Collections inside frozen inputs use tuples. Constructors reject duplicate tags and Evidence IDs and canonicalize accepted tag and ID tuples into fixed/lexical order; sorting is representation normalization only and does not infer semantic values.

A single flat input structure that attached sample metadata, dimension, stance, and independence to every Evidence ID was considered. It would couple sample validity to proposition semantics, duplicate generic Assessment inputs across samples, and make aggregate market-structure Evidence awkward. Keeping sample declarations and propositions separate allows both to share one Evidence index without falsely requiring every finding citation to belong to one competitor sample.

### 2. Preserve exact caller identities and invalidate every duplicate occurrence

Competitor identity and price band are non-empty UTF-8 strings whose exact values are preserved. Do not trim, case-fold, alias, parse numeric prices, or merge near-matches. Exact identity equality is the only duplicate rule available without an external identity-resolution contract.

Count every structurally valid supplied sample in `total_sample_count`. Build identity multiplicities before validating coverage. If an identity occurs more than once, mark every associated sample result invalid with `DUPLICATE_COMPETITOR_IDENTITY`; none contributes to `valid_sample_count`, strata, or price bands. Continue evaluating their Evidence Policy results so the result retains useful diagnostics.

First-wins or last-wins deduplication was rejected because it makes validity depend on caller ordering and can select different tags or price bands. Merging duplicate entries was rejected because it would invent an identity-resolution and metadata-conflict policy that ECO-16 does not own.

### 3. Validate each sample through existing claim-support Policy

For every structurally valid `CompetitorSample`, invoke the existing `validate_claim_support(...)` with that sample's non-empty Evidence-ID tuple, the shared Evidence index, the explicit sample validation context, and the existing policy. Store the returned `PolicyValidationResult` unchanged in a frozen `CompetitorSampleResult` together with the original sample, `valid`, and fixed-order sample factors.

A sample is valid only when:

1. its exact identity occurs once; and
2. claim-support validation returns fact-eligible acceptance for all declared IDs.

Because every declared citation is required support, one unresolved, stale, rejected, unsupported, or indeterminate citation invalidates that sample. Other sample results continue independently. This uses the existing Policy's `competition` EvidenceKind freshness behavior when the supplied Evidence declares that kind, but the Competition layer does not parse or duplicate Evidence-kind rules and does not infer domain meaning from kind.

Validating only one eligible citation was considered but rejected: it would silently treat other caller-declared required support as optional. Running Evidence Assessment for each sample was also rejected because sample identity validation has no proposition stance, independence, conflict, or missing-information semantics; existing claim-support Policy is the narrower authoritative contract.

### 4. Derive sample adequacy only from valid samples

`CompetitionResult` should preserve:

```text
total_sample_count
valid_sample_count
target_min = 10
target_max = 15
sample_adequacy
covered_strata
missing_strata
covered_price_bands
sample_limitations
sample_results
findings
factors
```

Required strata are the fixed tuple `HEAD`, `MIDDLE`, `NEW_ENTRANT`; `LOW_REVIEW` is supported and reported but optional. Compute coverage from valid samples only. Sort tags by the closed-vocabulary order and exact price-band labels lexically.

Emit limitations in one fixed priority:

1. `SAMPLE_SIZE_LIMITATION` when valid count is below 10;
2. `MISSING_REQUIRED_STRATUM` when any required tag is missing;
3. `INSUFFICIENT_PRICE_BAND_COVERAGE` when fewer than two distinct valid price bands exist.

Return `ADEQUATE` only when none of these limitations applies. Ten through fifteen is the default methodology target, not an upper acceptance limit: valid samples above 15 remain present and can still be adequate. A malformed sample container or unsafe shared input returns `UNKNOWN` adequacy instead of pretending the observed zero is a genuine small sample.

Automatically selecting 15 records was rejected because it would require a ranking or randomization policy and discard caller-supplied traceability. Numeric price thresholds were rejected because price meaning is market-specific and must remain caller/planner-owned.

### 5. Assess each material proposition exactly once and independently

For each `CompetitionPropositionInput`, call `assess_evidence(...)` once with its own Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared index, and policy. Store the complete returned `EvidenceAssessmentResult` unchanged.

Map it to a frozen `CompetitionFinding`:

```text
dimension
proposition
outcome
confidence
supporting_ids
adverse_ids
excluded_ids
assessment
factors
```

`SUPPORTED` is allowed only when the underlying outcome is exactly `SUPPORTED` and `usable_ids` is non-empty. In that case, copy the existing Assessment Confidence and usable IDs. `CONFLICTED`, `INSUFFICIENT`, or `ASSESSMENT_INPUT_ERROR` maps to `UNKNOWN`, Low Confidence, and the applicable fixed-order Competition factor. `adverse_ids` preserves the assessment's declared contradicting IDs, including rejected adverse Evidence; `excluded_ids` and the nested policy results show which records were unusable. Competition never raises Confidence or rewrites an Evidence Confidence.

Sort findings by fixed dimension order, then proposition, then lexical Evidence-ID tuple. Reject duplicate exact `(dimension, proposition)` keys at the finding-collection boundary rather than selecting or merging one. Different propositions in the same dimension remain separate.

One aggregate Assessment for all three dimensions was rejected because a conflict or missing fact in one proposition would contaminate unrelated conclusions and supporting IDs would no longer identify which claim they support. Flattening all Policy and Assessment fields into Competition findings was rejected because it would create a second generic assessment contract that can drift.

### 6. Fail closed at the narrowest safe boundary

Validate shared inputs first: the Evidence index must map exact `EvidenceId` keys to matching `Evidence` values, and the Policy and sample validation context must be exact existing value types. Unsafe shared inputs produce zero valid samples, `UNKNOWN` sample adequacy, all required strata missing, no covered price bands, and no supported findings with `COMPETITION_INPUT_ERROR`.

Then keep the two pipelines isolated:

- malformed sample collection/value → sample coverage is `UNKNOWN`; a separately well-formed proposition collection may still be assessed when shared inputs are safe;
- duplicate sample identity or sample Policy rejection → only those sample results are invalid;
- malformed or duplicate proposition collection identity → no proposition is allowed to become supported;
- incomplete relations, independence assignments, unresolved IDs, or another proposition-local Assessment error → only that finding becomes `UNKNOWN` through the existing fail-closed Assessment result.

Ordinary `Exception` failures from validation are converted to stable results. Programmer-control `BaseException` values are not swallowed, matching the existing domain precedent. No placeholder Evidence, sample, proposition, or Unknown-status Evidence is constructed.

Raising public domain exceptions for analysis-time failures was considered but rejected because Policy and Assessment already expose structured fail-closed results. Treating every local invalid sample as a failure of all propositions was also rejected because it would conflate sample adequacy with claim assessment and lose valid independent information.

### 7. Use frozen values and deterministic fixed priorities

Use `@dataclass(frozen=True)`, tuples, existing immutable constrained values, and the existing Policy/Assessment result objects. Validate exact tuple element types in public result constructors so mutable list aliases cannot enter results. Result collections are sorted before construction:

- Evidence IDs and price bands: lexical value;
- sample tags and dimensions: declared vocabulary order;
- sample limitations and factors: one documented fixed priority;
- sample results: exact identity, then price band, tags, and Evidence IDs;
- findings: dimension, proposition, and Evidence IDs.

The function reads but never writes the Evidence index, Evidence values, input tuples, contexts, or policy. Equality of frozen result graphs provides the replay assertion. No time, random, environment, I/O, or mutable module state is consulted.

### 8. Verify behavior and ownership statically as well as dynamically

Add focused RED tests before the module. Cover the full sample target/limitation matrix, duplicate handling, Policy exclusions, proposition outcomes, per-dimension independence, trace IDs, immutability, permutation replay, and unchanged Evidence values. Include AST/import/static inspections that reject acquisition/provider/network/browser/LLM paths; new Evidence definitions; `run_research`, `RawFinding`, `AcquisitionResult`, or ID allocation; numeric Competition scores, score thresholds/weights, recommendations, Red Team, persistence, and unrelated Phase 6 behavior.

Only after focused behavior is green should documentation route Competition to the executable boundary. Keep broader methodology examples explicitly non-normative and retain the unavailable-provider and unavailable-score statements.

## Risks / Trade-offs

- [Exact identity matching does not detect aliases for the same competitor] → Require caller-owned canonical identity and fail only exact duplicates; do not add speculative entity resolution.
- [One bad required citation invalidates an otherwise plausible sample] → Preserve the full Policy result and accept conservative under-counting until the caller repairs the explicit support set.
- [Requiring two price-band labels says nothing about economic distance] → Treat labels as opaque coverage only; market-specific boundaries remain caller-owned.
- [Samples above 15 can make result objects larger] → Preserve all explicit traceability; the requested default target is not a truncation rule and expected sample sizes remain small.
- [A supported proposition can retain Low Confidence due to missing information or weak evidence] → Preserve the existing Assessment outcome and Confidence exactly; downstream scoring remains responsible for later interpretation.
- [Nested Policy and Assessment results make the result graph verbose] → Prefer complete authoritative traceability over copied partial diagnostics that can drift.
- [Static ownership tests can over-match harmless names] → Inspect AST/imports and explicit public fields rather than broad substring bans where sample targets or diagnostic vocabulary legitimately use numbers.

## Migration Plan

1. Add focused RED tests for frozen vocabularies/inputs/results, sample Policy validation, adequacy and limitations, proposition Assessment mapping, fail-closed behavior, ordering, and scope ownership.
2. Add the minimal `product_research/competition.py` implementation using only current public Evidence, Policy, and Assessment contracts; make focused tests green without changing those modules.
3. Make only directly necessary routing/current-capability edits to Competition scenarios and Skill/reference documentation.
4. Run focused Phase 3, Phase 5, Market Demand, scoring, full-regression, static-scope, and strict OpenSpec gates; independently trace every requirement to code and tests.

Rollback removes the new module, focused tests, and narrow routing additions. There is no persisted data, shared schema, provider integration, score, or wire migration to reverse.
