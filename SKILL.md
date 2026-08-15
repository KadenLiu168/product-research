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

## Reference Routing

Read each reference before performing its stage:

| Stage | Required reference |
|---|---|
| Research planning and dimension analysis | [references/methodology.md](references/methodology.md) |
| Evidence collection, status, freshness, and confidence | [references/evidence-policy.md](references/evidence-policy.md) |
| Evidence representation and Evidence ID boundary | [product_research/evidence.py](product_research/evidence.py) |
| Multi-source consistency, source independence, conflict preservation, missing information, and claim-level Confidence | [product_research/evidence_assessment.py](product_research/evidence_assessment.py) |
| Eight-dimension scoring and thresholds | [references/scoring-policy.md](references/scoring-policy.md) |
| Risk and Unit Economics gates | [references/gates.md](references/gates.md) |
| Final output | [references/report-contract.md](references/report-contract.md) |

For a full evaluation, read all five references and the shared Evidence representation when creating or exchanging Evidence records, and the Evidence assessment boundary before combining multiple sources into a claim-level Confidence. For a narrower follow-up, read every reference governing the requested stage and any upstream evidence or gate rules it depends on.

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
12. Score the eight dimensions.
13. Check core-dimension thresholds.
14. Run Red Team Review.
15. Revise scores when warranted by evidence.
16. Generate final report and Evidence Appendix.

Do not skip an earlier stage merely because a later-stage answer appears intuitive. If evidence is insufficient for a stage, record the uncertainty and its downstream effect instead of inventing completion.

## Unimplemented Capabilities

This phase provides orchestration, the shared structural Evidence representation, deterministic Evidence Policy validation, and deterministic Evidence Assessment with explicit per-record stances, independence groups, missing information, conflict preservation, and claim-level Confidence ceilings. Research adapters, marketplace or supplier scrapers, evidence persistence, scoring/calculation engines, VOC clustering, risk scanning, Red Team automation, and report-generation code do not exist yet.

Use only tools actually available in the current environment. Never claim to have accessed a source, collected data, run a calculation, or completed a workflow stage when that capability was unavailable. In that case:

1. State the capability gap.
2. Preserve missing values as `Unknown` unless existing evidence supports a bounded `Estimated` value.
3. Describe the evidence or deterministic calculation still required.
4. Withhold unsupported scores and unqualified `GO` conclusions.
