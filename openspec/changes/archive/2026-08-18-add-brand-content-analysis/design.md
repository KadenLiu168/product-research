## Context

See `proposal.md` for motivation and `specs/brand-content-analysis/spec.md` for observable behavior.

The repository already provides every lower boundary ECO-21 needs:

- `Evidence` / `EvidenceId` are the only normalized evidence representation.
- Evidence Policy owns source, tier, status, claim-mode, temporal-scope, and freshness eligibility from explicit caller context.
- Evidence Assessment owns explicit stance, source independence, conflict, missing information, usable/adverse/excluded IDs, diagnostics, and claim-level Confidence.
- Phase 5 owns acquisition, `RawFinding` normalization, and Evidence-ID allocation.
- `voc.py` returns evidence-grounded VOC findings whose underlying Evidence IDs can guide a caller, but a VOC finding is not Evidence and has no confidence-inheritance contract.
- `market_demand.py`, `competition.py`, `voc.py`, and `supply_chain.py` establish the sibling-module pattern: frozen domain values compose Policy and Assessment, preserve traceability, derive deterministic coverage, and stop before scoring or decisions.
- `scoring_decision.py` executes caller-supplied normalized scores and does not derive qualitative Brand or Content scores.

Unlike Supply Chain, ECO-21 adds no stricter domain-level missing-information gate. Brand / Content consumes the existing Assessment outcome and Confidence exactly: only a genuinely supported Assessment with usable support becomes supported.

## Goals / Non-Goals

**Goals:**

- Add one narrow sibling module with explicit frozen dimension, aspect, proposition, key, finding, diagnostic, and aggregate result values.
- Preserve Brand Potential and Content Potential independently without trying to infer either from prose.
- Invoke `assess_evidence(...)` exactly once per unique well-formed proposition and preserve its complete result.
- Make five-aspect coverage, duplicate rejection, Evidence-ID traceability, Confidence mapping, and replay ordering deterministic.
- Fail closed at the narrowest safe boundary without constructing substitute Evidence, propositions, findings, scores, or labels.
- Keep Apply standard-library-only and limited to the new capability, focused tests, and minimal acceptance-scenario truth alignment.

**Non-Goals:**

- No provider, network, browser, scraping, orchestration, acquisition, normalization, Evidence-ID allocation, or Evidence/Policy/Assessment/VOC schema change.
- No automatic proposition generation from VOC, `VOCFinding -> BrandContentFinding` chaining, or inherited Confidence.
- No text interpretation, domain/aspect classification, NLP, embeddings, clustering, or internal LLM.
- No generic Structured Analysis base class or refactor of sibling Phase 6 modules.
- No numeric Brand or Content score, weight, threshold, scorecard, analytical label, recommendation, Risk / Compliance, Red Team, persistence, or reporting.
- No expansion beyond the five ECO-21 aspects into positioning, identity, trust, line extension, repeat purchase, or gifting taxonomies.

## Decisions

### 1. Add one sibling module with two explicit axes

Add `product_research/brand_content.py`, following current sibling-module style and without changing package-level exports. Conceptual public values are:

```text
BrandContentDimension:
  BRAND_POTENTIAL | CONTENT_POTENTIAL

BrandContentAspect:
  BRAND_PREMIUM | STORYTELLING | VISUAL_EXPRESSION |
  DEMO_POTENTIAL | UGC_PROPAGATION

BrandContentFindingOutcome: SUPPORTED | UNKNOWN
BrandContentFactor: fixed ordered diagnostics

BrandContentPropositionInput
  dimension
  aspect
  proposition
  evidence_ids
  relations
  independence
  missing_information
  assessment_context

BrandContentPropositionKey
  dimension
  aspect
  proposition
```

Expose one entry point:

```text
analyze_brand_content(
    propositions,
    evidence_index,
    policy,
) -> BrandContentResult
```

Every proposition carries a material `AssessmentContext`; there is no hidden validation instant, claim mode, minimum independent-source count, or clock. Exact proposition text is preserved as a non-empty UTF-8 string without trimming, case folding, parsing, or semantic normalization. Tuple inputs are canonicalized only into their documented deterministic order.

One module is preferable to separate Brand and Content subsystems because both dimensions use the same closed aspects, Assessment mapping, duplicate semantics, diagnostics, and aggregate coverage. A generic Phase 6 framework was rejected because sibling domains have different semantics and ECO-21 does not authorize their refactoring.

### 2. Keep dimension and aspect orthogonal and caller-declared

The module accepts every explicit pair of the two dimensions and five aspects. It does not embed a mapping such as Brand Premium only to Brand or Demo Potential only to Content. The exact semantics are therefore preserved in the proposition's full `(dimension, aspect, proposition)` identity, and downstream Phase 7 can group supported findings by dimension without reinterpreting text.

