## Context

See `proposal.md` for motivation and `specs/supply-chain-analysis/spec.md` for observable behavior.

The repository already has the boundaries this design must compose:

- `Evidence` / `EvidenceId` are the sole normalized durable evidence representation.
- Evidence Policy owns source/tier/status/freshness eligibility for an explicit `ValidationContext`; its `supplier_quotation` kind and default 90-day current-use freshness remain authoritative.
- Evidence Assessment owns explicit stance, source independence, conflict, missing information, usable/adverse/excluded IDs, ordered diagnostics, and claim-level Confidence for an explicit `AssessmentContext`.
- Phase 5 owns `RawFinding` normalization, Evidence-ID allocation, and fixed source-family routing. The `SUPPLIER` family has no concrete provider-backed acquisition and this design does not add one.
- `market_demand.py`, `competition.py`, and `voc.py` establish the current standard-library pattern: sibling immutable domain modules consume existing Evidence and explicit semantics, compose existing Policy/Assessment, and stop before scoring or final decisions.
- `unit_economics.py` exclusively owns deterministic product cost, international shipping, fulfillment, returns/after-sales economics, profitability, and viability gates.

Supply Chain most closely matches the VOC proposition/coverage shape but has no Complaint axes or Competition sample pipeline. Its stricter domain rule is that an otherwise supported Assessment with material or critical missing information remains an Unknown operational conclusion.

## Goals / Non-Goals

**Goals:**

- Add one narrow read-only Supply Chain module with explicit frozen proposition, key, finding, factor, and aggregate result values.
- Invoke the existing Evidence Assessment exactly once per unique well-formed proposition and preserve every complete result unchanged.
- Make eight-dimension coverage, duplicate handling, Evidence-ID traceability, missing-information resolution, Confidence restriction, and replay ordering deterministic.
- Fail closed without constructing substitute Evidence, estimates, numeric facts, or conclusions.
- Keep Apply standard-library-only and limited to the new capability, focused tests, and minimal routing truth-alignment.

**Non-Goals:**

- No provider mapping, supplier API, HTTP, browser, scraping, orchestration, acquisition, normalization, Evidence-ID allocation, or Evidence schema change.
- No text parsing, automatic numeric extraction, supplier identity/concentration inference, clustering, or internal LLM.
- No generic Structured Analysis base class or refactor of Market Demand, Competition, VOC, Policy, Assessment, or Unit Economics.
- No cost/shipping/returns calculation, FX conversion, score, weight, threshold, viability gate, recommendation, final commercial decision, Red Team, downstream Brand/Content analysis, persistence, or reporting.
- No dangerous-goods, certification, legal transportation restriction, or regulatory Risk severity classification owned by ECO-22.

## Decisions

### 1. Add one sibling module and one aggregate entry point

Add `product_research/supply_chain.py` without changing package exports. Follow the repository's constrained-value and frozen-dataclass style with these conceptual public values:

```text
SupplyChainDimension:
  SUPPLIER_LANDSCAPE | MOQ | SOURCING_COST | CUSTOMIZATION |
  QUALITY | WEIGHT_VOLUME | TRANSPORTATION | RETURNS_AFTER_SALES

SupplyChainFindingOutcome: SUPPORTED | UNKNOWN
SupplyChainFactor: fixed ordered domain diagnostics

SupplyChainPropositionInput
  dimension
  proposition
  evidence_ids
  relations
  independence
  missing_information
  assessment_context

SupplyChainPropositionKey
  dimension
  proposition
```

Expose one entry point:

```text
analyze_supply_chain(
    propositions,
    evidence_index,
    policy,
) -> SupplyChainResult
```

Each proposition carries its own material `AssessmentContext`; there is no hidden validation instant, claim mode, or minimum-independent-source rule. Exact proposition text is preserved as a non-empty UTF-8 string and is not trimmed, case-folded, parsed, or semantically compared. Accepted tuples are canonicalized into lexical or fixed-vocabulary order only for deterministic representation.

A generic `StructuredAnalysisProposition` framework was considered and rejected. Existing domain modules differ materially, and a shared framework would broaden ECO-19 and couple later Brand, Content, and Risk contracts prematurely.

### 2. Preserve one authoritative Assessment per unique material finding

For every unique well-formed proposition, call `assess_evidence(...)` exactly once with its Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared Evidence index, and Policy. Preserve the returned exact `EvidenceAssessmentResult` in the finding.

