## Purpose

Defines the persistent v1 evaluation contract that proves existing product-research behavior through reusable deterministic fixtures, authoritative acceptance assertions, and the established fresh-context Agent scenario protocol without becoming a runtime policy or decision layer.

## ADDED Requirements

### Requirement: Evaluation remains outside the production dependency graph
The v1 evaluation suite SHALL observe existing authoritative Evidence, assessment, analysis, Unit Economics, scoring, Gate, Red Team, workflow, and reporting boundaries without defining parallel runtime semantics. Evaluation support SHALL remain test-only and SHALL NOT introduce a production evaluation engine, an aggregate evaluation-quality score, a new product decision, or a replacement result model.

#### Scenario: Acceptance uses existing owners
- **WHEN** an evaluation exercises a deterministic production behavior
- **THEN** its oracle asserts the output of the narrowest existing authoritative boundary capable of proving that behavior
- **AND** it does not recalculate or reinterpret the owner's policy

#### Scenario: Cross-stage behavior uses the integration boundary
- **WHEN** an invariant depends on multiple workflow stages or downstream presentation
- **THEN** the evaluation crosses the existing workflow and, where report behavior is material, the existing final-report boundary

### Requirement: Reusable fixtures cover the required scenario matrix
The suite SHALL provide reusable deterministic test fixtures or builders for the `normal`, `missing`, `conflicting`, `expired`, `high-risk`, `economic-failure`, and `evidence-based-score-revision` scenario families. The suite SHALL also provide a focused variant in which the aggregate satisfies the existing explicit GO threshold while at least one existing core-dimension threshold fails. Every fixture SHALL be constructed from explicit fixed values, and every time-sensitive fixture SHALL receive an explicit timezone-aware `as_of` value.

#### Scenario: Normal fixture reaches reportable final state
- **WHEN** the complete normal fixture is evaluated
- **THEN** it can exercise Evidence traceability, stable scoring and decision, the complete workflow, and final-report generation

#### Scenario: Missing fixture preserves absence
- **WHEN** the missing fixture omits required input or Evidence
- **THEN** the authoritative owner retains its existing missing, unresolved, blocked, or failed state
- **AND** evaluation supplies neither a zero nor a fabricated fallback

#### Scenario: Conflicting fixture preserves conflict
- **WHEN** the conflicting fixture supplies explicit conflict through the existing Evidence assessment contract
- **THEN** the conflict and adverse Evidence remain observable
- **AND** the suite does not collapse them into unqualified factual support or introduce a new conflict algorithm

#### Scenario: Expired fixture uses explicit time
- **WHEN** the expired fixture is evaluated with fixed Evidence dates and a timezone-aware `as_of`
- **THEN** current-use rejection or contextual treatment follows the existing Evidence Policy without reading the system clock

#### Scenario: High-risk fixture retains Risk precedence
- **WHEN** valid explicit upstream state produces the existing fatal Risk condition while the score aggregate would otherwise be favorable
- **THEN** the final analytical label follows the existing Risk precedence

#### Scenario: Economic-failure fixture retains economics precedence
- **WHEN** valid explicit Unit Economics state produces the existing unviable condition while the score aggregate would otherwise be favorable
- **THEN** the final analytical label follows the existing Unit Economics precedence

#### Scenario: Evidence-based revision crosses the v1 path
- **WHEN** explicit baseline Evidence and valid current-run new Evidence authorize a score revision
- **THEN** the fixture exposes the baseline score, accepted authoritative revision, revised score, final scoring decision, and final-report causal trace

#### Scenario: Core-threshold variant defeats favorable aggregate
- **WHEN** the aggregate satisfies the existing GO threshold but an existing core-dimension threshold fails
- **THEN** the final result is not `GO`
- **AND** the failed core dimension and existing diagnostic or reason state remain explicit

