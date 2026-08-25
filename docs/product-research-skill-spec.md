# Product Research Skill Specification

## 1. Purpose

This Skill evaluates whether a candidate product is suitable for cross-border e-commerce.

The Skill does **not** discover products automatically in v1. Its responsibility is to evaluate a product provided by the user using current public evidence, structured analysis, deterministic scoring, and explicit uncertainty handling.

Default target market:

```text
United States
```

The Skill is platform-agnostic in v1. It does not optimize specifically for Amazon, Shopify, TikTok Shop, Etsy, or another sales channel.

The core principle is:

> No evidence, no conclusion.

This document describes the broader v1 target workflow. Current deterministic boundaries include the source-agnostic `product_research/research_orchestration.py` control plane for explicit plans, injected acquisition, raw-finding normalization, and execution coverage, the fixed five-family `product_research/research_adapters.py` composition for configured acquisition callables, the external configured DataForSEO runtime composition, the explicit read-only Phase 6 boundaries for caller-declared inputs over existing Evidence, the evidence-grounded `product_research/initial_scoring.py` bridge for explicit Agent/caller judgments and retained Unit Economics values, the narrow `product_research/red_team_revision.py` boundary for explicit current-run authorization and immutable revision history, the explicit normalized-input scoring boundary in `product_research/scoring_decision.py`, the thin deterministic 16-stage coordinator in `product_research/end_to_end_workflow.py`, and the downstream deterministic 15-section report boundary in `product_research/final_report_generation.py`. `RawFinding` is non-durable, existing `Evidence` is the sole normalized contract, and family composition stops at the acquisition-result/raw-finding boundary. Other provider-backed research acquisition, automatic qualitative judgment generation or objection generation, and Agent reasoning remain unavailable.

The configured DataForSEO runtime is the external `dataforseo_acquisition_runtime.py` boundary. It accepts explicit existing `ProviderBinding` values, reuses one validated `DataForSEOConfiguration`, and returns `ResearchSourceAdapters` directly. It can install the existing SEARCH family (Google Ads Search Volume, Google Trends Explore, and Amazon Bulk Search Volume) and the existing MARKETPLACE family (Amazon Products) together or independently; intentionally absent or unsupported families remain unavailable. Binding lookup is exact by `task_id`, not derived from free-form task text. The runtime stops at existing `AcquisitionResult` and ordered `RawFinding` values; DataForSEO `RawFinding -> Evidence` normalization remains the ECO-45 boundary, and the runtime performs no automatic workflow execution or live research by itself.

All material conclusions must be supported by verifiable evidence. If evidence is insufficient, stale, conflicting, or estimated, the Skill must say so explicitly rather than filling gaps with unsupported assumptions.

---

# 2. Scope

## 2.1 In Scope

The Skill evaluates a candidate product across the following eight dimensions:

1. Market Demand
2. Competition
3. Price & Profitability
4. Pain Points & Differentiation
5. Supply Chain & Fulfillment
6. Brand Potential
7. Content Potential
8. Risk & Compliance

It also includes:

- Evidence collection
- Evidence quality grading
- Evidence freshness validation
- Competitor sampling
- Voice of Customer analysis
- Unit Economics
- Risk Gate
- Core dimension thresholds
- Weighted scoring
- Red Team review
- Structured Final Result for downstream reporting
- Final report and Evidence appendix (downstream ECO-38, not produced by the deterministic coordinator)

---

## 2.2 Out of Scope for v1

The following capabilities are not primary responsibilities of this Skill:

- Automatic product discovery
- Automatic product sourcing or purchase
- Supplier negotiation
- Ad campaign creation
- Store creation
- Listing generation
- Inventory planning
- Platform-specific optimization
- Final business decision on behalf of the user

The Skill provides analysis and evidence. The user remains responsible for the final commercial decision.

---

# 3. Default Behavior

If the user provides only a product name:

```text
Evaluate natural stone bracelet
```

the Skill should assume:

```yaml
target_market: US
```

If the user explicitly specifies another market, that market overrides the default.

Example:

```text
Evaluate natural stone bracelet for Germany
```

becomes:

```yaml
target_market: DE
```