Map Assessment to Supply Chain as follows:

- Assessment `SUPPORTED`, non-empty `usable_ids`, and no `MATERIAL_INFORMATION_MISSING` or `CRITICAL_INFORMATION_MISSING` factor -> `SUPPORTED`, identical Assessment Confidence, and `usable_ids` as supporting IDs.
- Assessment `CONFLICTED`, `INSUFFICIENT`, input error, no usable support, or material/critical missing information -> `UNKNOWN` with Low Confidence.
- `adverse_ids` copies Assessment `contradicting_ids`, including excluded adverse Evidence for declared-stance traceability.
- `excluded_ids` copies Assessment policy-excluded IDs; complete nested Policy diagnostics remain in the preserved Assessment.

Supply Chain does not recompute missing-information severity or a Confidence ceiling. It consumes the existing Assessment's closed factors and applies the stricter ECO-19 acceptance rule that material unresolved operational inputs cannot produce a supported conclusion. `NON_MATERIAL` missing information remains preserved and does not independently downgrade a supported Assessment.

Aggregating all propositions into one Assessment was rejected because unrelated facts could contaminate one another and lose claim-level Evidence traceability. Reimplementing Policy freshness or supplier quotation age was rejected because it would create a drifting second eligibility contract.

### 3. Reject every exact duplicate proposition occurrence before Assessment

Build multiplicities for exact `(dimension, proposition)` keys before assessment. When a key occurs more than once:

- call Assessment zero times for that key;
- emit no finding for any occurrence;
- include the key once in `duplicate_proposition_keys`, ordered by dimension and proposition;
- treat the dimension as supplied, so it is Unknown unless another unique finding in it is supported;
- emit `DUPLICATE_PROPOSITION` at analysis level.

First-wins, last-wins, caller-order tie-breaking, and merging were rejected because any would select or invent Evidence relations, context, missing-information, or conflict semantics. Semantic paraphrase detection was rejected because it would require text interpretation that ECO-19 explicitly excludes.

### 4. Derive coverage from supplied keys and independently assessed findings

`SupplyChainResult` contains:

```text
supported_dimensions
unknown_dimensions
missing_dimensions
findings
duplicate_proposition_keys
factors
```

Coverage is fixed-order and mutually exclusive:

- supported: at least one finding in the dimension is `SUPPORTED`;
- unknown: propositions were supplied, including rejected duplicate keys, but no finding is supported;
- missing: no proposition key was supplied.

A dimension with both supported and Unknown findings is supported at coverage level while every finding remains visible. Creating synthetic Unknown findings for missing dimensions was rejected because there is no caller proposition or authoritative Assessment to preserve.

### 5. Fail closed at the narrowest safe boundary

Public proposition constructors require exact domain types, tuple collections, canonical unique IDs/assignments, and a material Assessment context. The aggregate entry point accepts only list/tuple proposition collections and an exact Policy/index shape consistent with sibling modules.

For each unique valid proposition, pass shared inputs into Assessment once even when an Evidence ID is unresolved or the index/Policy is malformed; Assessment owns structured failure and returns an `INSUFFICIENT`, Low, `ASSESSMENT_INPUT_ERROR` result. Convert that exact result into an Unknown finding. If Assessment unexpectedly raises or returns the wrong type, create one internal empty fail-closed Assessment result so the public boundary still has a single structured result mode.

If the proposition collection itself is malformed, no safe key or Assessment exists. Return no findings, all dimensions missing, and `SUPPLY_CHAIN_INPUT_ERROR`. Do not swallow `BaseException` programmer-control signals. This preserves valid per-proposition diagnostics where possible without allowing malformed shared state to create support.

Raising analysis-time domain exceptions was considered and rejected because the repository's Policy, Assessment, and Phase 6 consumers use structured fail-closed results. Fabricating placeholder findings for malformed collection members was rejected because no valid proposition or Assessment input exists.

### 6. Use frozen values and explicit deterministic ordering

Conceptual output values are:

```text
SupplyChainFinding
  dimension
  proposition
  outcome
  confidence
  supporting_ids
  adverse_ids
  excluded_ids
  assessment
  factors

SupplyChainResult
  supported_dimensions
  unknown_dimensions
  missing_dimensions
  findings
  duplicate_proposition_keys
  factors
```

