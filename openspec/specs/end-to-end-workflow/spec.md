# end-to-end-workflow Specification

## Purpose

Defines a deterministic 16-stage coordinator that preserves existing authoritative research, analysis, Gate, scoring, and Red Team results in one traceable structured final state for downstream reporting.

## Requirements

### Requirement: Workflow uses one canonical fixed stage sequence
The capability SHALL expose exactly the following 16 stages in this order: candidate and target-market normalization; research plan definition; Evidence collection and normalization; Risk analysis and Risk Gate; Unit Economics and Economics Gates; Market Demand analysis; Competition analysis; VOC and Differentiation analysis; Supply Chain and Fulfillment analysis; Brand Potential analysis; Content Potential analysis; Initial Scoring from explicit caller-owned judgments; initial scoring decision and core-threshold evaluation; explicit Evidence-backed Red Team review input acceptance; Red Team revision application; and post-Red-Team authoritative-state resolution plus final scoring decision. Every workflow result SHALL contain one execution record for every stage in this fixed order, including stages that cannot execute.

#### Scenario: Canonical workflow exposes exactly 16 ordered stages
- **WHEN** any workflow run returns a structured result
- **THEN** its stage trace contains exactly one record for each canonical stage in the specified order

#### Scenario: Blocked tail retains its declared positions
- **WHEN** an unavailable prerequisite prevents several later stages from executing
- **THEN** those stages remain present in their canonical positions with explicit blocked state

### Requirement: Workflow subject is explicit and caller-owned
Stage 1 SHALL accept an explicit normalized candidate product and target market, validate that both are present as non-empty deterministic values, and preserve them without inferring a product, category, audience, proposition, or market. The workflow SHALL NOT silently replace an invalid or absent workflow subject with fabricated domain input.

#### Scenario: Explicit normalized subject is retained
- **WHEN** the caller supplies a valid normalized candidate product and target market
- **THEN** Stage 1 completes and the same subject values remain inspectable in the workflow result

#### Scenario: Missing candidate blocks dependent work
- **WHEN** the candidate product is absent or malformed
- **THEN** Stage 1 fails narrowly and every stage requiring the normalized subject is blocked without a synthesized candidate

### Requirement: Stage execution state is immutable and semantically distinct
Each stage record SHALL be immutable and SHALL use exactly one of `COMPLETE`, `UNRESOLVED`, `BLOCKED`, or `FAILED`. `COMPLETE` SHALL mean that the authoritative boundary produced a valid determinate result, including a negative business result. `UNRESOLVED` SHALL mean that the authoritative boundary executed and returned a valid authoritative result that retains insufficient, indeterminate, partial, or failed domain state. `BLOCKED` SHALL mean that an authoritative prerequisite required to call the stage does not exist. `FAILED` SHALL be limited to malformed workflow/control-plane input or an execution failure for which no existing capability returned its own valid fail-closed result. Stage state SHALL NOT replace or reinterpret an existing domain status, outcome, diagnostic, Gate, score, or decision label; in particular, a valid lower-level `FAILED` domain status SHALL NOT by itself make the workflow stage `FAILED`.

#### Scenario: Fatal Risk is complete rather than failed
- **WHEN** Risk analysis returns a valid authoritative result whose Risk Gate is `FATAL`
- **THEN** the Risk stage is `COMPLETE` and retains that result as a negative analytical outcome

#### Scenario: Unviable economics is complete rather than failed
- **WHEN** Unit Economics returns a valid authoritative result whose outcome is `UNVIABLE`
- **THEN** the Unit Economics stage is `COMPLETE` and retains that result as a negative analytical outcome

#### Scenario: Insufficient authoritative result is unresolved
- **WHEN** an existing capability returns a valid result that explicitly retains insufficient evidence or an unresolved outcome
- **THEN** the corresponding workflow stage is `UNRESOLVED` without replacing the underlying domain representation

#### Scenario: Valid failed domain result is unresolved rather than failed
- **WHEN** an existing capability returns a valid fail-closed authoritative result whose domain status is `FAILED`
- **THEN** the corresponding workflow stage is `UNRESOLVED` and retains that result without replacing its status or diagnostics

#### Scenario: Missing prerequisite is blocked without invocation
- **WHEN** a stage's required authoritative input is unavailable
- **THEN** that stage is `BLOCKED` and its lower-level capability is not invoked with placeholder input

