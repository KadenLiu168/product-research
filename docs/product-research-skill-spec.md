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

All material conclusions must be supported by verifiable evidence. If evidence is insufficient, stale, conflicting, or estimated, the Skill must say so explicitly rather than filling gaps with unsupported assumptions.

---

# 2. Scope

## 2.1 In Scope

The Skill evaluates a candidate product across the following eight dimensions:

1. Market Demand
2. Competition
3. Pricing & Profitability
4. Customer Pain Points & Differentiation
5. Supply Chain & Fulfillment
6. Brand Potential
7. Content & Social Distribution Potential
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
- Final report
- Evidence appendix

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

VOC findings must support later scoring for:

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

Where exact information is unavailable, reasonable estimates may be used if clearly marked as `Estimated`.

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

The base weighting model is:

| Dimension | Base Weight |
|---|---:|
| Market Demand | 20% |
| Competition | 15% |
| Pricing & Profitability | 20% |
| Customer Pain Points & Differentiation | 15% |
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

The Skill must not adjust weights merely to produce a preferred outcome.

---

# 21. Quantitative vs LLM Scoring

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

Use LLM analysis for dimensions such as:

- Pain-point intensity
- Differentiation opportunity
- Brand potential
- Content potential
- Competitive entry opportunity
- Unmet needs

LLM-generated scores must still cite evidence.

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
| Pricing & Profitability | 60 |
| Customer Pain Points & Differentiation | 55 |
| Competition | 45 |

If a core dimension fails its threshold, the Skill must explicitly surface the weakness even if the weighted score is high.

A severe core-dimension failure should prevent an unqualified positive conclusion.

---

# 23. Final Decision Labels

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

Evidence indicates a fundamental problem such as:

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
Candidate Product
        ↓
Resolve Target Market
        ↓
Research Planning
        ↓
Evidence Collection
        ↓
Evidence Normalization
        ↓
Evidence Quality / Freshness Check
        ↓
Risk Gate
        ↓
Unit Economics Gate
        ↓
Market Demand Analysis
        ↓
Competition Analysis
        ↓
VOC Analysis
        ↓
Supply Chain Analysis
        ↓
Brand / Content Analysis
        ↓
8-Dimension Initial Scoring
        ↓
Core Dimension Threshold Check
        ↓
Red Team Review
        ↓
Score & Confidence Revision
        ↓
Final Analytical Report
        ↓
Evidence Appendix
```

---

# 28. Final Report Format

The final output should be an analysis report rather than a prescriptive action plan.

Recommended structure:

```text
1. Executive Summary
2. Product & Market Definition
3. Market Demand
4. Competition
5. Pricing & Unit Economics
6. Voice of Customer
7. Differentiation
8. Supply Chain & Fulfillment
9. Brand Potential
10. Content Potential
11. Risk & Compliance
12. Scorecard
13. Core Dimension Check
14. Red Team Findings
15. Key Uncertainties
16. Final Analytical Label
17. Evidence Appendix
```

---

# 29. Executive Summary

The summary should answer:

- What is the product?
- What market was evaluated?
- What is the overall opportunity?
- What are the strongest supporting factors?
- What are the biggest weaknesses?
- What is the final score?
- What is the final confidence?
- What analytical label applies?

Do not hide important risks simply to keep the summary concise.

---

# 30. Scorecard

The report should include:

| Dimension | Score | Weight | Weighted Score | Confidence |
|---|---:|---:|---:|---|
| Market Demand | — | 20% | — | — |
| Competition | — | 15% | — | — |
| Pricing & Profitability | — | 20% | — | — |
| Pain Points & Differentiation | — | 15% | — | — |
| Supply Chain & Fulfillment | — | 10% | — | — |
| Brand Potential | — | 8% | — | — |
| Content Potential | — | 7% | — | — |
| Risk & Compliance | — | 5% | — | — |

If weights were dynamically changed, both the base and final weights should be explainable.

---

# 31. Evidence Appendix

Use a complete evidence table.

Recommended structure:

| ID | Claim / Observation | Evidence | Source | Date | Tier | Status | Confidence |
|---|---|---|---|---|---|---|---|
| E001 | — | — | — | — | — | — | — |

Every evidence object should have a unique ID.

Example:

```text
E017
```

This ID may then be referenced throughout the report.

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