---

# 4. Input Model

The minimum required input is:

```yaml
product:
  name: string
```

Example:

```yaml
product:
  name: Natural stone bracelet
```

Optional user-provided inputs may include:

```yaml
product:
  name: Natural stone bracelet
  description: Optional description
  category: Optional category
  materials:
    - Optional
  target_customer: Optional
  expected_retail_price: Optional
  sourcing_cost: Optional
  weight: Optional
  dimensions: Optional
  moq: Optional
  supplier_url: Optional

target_market: US
```

User-provided factual data should take precedence over inferred or estimated data unless the Skill finds credible evidence that the data is inconsistent.

When a user-provided value cannot be independently verified, retain it but mark it appropriately.

---

# 5. Data Status

Every important data point must have one of the following statuses:

```text
Observed
Estimated
Calculated
Unknown
```

## Observed

Directly obtained from a source.

Example:

```text
Amazon listed price: $39.99
Status: Observed
```

## Estimated

Derived from comparable products, suppliers, public data, or bounded assumptions.

Example:

```text
Estimated sourcing cost: $3.50–5.50
Status: Estimated
```

## Calculated

Mathematically derived from other inputs.

Example:

```text
Contribution Margin: 27.4%
Status: Calculated
```

## Unknown

No sufficiently reliable value is available.

The Skill must never silently convert an `Estimated` or `Unknown` value into an observed fact.

---

# 6. Evidence Policy

## 6.1 Evidence Requirement

Every material claim should follow this structure:

```text
Claim
Evidence
Source
Evidence Date
Evidence Tier
Confidence
```

A conclusion without supporting evidence is invalid.

Important claims should preferably be supported by at least two independent sources.

---

# 7. Evidence Tiers

## Tier 1 — Authoritative Sources

Examples:

- U.S. government agencies
- FDA
- FCC
- CPSC
- FTC
- CBP
- USPTO
- Official statistical agencies
- Official manufacturers
- Official brand documentation

Use primarily for:

- Regulation
- Compliance
- Certification
- Customs
- Product safety
- Official specifications
- Trademark and patent information

---

## Tier 2 — First-Party Market Data

Examples:

- Amazon
- Walmart
- Etsy
- Google Trends
- TikTok Shop
- Alibaba
- 1688
- Other major marketplaces

Use primarily for:

- Pricing
- Product availability
- Market structure
- Competitive density
- Supplier availability
- Product specifications
- Demand proxies

---

## Tier 3 — Consumer Evidence

Examples:

- Customer reviews
- Reddit
- TikTok
- YouTube
- Forums
- Q&A discussions

Use primarily for:

- Pain points
- Purchase motivation
- Complaints
- Usage scenarios
- Purchase barriers
- Unmet needs
- Customer language

---

## Tier 4 — Secondary Industry Sources

Examples:

- Industry media
- Blogs
- Analyst articles
- Third-party market research

Tier 4 evidence may support analysis but should not independently justify critical conclusions when better sources are available.

---

# 8. Evidence Cross-Validation

Important conclusions should preferably have two or more independent supporting sources.

For example, a strong market-demand conclusion should not rely only on a single article.

Preferred pattern:

```text
Google Trends
+
Marketplace demand signal
+
Consumer/social signal
```

If sources conflict, the Skill must:

1. Surface the disagreement
2. Explain the likely reason
3. Reduce confidence where appropriate
4. Avoid selecting only the evidence that supports the preferred conclusion

---

# 9. Evidence Freshness

Evidence freshness depends on data type.

## Search, demand, pricing, competition and marketplace data

Prefer:

```text
Last 3–12 months
```

## Customer reviews, VOC and social discussions

Prefer:

```text
Last 12–24 months
```

Older reviews may still be used when they represent persistent product issues.

## Supplier prices

Prefer:

```text
Last 3 months
```

## Regulation, compliance, tariffs and certification requirements

Must be verified against the **currently effective version**.

## Long-term industry data

Older evidence may be used if:

- More recent authoritative data is unavailable
- The year is clearly stated
- The Skill explains whether the data is still relevant

---

# 10. Market Demand Analysis