### Requirement: Evidence Coverage has explicit acceptance oracles
Automated Evidence Coverage acceptance SHALL require authoritative factual or scored state that needs Evidence to retain existing Evidence-ID traceability. Required absent Evidence SHALL remain missing, unresolved, or blocked according to its existing owner contract and SHALL NOT be synthesized to complete evaluation. Agent acceptance SHALL require material claims to use Evidence and SHALL prohibit missing research from becoming a model-knowledge conclusion.

#### Scenario: Required support remains traceable
- **WHEN** an authoritative state declares Evidence support
- **THEN** every declared supporting Evidence ID remains inspectable through the existing authoritative Evidence boundary

#### Scenario: Missing coverage cannot be completed by evaluation
- **WHEN** required Evidence coverage is absent
- **THEN** the existing missing, unresolved, or blocked state is accepted as the observable result
- **AND** the evaluation fixture creates no substitute Evidence

### Requirement: Citation Accuracy has explicit acceptance oracles
Automated Citation Accuracy acceptance SHALL require every cited Evidence ID to resolve under the existing authoritative Evidence boundary and every current factual use to obey the existing Evidence Policy. Missing, unknown, duplicate, foreign-run, stale, or policy-ineligible Evidence SHALL NOT become valid factual support. Evidence selected for a final report SHALL remain within the current workflow Evidence universe. The suite SHALL NOT define a separate citation score.

#### Scenario: Eligible current citation resolves
- **WHEN** a factual claim cites current policy-eligible Evidence from the authoritative universe
- **THEN** the existing citation-support boundary accepts the reference without evaluation-side scoring

#### Scenario: Invalid citation fails closed
- **WHEN** a citation is missing, unknown, duplicated where uniqueness is required, foreign to the current run, stale for current use, or otherwise policy-ineligible
- **THEN** it cannot establish valid factual support

### Requirement: Hallucination Resistance spans deterministic and Agent acceptance
Deterministic Hallucination Resistance acceptance SHALL prove that missing, unknown, unsupported, stale, conflicting, or invalid inputs cannot be silently converted into successful authoritative state. Agent acceptance SHALL prove through observable fixed rubrics that the Agent does not fabricate facts, numeric inputs, Evidence, scores, completed research, Gate results, calculations, or viability conclusions and does not present unsupported model knowledge as researched fact. No LLM hallucination grader SHALL be introduced.

#### Scenario: Deterministic invalid state remains fail closed
- **WHEN** a fixture supplies missing, unknown, unsupported, stale, conflicting, or invalid input
- **THEN** the existing unresolved, blocked, failed, or ineligible state remains intact
- **AND** no successful authoritative value is fabricated

#### Scenario: Agent no-invention behavior uses a fixed rubric
- **WHEN** Hallucination Resistance requires Agent-level evaluation
- **THEN** a fresh-context RED/GREEN scenario judges only observable fabrication, unsupported factual claims, or premature conclusions as `PASS` or `FAIL`

### Requirement: Estimate Discipline has explicit acceptance oracles
Automated Estimate Discipline acceptance SHALL preserve the existing `Observed`, `Estimated`, `Calculated`, and `Unknown` semantics. `Estimated` SHALL NOT silently become `Observed`, `Unknown` SHALL NOT silently become known, and an estimate SHALL NOT support an observed-fact use that existing Evidence Policy forbids. Agent acceptance SHALL require evidence-supported estimates to be identified as estimates and SHALL prohibit missing or unsupported values from being presented as facts.

#### Scenario: Estimate cannot satisfy observed-fact use
- **WHEN** `Estimated` Evidence is offered for an observed-fact claim mode that existing policy forbids
- **THEN** the authoritative policy result remains ineligible
- **AND** evaluation does not promote the Evidence status

#### Scenario: Unknown remains unknown
- **WHEN** a required value is unavailable
- **THEN** deterministic and Agent acceptance retain `Unknown` or the existing unresolved representation rather than inventing a known value

### Requirement: Repeatability has explicit acceptance oracles
Equivalent normalized fixture inputs SHALL produce equivalent applicable policy and assessment results, workflow structured results, ordered stage traces, scores, Gate results, decision results, and accepted Red Team history. Equivalent reportable results SHALL render byte-for-byte identical Markdown. Expected results SHALL depend on explicit time inputs and SHALL NOT depend on wall-clock time. Natural-language Agent output SHALL NOT be required to be byte-identical.

