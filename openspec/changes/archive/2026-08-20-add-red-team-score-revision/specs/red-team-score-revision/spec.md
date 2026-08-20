## Purpose

Provide a deterministic, immutable, fail-closed Phase 8 boundary that preserves an initial scorecard while authorizing only explicitly declared, new-Evidence-backed score and authoritative Gate revisions with replay-stable findings and before/after traceability.

## ADDED Requirements

### Requirement: Red Team revision is a separate narrow capability
The system SHALL evaluate explicit Red Team findings and revision proposals in a capability separate from Evidence acquisition and interpretation, Phase 6 analysis, Initial Scoring, Risk classification, Unit Economics calculation, scoring-decision execution, reporting, persistence, and workflow orchestration. It SHALL consume only explicit normalized caller-owned values and semantically equivalent inputs MUST produce equivalent outputs.

#### Scenario: Caller reasoning crosses an explicit boundary
- **WHEN** a caller supplies normalized Red Team run provenance, findings, score proposals, and authoritative upstream results
- **THEN** the capability validates and records those values without acquiring Evidence, interpreting Evidence text, invoking an analyzer or provider, or generating a business judgment

### Requirement: Initial scores are retained and never mutated
Every evaluation SHALL accept one complete existing immutable `DimensionScores` as `initial_scores`, preserve it as independently inspectable output, and construct a distinct revised `DimensionScores` beginning from those exact eight values. The capability SHALL NOT mutate any `DimensionScore` or `DimensionScores`, accept a caller-supplied complete revised scorecard as the result source, introduce a second score hierarchy, or add, remove, reorder, or rename a dimension.

#### Scenario: No proposals preserve every initial slot
- **WHEN** a valid run contains no score revision proposals
- **THEN** the output retains the exact initial scorecard value and the revised scorecard contains eight values equal to their corresponding initial values

#### Scenario: Caller cannot replace the whole scorecard
- **WHEN** a caller attempts to submit an undeclared complete revised scorecard instead of per-dimension proposals
- **THEN** the capability does not use it to overwrite any initial dimension

### Requirement: Evidence delta is explicit canonical run provenance
Each evaluation SHALL receive separate caller-owned `baseline_evidence_ids` and `red_team_evidence_ids` collections containing only existing immutable `EvidenceId` values. Each collection MUST contain no duplicate, MUST use deterministic canonical Evidence-ID ordering, and the collections MUST be disjoint. Their union SHALL be the complete declared Evidence universe for all findings and revision records in that run; the capability SHALL NOT infer newness from absence in an initial score, search for Evidence, allocate IDs, silently deduplicate, reorder malformed input into validity, or infer either collection from another input.

#### Scenario: Canonical disjoint Evidence sets are accepted
- **WHEN** both Evidence collections contain canonical unique `EvidenceId` values in deterministic order and have no overlap
- **THEN** their union authoritatively defines the Evidence universe and the Red Team subset for the run

#### Scenario: Duplicate Evidence ID invalidates run provenance
- **WHEN** either Evidence collection contains the same `EvidenceId` more than once
- **THEN** the run provenance fails closed rather than silently deduplicating the collection

#### Scenario: Baseline and Red Team overlap invalidates run provenance
- **WHEN** one `EvidenceId` appears in both collections
- **THEN** the run provenance fails closed rather than choosing whether the ID is baseline or new

#### Scenario: Non-canonical collection is not silently repaired
- **WHEN** an Evidence collection has an unsupported container, non-`EvidenceId` member, or non-canonical ordering
- **THEN** the run provenance fails closed without coercion or sorting the malformed input into validity

### Requirement: Malformed top-level input fails conservatively
If `initial_scores` is not the exact existing `DimensionScores` type, the capability SHALL NOT produce a replacement scorecard. If run provenance or a top-level findings or proposal collection is malformed, the capability SHALL preserve all valid initial dimension values as the revised state and SHALL NOT authorize an actual score, Confidence, or Gate revision from that malformed run. Ordinary invalid member proposals in an otherwise valid collection SHALL instead follow per-target isolation requirements.

#### Scenario: Malformed proposal collection authorizes no revisions
- **WHEN** the proposal aggregate itself is not an accepted immutable collection even though some nested object could be inspected
- **THEN** the result preserves the complete initial scorecard and records no score or Gate revision

#### Scenario: Invalid initial scorecard is not fabricated
- **WHEN** `initial_scores` is missing, malformed, or a parallel lookalike type
- **THEN** evaluation does not fabricate an eight-slot initial or revised scorecard