### Requirement: Research orchestration remains the Research to Evidence owner
Stages 2 and 3 SHALL reuse the existing research-orchestration boundary with its explicit objective, ordered plan, injected acquisition, RawFinding normalization, run-local Evidence-ID allocation, task coverage, failures, and `ResearchRunResult`. Stage 2 SHALL expose only the plan outcome: it SHALL be `COMPLETE` with the exact existing `ResearchPlan` when a valid returned `ResearchRunResult` contains a plan, and SHALL be `UNRESOLVED` with no fabricated plan or workflow failure when that valid result contains no plan. Stage 3 SHALL be the sole canonical workflow holder of the complete existing value of every valid returned `ResearchRunResult`; it SHALL be `COMPLETE` when the retained run status is `COMPLETE` and otherwise `UNRESOLVED`, without changing the retained run's `COMPLETE`, `PARTIAL`, or `FAILED` domain status. The workflow-level Research-run accessor SHALL expose that same retained Stage 3 result. Only failure to obtain a valid `ResearchRunResult` SHALL make Stage 2 `FAILED` for an execution error and Stage 3 `BLOCKED`. The workflow SHALL NOT copy Research failures into Stage 2, create a replacement failure object, allocate, remap, renumber, clone, or translate Evidence IDs, or introduce another Research, Evidence, RawFinding, failure, or Research-status representation.

#### Scenario: Real in-memory research crosses the workflow boundary
- **WHEN** explicit in-memory planning, acquisition, and normalization inputs produce a valid complete research run
- **THEN** Stages 2 and 3 retain the existing plan, `ResearchRunResult`, normalized `Evidence`, and original allocated Evidence IDs
- **AND** both Research stages are `COMPLETE`

#### Scenario: Partial coverage remains visible
- **WHEN** research returns a valid `PARTIAL` `ResearchRunResult` with a plan and some Evidence but reports missing required task coverage
- **THEN** Stage 2 is `COMPLETE` with the exact existing plan and Stage 3 is `UNRESOLVED` with the complete existing `ResearchRunResult`
- **AND** the final workflow trace retains that partial state even if later stages produce valid results

#### Scenario: Failed Research run with a valid plan remains retained
- **WHEN** the Research boundary returns a valid `FAILED` `ResearchRunResult` with a valid plan but no Evidence
- **THEN** Stage 2 is `COMPLETE` with the exact existing plan and Stage 3 is `UNRESOLVED` with the complete existing `ResearchRunResult`

#### Scenario: Planner failure remains a retained Research run
- **WHEN** the existing Research boundary returns a valid `ResearchRunResult` with no plan and `RunStatus("FAILED")`
- **THEN** Stage 2 is `UNRESOLVED` with no output and no workflow failure kind
- **AND** Stage 3 is `UNRESOLVED` and retains that complete existing `ResearchRunResult`
- **AND** its run status, failures, and diagnostics remain inspectable through the same Stage 3 result
- **AND** the workflow does not reinterpret the valid lower-level fail-closed result as a workflow execution failure

#### Scenario: Planner exception diagnostics remain traceable
- **WHEN** the existing Research boundary returns a valid failed `ResearchRunResult` containing `PLANNER_EXCEPTION`
- **THEN** that exact failure remains reachable through the Stage 3 `ResearchRunResult`
- **AND** no workflow-specific replacement failure object is created

#### Scenario: Invalid plan diagnostics remain traceable
- **WHEN** the existing Research boundary returns a valid failed `ResearchRunResult` containing `INVALID_PLAN`
- **THEN** that exact failure remains reachable through the Stage 3 `ResearchRunResult`
- **AND** no workflow-specific replacement failure object is created

#### Scenario: No valid Evidence blocks Evidence-dependent analysis
- **WHEN** the retained Stage 3 `ResearchRunResult` contains no valid normalized Evidence
- **THEN** stages requiring an Evidence index are blocked and their analyzers are not invoked with fabricated or placeholder Evidence
- **AND** an independent Unit Economics stage still executes when all of its own explicit inputs are valid

#### Scenario: Absence of a valid ResearchRunResult is a workflow execution failure
- **WHEN** the Research boundary raises without returning its valid fail-closed contract or returns a value that is not a valid `ResearchRunResult`
- **THEN** Stage 2 is `FAILED` for an execution error and Stage 3 is `BLOCKED` by Stage 2
- **AND** the workflow does not fabricate a Research run