Use `@dataclass(frozen=True)`, tuples, existing immutable constrained values, and the unchanged nested Assessment. Sort dimensions by the declared eight-value order; sort findings and duplicate keys by dimension then exact proposition and lexical Evidence-ID tie-breakers; sort all Evidence-ID tuples lexically by `EvidenceId.value`; preserve Assessment ordering unchanged.

Use a fixed `SupplyChainFactor` priority beginning with `SUPPLY_CHAIN_INPUT_ERROR` and `DUPLICATE_PROPOSITION`, followed by `ASSESSMENT_INPUT_ERROR`, `ASSESSMENT_NOT_SUPPORTED`, and `MATERIAL_INFORMATION_UNRESOLVED`. The first two are analysis-level; the latter three explain finding-level Unknown outcomes. Duplicate factor values are removed without depending on caller order.

Mutable public collections and flattened copies of generic Policy/Assessment details were rejected because they would weaken replay equality, immutability, and ownership clarity.

### 7. Keep operational facts separate from calculations and regulatory Risk

`SOURCING_COST`, `TRANSPORTATION`, and `RETURNS_AFTER_SALES` accept exact caller-declared facts like every other dimension. The module never imports or calls Unit Economics calculation functions and never turns a proposition into a monetary or viability value. Downstream callers may separately decide whether a supported fact is an input to Unit Economics, but ECO-19 performs no conversion or gate.

`TRANSPORTATION` is limited to physical and operational burden. Dangerous-goods status, certification, legal restriction, and fatal/reviewable/normal severity belong to ECO-22. The module does not classify these from the proposition text; scope is enforced through API behavior, documentation, and static tests that exclude Risk vocabulary and paths.

Combining Supply Chain with Unit Economics or Risk was rejected because it would duplicate established ownership, create hidden conversions or thresholds, and make Unknown facts look decision-ready.

### 8. Verify behavior and ownership statically

Focused tests first establish RED behavior for all eight dimensions, supported/conflicted/insufficient/missing-information mapping, same-dimension independence, duplicate handling, traceability, stale/fresh supplier quotations, malformed inputs, replay, and immutability. Patch `assess_evidence` in a call-count test to prove exactly one call per unique proposition and zero calls for duplicates.

AST/import/static audits reject another Evidence definition, provider/network/browser/scraper/async/retry/cache/clock/random/environment/LLM/acquisition/orchestration/normalization path, supplier extraction or clustering, Evidence-ID allocation, Unit Economics calculations, FX, scores/weights/thresholds, recommendations/final decisions, downstream Brand/Content/Red Team, regulatory Risk classifications, persistence, or reporting.

Only after focused behavior is green should minimal routing documentation stop describing Supply Chain analysis as unavailable. Provider-backed supplier acquisition must remain explicitly unavailable.

## Risks / Trade-offs

- [A dimension can contain mixed supported and Unknown findings] -> Coverage reports supported if any finding is supported while the complete ordered finding list preserves every outcome.
- [Material missing information can coexist with a technically supported Assessment] -> The Supply Chain layer consumes the existing missing-information factor and conservatively maps the domain finding to Unknown without altering the Assessment.
- [Duplicate keys produce no findings] -> Preserve each rejected key once and retain its dimension as supplied/Unknown; never select or merge an occurrence.
- [Exact proposition identity does not detect paraphrases] -> Preserve exact caller text and keep semantic deduplication outside this deterministic boundary.
- [No automatic extraction means numeric Evidence requires explicit propositions] -> Treat missing declarations as missing/Unknown rather than inventing parsing, estimates, or a premature metric schema.
- [Documentation could imply supplier acquisition now works] -> Limit edits to capability routing/current truth and retain explicit provider-acquisition gaps.

## Migration Plan

1. Add focused RED tests for frozen inputs/results, all dimensions, independent Assessment mapping, unresolved material inputs, coverage, duplicates, traceability, supplier quotation freshness, malformed inputs, replay, and static ownership.
2. Add only `product_research/supply_chain.py`, compose existing Assessment and Policy behavior, and make the focused suite green without changing adjacent contracts.
3. Make minimal acceptance/routing truth-alignment edits, then run focused adjacent suites and the full standard-library regression suite.
4. Run named and all-change strict OpenSpec validation plus doctor, inspect the final diff, and independently trace every requirement through implementation and tests before any archive or delivery decision.

Rollback removes the new module, focused tests, and narrow routing additions. There is no persisted data, Evidence schema, provider, score, wire, dependency, economics, or regulatory migration to reverse.
