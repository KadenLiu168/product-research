## Purpose

Defines a deterministic downstream presentation capability that projects the authoritative structured end-to-end workflow result into one human-readable, evidence-traceable final research report without introducing new analytical semantics.

## ADDED Requirements

### Requirement: Reporting is a downstream presentation boundary
The capability SHALL accept an existing well-formed `EndToEndWorkflowResult` as its sole research-state input and SHALL project only values already present in that result or presentation-only values explicitly permitted by this specification. It MUST NOT acquire Evidence, call providers or external services, rerun workflow stages, interpret Evidence text, generate qualitative judgments, recalculate Unit Economics, execute Risk Gate, scoring, core-threshold, Red Team, or decision policy, or create another authoritative domain model. The workflow coordinator and lower-level capabilities MUST NOT depend on final-report generation or absorb report rendering.

#### Scenario: Complete result is projected without upstream execution
- **WHEN** a complete workflow result is submitted for reporting
- **THEN** the report is produced from its retained authoritative state without invoking research, analysis, scoring, Gate, Red Team, or decision execution

#### Scenario: Dependency direction remains one way
- **WHEN** the reporting capability is integrated
- **THEN** dependencies flow from existing domain capabilities through the end-to-end workflow to reporting, with no reporting dependency in the coordinator or lower-level modules

### Requirement: Report uses one canonical section structure
The report SHALL contain exactly these canonical sections in this order: Executive Summary; Market Demand; Competition; Price & Profitability; VOC & Differentiation; Supply Chain & Fulfillment; Brand Potential; Content Potential; Risk & Compliance; Scorecard; Key Evidence; Key Uncertainties; Red Team Findings; Final Analysis Label; and Evidence Appendix. Repository Skill, reference, methodology, and broader documentation SHALL describe this same runtime structure and MUST NOT retain a competing canonical runtime layout.

#### Scenario: Complete report contains all canonical sections
- **WHEN** a complete workflow result is rendered
- **THEN** all 15 canonical sections appear exactly once in canonical order

#### Scenario: Incomplete report retains the canonical structure
- **WHEN** a well-formed workflow result contains unresolved, blocked, failed, or unavailable stages
- **THEN** the same 15 canonical sections remain present and expose unavailable content explicitly rather than omitting the contractual section

### Requirement: Analytical dimension sections preserve authoritative findings
The eight analytical sections SHALL correspond exactly, and in canonical order, to Market Demand, Competition, Price & Profitability, VOC & Differentiation, Supply Chain & Fulfillment, Brand Potential, Content Potential, and Risk & Compliance. Each section SHALL organize only the authoritative state available for its dimension, including existing outcomes or conclusions, Confidence, supporting and adverse Evidence IDs, missing or unknown state, diagnostics, factors, coverage, and retained domain findings where those values exist. Presentation MUST NOT semantically reinterpret Evidence or derive a replacement conclusion.

#### Scenario: Available dimension state is preserved
- **WHEN** a dimension has authoritative findings, Confidence, Evidence lineage, diagnostics, factors, or coverage state
- **THEN** its section preserves those values without rewriting their business meaning

#### Scenario: Missing dimension state remains unavailable
- **WHEN** a dimension has no authoritative analysis or score
- **THEN** its section marks the missing or unresolved state explicitly and does not substitute zero, neutral, or inferred content

### Requirement: Scorecard projects the final authoritative score state
The Scorecard SHALL contain exactly the eight canonical dimensions in canonical order and SHALL use the final post-Red-Team `DimensionScores` when available rather than initial scores. For each dimension it SHALL preserve the authoritative score or absence, base weight, final weight when available, per-dimension Confidence, and supporting Evidence IDs. It SHALL project final-decision core-threshold results, failed and unresolved core dimensions, and the authoritative aggregate score directly when available. The reporting capability MUST NOT independently recompute an available aggregate or execute scoring-decision policy.

#### Scenario: Revised scores and final weights win
- **WHEN** accepted Red Team revisions changed a dimension and the final decision contains weights
- **THEN** the Scorecard uses the revised final score and the final decision's authoritative weights while retaining the dimension's Confidence and Evidence IDs

#### Scenario: Aggregate and thresholds are projected directly
- **WHEN** the final decision contains an aggregate and core-threshold results
- **THEN** the report presents those exact values and outcomes without recalculating them

#### Scenario: Missing score is not converted to zero
- **WHEN** a final dimension score is unresolved or no final score state exists
- **THEN** the corresponding report value remains explicitly unavailable and no numeric fallback is rendered

### Requirement: Weighted contributions are presentation-only and Decimal-exact
If the Scorecard includes a per-dimension weighted contribution that is not stored upstream, the value SHALL be derived solely from that dimension's authoritative final score and final weight using the repository's exact `Decimal` semantics. The derived contributions SHALL remain presentation-only, SHALL NOT mutate or replace authoritative scoring state, and SHALL be checked for consistency with the authoritative aggregate when that aggregate exists.