### Requirement: Workflow derives effective required-research readiness from two owned truths
The workflow SHALL accept one explicit caller-owned semantic-sufficiency input for required research with no positive default. For a valid exact boolean input, it SHALL derive one effective provider-neutral readiness value by requiring both: a valid retained Stage 3 `ResearchRunResult` whose status is `COMPLETE` and whose `missing_required_task_ids` is empty; and caller-owned semantic sufficiency equal to `true`. A false caller judgment SHALL produce effective readiness `false`. A missing or malformed caller judgment SHALL remain an invalid readiness input for fail-closed decision diagnostics rather than being coerced. The workflow MUST NOT change `ResearchRunResult`, infer semantic sufficiency from provider/acquisition success or Evidence text, or allow caller sufficiency to override incomplete execution coverage.

#### Scenario: Complete execution and explicit sufficiency are ready
- **WHEN** Stage 3 retains a valid `COMPLETE` run with no missing required task IDs and the caller supplies semantic sufficiency `true`
- **THEN** effective required-research readiness is `true`

#### Scenario: Missing required execution cannot be overridden
- **WHEN** Stage 3 is `PARTIAL` or `FAILED`, or retains any missing required task ID, and the caller supplies semantic sufficiency `true`
- **THEN** effective required-research readiness remains `false`

#### Scenario: Complete execution does not imply semantic sufficiency
- **WHEN** Stage 3 is `COMPLETE` with no missing required task IDs and the caller supplies semantic sufficiency `false`
- **THEN** effective required-research readiness is `false`

#### Scenario: Approved fallback does not imply sufficiency
- **WHEN** an approved fallback acquisition has already been normalized through the existing research contract but the caller judges the same declared Evidence need semantically insufficient
- **THEN** effective required-research readiness is `false` without inferring or storing fallback semantics in the workflow

#### Scenario: Missing or malformed semantic input fails closed
- **WHEN** the caller omits the semantic-sufficiency input or supplies a non-boolean representation
- **THEN** Stage 13 and Stage 16 cannot produce `GO` and retain the decision executor's readiness-input diagnostic

### Requirement: Existing authoritative analysis and Gate capabilities are composed directly
Stages 4 through 11 SHALL invoke the existing Risk, Unit Economics, Market Demand, Competition, VOC, Supply Chain, and Brand / Content capabilities using explicit caller-owned semantic inputs and the existing normalized Evidence, Evidence Policy, and assessment contracts. Brand Potential and Content Potential SHALL be recorded as separate ordered workflow stages while retaining their one authoritative existing Brand / Content result. The workflow SHALL NOT acquire additional data, infer propositions, classify Evidence text, generate qualitative judgments, calculate alternative Gate values, or convert outputs into parallel workflow domain models.

#### Scenario: Domain outputs cross without conversion
- **WHEN** the existing analyzers return authoritative immutable results
- **THEN** the workflow stores and exposes those same result values without a workflow-specific Evidence, analysis, Risk, economics, or Gate model

#### Scenario: Independent stages continue after an unresolved analysis
- **WHEN** one analysis stage is unresolved but another later analysis has all of its own authoritative prerequisites
- **THEN** the later analysis executes in canonical order and the earlier unresolved record remains unchanged

#### Scenario: Existing decision precedence survives valid negative gates
- **WHEN** Risk is `FATAL` or Unit Economics is `UNVIABLE` and all scoring inputs are otherwise valid
- **THEN** the workflow completes those Gate stages and later decisions retain the existing scoring-decision precedence

### Requirement: Upstream unresolved and adverse state is cumulative
The workflow result SHALL preserve every earlier unresolved, blocked, or failed stage record and every retained lower-level diagnostic through the end of the run. A later `COMPLETE` stage, accepted revision, resolved score, aggregate, Gate, or decision label SHALL NOT delete, overwrite, relabel, or imply resolution of an earlier stage record.

#### Scenario: Later valid result cannot erase earlier uncertainty
- **WHEN** an earlier stage is `UNRESOLVED` and a later stage returns a valid determinate result
- **THEN** both records remain independently inspectable with their original states in the final trace

#### Scenario: Final label does not rewrite history
- **WHEN** Stage 16 returns a determinate final analytical label
- **THEN** all earlier unresolved, blocked, and failed records remain present and unchanged

### Requirement: Initial Scoring reuses caller-owned judgments and existing outputs
Stage 12 SHALL invoke the existing Initial Scoring capability with explicit caller-owned qualitative judgments and the authoritative Phase 6, Risk, and Unit Economics results required by that capability. It SHALL retain the returned existing `DimensionScores`, including every canonical unresolved dimension, and SHALL NOT generate judgments, synthesize scores, convert missing values to zero, or introduce a second score hierarchy.

