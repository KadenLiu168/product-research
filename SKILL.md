---
name: product-research
description: Use when researching or evaluating a specific candidate product for cross-border e-commerce viability, including market demand, competition, profitability, differentiation, supply chain, consumer needs, or compliance.
---

# Product Research

Evaluate a candidate product supplied by the user. Do not use this version to discover candidate products automatically.

## Core Rules

- If the user does not name a target market, set `target_market = United States`. An explicit user market overrides this default.
- **Research before conclusions.** Every material factual claim must trace to evidence.
- Classify important data as exactly one of `Observed`, `Estimated`, `Calculated`, or `Unknown`. Never present `Estimated` as `Observed`.
- Missing evidence must not be converted into assumed facts. Research it, use a bounded evidence-supported `Estimated` value, or mark it `Unknown`.
- When reliable sources conflict, surface the conflict, compare quality and freshness, and reduce confidence when unresolved. Do not hide adverse evidence.
- Run `Risk Gate` and `Unit Economics Gate` independently of the weighted score. Aggregate scoring cannot override a fatal risk or failed economics gate.
- After Phase 6 results and Unit Economics are available, the Agent/caller may submit explicit qualitative judgments to `product_research/initial_scoring.py`; it validates ownership, Evidence-ID traceability, nested uncertainty, and Confidence ceilings, then emits the existing eight-slot `DimensionScores`. It does not generate or infer qualitative judgments.
- `product_research/initial_scoring.py` maps retained Contribution Margin relative to the caller-owned Minimum Viability and Dynamic Target thresholds using its frozen Decimal rubric; it does not recalculate economics or rerun either gate.
- When normalized scores, explicit adjustments, upstream gate results, and an explicit GO threshold are available, route deterministic scoring and analytical decision execution to `product_research/scoring_decision.py`; it does not generate scores or policy inputs.
- After Initial Scoring, the Agent/caller owns adversarial reasoning and any upstream re-evaluation. Pass only explicit canonical findings, per-dimension proposals, and complete revised Risk or Unit Economics results to `product_research/red_team_revision.py`; it authorizes traceable changes and preserves history but does not generate objections, interpret Evidence, rerun analysis, calculate economics, or choose a final decision.
- For full deterministic execution with explicit normalized inputs, route the fixed 16-stage composition through `product_research/end_to_end_workflow.py`; it retains the existing authoritative values and cumulative stage trace, but does not generate judgments, acquire Evidence, change policy, or render reports.
- After Stage 16, route the immutable `EndToEndWorkflowResult` to `product_research/final_report_generation.py` for the canonical 15-section Markdown report and complete Evidence Appendix. This downstream boundary only projects retained authoritative values and does not execute upstream policy.

## Reference Routing

Read each reference before performing its stage:

| Stage | Required reference |
|---|---|
| Research planning and dimension analysis | [references/methodology.md](references/methodology.md) |
| Ordered research planning, injected acquisition, raw-finding normalization, and run coverage/status | [product_research/research_orchestration.py](product_research/research_orchestration.py) |
| Fixed five-family acquisition composition | [product_research/research_adapters.py](product_research/research_adapters.py) |
| Evidence collection, status, freshness, and confidence | [references/evidence-policy.md](references/evidence-policy.md) |
| Evidence representation and Evidence ID boundary | [product_research/evidence.py](product_research/evidence.py) |
| Multi-source consistency, source independence, conflict preservation, missing information, and claim-level Confidence | [product_research/evidence_assessment.py](product_research/evidence_assessment.py) |
| Explicit Market Demand interpretation from existing Evidence | [product_research/market_demand.py](product_research/market_demand.py) |
| Explicit Competition sample coverage and independently assessed findings from existing Evidence | [product_research/competition.py](product_research/competition.py) |
| Explicit VOC propositions, independently assessed findings, category coverage, and Complaint axes from existing Evidence | [product_research/voc.py](product_research/voc.py) |
| Explicit Supply Chain propositions, independently assessed findings, eight-dimension coverage, and traceability from existing Evidence | [product_research/supply_chain.py](product_research/supply_chain.py) |
| Explicit Brand / Content propositions, independently assessed findings, five-aspect coverage, and traceability from existing Evidence | [product_research/brand_content.py](product_research/brand_content.py) |
| Explicit Risk & Compliance propositions, evidence-grounded findings, caller-owned required-area coverage, and the decision-facing Risk Gate state from existing Evidence | [product_research/risk_compliance.py](product_research/risk_compliance.py) |
| Deterministic Unit Economics calculation and gate execution | [product_research/unit_economics.py](product_research/unit_economics.py) |
| Evidence-grounded initial score normalization | [product_research/initial_scoring.py](product_research/initial_scoring.py) |
| Normalized eight-dimension scoring, thresholds, and analytical decisions | [product_research/scoring_decision.py](product_research/scoring_decision.py) and [references/scoring-policy.md](references/scoring-policy.md) |
| Red Team revision authorization and immutable before/after history | [product_research/red_team_revision.py](product_research/red_team_revision.py) |
| Fixed 16-stage deterministic composition and structured Final Result | [product_research/end_to_end_workflow.py](product_research/end_to_end_workflow.py) |
| Risk and Unit Economics gates | [references/gates.md](references/gates.md) |
| Downstream human-readable report and Evidence Appendix contract | [references/report-contract.md](references/report-contract.md) |