### Requirement: Findings are evidence-backed and distinct from revisions
The system SHALL support immutable Red Team findings that contain a non-empty finding statement or reason and a non-empty causal Evidence-ID collection. Every finding ID MUST belong to the declared Evidence universe and at least one finding ID MUST belong to `red_team_evidence_ids`. A valid finding SHALL be retained whether or not any score, Confidence, Risk Gate, Unit Economics Gate, or economics outcome changes. A finding alone SHALL NOT alter a score or Gate, and a state-preserving proposal SHALL NOT create an artificial revision record merely to attach Evidence IDs.

#### Scenario: Evidence-backed challenge changes no state
- **WHEN** a valid finding cites current-run Red Team Evidence but every compared score and authoritative Gate state remains equal
- **THEN** the finding is retained and no score or Gate revision record is created

#### Scenario: Evidence-only score enrichment is not a revision
- **WHEN** a proposal supplies the same score and Confidence as the target's initial value but changes only Evidence IDs
- **THEN** the initial target remains unchanged and no score revision record is created

#### Scenario: Undeclared Evidence cannot support a finding
- **WHEN** any finding Evidence ID is outside the declared baseline and Red Team union
- **THEN** that finding is rejected without authorizing any state change

### Requirement: Score revisions use one explicit proposal per dimension
Every score or Confidence change SHALL be expressed as an independently validated typed proposal containing one existing target dimension, one proposed revised existing `DimensionScore`, a non-empty revision reason, and a non-empty deterministic tuple of causal Evidence IDs. Every causal ID MUST belong to the declared Evidence universe, and at least one MUST belong to `red_team_evidence_ids`. A baseline-only causal trace or an empty Red Team Evidence set SHALL NOT authorize a score or Confidence change.

#### Scenario: New Evidence authorizes a downward score revision
- **WHEN** one valid proposal lowers a score and cites at least one causal ID declared in `red_team_evidence_ids`
- **THEN** the target is replaced in the revised scorecard and one revision record preserves its initial and revised values, reason, and causal IDs

#### Scenario: New Evidence can authorize an upward revision
- **WHEN** current-run Evidence disproves a concern and one otherwise valid proposal raises the score
- **THEN** the revision is eligible under the same validation rules as a downward revision and no directional winner rule is applied

#### Scenario: Confidence-only change is an actual revision
- **WHEN** the proposed score equals the initial score but Confidence changes and causal current-run Evidence is declared
- **THEN** one revision record preserves the before/after `DimensionScore` values and the revised target is applied

#### Scenario: Baseline-only Evidence cannot authorize change
- **WHEN** a score or Confidence differs but every causal ID belongs only to `baseline_evidence_ids`
- **THEN** the proposal is rejected and the target retains its initial `DimensionScore`

#### Scenario: Evidence outside the run is rejected
- **WHEN** any proposal causal ID is outside the declared Evidence universe
- **THEN** the proposal is rejected and the target retains its initial `DimensionScore`

### Requirement: Revised concrete scores remain grounded in current-run Evidence
A proposed revised `DimensionScore` with a concrete score SHALL satisfy the existing `DimensionScore` contract unchanged. In addition, at least one causal ID belonging to `red_team_evidence_ids` MUST also appear in that revised score's own `evidence_ids`. The Red Team capability SHALL NOT rerun dimension ownership, Evidence Policy or Assessment, Confidence ceilings, qualitative validation, or the profitability rubric; callers SHALL use existing upstream owners and Initial Scoring to produce a normalized proposed value where regeneration is required.

#### Scenario: Revised concrete score shares causal new Evidence
- **WHEN** a valid concrete proposal cites a causal Red Team Evidence ID that also appears in the proposed score's existing Evidence-ID trace
- **THEN** the proposal may be accepted without reimplementing Initial Scoring validation

#### Scenario: External note alone cannot ground a concrete score
- **WHEN** a concrete proposed score cites current-run Evidence only in the revision reason or causal tuple and none of those new causal IDs appears in the score's `evidence_ids`
- **THEN** the proposal is rejected and the initial target remains unchanged

#### Scenario: Unresolved becomes concrete through existing scoring
- **WHEN** new Evidence supports upstream re-evaluation and existing Initial Scoring produces a concrete proposed score grounded in that Evidence
- **THEN** the Red Team capability may apply the unresolved-to-concrete revision without creating another scoring engine