#### Scenario: Unresolved dimension remains canonical
- **WHEN** Initial Scoring returns a dimension with no supported score
- **THEN** Stage 12 retains the existing canonical unresolved `DimensionScore` and marks the stage unresolved without synthesizing a value

#### Scenario: Initial scorecard is the existing type
- **WHEN** Stage 12 executes successfully
- **THEN** its authoritative scorecard is directly usable by the existing scoring-decision capability without conversion

### Requirement: Initial decision uses the existing decision executor
Stage 13 SHALL invoke the existing scoring-decision executor with the Stage 12 `DimensionScores`, the caller-owned `WeightAdjustments`, original authoritative Risk Gate, original authoritative `UnitEconomicsResult`, the workflow-derived effective required-research readiness, and `DecisionPolicy`. It SHALL retain the complete existing pre-Red-Team `DecisionResult`, including aggregate, core-threshold results, failed core dimensions, unresolved dimensions, normalized readiness, Gate precedence, label, diagnostics, and Evidence IDs. The workflow SHALL NOT implement another aggregate, core-threshold, readiness-policy, precedence, or label engine.

#### Scenario: Core thresholds and readiness exactly match existing policy
- **WHEN** Stage 13 receives valid inputs
- **THEN** its core-threshold results, normalized readiness, and analytical label equal the result of the existing decision executor over those same inputs

#### Scenario: Core thresholds exactly match existing policy
- **WHEN** Stage 13 receives valid inputs
- **THEN** its core-threshold results and analytical label equal the result of the existing decision executor over those same inputs

#### Scenario: Initial decision remains inspectable
- **WHEN** Red Team and final decision stages later execute
- **THEN** the complete Stage 13 `DecisionResult` remains independently inspectable and unchanged

### Requirement: Red Team inputs remain explicit, caller-owned, and bound to the current run
Stage 14 SHALL accept only explicit caller-owned baseline Evidence IDs, Red Team Evidence IDs, findings, score revision proposals, and optional authoritative Risk and Unit Economics revision proposals expressed through the existing Red Team input contract. Every supplied baseline Evidence ID and Red Team Evidence ID SHALL resolve to an existing `Evidence` produced by Stage 3 of the same workflow run. A supplied Risk revision proposal's initial authoritative result SHALL value-equal the Stage 4 authoritative `RiskComplianceResult`, and a supplied economics revision proposal's initial authoritative result SHALL value-equal the Stage 5 authoritative `UnitEconomicsResult`. Authoritative value equality SHALL satisfy baseline binding without requiring Python object identity, including for a reconstructed immutable result with the same complete value.

If an Evidence ID is foreign to the current Stage 3 universe or an optional proposal baseline does not bind to the corresponding current-run result, Stage 14 SHALL be `FAILED` for invalid workflow/control-plane input, Stages 15 and 16 SHALL be `BLOCKED`, and the existing Red Team evaluator SHALL NOT be invoked. The workflow SHALL NOT silently drop, filter, replace, remap, renumber, repair, or substitute an offending ID or proposal. It SHALL NOT generate objections, perform hidden LLM reasoning, acquire or fabricate Evidence, allocate another Evidence ID, infer Evidence newness, rerun upstream analysis, or alter weights or business policy. Explicit empty Red Team collections SHALL represent a valid review with no proposed revision.

#### Scenario: Empty explicit review is valid
- **WHEN** the caller supplies canonical provenance and explicit empty findings and proposal collections
- **THEN** Stage 14 completes without inventing an objection or revision

#### Scenario: Red Team provenance belongs to the current workflow run
- **WHEN** any baseline Evidence ID or Red Team Evidence ID does not resolve to an `Evidence` produced by Stage 3 of the same workflow run
- **THEN** Stage 14 is `FAILED` without remapping, fabricating, replacing, or silently dropping that Evidence ID
- **AND** Stage 15 does not invoke the existing Red Team evaluator and Stages 15 and 16 remain `BLOCKED`

#### Scenario: Current-run Evidence provenance crosses unchanged
- **WHEN** every baseline Evidence ID and Red Team Evidence ID resolves to Stage 3 Evidence from the same workflow run
- **THEN** those exact IDs are passed unchanged to the existing Red Team evaluator
- **AND** the workflow introduces no second Evidence namespace, allocator, or renumbering step

