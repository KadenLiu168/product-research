# Final Report Contract

This is the downstream ECO-38 runtime contract. Its input is one immutable
`EndToEndWorkflowResult` from `product_research/end_to_end_workflow.py` and its
output is deterministic human-readable Markdown. The ECO-37 coordinator and
all lower-level modules remain report-free.

## Canonical Structure

The report contains exactly these sections, in this order, once each:

1. Executive Summary
2. Market Demand
3. Competition
4. Price & Profitability
5. VOC & Differentiation
6. Supply Chain & Fulfillment
7. Brand Potential
8. Content Potential
9. Risk & Compliance
10. Scorecard
11. Key Evidence
12. Key Uncertainties
13. Red Team Findings
14. Final Analysis Label
15. Evidence Appendix

`UNAVAILABLE` is the stable marker for a value that is absent from the
authoritative workflow result. A missing value is never rendered as zero,
neutral, complete, or positive.

## Authoritative State

When Stage 16 contains `WorkflowFinalState`, the report uses its scores, Risk,
Unit Economics, final weights, aggregate, core-threshold results, and
`DecisionResult` label and reasons exactly. Stage 13's initial decision never
substitutes for the final decision.

When Stage 16 is unavailable, accepted Stage 15 revisions are rendered as
`LATEST-KNOWN`; otherwise available Stage 12/4/5 values are rendered as
`INITIAL`. Latest-known and initial values are explicitly not final: final
weights, aggregate, core results, and Final Analysis Label remain
`UNAVAILABLE` without Stage 16.

## Executive Summary and Presentation Labels

The Executive Summary retains the candidate, target market, state source,
final label, aggregate, Risk, Unit Economics, core state, accepted Red Team
state, and Key Decision `Evidence IDs` when authoritative. When every stage is
complete it emits one `Workflow Status: COMPLETE` line. Otherwise it emits
only the non-complete `UNRESOLVED`, `BLOCKED`, and `FAILED` stage records in canonical order,
including retained failure kinds and `blocked_by` dependencies.

Analytical sections use explicit fixed reader-facing labels for the supported
field registry. They never expose internal `snake_case` names, reflect over
arbitrary attributes, or dynamically humanize fields. A missing value remains
`UNAVAILABLE`.

## Analytical Sections and Scorecard

The eight analytical sections preserve the retained domain result fields,
including outcomes, Confidence, findings, diagnostics, factors, coverage,
missing or unknown state, supporting Evidence IDs, adverse Evidence IDs, and
excluded Evidence IDs. Each retained finding is rendered once as a compact,
ordered field group containing every applicable proposition or text, outcome,
dimension/category/area/aspect, Confidence, lineage, factors, diagnostics, and
Evidence IDs. Values remain authoritative and in input order; presentation
does not rank, summarize, or reinterpret them. Evidence text is not
interpreted by presentation.

The Scorecard contains exactly the eight canonical dimensions in canonical
order. It renders the authoritative score or `UNAVAILABLE`, base and final
weights, per-dimension Confidence, and supporting Evidence IDs. Core-threshold
results, failed or unresolved core dimensions, and the authoritative aggregate
are copied from Stage 16 when available.

The only permitted numeric presentation derivation is:

```text
weighted contribution = score * final weight / Decimal("100")
```

It uses the repository's 34-digit `ROUND_HALF_EVEN` Decimal context, never
mutates or replaces authoritative state, and never creates an aggregate or
decision. When all contributions and an authoritative aggregate exist, their
Decimal sum must equal that aggregate; otherwise reporting raises a
deterministic input-consistency error.

## Gates, Label, and Red Team History

Final Risk, Unit Economics, and Final Analysis Label are copied from the
authoritative post-Red-Team objects. Accepted score, Risk, and Unit Economics
revisions retain their before value, after value, reason, and causal Evidence
IDs through type-specific transitions. Score transitions contain dimension,
score and available Confidence transitions; Risk transitions contain the Risk
Gate before and after as the authoritative Risk Gate transition; Unit Economics transitions contain outcome, Minimum Viability Gate, and Dynamic Target Gate before and after. Complete Risk and
Unit Economics objects are not serialized as revision output. Rejected or
absent proposals are not reinterpreted.

The Executive Summary exposes subject, final-state facts, gate state, core
state, material workflow incompleteness, key decision Evidence IDs, and
accepted revisions. It does not create a recommendation, an overall-report
Confidence, an Evidence-strength ranking, or a cross-domain severity order.

## Key Evidence and Key Uncertainties

Key Evidence is a deterministic membership projection of current-run Evidence
IDs materially referenced by authoritative scores, Risk, Unit Economics,
domain findings, accepted Red Team history, or the final decision. The union is
deduplicated and rendered in Evidence-ID order; membership is not a rank.
Unreferenced current-run records remain in the Appendix.

Key Uncertainties contains only explicit workflow `UNRESOLVED`, `BLOCKED`, or
`FAILED` state, missing or unknown domain state, existing diagnostics/factors/
reasons, unresolved scores or core thresholds, and unresolved Risk or Unit
Economics state. Known fields use the same fixed reader-facing labels as the
analytical projection. Entries use canonical structural order and are not
compared using an invented severity model.

## Evidence Appendix and Traceability

Every Evidence reference selected for presentation must resolve inside the
current run's normalized Stage 3 Evidence universe. Dangling or foreign-run
IDs fail closed; reporting does not drop, renumber, clone, or fabricate them.

The Appendix contains exactly one entry for every normalized Stage 3 `Evidence`
record, in Evidence-ID order, and no other entries. It preserves ID, claim,
Evidence content, source, observed timestamp, tier, status, and Confidence.
Markdown/control-character escaping is deterministic and lossless with respect
to those values. An empty Evidence universe is rendered explicitly.

## Incomplete and Side-Effect-Free Rendering

Well-formed results remain reportable for `COMPLETE`, `UNRESOLVED`, `BLOCKED`,
and `FAILED` stage states. Stage statuses and retained failure or blocking
reasons remain visible; absence never becomes a successful conclusion. The
complete Evidence Appendix remains lossless and contains every normalized
Stage 3 record exactly once, including adverse Evidence.

Equivalent structured inputs produce byte-identical output. Rendering performs
no provider or network access, clock or randomness reads, persistence, LLM or
asynchronous work, upstream policy execution, or report-specific Evidence
acquisition. It is a one-way presentation boundary downstream of the
structured workflow.