Market demand must not rely on a single signal.

The Skill should evaluate three demand categories.

## 10.1 Search Demand

Examples:

- Google Trends
- Search interest
- Keyword trend
- Search growth
- Seasonality

---

## 10.2 Commerce Demand

Examples:

- Amazon activity
- Walmart activity
- Etsy activity
- Review accumulation
- Bestseller signals
- Product availability
- Other marketplace demand proxies

---

## 10.3 Social Demand

Examples:

- TikTok
- YouTube
- Reddit
- Social discussions
- Creator activity

---

## 10.4 Validation Rule

A strong market-demand conclusion should normally have support from at least:

```text
2 of 3 demand signal categories
```

The Skill must distinguish:

```text
Stable Demand
```

from:

```text
Short-Term Hype
```

---

# 11. Competition Analysis

Competition analysis must focus on:

> Can a new seller reasonably enter this market?

It should not rely only on the number of existing products.

Analyze:

- Number of meaningful competitors
- Product similarity
- Product commoditization
- Top seller concentration
- Review concentration
- Brand concentration
- Price-band crowding
- Ad/search-result crowding
- New-product visibility
- Existing differentiation
- Unoccupied positioning
- Ease of copying differentiation

---

# 12. Competitor Sampling

Use stratified sampling.

Default target:

```text
10–15 valid competitor products
```

The sample should include, where available:

- Market leaders
- Mid-tier products
- New entrants
- Low-review products
- Premium products
- Mid-price products
- Lower-price products
- Different positioning
- Different product claims

Do not sample only bestselling products.

If fewer than 10 meaningful competitors exist, use all available valid samples and explicitly flag:

```text
Sample Size Limitation
```

---

# 13. Voice of Customer Analysis

VOC should use multiple consumer evidence sources where practical.

The current executable boundary is `product_research/voc.py`. It accepts only explicit propositions over existing normalized Evidence, reuses the existing Policy and Assessment contracts, and returns immutable, deterministic, traceable findings. It does not acquire or normalize provider data, infer categories or customer meaning, automatically cluster text, generate scores, or perform later Brand, Content, or other Phase 6 analysis.

Potential sources include:

- Amazon reviews
- Etsy reviews
- Walmart reviews
- Reddit
- TikTok
- YouTube
- Forums
- Product Q&A

VOC findings should be structured into:

```text
Purchase Motivation
Pain Points
Frequent Complaints
Unmet Needs
Use Cases
Purchase Barriers
Customer Language
Audience Segments
```

Whenever possible, the Skill should distinguish between:

- Common complaints
- Edge-case complaints
- Product-specific complaints
- Category-wide complaints

Downstream scoring is a later capability. The current VOC boundary emits no numeric score and supplies traceable findings for later analysis when those capabilities become available:

- Differentiation
- Brand Potential
- Content Potential

---

# 14. Supply Chain & Fulfillment Analysis

Analyze:

- Number of available suppliers
- Supplier concentration
- Sourcing price
- Price range
- MOQ
- Customization capability
- Manufacturing complexity
- Quality consistency
- Material availability
- Weight
- Package volume
- Fragility
- Shipping difficulty
- Dangerous goods restrictions
- Storage complexity
- Return complexity
- After-sales complexity

The current executable boundary is `product_research/supply_chain.py`. It accepts only explicit non-empty propositions in the eight closed Supply Chain dimensions over existing normalized Evidence, invokes the existing Policy and Assessment boundaries independently per unique proposition, and returns immutable findings with deterministic coverage and Evidence-ID traceability. It does not infer supplier, numeric, stance, independence, or operational facts from Evidence text or provenance; it does not acquire, extract, cluster, calculate, score, recommend, or classify regulatory Risk. Unavailable information remains `UNKNOWN` rather than becoming zero or an `Estimated` value. The module is normative for this current boundary; the preceding analysis list remains target methodology.

---

# 15. Unit Economics

Unit Economics is a dedicated Gate and scoring input.

The core model is:

```text
Selling Price
- Product Cost
- International Shipping
- Fulfillment
- Payment Fees
- Platform Cost
- Advertising CAC
- Return / After-sales Loss
--------------------------------
= Contribution Profit
```