#### Scenario: Reconstructed value-equal Risk baseline binds to Stage 4
- **WHEN** a Risk revision proposal contains a reconstructed immutable initial result that value-equals the current Stage 4 authoritative `RiskComplianceResult`
- **THEN** Stage 14 accepts the current-run Risk baseline binding without requiring object identity

#### Scenario: Foreign Risk baseline fails the workflow boundary
- **WHEN** a Risk revision proposal contains a structurally valid initial result that is not value-equal to the current Stage 4 authoritative `RiskComplianceResult`
- **THEN** Stage 14 is `FAILED` without dropping, repairing, substituting, or rewriting the proposal
- **AND** Stage 15 does not invoke the existing Red Team evaluator and Stages 15 and 16 remain `BLOCKED`

#### Scenario: Reconstructed value-equal economics baseline binds to Stage 5
- **WHEN** an economics revision proposal contains a reconstructed immutable initial result that value-equals the current Stage 5 authoritative `UnitEconomicsResult`
- **THEN** Stage 14 accepts the current-run economics baseline binding without requiring object identity

#### Scenario: Foreign economics baseline fails the workflow boundary
- **WHEN** an economics revision proposal contains a structurally valid initial result that is not value-equal to the current Stage 5 authoritative `UnitEconomicsResult`
- **THEN** Stage 14 is `FAILED` without dropping, repairing, substituting, or rewriting the proposal
- **AND** Stage 15 does not invoke the existing Red Team evaluator and Stages 15 and 16 remain `BLOCKED`

### Requirement: Red Team revisions reuse existing fail-closed semantics
After Stage 14 current-run binding succeeds, Stage 15 SHALL invoke the existing Red Team revision capability using the Stage 12 initial scores and the unchanged Stage 14 explicit inputs. It SHALL retain the complete existing `RedTeamRevisionResult`, including initial and revised scores, accepted findings, score revision records, and accepted authoritative Risk and economics revision records. The existing Red Team capability SHALL remain the sole owner of canonical ordering, uniqueness, disjointness, causal Evidence authorization, proposal-local validity, duplicate/conflicting behavior, authoritative revised-result validity, economics threshold consistency, and per-target or whole-run fail-closed semantics. The workflow SHALL NOT implement a second Red Team validator or reinterpret a proposal-local rejection.

#### Scenario: No accepted revision preserves initial values
- **WHEN** the existing Red Team boundary accepts no revision
- **THEN** revised scores equal the initial scores and no Risk or economics override is manufactured

#### Scenario: Valid score revision changes only accepted dimensions
- **WHEN** the existing Red Team boundary accepts one dimension revision and rejects another
- **THEN** the Stage 15 result changes only the accepted dimension and preserves every other initial score

#### Scenario: Duplicate or conflicting proposal remains fail closed
- **WHEN** multiple proposals target the same dimension
- **THEN** Stage 15 retains the existing Red Team result that leaves that dimension unchanged rather than selecting a winner

#### Scenario: Red Team cannot mutate policy
- **WHEN** a review proposes or implies different weights, GO threshold, economics thresholds, core thresholds, or scoring policy
- **THEN** the workflow does not apply that change through the Red Team boundary

### Requirement: Final authoritative state is resolved only from accepted revisions
Stage 16 SHALL use `RedTeamRevisionResult.revised_scores` as final scores. It SHALL use the accepted Risk revision's complete revised authoritative result when present and otherwise the exact original Risk result. It SHALL use the accepted economics revision's complete revised authoritative result when present and otherwise the exact original Unit Economics result. It SHALL pass the resolved Risk result's existing Risk Gate, the resolved Unit Economics result, and the exact same caller-owned `WeightAdjustments`, workflow-derived effective required-research readiness, and `DecisionPolicy` used at Stage 13 to the existing scoring-decision executor. A raw workflow-level Gate or readiness override SHALL NOT be accepted.

#### Scenario: Accepted authoritative revisions drive final evaluation
- **WHEN** Stage 15 accepts revised scores plus authoritative Risk or economics revisions
- **THEN** Stage 16 invokes the existing decision executor with those revised scores, accepted complete authoritative results, and the unchanged effective readiness

#### Scenario: Unrevised authoritative values preserve identity
- **WHEN** Stage 15 accepts no Risk or economics revision
- **THEN** Stage 16 uses the exact original authoritative Risk and Unit Economics values