#### Scenario: Weighted contribution follows authoritative inputs
- **WHEN** a final score and final weight are both available for a dimension
- **THEN** any displayed weighted contribution uses only those two values with exact deterministic `Decimal` arithmetic

#### Scenario: Derived contributions cannot create an aggregate
- **WHEN** the authoritative aggregate is unavailable
- **THEN** presentation-derived contributions do not manufacture a replacement aggregate or decision input

#### Scenario: Inconsistent authoritative aggregate fails closed
- **WHEN** presentation-derived contributions cannot be reconciled with an available authoritative aggregate under the repository's scoring semantics
- **THEN** reporting exposes a deterministic input inconsistency rather than silently publishing a competing aggregate

### Requirement: Executive Summary projects material final-state facts
The Executive Summary SHALL concisely present the known candidate product, target market, authoritative final analytical label, authoritative aggregate score, final Risk state, final Unit Economics state, failed or unresolved core dimensions, material unresolved workflow state, key decision Evidence references, and material accepted Red Team changes when each is available. It MUST NOT hide material adverse or unresolved state for brevity and MUST NOT invent an overall-report Confidence, strongest-Evidence claim, unsupported recommendation, generic severity order, or autonomous commercial decision.

#### Scenario: Complete summary uses authoritative facts
- **WHEN** the final workflow result contains the listed authoritative facts
- **THEN** the Executive Summary presents them without deriving a second recommendation or confidence value

#### Scenario: Material incompleteness remains prominent
- **WHEN** workflow, core-threshold, Risk, Economics, or decision state is unresolved, blocked, failed, or absent
- **THEN** the Executive Summary exposes that material state rather than implying successful completion

### Requirement: Risk, Unit Economics, and Final Analysis Label remain authoritative
The report SHALL use resolved post-Red-Team Risk and Unit Economics results and the existing final `DecisionResult.label` exactly when available. It SHALL preserve relevant before-and-after history when accepted Red Team revisions changed Risk or Unit Economics. It MUST NOT recompute either Gate, reinterpret Gate precedence or decision reasons, infer a new classification or economics outcome, promote or downgrade a label, or fabricate a fallback commercial label.

#### Scenario: Accepted Gate revisions are visible
- **WHEN** an accepted Red Team revision changed Risk or Unit Economics
- **THEN** the final presentation uses the resolved result and retains the relevant authoritative before-and-after change

#### Scenario: Final label is copied exactly
- **WHEN** an authoritative final decision exists
- **THEN** Final Analysis Label equals its label exactly and its reasons are not reinterpreted

#### Scenario: Absent final decision stays unresolved
- **WHEN** no authoritative final decision exists
- **THEN** Final Analysis Label explicitly reports unavailable or unresolved state and does not create a fallback label

### Requirement: Red Team presentation preserves accepted history only
The Red Team Findings section SHALL project existing accepted findings and accepted revisions, including score, Risk, and Unit Economics changes where present. Each accepted revision SHALL retain its authoritative initial value, revised value, reason, and causal Evidence IDs. Reporting MUST NOT generate new objections, reinterpret rejected or absent proposals, re-evaluate proposal validity, infer causal Evidence, or rerun Red Team reasoning.

#### Scenario: Accepted revision retains provenance
- **WHEN** the workflow contains an accepted revision
- **THEN** the report preserves its before value, after value, reason, and causal Evidence IDs

#### Scenario: Rejected proposal is not reinterpreted
- **WHEN** a Red Team proposal was rejected or no revision was accepted
- **THEN** reporting does not convert it into an accepted finding or derive an alternative revision

### Requirement: Key Evidence is deterministic and non-ranked
Key Evidence SHALL contain Evidence records or IDs already materially referenced by authoritative final-state artifacts, including final scores, final Risk state, final Unit Economics state, material analysis findings, accepted Red Team revisions, or the final decision. It SHALL use explicit deterministic structural and Evidence-ID ordering and MUST NOT assign an Evidence-strength score, claim an objective strongest record, or introduce another Evidence-ranking policy.

#### Scenario: Material references select Key Evidence
- **WHEN** authoritative final-state artifacts reference current-run Evidence IDs
- **THEN** Key Evidence presents the referenced records deterministically without ranking them by unsupported strength

#### Scenario: Unreferenced Evidence remains in the appendix only
- **WHEN** a current-run Evidence record is not materially referenced by an authoritative final-state artifact
- **THEN** it remains present in the complete Evidence Appendix but is not promoted through a newly invented importance rule

### Requirement: Key Uncertainties uses explicit structured state only
Key Uncertainties SHALL project only explicit existing `UNRESOLVED`, `BLOCKED`, or `FAILED` workflow state; missing, unknown, or unresolved domain state; existing diagnostics, factors, or reasons; unresolved score dimensions or core thresholds; and unresolved Risk or Unit Economics state. It SHALL use deterministic structural ordering when no authoritative cross-domain priority exists and MUST NOT invent hypothetical weaknesses or a generic severity-ranking model.

