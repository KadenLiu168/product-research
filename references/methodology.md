# Product Research Methodology

## Scope and Default

Evaluate a user-provided candidate product for cross-border e-commerce viability. Do not automatically discover candidates. Use `United States` when the user does not specify a target market; otherwise use the explicit market.

## Eight Evaluation Dimensions

1. Market Demand
2. Competition
3. Price & Profitability
4. Pain Points & Differentiation
5. Supply Chain & Fulfillment
6. Brand Potential
7. Content Potential
8. Risk & Compliance

Use [scoring-policy.md](scoring-policy.md) for weights, thresholds, and scoring rules. Use [gates.md](gates.md) for independent gate decisions.

## Research Method

1. Normalize the product, intended customer, target market, and known inputs.
2. Turn each dimension and gate into explicit research questions.
3. Collect evidence under [evidence-policy.md](evidence-policy.md), then normalize claims, dates, sources, statuses, and confidence.
4. Evaluate gates before treating aggregate commercial attractiveness as actionable.
5. Analyze all eight dimensions, score only where evidence supports scoring, check core thresholds, and run an evidence-based Red Team review.
6. Revise scores or confidence when contrary evidence warrants it, then report under [report-contract.md](report-contract.md).

## Market Demand

Validate demand with multiple signals rather than a single proxy:

- **Search demand:** search interest, trend, growth, and seasonality.
- **Commerce demand:** marketplace activity, review accumulation, availability, and other purchase-oriented proxies.
- **Social demand:** creator activity and consumer discussion.

A strong demand conclusion normally needs support from at least two of these three categories. Distinguish stable demand from short-term hype.

The current executable boundary is `product_research/market_demand.py`. It consumes existing normalized Evidence and requires callers to bind each participating Evidence ID explicitly to one demand category and one temporal interpretation. It reuses the existing Policy and Assessment results, returns conservative traceability, and does not acquire data or generate a numeric score. The module is the normative source for this behavior; the examples above remain methodology guidance.

## Competition Structure

Assess whether a new seller can reasonably enter, not merely how many listings exist. Examine meaningful competitor count, similarity and commoditization, seller/brand/review concentration, price-band and ad crowding, new-product visibility, positioning gaps, and how easily differentiation can be copied.

Use a stratified sample of 10–15 valid competitors where available: leaders, mid-tier products, new entrants, low-review products, multiple price bands, claims, and positioning. Do not sample only bestsellers. If fewer than 10 meaningful competitors exist, use all valid samples and flag `Sample Size Limitation`.

The current executable boundary is `product_research/competition.py`. It consumes existing normalized Evidence plus caller-declared competitor samples and material propositions, reuses the existing Policy and Assessment results, reports deterministic sample coverage and independent findings, and does not acquire data or generate a numeric score. The module is the normative source for this behavior; the sampling examples above remain methodology guidance.

## VOC and Differentiation

Use multiple consumer sources where practical. Structure findings as purchase motivation, pain points, frequent complaints, unmet needs, use cases, purchase barriers, customer language, and audience segments. Distinguish common, edge-case, product-specific, and category-wide complaints. Use VOC evidence to evaluate differentiation, brand, and content potential.

## Supply Chain and Fulfillment

Assess supplier availability and concentration, sourcing range, MOQ, customization, manufacturing complexity, quality consistency, materials, weight, package volume, fragility, shipping restrictions, storage, returns, and after-sales burden. Exact unavailable values remain `Unknown`; bounded estimates require evidence and the `Estimated` status.

## Brand and Content Potential

- **Brand Potential:** evaluate whether the product supports defensible positioning, recognizable customer identity, trust, line extension, repeat or gifting behavior, and differentiation beyond a generic listing.
- **Content Potential:** evaluate whether benefits, use cases, transformation, demonstrations, comparisons, and customer language can produce credible repeatable content rather than one-off novelty.

## Red Team

After initial scoring, separately seek evidence that demand is overstated, commerce signals are weak, interest is hype, competition or incumbent concentration is understated, cost/CAC/returns are optimistic, VOC is biased, differentiation is copyable, or IP/compliance/liability risks are hidden. Objections require evidence. Revise scores or confidence only when warranted and identify what changed, why, and which evidence caused it.