#### Scenario: Same business policy and readiness are reused
- **WHEN** initial and final decision execution occur in one workflow run
- **THEN** both evaluations receive the same caller-owned `WeightAdjustments`, derived effective required-research readiness, and `DecisionPolicy`

#### Scenario: Same business policy is reused
- **WHEN** initial and final decision execution occur in one workflow run
- **THEN** both evaluations receive the same caller-owned `WeightAdjustments` and `DecisionPolicy`

#### Scenario: Final label changes only through existing semantics
- **WHEN** accepted Evidence-backed revisions change a final analytical label
- **THEN** the change is produced solely by the existing revised scores, authoritative Gate values, unchanged readiness, and scoring-decision precedence

### Requirement: Structured final result retains one source of truth
The workflow endpoint SHALL be one immutable structured analytical result, not a rendered report. It SHALL expose the ordered 16-stage trace; normalized Evidence traceability through existing outputs; authoritative analysis results; initial Risk and Unit Economics values; initial `DimensionScores`; initial `DecisionResult`; complete `RedTeamRevisionResult`; resolved post-Red-Team Risk and economics values; revised `DimensionScores`; final `DecisionResult`; and all unresolved, blocked, or failed stage information. Typed convenience accessors MAY reference these same values but SHALL NOT copy or translate them into competing authoritative objects.

#### Scenario: Initial and final decisions coexist
- **WHEN** a workflow reaches Stage 16
- **THEN** both complete existing `DecisionResult` values remain independently accessible in the structured result

#### Scenario: Downstream reporting receives structured state
- **WHEN** a downstream consumer receives the ECO-37 result
- **THEN** it can inspect the Evidence, analyses, Gate history, score history, Red Team trace, and final analytical decision without parsing rendered prose

#### Scenario: Workflow renders no report
- **WHEN** ECO-37 completes successfully
- **THEN** it returns structured values only and does not render a human-readable report or Evidence Appendix

### Requirement: Workflow is deterministic, replay-stable, and side-effect-free
The workflow and all new public nested values SHALL depend only on explicit inputs and existing deterministic capabilities. Equivalent normalized explicit inputs SHALL produce value-equal complete workflow results regardless of caller ordering where an existing contract already canonicalizes ordering. Repeated execution SHALL add no timestamp, runtime-generated identity, random value, persistence key, hidden environment policy, mutable global state, network access, internal LLM call, retry, cache, or asynchronous execution behavior.

#### Scenario: Equivalent inputs produce equivalent results
- **WHEN** two runs receive semantically equivalent normalized explicit inputs
- **THEN** their ordered stage states, authoritative outputs, revision history, and final result compare equal

#### Scenario: Repeated execution has no runtime metadata drift
- **WHEN** the same normalized inputs are evaluated repeatedly
- **THEN** no identity, timestamp, ordering, or hidden-state difference appears in the result

#### Scenario: Result is immutable
- **WHEN** a caller attempts to mutate a stage record or final workflow field
- **THEN** mutation is rejected and the retained execution history remains unchanged

### Requirement: Dependency direction and downstream reporting boundary remain enforced
Only the new workflow layer SHALL depend on the composed lower-level capabilities. Existing Research, Evidence, analysis, Risk, Unit Economics, Initial Scoring, scoring-decision, and Red Team modules SHALL NOT import or depend on the workflow. `research_orchestration` SHALL continue to stop at Research to Evidence. The workflow SHALL NOT add provider-backed acquisition, a generic plugin or workflow framework, persistence, checkpoints, event sourcing, final-report rendering, Evidence Appendix rendering, or ECO-39 evaluation-suite infrastructure. Skill and methodology documentation SHALL describe Stage 16 as structured Final Result resolution and SHALL route readable final-report generation to the downstream ECO-38 capability.

#### Scenario: Lower-level architecture remains acyclic
- **WHEN** module dependencies are inspected after implementation
- **THEN** no lower-level module imports the end-to-end workflow capability

#### Scenario: Research boundary remains narrow
- **WHEN** the research-orchestration module is inspected after implementation
- **THEN** it still owns only planning, injected acquisition, RawFinding normalization, Evidence allocation, and run coverage rather than downstream workflow execution

#### Scenario: Documentation preserves the ECO-37 to ECO-38 handoff
- **WHEN** the Skill workflow and relevant methodology routing are read after implementation
- **THEN** Stage 16 ends in the structured Final Result and human-readable report plus Evidence Appendix generation is identified as downstream and unavailable until ECO-38