#### Scenario: Explicit uncertainty is retained
- **WHEN** an authoritative workflow or domain artifact records uncertainty or failure
- **THEN** Key Uncertainties presents that state and its existing reason or effect without inventing a new weakness

#### Scenario: Cross-domain uncertainty is not severity-ranked
- **WHEN** multiple uncertainty categories have no shared authoritative severity vocabulary
- **THEN** they appear in deterministic structural order without claims that one is objectively more severe

### Requirement: Evidence references remain within the current workflow universe
Every Evidence reference in the report SHALL resolve to an actual normalized Stage 3 `Evidence` record retained by the current workflow. Traceability MAY follow existing authoritative lineage through decisions, scores, Gates, analysis results, or Red Team revisions and MUST NOT require report-specific Evidence IDs on every derived value. Reporting MUST reject or expose dangling, foreign-run, duplicate, or otherwise invalid report references rather than allocating, renumbering, cloning, or fabricating Evidence IDs.

#### Scenario: Indirect decision lineage remains valid
- **WHEN** a final label is traceable through its authoritative decision inputs to current-run Evidence
- **THEN** the report preserves that lineage without adding report-specific citations to the label

#### Scenario: Dangling Evidence reference fails closed
- **WHEN** an artifact selected for reporting references an Evidence ID outside the current workflow Evidence universe
- **THEN** reporting exposes a deterministic traceability failure and does not fabricate an appendix record

### Requirement: Evidence Appendix is complete and lossless
The Evidence Appendix SHALL contain exactly one entry for every actual normalized Stage 3 `Evidence` record retained by the workflow and no other records. Entries SHALL use stable Evidence-ID ordering and preserve each record's Evidence ID, claim, evidence text or value, source, observed date/time, tier, status, and Confidence without rewriting content or provenance. Adverse Evidence MUST NOT be silently omitted.

#### Scenario: Complete Evidence universe appears exactly once
- **WHEN** a workflow result retains normalized Evidence records
- **THEN** the appendix contains every record exactly once in stable Evidence-ID order

#### Scenario: Evidence content is preserved
- **WHEN** an appendix entry is rendered
- **THEN** all required fields match the authoritative normalized Evidence record without renumbering, cloning, or semantic rewriting

#### Scenario: Empty Evidence universe is explicit
- **WHEN** Stage 3 retains no normalized Evidence
- **THEN** the appendix explicitly represents the empty authoritative universe and does not create placeholder Evidence records

### Requirement: Incomplete workflow results are reportable and fail closed
Every well-formed `EndToEndWorkflowResult` SHALL remain reportable across `COMPLETE`, `UNRESOLVED`, `BLOCKED`, and `FAILED` stage states, including partial research, unresolved analysis, blocked downstream stages, failed control-plane stages, missing scores, unresolved core thresholds, and absent final decisions. The report SHALL render known authoritative state and explicit status or reasons, mark or omit unavailable values according to the canonical contract, and MUST NOT turn absence into zero, successful completion, a positive conclusion, or any fabricated state.

#### Scenario: Unresolved state remains explicit
- **WHEN** one or more stages are `UNRESOLVED`
- **THEN** the report identifies the unresolved stages and preserves all known upstream state without claiming completion

#### Scenario: Blocked state remains explicit
- **WHEN** one or more stages are `BLOCKED`
- **THEN** the report identifies the blocked stages and their retained reasons without filling dependent values

#### Scenario: Failed state remains explicit
- **WHEN** one or more stages are `FAILED`
- **THEN** the report identifies the failed stages and retained failure state without silently degrading them to unresolved or successful state

### Requirement: Report generation is deterministic and side-effect free
Equivalent structured workflow inputs SHALL produce byte-for-byte equivalent report output. Report generation MUST NOT depend on network access, external services, system time, randomness, persistence, environment-derived policy, mutable global state, hidden LLM calls, or asynchronous behavior. All presentation ordering and textual markers SHALL be fixed by the report contract.

#### Scenario: Equivalent inputs produce equivalent output
- **WHEN** equivalent workflow results are rendered more than once
- **THEN** the resulting reports are byte-for-byte identical

#### Scenario: Rendering requires no external or mutable input
- **WHEN** a report is generated
- **THEN** no network, provider, clock, randomness, persistence, environment policy, LLM, or asynchronous facility is consulted

### Requirement: Documentation and tests align to the implemented boundary
Implementation SHALL update the report contract, Skill routing and availability statements, methodology, broader Skill documentation, focused contract-style unit tests, and relevant Agent RED/GREEN scenarios so they describe and verify one consistent reporting boundary. The change MUST NOT implement ECO-39 evaluation-suite infrastructure.

#### Scenario: Documentation declares reporting available once implemented
- **WHEN** ECO-38 implementation is complete
- **THEN** repository documentation routes final-report requests to the implemented capability and no longer describes human-readable reporting or Evidence Appendix rendering as unavailable

#### Scenario: Test coverage remains scoped to ECO-38
- **WHEN** ECO-38 tests and Agent scenarios are added
- **THEN** they verify reporting contracts and boundaries without adding the ECO-39 evaluation suite