#### Scenario: Equivalent deterministic replay is equal
- **WHEN** semantically equivalent normalized deterministic inputs are evaluated repeatedly
- **THEN** all applicable structured outputs and canonical orderings compare equal

#### Scenario: Equivalent report replay is byte-identical
- **WHEN** equivalent reportable workflow results are rendered repeatedly
- **THEN** the complete Markdown outputs are byte-for-byte identical

### Requirement: Scoring Stability has explicit acceptance oracles
Semantically equivalent explicit scoring inputs SHALL produce the same applicable `DimensionScores`, final weights, aggregate, core-threshold outcomes, failed or unresolved dimensions, reason codes, and analytical label. Acceptance SHALL reuse the existing deterministic `Decimal` semantics and SHALL NOT introduce a tolerance band.

#### Scenario: Equivalent scoring input preserves exact result
- **WHEN** equivalent explicit scoring inputs are evaluated in semantically irrelevant orders or replayed
- **THEN** scores, weights, aggregate, thresholds, diagnostics, and analytical label are exactly equivalent under existing Decimal semantics

### Requirement: Gate Correctness has explicit acceptance oracles
Gate Correctness acceptance SHALL prove that fatal Risk and unviable Unit Economics retain their existing independent precedence over an otherwise favorable aggregate. Evaluation SHALL invoke the existing decision owner and SHALL NOT reproduce Gate precedence locally.

#### Scenario: Fatal Risk overrides favorable aggregate
- **WHEN** Risk is `FATAL` and the aggregate would otherwise satisfy the positive threshold
- **THEN** the existing final analytical label reflects fatal Risk precedence

#### Scenario: Unviable economics overrides favorable aggregate
- **WHEN** Unit Economics is `UNVIABLE` and the aggregate would otherwise satisfy the positive threshold
- **THEN** the existing final analytical label reflects Unit Economics precedence

### Requirement: Core Threshold Enforcement has an explicit acceptance oracle
Core Threshold Enforcement acceptance SHALL include a focused case whose aggregate otherwise satisfies the explicit GO threshold while at least one existing core-dimension threshold fails. The authoritative result SHALL not be `GO` and SHALL retain the failed core dimension and existing diagnostic or reason state. Evaluation SHALL NOT duplicate core-threshold logic.

#### Scenario: Failed core dimension prevents GO
- **WHEN** an otherwise favorable aggregate accompanies an existing core-threshold failure
- **THEN** the authoritative result is not `GO`
- **AND** the failed dimension and diagnostic or reason state remain explicit

### Requirement: Red Team Effectiveness has explicit acceptance oracles
Red Team Effectiveness acceptance SHALL use existing deterministic authorization and revision semantics. Baseline-only Evidence SHALL NOT authorize an actual score or Confidence revision; valid current-run new Evidence SHALL be able to authorize an otherwise valid revision. Only accepted targets SHALL change, unrelated dimensions SHALL remain unchanged, and duplicate or conflicting target proposals SHALL retain existing fail-closed behavior. Accepted revisions SHALL preserve before value, after value, reason, and causal Evidence IDs. Final scoring SHALL consume the authoritative revised state, and final reporting SHALL expose accepted history and causal trace without recomputing Red Team reasoning.

#### Scenario: Baseline-only Evidence cannot authorize revision
- **WHEN** an otherwise actual score or Confidence change cites no valid current-run new Evidence
- **THEN** the existing Red Team boundary accepts no actual revision

#### Scenario: New Evidence authorizes only valid targets
- **WHEN** valid current-run new Evidence causally supports an otherwise valid revision proposal
- **THEN** the accepted target changes with before, after, reason, and causal Evidence trace
- **AND** unrelated dimensions remain unchanged

