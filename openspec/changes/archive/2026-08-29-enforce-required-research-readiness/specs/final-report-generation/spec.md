## MODIFIED Requirements

### Requirement: Executive Summary projects material final-state facts
The Executive Summary SHALL concisely present the known candidate product, target market, state source as `FINAL`, `LATEST-KNOWN`, or `INITIAL`, authoritative final analytical label, authoritative aggregate score, final Risk state, final Unit Economics state, authoritative required-research readiness, retained research-run status, missing required task IDs, failed or unresolved core dimensions, material unresolved workflow state, key decision Evidence references, and a concise accepted Red Team change count or state when each is available. A workflow whose stages are all complete SHALL expose one compact completion statement and MUST NOT enumerate all successful stage records. An incomplete workflow SHALL expose only its `UNRESOLVED`, `BLOCKED`, and `FAILED` stage records in the workflow-status projection, retaining existing failure kinds and blocking dependencies where present. The summary MUST NOT hide material adverse or unresolved state for brevity and MUST NOT invent an overall-report Confidence, strongest-Evidence claim, unsupported recommendation, generic severity order, autonomous commercial decision, or report-owned readiness conclusion.

#### Scenario: Complete summary uses authoritative facts
- **WHEN** the final workflow result contains the listed authoritative facts
- **THEN** the Executive Summary presents them without deriving a second recommendation, readiness judgment, or confidence value

#### Scenario: Material incompleteness remains prominent
- **WHEN** workflow, required-research readiness, research execution, core-threshold, Risk, Economics, or decision state is unresolved, blocked, failed, false, or absent
- **THEN** the Executive Summary exposes that material state rather than implying successful completion

#### Scenario: Semantic insufficiency remains visible after complete execution
- **WHEN** the retained research run is `COMPLETE` but the authoritative effective required-research readiness is `false`
- **THEN** the Executive Summary presents both facts without treating execution completeness as semantic sufficiency

#### Scenario: Complete workflow is reported once
- **WHEN** all workflow stages are `COMPLETE`
- **THEN** the Executive Summary reports `Workflow Status: COMPLETE` or an equivalent single completion statement and does not enumerate the 16 successful stage records

#### Scenario: Incomplete workflow lists only non-complete stages
- **WHEN** one or more workflow stages are `UNRESOLVED`, `BLOCKED`, or `FAILED`
- **THEN** the Executive Summary lists those non-complete stages in canonical workflow order without listing successful stages

#### Scenario: Failure and blocking detail is retained
- **WHEN** a listed non-complete stage retains a failure kind or blocking dependencies
- **THEN** the Executive Summary preserves that failure kind and those blocking dependencies with the stage status

### Requirement: Risk, Unit Economics, and Final Analysis Label remain authoritative
The report SHALL use resolved post-Red-Team Risk and Unit Economics results, the existing final `DecisionResult.label`, its normalized required-research readiness, and its reasons exactly when available. It SHALL preserve relevant before-and-after history when accepted Red Team revisions changed Risk or Unit Economics. Risk revision presentation SHALL expose at minimum the authoritative Risk Gate before and after. Unit Economics revision presentation SHALL expose the authoritative Economics outcome before and after and the Minimum Viability Gate and Dynamic Target Gate transitions where applicable. These transitions MUST NOT rely on rendering the complete Risk or Unit Economics result-object representation. The report MUST NOT recompute either Gate, derive readiness, reinterpret Gate precedence or decision reasons, infer a new classification or economics outcome, promote or downgrade a label, or fabricate a fallback commercial label.

#### Scenario: Accepted Gate revisions are visible
- **WHEN** an accepted Red Team revision changed Risk or Unit Economics
- **THEN** the final presentation uses the resolved result and retains the relevant authoritative before-and-after change

#### Scenario: Final label and readiness are copied exactly
- **WHEN** an authoritative final decision exists
- **THEN** Final Analysis Label and required-research readiness equal its values exactly and its reasons are not reinterpreted

#### Scenario: Final label is copied exactly
- **WHEN** an authoritative final decision exists
- **THEN** Final Analysis Label equals its label exactly and its reasons are not reinterpreted

#### Scenario: Absent final decision stays unresolved
- **WHEN** no authoritative final decision exists
- **THEN** Final Analysis Label and required-research readiness explicitly report unavailable or unresolved state and do not create fallback values

#### Scenario: Risk revision presents the Gate transition
- **WHEN** an accepted Risk revision is rendered
- **THEN** the report presents its Risk Gate before and after without serializing the complete Risk result objects

#### Scenario: Unit Economics revision presents closed-state transitions
- **WHEN** an accepted Unit Economics revision is rendered
- **THEN** the report presents its Economics outcome and applicable Minimum Viability and Dynamic Target Gate transitions without serializing the complete Unit Economics result objects

### Requirement: Key Uncertainties uses explicit structured state only
Key Uncertainties SHALL project only explicit existing `UNRESOLVED`, `BLOCKED`, or `FAILED` workflow state; false or invalid authoritative required-research readiness; retained research status, missing required task IDs, failed task IDs, task status, and existing structured failure reasons; missing, unknown, or unresolved domain state; existing diagnostics, factors, or reasons; unresolved score dimensions or core thresholds; and unresolved Risk or Unit Economics state. It SHALL preserve canonical structural ordering and authoritative closed values while using explicit fixed reader-facing labels for known fields instead of report-internal `snake_case` names. It MUST NOT dynamically humanize arbitrary attributes, infer semantics from free text or arbitrary metadata, fabricate provider operation or fallback state, expose credentials or raw authentication/configuration values, invent hypothetical weaknesses, select only purportedly important uncertainties, or introduce a generic severity-ranking model.

#### Scenario: Explicit uncertainty is retained
- **WHEN** an authoritative workflow, research, decision, or domain artifact records uncertainty, incomplete readiness, or failure
- **THEN** Key Uncertainties presents that state and its existing reason or effect without inventing a new weakness

#### Scenario: Missing required task details retain research ownership
- **WHEN** the retained research result contains missing required task IDs and structured task or failure state
- **THEN** Key Uncertainties projects those existing values deterministically without copying them into the decision result

#### Scenario: Semantic insufficiency is visible without fabricated acquisition detail
- **WHEN** Stage 3 execution is `COMPLETE` but authoritative required-research readiness is `false` and no structured provider operation or fallback value exists
- **THEN** Key Uncertainties presents the readiness state without inventing provider operation, provider task, fallback-used, or fallback-approval detail

#### Scenario: Cross-domain uncertainty is not severity-ranked
- **WHEN** multiple uncertainty categories have no shared authoritative severity vocabulary
- **THEN** they appear in deterministic structural order without claims that one is objectively more severe

#### Scenario: Uncertainty fields use fixed reader-facing labels
- **WHEN** Key Uncertainties renders a known missing, unknown, unresolved, diagnostic, factor, reason, research, or readiness field
- **THEN** it uses the field's stable reader-facing label and preserves the authoritative value without exposing the internal field name

#### Scenario: Secrets are not report inputs
- **WHEN** readiness and research state are rendered
- **THEN** reporting neither reads nor adds provider credentials, authentication values, or raw configuration secrets