### Requirement: Concrete-to-unresolved revisions preserve independent causality
The canonical unresolved score representation SHALL remain `score = None`, `Confidence = Low`, and `evidence_ids = ()`. A concrete-to-unresolved proposal MAY be accepted when its separate causal Evidence-ID tuple contains at least one current-run Red Team Evidence ID and otherwise satisfies the revision contract. Its revision record SHALL preserve the initial concrete `DimensionScore`, canonical revised unresolved `DimensionScore`, non-empty reason, and causal IDs without placing those IDs into the unresolved score.

#### Scenario: Adverse Evidence makes a concrete score unresolved
- **WHEN** valid new adverse Evidence invalidates a formerly concrete conclusion and the proposal uses the canonical unresolved value
- **THEN** the revised slot remains canonically unresolved while the revision record retains the causal new Evidence ID

#### Scenario: Non-canonical unresolved value is rejected
- **WHEN** a proposal uses `score = None` with stronger-than-Low Confidence or non-empty score Evidence IDs
- **THEN** the proposal is rejected rather than weakening the canonical unresolved representation

### Requirement: Duplicate or conflicting targets fail closed locally
At most one proposal MAY target a dimension in one run. If two or more proposals target the same dimension, all proposals for that target SHALL be rejected and the initial value SHALL be retained regardless of proposal order, score magnitude, Confidence, direction, or equality. An invalid, unsupported, duplicated, or conflicting target SHALL NOT erase an independently valid revision for another dimension.

#### Scenario: Duplicate proposals do not select a winner
- **WHEN** two otherwise valid proposals target the same dimension
- **THEN** neither proposal is applied and that dimension retains its initial value

#### Scenario: Conflicting proposals preserve initial value
- **WHEN** proposals target one dimension with different revised values or reasons
- **THEN** no ordering, score, Confidence, or direction rule selects a proposal and the target remains initial

#### Scenario: Invalid target is isolated
- **WHEN** one target is duplicated or malformed and another target has one valid proposal
- **THEN** the invalid target remains initial while the independent valid target is revised

### Requirement: Revised scorecard is built only from accepted revisions
For a valid top-level run, the evaluator SHALL begin with the eight initial `DimensionScore` values, independently validate each target, replace only accepted target values, and construct a new immutable existing `DimensionScores`. Dimensions with no proposal or with invalid, unsupported, duplicate, conflicting, or state-preserving proposals MUST remain exactly equal to their initial values.

#### Scenario: Accepted revisions are applied without collateral changes
- **WHEN** one proposal is valid, one proposal is invalid, and six dimensions have no proposal
- **THEN** exactly the valid target changes and every other revised slot equals its initial slot

### Requirement: Risk Gate changes require authoritative Risk results
The capability SHALL accept only existing complete `RiskComplianceResult` values as the initial and revised Risk inputs for a Risk Gate comparison. It SHALL NOT accept a raw `RiskGateState` override, reclassify a finding, infer legal applicability, rerun Risk analysis, or alter existing Risk Gate precedence. An actual Risk Gate change SHALL create a trace only when the initial and revised authoritative gate states differ, a non-empty reason is supplied, every causal Evidence ID belongs to the declared universe, and at least one causal ID belongs to `red_team_evidence_ids`; otherwise no Risk Gate revision SHALL be accepted.

#### Scenario: Authoritative Risk re-evaluation changes Gate
- **WHEN** valid initial and revised `RiskComplianceResult` values expose different Risk Gate states and the comparison cites causal current-run Evidence
- **THEN** one Risk Gate revision trace retains both complete authoritative results, the reason, and causal Evidence IDs

#### Scenario: Raw Risk Gate override is unsupported
- **WHEN** a caller supplies a revised `RiskGateState` without a revised authoritative `RiskComplianceResult`
- **THEN** no Risk Gate revision is accepted

#### Scenario: Risk Gate change without new Evidence is rejected
- **WHEN** authoritative Risk Gate states differ but the causal trace is empty or baseline-only
- **THEN** no Risk Gate revision is accepted

#### Scenario: Unchanged authoritative Risk Gate creates no fake revision
- **WHEN** a revised authoritative Risk result is supplied but its Risk Gate equals the initial authoritative Risk Gate
- **THEN** no Risk Gate revision record is created and a separately valid Red Team finding may retain the new Evidence

