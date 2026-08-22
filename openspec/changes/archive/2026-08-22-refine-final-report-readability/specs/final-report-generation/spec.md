## MODIFIED Requirements

### Requirement: Analytical dimension sections preserve authoritative findings
The eight analytical sections SHALL correspond exactly, and in canonical order, to Market Demand, Competition, Price & Profitability, VOC & Differentiation, Supply Chain & Fulfillment, Brand Potential, Content Potential, and Risk & Compliance. Each section SHALL organize only the authoritative state available for its dimension, including existing outcomes or conclusions, Confidence, supporting, adverse, and excluded Evidence IDs, missing or unknown state, diagnostics, factors, coverage, and every retained domain finding where those values exist. User-visible field labels SHALL come from explicit fixed presentation mappings and MUST NOT expose report-internal `snake_case` names or dynamically humanize arbitrary attributes. Findings SHALL use a compact deterministic layout while preserving each applicable proposition or text, outcome, dimension, category, area, aspect, Confidence, supporting, adverse, and excluded Evidence IDs, prevalence and its supporting Evidence IDs, scope and its supporting Evidence IDs, factors, and diagnostics without ranking, omission, or semantic summarization. Closed domain values MUST remain unchanged, and presentation MUST NOT semantically reinterpret Evidence or derive a replacement conclusion.

#### Scenario: Available dimension state is preserved
- **WHEN** a dimension has authoritative findings, Confidence, Evidence lineage, diagnostics, factors, or coverage state
- **THEN** its section preserves those values without rewriting their business meaning

#### Scenario: Missing dimension state remains unavailable
- **WHEN** a dimension has no authoritative analysis or score
- **THEN** its section marks the missing or unresolved state explicitly and does not substitute zero, neutral, or inferred content

#### Scenario: Analytical fields use fixed reader-facing labels
- **WHEN** an analytical section renders a retained field with a defined presentation mapping
- **THEN** the report uses its stable reader-facing label while preserving the authoritative field value exactly

#### Scenario: All retained findings remain compact and traceable
- **WHEN** an analytical result contains multiple authoritative findings
- **THEN** every finding appears in canonical input order in a compact layout with all applicable outcome, Confidence, lineage, factor, and diagnostic values and none is ranked or dropped

#### Scenario: Risk findings retain their authoritative structure
- **WHEN** the final authoritative Risk result contains coverage state and findings
- **THEN** Risk & Compliance concisely preserves the Risk Gate, required, supported, unresolved, and missing areas, proposition, outcome, supported classification, Confidence, supporting, adverse, and excluded Evidence IDs, and diagnostics

### Requirement: Executive Summary projects material final-state facts
The Executive Summary SHALL concisely present the known candidate product, target market, state source as `FINAL`, `LATEST-KNOWN`, or `INITIAL`, authoritative final analytical label, authoritative aggregate score, final Risk state, final Unit Economics state, failed or unresolved core dimensions, material unresolved workflow state, key decision Evidence references, and a concise accepted Red Team change count or state when each is available. A workflow whose stages are all complete SHALL expose one compact completion statement and MUST NOT enumerate all successful stage records. An incomplete workflow SHALL expose only its `UNRESOLVED`, `BLOCKED`, and `FAILED` stage records in the workflow-status projection, retaining existing failure kinds and blocking dependencies where present. The summary MUST NOT hide material adverse or unresolved state for brevity and MUST NOT invent an overall-report Confidence, strongest-Evidence claim, unsupported recommendation, generic severity order, or autonomous commercial decision.

#### Scenario: Complete summary uses authoritative facts
- **WHEN** the final workflow result contains the listed authoritative facts
- **THEN** the Executive Summary presents them without deriving a second recommendation or confidence value

#### Scenario: Material incompleteness remains prominent
- **WHEN** workflow, core-threshold, Risk, Economics, or decision state is unresolved, blocked, failed, or absent
- **THEN** the Executive Summary exposes that material state rather than implying successful completion

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
The report SHALL use resolved post-Red-Team Risk and Unit Economics results and the existing final `DecisionResult.label` exactly when available. It SHALL preserve relevant before-and-after history when accepted Red Team revisions changed Risk or Unit Economics. Risk revision presentation SHALL expose at minimum the authoritative Risk Gate before and after. Unit Economics revision presentation SHALL expose the authoritative Economics outcome before and after and the Minimum Viability Gate and Dynamic Target Gate transitions where applicable. These transitions MUST NOT rely on rendering the complete Risk or Unit Economics result-object representation. The report MUST NOT recompute either Gate, reinterpret Gate precedence or decision reasons, infer a new classification or economics outcome, promote or downgrade a label, or fabricate a fallback commercial label.

