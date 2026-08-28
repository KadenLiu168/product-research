## ADDED Requirements

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

## MODIFIED Requirements

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