### Requirement: Unit Economics Gate changes require authoritative results and unchanged policy
The capability SHALL accept only existing complete `UnitEconomicsResult` values as the initial and revised economics inputs. It SHALL compare their retained Minimum Viability Gate, Dynamic Target Gate, and `EconomicsOutcome` without recalculating economics, margins, thresholds, or Gate outcomes and without accepting raw outcome overrides. When both results are supplied, the retained Minimum Viability thresholds MUST be equal and the retained Dynamic Target thresholds MUST be equal. An actual economics Gate or outcome change SHALL create a trace only when those policy thresholds are unchanged, a non-empty reason is supplied, every causal Evidence ID belongs to the declared universe, and at least one causal ID belongs to `red_team_evidence_ids`; otherwise no economics Gate revision SHALL be accepted.

#### Scenario: Authoritative economics re-evaluation changes a Gate
- **WHEN** valid initial and revised `UnitEconomicsResult` values use equal policy thresholds, expose a changed Gate or economics outcome, and cite causal current-run Evidence
- **THEN** one economics revision trace retains both complete authoritative results, the reason, and causal Evidence IDs

#### Scenario: Raw economics Gate override is unsupported
- **WHEN** a caller supplies raw Minimum Viability, Dynamic Target, or `EconomicsOutcome` values without a revised authoritative `UnitEconomicsResult`
- **THEN** no economics Gate revision is accepted

#### Scenario: Policy threshold change invalidates economics revision
- **WHEN** the initial and revised authoritative economics results retain different Minimum Viability or Dynamic Target thresholds
- **THEN** no economics Gate revision is accepted even if a Gate outcome differs

#### Scenario: Economics change without new Evidence is rejected
- **WHEN** an authoritative economics Gate or outcome differs but the causal trace is empty or baseline-only
- **THEN** no economics Gate revision is accepted

#### Scenario: Unchanged economics Gate state creates no fake revision
- **WHEN** revised authoritative economics values are supplied but both Gates and `EconomicsOutcome` equal their initial values
- **THEN** no economics revision record is created and a separately valid Red Team finding may retain the new Evidence

### Requirement: Revision history is immutable, deterministic, and replay-stable
Output SHALL preserve the initial scores, revised scores, accepted Red Team findings, accepted per-dimension score or Confidence revision records, and accepted authoritative Risk and Unit Economics revision traces. Every actual revision record SHALL retain complete before and after values, a non-empty reason, and canonical causal Evidence IDs. Findings, score revisions, Gate traces, and all nested Evidence-ID tuples SHALL use one specified deterministic ordering independent of caller ordering. The output and all public nested values SHALL be immutable and SHALL contain no timestamp, runtime-generated identifier, persistence key, or mutable hidden state.

#### Scenario: Equivalent input ordering produces equivalent output
- **WHEN** semantically identical valid findings and independent proposals are supplied in different caller orders
- **THEN** all revised values, record ordering, reasons, and Evidence-ID ordering are equivalent

#### Scenario: Repeated execution is stable
- **WHEN** the same normalized run is evaluated repeatedly
- **THEN** the complete output values compare equal and no runtime metadata differs

#### Scenario: Output cannot be mutated
- **WHEN** a caller attempts to replace an output field, nested score, finding, or revision value
- **THEN** mutation is rejected and the retained history remains unchanged

### Requirement: Revised scores preserve downstream compatibility and ownership
The revised output SHALL use the existing `DimensionScores` contract directly accepted by `evaluate_scoring_decision(...)`. The Red Team capability SHALL NOT choose or revise weights, calculate aggregates, execute core thresholds, apply Risk or economics precedence, select a GO threshold, emit a final analytical label, create `FinalScorecard`, or orchestrate the end-to-end workflow. Existing Initial Scoring, Risk, Unit Economics, and scoring-decision semantics SHALL remain unchanged.

#### Scenario: Revised scorecard flows directly into decision execution
- **WHEN** Red Team evaluation returns revised scores and the caller supplies the existing remaining decision inputs
- **THEN** `evaluate_scoring_decision(...)` consumes the revised `DimensionScores` without conversion or contract adaptation

### Requirement: Deterministic core has no hidden external behavior
Evaluation SHALL be standard-library-only, side-effect-free, and dependent only on explicit inputs. It SHALL NOT access a network, system clock, random source, environment-owned policy, filesystem persistence, mutable global state, provider, browser, scraper, LLM, Evidence free text, acquisition or normalization boundary, Phase 6 analyzer, Evidence Policy or Assessment execution, Initial Scoring execution, Unit Economics calculation, Risk classification, report generator, or workflow orchestrator.

#### Scenario: Architecture remains offline and replayable
- **WHEN** the Red Team boundary is evaluated with valid explicit inputs
- **THEN** it performs only typed validation, new-Evidence authorization, deterministic accepted-revision application, and immutable trace construction