This avoids an undocumented methodology expansion: storytelling or visual expression can contribute to either future scoring dimension depending on the caller's explicit proposition. If future product requirements need a restricted compatibility matrix, that is a separate observable contract change.

Inferring dimension from aspect was rejected because it would erase the two-dimensional model. Inferring either axis from Evidence or VOC text was rejected because it would introduce qualitative interpretation and nondeterministic domain ownership.

### 3. Preserve one authoritative Assessment per unique proposition

For every unique well-formed proposition, call `assess_evidence(...)` exactly once with its Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared Evidence index, and Policy. Preserve the returned exact `EvidenceAssessmentResult` in the finding.

Map the Assessment as follows:

- `SUPPORTED` plus non-empty `usable_ids` -> finding `SUPPORTED`, identical Assessment Confidence, and `usable_ids` as supporting IDs.
- `CONFLICTED`, `INSUFFICIENT`, input error, no usable support, rejected/stale/unresolved Evidence, or any other unsupported result -> `UNKNOWN` with Low Confidence.
- `adverse_ids` copies Assessment `contradicting_ids`, retaining declared adverse Evidence even when Policy excludes it from usable conflict.
- `excluded_ids` copies Assessment `excluded_ids`; the complete nested Policy results and claim-support result remain available through the Assessment.

The Brand / Content layer neither recalculates a missing-information severity nor adds a domain-specific Confidence cap. Existing Assessment factors already conservatively control outcome and Confidence. This design also never mutates `Evidence.confidence` or derives finding Confidence from a VOC finding.

One aggregate Assessment was rejected because unrelated creative propositions could contaminate conflicts, missing information, and independence counts. Reimplementing Policy or Assessment rules was rejected because it would create a drifting second source of eligibility and Confidence truth.

### 4. Reject exact duplicate full keys before Assessment

Build multiplicities for exact `(dimension, aspect, proposition)` keys before calling Assessment. When a key occurs more than once:

- call Assessment zero times for the key;
- emit no finding for any occurrence;
- include the key once in `duplicate_proposition_keys` ordered by dimension, aspect, and exact proposition;
- treat its aspect as supplied for coverage;
- emit `DUPLICATE_PROPOSITION` at analysis level.

The full triple is required: the same proposition text under a different dimension or aspect expresses different explicit caller semantics and is independently assessed. First-wins, last-wins, caller-order tie-breaking, and merge behavior were rejected because each would select or manufacture Evidence, relation, context, independence, and missing-information meaning. Semantic paraphrase detection was rejected because it requires out-of-scope language interpretation.

### 5. Derive five-aspect coverage without synthetic findings

`BrandContentResult` conceptually contains:

```text
supported_aspects
unknown_aspects
missing_aspects
findings
duplicate_proposition_keys
factors
```

Coverage is fixed-order, mutually exclusive, and exhaustive:

- supported: at least one finding for the aspect is `SUPPORTED`;
- unknown: at least one proposition key was supplied, including a rejected duplicate, but no finding for the aspect is supported;
- missing: no proposition key was supplied for the aspect.

An aspect with both supported and Unknown findings is supported at aggregate coverage while all findings and their dimensions remain visible. Dimension is intentionally not collapsed into a second coverage state: structural separation is provided by every proposition, key, and finding. Synthetic Unknown findings for missing aspects were rejected because there is no caller proposition or authoritative Assessment to preserve.

### 6. Fail closed at the narrowest safe boundary

Constructors require exact constrained types, tuple collections, unique Evidence IDs and assignments, and a material Assessment context. The aggregate boundary follows existing sibling behavior for safe collection/index/Policy validation.

For a unique structurally valid proposition, unresolved IDs and incomplete Assessment assignments are passed once into the existing Assessment, which returns an `INSUFFICIENT`, Low, `ASSESSMENT_INPUT_ERROR` result. That exact result becomes an Unknown finding. If Assessment unexpectedly raises an ordinary `Exception` or returns the wrong result type, create one narrow internal empty fail-closed `EvidenceAssessmentResult` so the public boundary retains structured behavior. Do not catch programmer-control `BaseException` signals.

If the proposition collection cannot be interpreted safely, no safe key or Assessment exists: return no findings, all aspects missing, and `BRAND_CONTENT_INPUT_ERROR`. If shared Evidence index or Policy input is malformed, no proposition may become supported. The boundary never repairs caller input or fabricates a placeholder proposition, Evidence value, relation, independence assignment, or finding.

Raising analysis-time domain exceptions was rejected because current Policy, Assessment, and sibling Phase 6 public boundaries return structured fail-closed results. Fabricating a finding for an invalid collection member was rejected because no valid proposition identity or Assessment exists.

### 7. Use frozen values and documented deterministic ordering

Conceptual outputs are:

```text
BrandContentFinding
  dimension
  aspect
  proposition
  outcome
  confidence
  supporting_ids
  adverse_ids
  excluded_ids
  assessment
  factors

BrandContentResult
  supported_aspects
  unknown_aspects
  missing_aspects
  findings
  duplicate_proposition_keys
  factors
```

Use `@dataclass(frozen=True)`, tuples, the existing `_ConstrainedValue` style, and the unchanged nested Assessment. Fixed dimension order is `BRAND_POTENTIAL`, then `CONTENT_POTENTIAL`; fixed aspect order is `BRAND_PREMIUM`, `STORYTELLING`, `VISUAL_EXPRESSION`, `DEMO_POTENTIAL`, then `UGC_PROPAGATION`. Sort findings and duplicate keys by dimension, aspect, exact proposition, and lexical Evidence-ID tie-breakers; sort all projected Evidence-ID tuples lexically; preserve Assessment ordering unchanged.

Use a fixed `BrandContentFactor` order beginning with `BRAND_CONTENT_INPUT_ERROR` and `DUPLICATE_PROPOSITION`, followed by `ASSESSMENT_INPUT_ERROR` and `ASSESSMENT_NOT_SUPPORTED`. The first two are analysis-level; the latter two explain Unknown findings. Remove repeated factor values without depending on caller order.

Mutable public collections and flattened copies of Policy/Assessment internals were rejected because they would weaken replay equality, immutability, and ownership clarity.

### 8. Keep VOC guidance and downstream scoring outside the boundary

VOC may guide callers to formulate a proposition and locate the original Evidence IDs in a VOC finding. The caller must still pass those original `Evidence` objects and complete new proposition-specific Assessment declarations. `BrandContentPropositionInput` accepts neither `VOCResult` nor `VOCFinding`, and the module does not import or call VOC analysis.

The module exposes qualitative support state and existing Confidence only. It does not import or call `scoring_decision.py`, select a score, translate Confidence into a score, aggregate across aspects, establish a weight/threshold, or emit a scorecard/recommendation label. Brand and Content dimension fields are future inputs, not current scores.

Direct VOC chaining was rejected because it would invent a derived Evidence representation and undefined confidence inheritance. Automatic proposition generation was rejected because it would require text interpretation or internal LLM inference. Early scoring was rejected because ECO-23 depends on all Phase 6 analyses and owns that later contract.

### 9. Verify both behavior and negative ownership

Focused tests first establish RED behavior for all five aspects and both dimensions, exact proposition identity, independent Assessment call counts, supported/conflicted/insufficient/rejected/unresolved/malformed mapping, traceability, coverage, duplicates, replay, and immutability.

AST/import/static audits reject another Evidence definition, VOC value acceptance, provider/network/browser/scraper/async/retry/cache/hidden-clock/random/environment/internal-LLM path, acquisition/normalization/ID allocation, NLP/embedding/clustering, score/weight/threshold/scorecard/recommendation, Risk / Red Team, persistence/reporting, or generic Structured Analysis framework. They also prove the module does not import or call sibling analysis or scoring modules.

After focused behavior is green, update only `tests/scenarios.md` if needed to align acceptance truth. The repository has no README capability registry and `product_research/__init__.py` currently exports nothing, so this design does not add speculative routing edits.

## Risks / Trade-offs

- [One aspect can contain findings from both dimensions] -> Preserve the dimension on every key and finding; aggregate aspect coverage reports only whether any supplied proposition is supported.
- [The same text under two axes is assessed twice] -> Treat the full explicit triple as identity because distinct dimension/aspect semantics must not be inferred or merged.
- [Exact identity does not detect paraphrases] -> Keep semantic deduplication out of this deterministic boundary and make callers responsible for explicit unique propositions.
- [A supported aspect may also contain Unknown propositions] -> Retain every independent finding; coverage means at least one supported finding, not universal support.
- [VOC-guided propositions require original Evidence to be resupplied] -> Preserve a single Evidence authority and avoid unsupported confidence inheritance.
- [Structured fail-closed fallback creates an Assessment when execution fails] -> Limit it to an empty Low/INSUFFICIENT input-error result and never use it to support a finding.

## Migration Plan

1. Add focused RED tests for closed vocabularies, frozen inputs/results, both dimensions, all aspects, independent Assessment mapping, duplicate rejection, coverage, traceability, malformed inputs, replay, and negative ownership.
2. Add only `product_research/brand_content.py`, compose existing Assessment and Policy behavior, and make the focused suite green without changing adjacent contracts.
3. Add minimal acceptance-scenario truth alignment, then run adjacent Evidence/Policy/Assessment/VOC/Supply Chain/Scoring suites and the full standard-library regression suite.
4. Run named and all-change strict OpenSpec validation plus doctor, inspect the final diff, and independently trace every requirement through implementation and tests before any archive or delivery decision.

Rollback removes the new module, focused tests, and narrow scenario additions. There is no persisted data, schema, provider, scoring, wire, dependency, or migration state to reverse.