#### Scenario: Duplicate or conflicting target fails closed
- **WHEN** proposals duplicate or conflict for the same target
- **THEN** existing fail-closed target behavior is preserved without winner selection

#### Scenario: Revised state reaches decision and report
- **WHEN** a score revision is accepted
- **THEN** final scoring consumes the authoritative revised scores
- **AND** reporting exposes the accepted revision history and causal Evidence without recomputing it

### Requirement: Report Traceability has explicit acceptance oracles
Report Traceability acceptance SHALL require report-selected Evidence references to resolve within the current workflow Evidence universe and SHALL require dangling or foreign references to fail closed. The Evidence Appendix SHALL contain the authoritative Evidence universe according to the existing report contract, adverse Evidence SHALL NOT be silently removed, and unresolved, blocked, or failed workflow state SHALL remain visible. Accepted Red Team revisions SHALL preserve their causal trace. Reporting SHALL NOT manufacture missing score, Gate, decision, or Evidence state.

#### Scenario: Current-run report references resolve
- **WHEN** a report selects Evidence from a workflow result
- **THEN** every selected reference resolves inside that result's authoritative Evidence universe

#### Scenario: Foreign report reference fails closed
- **WHEN** reportable state contains a dangling or foreign Evidence reference
- **THEN** the existing report boundary rejects it rather than rendering invented support

#### Scenario: Appendix and adverse state remain complete
- **WHEN** a report is rendered from a workflow result containing supporting and adverse Evidence
- **THEN** its Evidence Appendix follows the existing authoritative-universe contract
- **AND** adverse Evidence is not silently removed

#### Scenario: Incomplete and revised state remains visible
- **WHEN** workflow state is unresolved, blocked, or failed, or contains accepted Red Team revisions
- **THEN** the report preserves the incomplete state and any accepted causal revision trace without manufacturing missing values

### Requirement: Agent behavior acceptance reuses the existing scenario protocol
Agent-owned behavior SHALL be evaluated through the existing fresh-context RED/GREEN protocol in `tests/scenarios.md`, using its fixed per-item `PASS` or `FAIL` rubrics and observable behavior summaries. The evaluation suite SHALL first inventory and map existing scenarios to ECO-39 Agent oracles. It SHALL add only the minimum scenario needed for an uncovered Agent-owned behavior and SHALL NOT require byte-identical prose, judge writing style, assign a product-viability or overall Agent-quality score, create a second Agent judge framework, or use LLM-as-a-judge.

#### Scenario: Existing rubric already covers an Agent oracle
- **WHEN** an existing scenario and rubric observably prove an ECO-39 Agent-owned behavior
- **THEN** the evaluation mapping reuses that scenario without adding a duplicate ECO-39-named scenario

#### Scenario: Agent behavior remains uncovered
- **WHEN** the inventory finds an Agent-owned Hallucination Resistance, Estimate Discipline, Evidence-use, citation-discipline, or unresolved-risk behavior with no sufficient existing rubric
- **THEN** one minimal fresh-context RED/GREEN scenario is added with a fixed observable `PASS` or `FAIL` rubric

### Requirement: Acceptance is offline and regression-complete
Automated acceptance SHALL use the repository's existing standard-library test command and SHALL require no network, live provider, browser, scraper, LLM, system clock, randomness, persistence, or new third-party dependency. The focused evaluation suite and the complete existing automated suite SHALL pass together. Any unrelated production defect exposed by evaluation SHALL remain recorded as failing evidence and SHALL be corrected only through a separately scoped Change unless this capability cannot operate without the correction.

#### Scenario: Complete automated suite runs offline
- **WHEN** the repository's standard automated test command executes with the v1 evaluation suite
- **THEN** every deterministic fixture and acceptance assertion runs without an external service, hidden time source, random source, persistence side effect, or added test framework

#### Scenario: Evaluation exposes an unrelated defect
- **WHEN** an ECO-39 acceptance case reveals a contradiction outside the evaluation contract
- **THEN** the failing evidence is preserved
- **AND** ECO-39 does not silently expand into an unrelated production repair
