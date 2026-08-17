## Context

See `proposal.md` for motivation and `specs/voc-analysis/spec.md` for observable behavior.

The current repository already has the boundaries this design must compose rather than replace:

- `Evidence` / `EvidenceId` are the sole normalized durable evidence representation.
- Evidence Policy owns source/tier/status/freshness eligibility and material claim-support validation for an explicit `ValidationContext`. Its existing `voc` kind and 730-day current-use freshness behavior remain authoritative.
- Evidence Assessment owns explicit stance, source independence, conflict, missing information, usable/adverse/excluded IDs, ordered diagnostics, and claim-level Confidence for an explicit `AssessmentContext`.
- ECO-13 owns `RawFinding` validation, normalization, and Evidence-ID allocation; ECO-14 owns fixed acquisition-family composition and stops before structured analysis.
- `market_demand.py` and `competition.py` establish the current standard-library pattern: a sibling domain module consumes existing Evidence, requires explicit domain semantics, composes existing Policy/Assessment results, and returns frozen deterministic values.

VOC differs from Competition only in its domain output: it has eight finding categories, deterministic category coverage, and optional Evidence-gated Complaint prevalence/scope axes. It does not need a sample-adequacy pipeline or a generic Structured Analysis framework.

## Goals / Non-Goals

**Goals:**

- Add one narrow read-only VOC module with explicit frozen proposition, Complaint-characterization, finding, and aggregate result values.
- Invoke the existing Evidence Assessment independently once per unique well-formed proposition and preserve each complete result unchanged.
- Make category coverage, duplicate handling, Complaint axes, Evidence-ID traceability, Confidence restriction, and replay ordering deterministic.
- Fail closed at the narrowest safe boundary without hiding valid independent propositions or constructing substitute Evidence/facts.
- Keep the Apply surface standard-library-only and limited to the new capability, focused tests, and minimal routing truth-alignment.

**Non-Goals:**

- No acquisition, provider mapping, scraping, orchestration, normalization, Evidence-ID allocation, or Evidence schema change.
- No automatic theme extraction, NLP, embeddings, topic discovery, clustering, semantic inference, or internal LLM call.
- No generic analysis base classes or refactor of Market Demand, Competition, Policy, or Assessment.
- No numeric VOC/differentiation score, weight, threshold, recommendation, Red Team, downstream Brand/Content/Supply Chain/Risk analysis, persistence, or reporting.

## Decisions

### 1. Add one sibling module and one aggregate entry point

Add `product_research/voc.py` without changing package exports. Follow the repository's constrained-value and frozen-dataclass style with these conceptual public values:

```text
VOCCategory:
  PURCHASE_MOTIVATION | PAIN_POINT | COMPLAINT | UNMET_NEED |
  USE_CASE | PURCHASE_BARRIER | CUSTOMER_LANGUAGE | SEGMENT

VOCFindingOutcome: SUPPORTED | UNKNOWN
ComplaintPrevalence: COMMON | EDGE_CASE | UNKNOWN
ComplaintScope: PRODUCT_SPECIFIC | CATEGORY_WIDE | UNKNOWN
VOCFactor: fixed ordered domain diagnostics

ComplaintCharacterizationInput
  prevalence
  prevalence_evidence_ids
  scope
  scope_evidence_ids

VOCPropositionInput
  category
  proposition
  evidence_ids
  relations
  independence
  missing_information
  assessment_context
  complaint_characterization
```

Expose one entry point conceptually shaped as:

```text
analyze_voc(
    propositions,
    evidence_index,
    policy,
) -> VOCResult
```

Each proposition carries its own `AssessmentContext`; there is no shared hidden validation instant or minimum-independent-source setting. Collections inside frozen values use tuples. Exact proposition text is preserved and must be a non-empty UTF-8 string; it is not trimmed, case-folded, tokenized, or semantically compared. Accepted tuples are canonicalized into lexical or fixed-vocabulary order solely for representation normalization.

A generic `StructuredAnalysisProposition` base type was considered and rejected. Only three domain consumers exist, their category and conclusion semantics differ, and introducing a framework would broaden ECO-18 and risk coupling future analysis contracts prematurely.

### 2. Keep one authoritative Assessment per material finding

For every unique well-formed `VOCPropositionInput`, call `assess_evidence(...)` exactly once with that proposition's Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared Evidence index, and Policy. Preserve the returned `EvidenceAssessmentResult` unchanged in the corresponding finding.

Map Assessment to the domain result as follows:

- Assessment `SUPPORTED` plus non-empty `usable_ids` → VOC `SUPPORTED`, identical Assessment Confidence, and `usable_ids` as the finding's supporting IDs.
- Assessment `CONFLICTED`, `INSUFFICIENT`, an input-error factor, or no usable support → VOC `UNKNOWN`, Low Confidence, and the applicable fixed-order VOC factor.
- `adverse_ids` copies the Assessment's declared `contradicting_ids`, including excluded adverse Evidence for stance traceability.
- `excluded_ids` copies the Assessment's policy-excluded IDs; nested Policy results remain available through the preserved Assessment.

Material or critical missing information is not reinterpreted by VOC. If the existing Assessment remains `SUPPORTED` with a conservative Confidence ceiling, VOC preserves that supported outcome and Confidence; if Assessment becomes insufficient, VOC maps it to Unknown. This keeps missing-information ownership in the existing contract.

One aggregate Assessment per category was considered and rejected because it would merge unrelated claims, let one conflict contaminate another, and make Evidence IDs ambiguous. Reimplementing Policy eligibility or Confidence ceilings in VOC was rejected because it would create a drifting second assessment contract.

### 3. Derive category coverage from supplied proposition keys and resulting findings

`VOCResult` contains three fixed-order, mutually exclusive category tuples:

- `supported_categories`: at least one resulting finding in the category is supported;
- `unknown_categories`: at least one proposition was supplied for the category, including a rejected duplicate key, but no resulting finding is supported;
- `missing_categories`: no proposition was supplied for the category.

The result also contains all unique assessed findings, `duplicate_proposition_keys`, and analysis-level factors. A category with both supported and Unknown findings is classified as supported while retaining both finding outcomes. Coverage does not summarize away propositions and never creates placeholder findings for missing categories.

Generating one synthetic Unknown finding per absent category was considered and rejected because it would fabricate a proposition and Assessment that the caller never supplied. Omitting coverage entirely was rejected because callers would silently confuse absence with completeness.

### 4. Gate each explicit Complaint axis by the finding's usable support

Only `COMPLAINT` propositions may carry `ComplaintCharacterizationInput`. The characterization declares each axis independently:

```text
prevalence: COMMON | EDGE_CASE | UNKNOWN
prevalence_evidence_ids: tuple[EvidenceId, ...]
scope: PRODUCT_SPECIFIC | CATEGORY_WIDE | UNKNOWN
scope_evidence_ids: tuple[EvidenceId, ...]
```

The output finding always has prevalence/scope values and axis support tuples. For each axis independently:

1. an explicit `UNKNOWN` input remains `UNKNOWN` with no support IDs;
2. a non-Unknown input is preserved only when the overall finding is `SUPPORTED`;
3. its declared axis tuple must be non-empty and every axis ID must be a member of the finding's `supporting_ids`;
4. otherwise only that axis becomes `UNKNOWN`, its support tuple becomes empty, and a stable axis-specific factor is emitted.

Constructors require `UNKNOWN` axes to carry no IDs and reject Complaint characterization on non-Complaint propositions. They allow an empty tuple for a non-Unknown axis so the public analysis can return an explicit unsupported-axis diagnostic rather than infer support. Axis ID tuples are canonicalized lexically and duplicate IDs are rejected.

Separate axis Assessments were considered. They would require callers to supply three full Assessment input sets for one Complaint proposition and would turn prevalence/scope into separate material findings, which the requested result shape does not require. Treating any usable proposition Evidence as support for both axes was also rejected because it would not trace which Evidence explicitly permits each classification.

### 5. Reject every exact duplicate proposition occurrence without selecting a winner

Build multiplicities for exact `(category, proposition)` keys before assessment. When a key occurs more than once:

- assess none of its occurrences;
- emit no finding for that key;
- include the key once in `duplicate_proposition_keys` using category/proposition order;
- treat its category as supplied, so it becomes Unknown unless another unique finding in that category is supported;
- emit `DUPLICATE_PROPOSITION` at analysis level.

Continue assessing unique propositions when shared inputs are safe. This is deterministic even when duplicate occurrences carry different Evidence IDs or contexts.

First-wins, last-wins, and caller-order tie-breaking were rejected because each can select a different customer fact. Merging duplicates was rejected because it would invent relation, context, missing-information, and Evidence-conflict policies that VOC does not own. Emitting multiple Unknown findings with the same key was rejected because it would violate stable finding identity.

### 6. Fail closed at the narrowest safe boundary

Validate shared inputs first: the Evidence index must map exact `EvidenceId` keys to matching `Evidence` values, and Policy must be the existing exact value type. Unsafe shared input returns no supported findings and `VOC_INPUT_ERROR`; it does not construct placeholder Evidence or an alternate Assessment result.

Then isolate proposition behavior:

- malformed proposition container or non-proposition element → collection-level fail-closed result with no supported finding;
- duplicate exact key → exclude only that key as described above;
- incomplete relation/independence assignment, unresolved ID, or other proposition-local Assessment error → preserve the existing fail-closed Assessment in one Unknown finding;
- unsupported Complaint axis → downgrade only that axis when the proposition itself remains supported;
- an ordinary `Exception` from Policy/Assessment execution → structured fail-closed result at the applicable boundary.

Programmer-control `BaseException` values are not swallowed, matching existing domain modules. Public input constructors reject unsupported closed values and impossible structural states early; the analysis entry point still validates exact container and shared identity invariants so mutation-like or foreign values cannot create optimistic results.

Raising analysis-time domain exceptions was considered and rejected because Policy and Assessment already return structured fail-closed results. Failing all unique propositions because one proposition's assignments are incomplete was rejected because it would erase independently valid VOC evidence.

### 7. Use frozen values and explicit deterministic ordering

Use `@dataclass(frozen=True)`, tuples, existing immutable constrained values, and the unchanged existing Assessment result. Conceptually:

```text
VOCPropositionKey
  category
  proposition

VOCFinding
  category
  proposition
  outcome
  confidence
  supporting_ids
  adverse_ids
  excluded_ids
  assessment
  prevalence
  prevalence_supporting_ids
  scope
  scope_supporting_ids
  factors

VOCResult
  supported_categories
  unknown_categories
  missing_categories
  findings
  duplicate_proposition_keys
  factors
```

Sort categories by the declared eight-value order, findings and duplicate keys by category then exact proposition then lexical Evidence-ID tie-breakers, and all Evidence-ID tuples lexically by `EvidenceId.value`. Define one fixed VOC factor priority beginning with shared input and duplicate errors, followed by Assessment outcome reasons and Complaint-axis reasons. Preserve existing Assessment ordering unchanged.

The result repeats only the Evidence-ID classes and domain classifications needed for direct VOC consumption; generic Policy, missing-information, conflict, and source-count details remain authoritative in the nested Assessment. Mutable lists/dicts in public domain values were rejected because they would undermine replay equality and caller-visible immutability.

### 8. Verify domain behavior and ownership statically

Focused tests should first establish RED behavior for all eight categories, same-category independence, Policy/Assessment mapping, VOC freshness, conflicts, missing information, duplicate handling, category coverage, Complaint axes, ordering, and immutability. An AST/import/static audit should reject a second Evidence definition, provider/network/browser/scraper/retry/cache/async/persistence/clock/random/environment/LLM/embedding/NLP path, acquisition/orchestration types, RawFinding normalization, Evidence-ID allocation, automatic clustering, numeric scoring, thresholds/weights, recommendations, downstream analysis, Red Team, or reporting in the new module.

Only after focused behavior is green should documentation route callers to `voc.py` and stop describing VOC interpretation as wholly unavailable. Concrete acquisition and automatic clustering must remain explicitly unavailable.

## Risks / Trade-offs

- [One category can contain mixed supported and Unknown findings] → Category coverage reports supported if any finding is supported, while the complete ordered finding list preserves every outcome and diagnostic.
- [Axis evidence can support a Complaint proposition without supporting its prevalence or scope] → Require separate explicit axis Evidence-ID subsets and downgrade axes independently to Unknown.
- [Duplicate keys are dropped from finding output] → Preserve the rejected keys and category-level Unknown coverage; never choose or merge an occurrence.
- [Strict exact proposition identity does not detect paraphrases] → Preserve exact caller text and keep semantic deduplication/automatic clustering out of scope.
- [Conservative rules may produce many Unknown findings and axes] → Treat Unknown as the required honest state until callers provide explicit usable support; do not add hidden thresholds or inference.
- [Nested Assessment makes result objects larger] → Prefer one authoritative complete contract over flattened duplicate Policy/Assessment fields.
- [Documentation could imply provider-backed VOC research now works] → Limit edits to capability routing/current truth and retain explicit acquisition and clustering gaps.

## Migration Plan

1. Add focused RED tests for frozen inputs/results, all categories, independent propositions, Assessment mapping, coverage, Complaint axes, fail-closed behavior, replay, and scope ownership.
2. Add only `product_research/voc.py`, compose the existing Evidence Assessment, and make the focused tests green without changing adjacent contracts.
3. Make minimal scenario/Skill/methodology truth-alignment edits, then run focused adjacent suites and the full regression suite.
4. Run named and all-change strict OpenSpec validation plus doctor, inspect the final diff, and independently trace every VOC requirement through tests and implementation before any archive or delivery decision.

Rollback removes the new module, focused tests, and narrow routing additions. There is no persisted data, Evidence schema, provider, score, wire, or dependency migration to reverse.