And:

```text
Contribution Margin
=
Contribution Profit / Selling Price
```

Whenever feasible, each variable should provide:

```text
Value
Status
Source
Confidence
```

---

# 16. Unit Economics Gate

Use a two-level model.

## Level 1 — Minimum Viability

If the economics are clearly unsustainable, the Skill should flag a serious profitability failure regardless of the overall score.

This represents the minimum economic survival requirement.

---

## Level 2 — Dynamic Target

The target profitability level may vary depending on:

- Price point
- Repeat purchase potential
- Return rate
- Advertising dependency
- Shipping cost
- Product risk
- Customer support burden

A product that technically makes money is not automatically considered economically attractive.

The Skill should distinguish between:

```text
Barely Viable
Viable
Healthy
Strong
```

where supported by evidence.

---

# 17. Risk & Compliance

Risk analysis is independent of the weighted score.

Analyze areas such as:

- FDA
- FCC
- CPSC
- FTC
- Product safety
- Customs
- Intellectual property
- Patent
- Trademark
- Copyright
- Dangerous goods
- Batteries
- Liquids
- Food
- Cosmetics
- Children's products
- Medical claims
- Restricted materials
- Transportation restrictions
- Product liability

---

# 18. Risk Gate

Risk must use three levels.

## Fatal Risk

Examples:

- Clearly illegal
- Very high probability of infringement
- Cannot legally be sold
- Cannot be reasonably transported or imported

Typical result:

```text
NO-GO
```

---

## Reviewable Risk

Examples:

- Certification required
- Regulatory approval required
- Patent risk requiring specialist review
- Special shipping requirements

Typical result:

```text
RISK REVIEW
```

---

## Normal Risk

Non-critical risks remain part of the regular analysis and scoring.

Risk Gate always takes precedence over aggregate score.

---

# 19. Eight-Dimension Scoring Model

For normalized score inputs, execution belongs to `product_research/scoring_decision.py`. The module accepts exactly the eight fixed dimensions below in policy order and preserves missing scores as unresolved. Before it, `product_research/initial_scoring.py` validates explicit Agent/caller qualitative judgments against owned Phase 6 support and maps retained Unit Economics Contribution Margin; it does not generate those judgments.

The base weighting model is:

| Dimension | Base Weight |
|---|---:|
| Market Demand | 20% |
| Competition | 15% |
| Price & Profitability | 20% |
| Pain Points & Differentiation | 15% |
| Supply Chain & Fulfillment | 10% |
| Brand Potential | 8% |
| Content Potential | 7% |
| Risk & Compliance | 5% |

Total:

```text
100%
```

---

# 20. Dynamic Weight Adjustment

Use:

```text
Fixed Base Weight + Limited Dynamic Adjustment
```

Weights may be adjusted based on product characteristics.

Examples:

A bulky furniture product may justify a higher Supply Chain & Fulfillment weight.

A jewelry or lifestyle product may justify a higher Brand Potential weight.

Rules:

```text
Maximum adjustment per dimension:
±5 percentage points
```

Final weights must always total:

```text
100%
```

Any weight adjustment must include an explicit justification.

The Skill must not adjust weights merely to produce a preferred outcome. The deterministic executor receives a complete caller-owned adjustment vector, including explicit zero values, validates the `±5` bounds and exact `100%` total, and does not select or justify adjustments.

---

# 21. Quantitative vs LLM Scoring

The executor performs only the deterministic execution of already normalized scores. Initial Scoring validates explicit Agent/caller judgments but does not call an LLM, generate qualitative judgments, or infer scores from Evidence text.

Use a hybrid model.

## Deterministic / Quantitative Scoring

Use formulas or scripts where appropriate for:

- Price
- Cost
- Contribution Margin
- Weight
- Competitor count
- Review counts
- Growth rates
- Price distribution
- Supplier counts
- Other measurable data

---

## Evidence-Based LLM Scoring

The Agent/caller may use its available reasoning capability for dimensions such as:

- Pain-point intensity
- Differentiation opportunity
- Brand potential
- Content potential
- Competitive entry opportunity
- Unmet needs