For a full evaluation, read all five references and the shared Evidence representation when creating or exchanging Evidence records, and the Evidence assessment boundary before combining multiple sources into a claim-level Confidence. For a narrower follow-up, read every reference governing the requested stage and any upstream evidence or gate rules it depends on.

## Configured DataForSEO Acquisition Runtime

The external `dataforseo_acquisition_runtime.py` module composes the existing
DataForSEO providers into the existing `ResearchSourceAdapters` value. Callers
supply explicit existing `ProviderBinding` values and one validated shared
`DataForSEOConfiguration`; the runtime resolves bindings by exact `task_id`
and does not infer operations from `research_question` or `query_intent`.

The configured runtime can install the existing SEARCH family (Google Ads
Search Volume, Google Trends Explore, and Amazon Bulk Search Volume) and the
existing MARKETPLACE family (Amazon Products) together or independently.
Intentionally absent or unsupported families remain unavailable. The runtime
stops at existing `AcquisitionResult` and ordered `RawFinding` values; it does
not normalize findings into Evidence, which remains the ECO-45 boundary, and
it does not execute the complete workflow or perform live research by itself.

## Workflow

Follow this order:

1. Normalize candidate product and target market.
2. Define research questions.
3. Collect and normalize evidence.
4. Run Risk Gate.
5. Build Unit Economics.
6. Analyze Market Demand.
7. Analyze Competition Structure.
8. Analyze VOC and Differentiation.
9. Analyze Supply Chain and Fulfillment.
10. Evaluate Brand Potential.
11. Evaluate Content Potential.
12. Produce explicit Agent/caller qualitative judgments where relevant Evidence supports them, then pass Phase 6 results, Unit Economics, and those judgments through Initial Scoring.
13. Check core-dimension thresholds.
14. Accept explicit current-run Evidence-backed Red Team review inputs.
15. Apply accepted Red Team revisions through the existing revision boundary.
16. Resolve authoritative post-Red-Team state and run the final scoring decision.

Do not skip an earlier stage merely because a later-stage answer appears intuitive. If evidence is insufficient for a stage, record the uncertainty and its downstream effect instead of inventing completion.

Stage 16 returns the immutable structured Final Result: the ordered stage trace, Evidence traceability, analysis and Gate history, initial and revised scores, Red Team history, and initial/final decisions. It does not render prose. The downstream `product_research.final_report_generation` boundary renders the canonical 15-section human-readable report and lossless Evidence Appendix without rerunning any upstream stage.

## Unimplemented Capabilities

This phase provides the shared structural Evidence representation, deterministic Evidence Policy validation, deterministic Evidence Assessment with explicit per-record stances, independence groups, missing information, conflict preservation, and claim-level Confidence ceilings, explicit read-only Market Demand, Competition, VOC, Supply Chain, Brand / Content, and Risk & Compliance interpretations from existing Evidence, deterministic Unit Economics calculation from explicit normalized inputs with caller-supplied thresholds and fail-closed gate results, evidence-grounded Initial Scoring from explicit Agent/caller judgments and retained Unit Economics values, deterministic scoring/analytical decision execution from explicit normalized inputs, the fixed 16-stage coordinator in `product_research/end_to_end_workflow.py`, the downstream deterministic report boundary in `product_research/final_report_generation.py`, a narrow Red Team revision authorization/history boundary, a source-agnostic orchestration boundary for injected research planning, acquisition, and Evidence normalization, and a fixed five-family adapter composition in `product_research/research_adapters.py`. The VOC, Supply Chain, Brand / Content, Risk & Compliance, Red Team, workflow, and report boundaries accept only caller-declared normalized values and do not infer meaning from Evidence. `RawFinding` is an acquisition-only, non-durable value; existing `Evidence` remains the sole normalized contract, and configured family adapters stop at `AcquisitionResult` / `RawFinding`. Configured DataForSEO SEARCH acquisition is available for the three declared Live operations: Google Ads Search Volume, Google Trends Explore, and Amazon Bulk Search Volume; configured Amazon Products MARKETPLACE acquisition is also available through the concrete DataForSEO provider. Other concrete provider-backed adapters, marketplace or supplier scrapers, provider-backed regulation, patent, or trademark search, automatic risk scanning, automatic qualitative judgment generation, automatic weight selection, automatic VOC clustering, automatic Red Team objection generation, persistence, and the full provider-backed workflow remain unavailable. Neither boundary performs external research by itself.

Use only tools actually available in the current environment. Never claim to have accessed a source, collected data, run a calculation, or completed a workflow stage when that capability was unavailable. In that case:

1. State the capability gap.
2. Preserve missing values as `Unknown` unless existing evidence supports a bounded `Estimated` value.
3. Describe the evidence or deterministic calculation still required.
4. Withhold unsupported scores and unqualified `GO` conclusions.