#### Scenario: Accepted Gate revisions are visible
- **WHEN** an accepted Red Team revision changed Risk or Unit Economics
- **THEN** the final presentation uses the resolved result and retains the relevant authoritative before-and-after change

#### Scenario: Final label is copied exactly
- **WHEN** an authoritative final decision exists
- **THEN** Final Analysis Label equals its label exactly and its reasons are not reinterpreted

#### Scenario: Absent final decision stays unresolved
- **WHEN** no authoritative final decision exists
- **THEN** Final Analysis Label explicitly reports unavailable or unresolved state and does not create a fallback label

#### Scenario: Risk revision presents the Gate transition
- **WHEN** an accepted Risk revision is rendered
- **THEN** the report presents its Risk Gate before and after without serializing the complete Risk result objects

#### Scenario: Unit Economics revision presents closed-state transitions
- **WHEN** an accepted Unit Economics revision is rendered
- **THEN** the report presents its Economics outcome and applicable Minimum Viability and Dynamic Target Gate transitions without serializing the complete Unit Economics result objects

### Requirement: Red Team presentation preserves accepted history only
The Red Team Findings section SHALL project existing accepted findings and accepted revisions, including score, Risk, and Unit Economics changes where present. Each accepted revision SHALL retain its authoritative initial value, revised value, reason, and causal Evidence IDs. Score revisions SHALL present the dimension, score before and after, and Confidence before and after when available. Risk revisions SHALL present the Risk Gate transition, and Unit Economics revisions SHALL present the authoritative outcome and applicable Gate transitions. Reporting MUST NOT render complete Risk or Unit Economics result-object representations as the transition, build a generic object-diff mechanism, generate new objections, reinterpret rejected or absent proposals, re-evaluate proposal validity, infer causal Evidence, or rerun Red Team reasoning.

#### Scenario: Accepted revision retains provenance
- **WHEN** the workflow contains an accepted revision
- **THEN** the report preserves its before value, after value, reason, and causal Evidence IDs

#### Scenario: Rejected proposal is not reinterpreted
- **WHEN** a Red Team proposal was rejected or no revision was accepted
- **THEN** reporting does not convert it into an accepted finding or derive an alternative revision

#### Scenario: Score revision preserves score and Confidence transition
- **WHEN** an accepted score revision is rendered
- **THEN** the report presents its dimension, score before and after, available Confidence before and after, reason, and causal Evidence IDs

#### Scenario: Gate revisions avoid full-object dumps
- **WHEN** accepted Risk or Unit Economics revisions are rendered
- **THEN** the report presents only the required authoritative closed-state transitions with their reasons and causal Evidence IDs rather than complete result-object representations

### Requirement: Key Uncertainties uses explicit structured state only
Key Uncertainties SHALL project only explicit existing `UNRESOLVED`, `BLOCKED`, or `FAILED` workflow state; missing, unknown, or unresolved domain state; existing diagnostics, factors, or reasons; unresolved score dimensions or core thresholds; and unresolved Risk or Unit Economics state. It SHALL preserve canonical structural ordering and authoritative closed values while using explicit fixed reader-facing labels for known fields instead of report-internal `snake_case` names. It MUST NOT dynamically humanize arbitrary attributes, invent hypothetical weaknesses, select only purportedly important uncertainties, or introduce a generic severity-ranking model.

#### Scenario: Explicit uncertainty is retained
- **WHEN** an authoritative workflow or domain artifact records uncertainty or failure
- **THEN** Key Uncertainties presents that state and its existing reason or effect without inventing a new weakness

#### Scenario: Cross-domain uncertainty is not severity-ranked
- **WHEN** multiple uncertainty categories have no shared authoritative severity vocabulary
- **THEN** they appear in deterministic structural order without claims that one is objectively more severe

#### Scenario: Uncertainty fields use fixed reader-facing labels
- **WHEN** Key Uncertainties renders a known missing, unknown, unresolved, diagnostic, factor, or reason field
- **THEN** it uses the field's stable reader-facing label and preserves the authoritative value without exposing the internal field name