Any caller-produced judgment must still cross the explicit Initial Scoring boundary with a finite Decimal score, Confidence, and relevant Evidence IDs. Rationale is review context only; unsupported judgments remain unresolved.

Example:

```text
Differentiation Score: 72/100

Supporting Evidence:
E017
E021
E034

Confidence:
Medium
```

Unsupported intuitive scoring is prohibited.

---

# 22. Core Dimension Thresholds

Overall score alone cannot compensate for failure in critical dimensions.

Minimum thresholds:

| Core Dimension | Minimum Score |
|---|---:|
| Market Demand | 60 |
| Price & Profitability | 60 |
| Pain Points & Differentiation | 55 |
| Competition | 45 |

If a core dimension fails its threshold, the Skill must explicitly surface the weakness even if the weighted score is high. In the current executor, a failed or unresolved core result constrains the analytical label to at most `CONDITIONAL GO`; no score-based severe-failure `NO-GO` threshold is defined.

A severe core-dimension failure should prevent an unqualified positive conclusion.

---

# 23. Final Decision Labels

The deterministic executor requires an explicit aggregate GO threshold; it has no default. Its precedence is `NO-GO` for fatal Risk or `UNVIABLE` economics, then `RISK REVIEW` for review-required or malformed Risk, then `CONDITIONAL GO` for other unresolved or failed prerequisites, and `GO` only when every explicit prerequisite passes. The labels remain analytical classifications rather than autonomous commercial decisions.

The Skill may use the following analytical labels:

```text
GO
CONDITIONAL GO
RISK REVIEW
NO-GO
```

These are analytical classifications, not autonomous business decisions.

## GO

Evidence and scoring are broadly supportive and no material Gate has failed.

## CONDITIONAL GO

The opportunity appears potentially attractive, but meaningful uncertainty, missing data, or a core weakness remains.

## RISK REVIEW

A regulatory, IP, compliance, logistics, or similar risk requires further validation before a reliable commercial conclusion can be made.

## NO-GO

Within the deterministic executor, `NO-GO` is reserved for an explicit fatal Risk state or `UNVIABLE` Unit Economics outcome. Other fundamental problems such as severe demand weakness or competitive disadvantage must be established by the upstream analysis policy; the executor does not invent a score-based severe-failure threshold.

Evidence may indicate a fundamental problem such as:

- Fatal compliance risk
- Clearly unsustainable economics
- Severe demand weakness
- Severe competitive disadvantage
- Another critical failure

---

# 24. Confidence

Major conclusions should carry a confidence level:

```text
High
Medium
Low
```

Confidence should consider:

- Number of sources
- Evidence Tier
- Evidence freshness
- Cross-source agreement
- Sample size
- Amount of estimated data
- Data quality

A high numerical score with low-confidence evidence must be reported as low confidence.

---

# 25. Red Team Review

After the initial analysis and scoring, the Skill must run a separate adversarial review.

The Red Team objective is:

> Find credible reasons why this product may be a worse opportunity than the initial analysis suggests.

The Red Team should challenge at least:

- Is demand overstated?
- Are search signals translating into purchases?
- Is social activity only short-term hype?
- Are marketplace demand proxies misleading?
- Is competition understated?
- Is incumbent concentration stronger than it appears?
- Is the assumed sourcing price unrealistic?
- Are shipping costs understated?
- Is CAC too optimistic?
- Are returns understated?
- Is VOC suffering from sampling bias?
- Is the perceived differentiation easy to copy?
- Are there hidden IP risks?
- Are there hidden compliance risks?
- Are there hidden product-liability risks?
- Why has the opportunity not already been captured by more sellers?

The Red Team must use evidence, not hypothetical objections alone.

---

# 26. Score Revision

After Red Team review:

```text
Initial Score
↓
Red Team Findings
↓
Score / Confidence Revision
↓
Final Score
```

Any material score change must explain:

```text
What changed
Why it changed
Which evidence caused the change
```

Red Team review may:

- Lower a score
- Raise a score if an apparent concern is disproven
- Lower confidence
- Trigger Risk Review
- Trigger No-Go

---

# 27. Analysis Workflow

The full workflow is:

```text
1. Candidate and target-market normalization
        ↓
2. Research plan definition
        ↓
3. Evidence collection and normalization
        ↓
4. Risk analysis and Risk Gate
        ↓
5. Unit Economics and Economics Gates
        ↓
6. Market Demand analysis
        ↓
7. Competition analysis
        ↓
8. VOC and Differentiation analysis
        ↓
9. Supply Chain and Fulfillment analysis
        ↓
10. Brand Potential analysis
        ↓
11. Content Potential analysis
        ↓
12. Initial Scoring from explicit caller-owned judgments
        ↓
13. Initial scoring decision and core-threshold evaluation
        ↓
14. Evidence-backed Red Team review input acceptance
        ↓
15. Red Team revision application
        ↓
16. Post-Red-Team authoritative-state resolution and final scoring decision
        ↓
Structured Final Result
        ↓
Downstream ECO-38 15-section report and complete Evidence Appendix
```

The coordinator preserves unresolved, blocked, and failed stage records cumulatively. It does not acquire Evidence, generate judgments, change policy, persist checkpoints, or render the downstream report contract.

---

# 28. Final Report Format

The final output is an analysis report rather than a prescriptive action plan.
The downstream ECO-38 runtime contract is defined in
[`references/report-contract.md`](../references/report-contract.md) and uses
exactly this 15-section structure:

```text
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
```

The report consumes the structured Stage 16 result through
`product_research/final_report_generation.py`. It preserves final-state
ownership, explicit incomplete state, per-dimension Confidence, non-ranked
key decision Evidence membership, and a complete lossless Evidence Appendix.

---

# 29. Executive Summary

The summary names the candidate product and target market and presents
available final-state facts: analytical label, aggregate, Risk, Unit
Economics, core state, workflow incompleteness, key decision Evidence IDs, and
accepted Red Team changes. It does not invent an overall-report Confidence,
recommendation, Evidence ranking, or cross-domain severity order.

---

# 30. Scorecard

The report contains exactly eight ordered rows with score, base weight, final
weight when available, presentation-only weighted contribution, per-dimension
Confidence, and supporting Evidence IDs. The authoritative aggregate and core
threshold results are copied when Stage 16 provides them. A missing value is
`UNAVAILABLE`, never zero.

---

# 31. Evidence Appendix

The Appendix contains exactly one row for every normalized Stage 3 Evidence
record in Evidence-ID order and no other rows:

| ID | Claim | Evidence | Source | Observed At | Tier | Status | Confidence |
|---|---|---|---|---|---|---|---|
| E001 | — | — | — | — | — | — | — |

Evidence content and provenance, including adverse, multiline, Unicode, and
control-character-sensitive content, are preserved with deterministic display
escaping. Empty Evidence is rendered explicitly.

---

# 32. Handling Missing Information

The Skill must not fail simply because the user provides only a product name.

Missing information should be handled in this order:

```text
1. Search for reliable observed data
2. Search for comparable data
3. Produce bounded estimates where reasonable
4. Mark estimates explicitly
5. Use Unknown when evidence is not reliable enough
6. Reduce confidence where uncertainty is material
```

If a critical variable cannot be reliably established, the Skill must avoid an unqualified `GO`.

---

# 33. Handling Conflicting Information

When credible sources disagree:

1. Preserve both pieces of evidence
2. Compare source quality
3. Compare freshness
4. Explain the disagreement
5. Choose a working assumption only when justified
6. Reduce confidence if uncertainty remains

Never silently discard inconvenient evidence.

---

# 34. Anti-Hallucination Rules

The Skill must not:

- Invent sales figures
- Invent keyword volumes
- Invent supplier prices
- Invent certifications
- Invent regulatory requirements
- Invent patents
- Invent review statistics
- Present estimates as observed values
- Cite a source that does not support the claim
- Use stale regulatory information without revalidation
- Give a numerical score without explaining its evidence basis

If reliable evidence is unavailable:

```text
Unknown
```

is preferable to fabricated precision.

---

# 35. Design Principle: Evidence Before Interpretation

The intended pipeline is:

```text
Research
↓
Raw Findings
↓
Normalized Evidence
↓
Structured Analysis
↓
Scoring
↓
Red Team
↓
Final Report
```

Avoid:

```text
Search
↓
LLM Impression
↓
Conclusion
```

Evidence should exist independently of the later interpretation whenever practical.

---

# 36. Design Principle: Deterministic Where Possible

Calculations should be deterministic whenever the problem is mathematical or rules-based.

Examples:

- Weighted score
- Margin calculations
- Threshold checks
- Weight validation
- Cost aggregation
- Evidence freshness checks

Do not rely on the LLM to perform calculations that can reliably be implemented in code.

---

# 37. Design Principle: Explicit Uncertainty

The Skill should prefer:

```text
Estimated sourcing cost:
$4–6
Confidence: Medium
```

over:

```text
Sourcing cost:
$5
```

when the underlying evidence does not support that precision.

Uncertainty is part of the analysis rather than a failure of the analysis.

---

# 38. v1 Success Criteria

These are full-workflow target criteria, not a claim that the current repository can already perform every listed stage. The current repository implements the source-agnostic orchestration control plane, fixed family-level adapter composition, explicit read-only analysis boundaries over existing normalized Evidence, deterministic Unit Economics, Initial Scoring, scoring and analytical decision boundaries, the narrow deterministic Red Team revision boundary, the fixed deterministic end-to-end coordinator for explicit normalized inputs, and the downstream deterministic 15-section report and Evidence Appendix projection. Provider-backed research acquisition, automatic qualitative judgment generation or objection generation, and Agent reasoning remain unavailable.

The v1 Skill is considered successful when it can take a candidate product and reliably:

1. Default to the U.S. market unless another market is specified
2. Conduct current web research
3. Collect traceable evidence
4. Classify evidence quality and freshness
5. Distinguish observed, estimated, calculated and unknown data
6. Analyze market demand from multiple signals
7. Analyze 10–15 stratified competitors where available
8. Extract structured VOC
9. Estimate Unit Economics
10. Evaluate supply chain feasibility
11. Detect significant regulatory, compliance and IP risks
12. Score all eight dimensions
13. Enforce core-dimension thresholds
14. Enforce Risk and Unit Economics Gates
15. Run a separate Red Team review
16. Revise scores when contrary evidence warrants it
17. Produce a concise main report
18. Produce a complete evidence appendix
19. Clearly communicate uncertainty
20. Avoid unsupported factual claims

---

# 39. v1 Evaluation Criteria

The Skill should be tested against multiple product categories.

Suggested test products include:

```text
Natural stone bracelet
Phone case
Pet toy
Office chair
Children's product
Battery-powered product
Cosmetic product
Bulky furniture
Seasonal product
Highly branded commodity
```

Evaluation should cover:

## Evidence Coverage

Do material conclusions have valid evidence?

## Citation Accuracy

Does each cited source actually support the associated claim?

## Hallucination Resistance

Does the Skill avoid fabricating missing information?

## Estimate Discipline

Does it clearly distinguish Estimated from Observed?

## Repeatability

Does repeated evaluation of the same product produce reasonably stable results?

## Scoring Stability

Are deterministic calculations identical across repeated runs?

## Gate Correctness

Do high-risk products correctly trigger Risk Review or No-Go?

## Core Dimension Enforcement

Can a high weighted score still be constrained by a critical dimension failure?

## Red Team Effectiveness

Does the Red Team actually challenge optimistic assumptions and revise results when evidence warrants it?

## Report Traceability

Can a reviewer trace important conclusions back to specific evidence objects?

---

# 40. Final Definition

This Skill can be summarized as:

> A platform-agnostic cross-border e-commerce product validation Skill that defaults to the U.S. market and uses current public evidence, deterministic economics and scoring, structured VOC and competition analysis, explicit risk gates, and adversarial Red Team review to produce a traceable and evidence-backed assessment of a candidate product.

Its purpose is not to make a product look attractive.

Its purpose is to determine, as objectively as available evidence permits:

> What is known, what is estimated, what is uncertain, what the opportunity appears to be, and what evidence supports that assessment.
