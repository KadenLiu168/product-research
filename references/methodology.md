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
5. Analyze all eight dimensions, score only where evidence supports scoring, check core thresholds, and prepare explicit Evidence-backed Red Team inputs.
6. Apply accepted revisions, resolve the final authoritative state, and consume the structured result downstream; report rendering remains outside this deterministic endpoint.

## Deterministic End-to-End Endpoint

When all inputs are explicit and normalized, `product_research/end_to_end_workflow.py` runs the fixed 16-stage coordinator: subject validation; research plan; research Evidence; Risk analysis and Gate; Unit Economics and Gates; Market Demand; Competition; VOC and Differentiation; Supply Chain and Fulfillment; Brand Potential; Content Potential; Initial Scoring; initial scoring decision and core thresholds; Red Team input acceptance; Red Team revision; and post-Red-Team authoritative-state resolution plus final scoring decision.

The coordinator retains one immutable ordered record for every stage, including unresolved, blocked, or failed stages, and reuses the existing Evidence, analysis, Gate, score, Red Team, and decision values without conversion or a second policy engine. Missing information remains unresolved or blocks only the dependent boundary. Its Stage 16 output is a structured Final Result for downstream consumers; it does not render the human-readable report or Evidence Appendix. Those reporting capabilities are downstream ECO-38 work and are unavailable until implemented.

## Initial Scoring Bridge

Initial Scoring is the narrow boundary between these structured results and the existing score executor. The Agent/caller owns qualitative judgment generation; each judgment must explicitly carry one qualitative dimension, a finite `Decimal` score from `0` through `100`, existing `Confidence`, and non-empty Evidence IDs. `rationale` is optional review context and never replaces Evidence IDs or affects scoring.

`product_research/initial_scoring.py` accepts only Evidence IDs traceable through relevant supported or adverse IDs in existing Phase 6 findings/results. Ownership is fixed: Market Demand → positive Market Demand result; Competition → adequate Competition findings declared `MARKET_STRUCTURE`; Pain Points & Differentiation → VOC findings plus Competition `POSITIONING` / `DIFFERENTIATION`; Supply Chain & Fulfillment → Supply Chain findings; Brand Potential / Content Potential → matching Brand / Content finding dimensions; Risk & Compliance → Risk findings with complete required-area coverage. Excluded, unrelated, unknown, unsupported, conflicted, insufficient, materially or critically unresolved support remains unresolved.

The boundary preserves the declared judgment Confidence only when it is no stronger than the weakest relevant cited source. Missing or malformed inputs produce the canonical unresolved slot (`score=None`, `Confidence=Low`, `Evidence IDs=()`); no unknown-to-zero or neutral fallback is permitted. Risk scoring does not alter `RiskGateState`, and Initial Scoring does not perform Red Team revision, weighting, aggregation, thresholds, labels, research, or reporting.

Price & Profitability is the only quantitative mapping: for a coherent retained `UnitEconomicsResult`, calculate `100 * (Contribution Margin - Minimum Viability) / (Dynamic Target - Minimum Viability)` under a fresh 34-digit `ROUND_HALF_EVEN` Decimal context, clamp known values to `0..100`, and leave equal/missing/malformed thresholds, mismatched actual margins or Evidence IDs, unresolved economics, and missing margin values unresolved. The thresholds and economics ownership remain caller-owned by Unit Economics.

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

The current executable boundary is `product_research/voc.py`. It consumes existing normalized Evidence plus caller-declared propositions, reuses the existing Policy and Assessment results, returns deterministic traceable findings and category coverage, and gates explicit Complaint prevalence and scope values by their declared supporting Evidence IDs. It does not acquire data, infer customer meaning, cluster text, generate scores, or run later Phase 6 analysis; those capabilities remain unavailable.

## Supply Chain and Fulfillment

Assess supplier availability and concentration, sourcing range, MOQ, customization, manufacturing complexity, quality consistency, materials, weight, package volume, fragility, shipping restrictions, storage, returns, and after-sales burden. The current executable boundary is `product_research/supply_chain.py`: it consumes existing normalized Evidence by caller-supplied `EvidenceId` together with explicit propositions in the eight closed dimensions, reuses the existing Policy and Assessment contracts, and returns immutable, deterministic, traceable findings and coverage. It does not acquire supplier data, infer meaning or numeric facts, calculate economics, generate scores or decisions, or classify regulatory Risk. Missing or unresolved inputs remain `UNKNOWN`; the boundary does not substitute an `Estimated` value. The module is the normative source for this behavior; the broader supply-chain methodology remains guidance for explicitly declared propositions.

## Brand and Content Potential

- **Brand Potential:** evaluate whether the product supports defensible positioning, recognizable customer identity, trust, line extension, repeat or gifting behavior, and differentiation beyond a generic listing.
- **Content Potential:** evaluate whether benefits, use cases, transformation, demonstrations, comparisons, and customer language can produce credible repeatable content rather than one-off novelty.

The current executable boundary is `product_research/brand_content.py`: it consumes existing normalized Evidence by caller-supplied `EvidenceId` together with explicit propositions carrying an explicit dimension (`BRAND_POTENTIAL` or `CONTENT_POTENTIAL`) and one of the five closed aspects (`BRAND_PREMIUM`, `STORYTELLING`, `VISUAL_EXPRESSION`, `DEMO_POTENTIAL`, `UGC_PROPAGATION`), reuses the existing Policy and Assessment contracts, and returns immutable, deterministic, traceable findings and aspect coverage. It does not acquire data, generate propositions from VOC or text, infer dimensions or aspects, or produce numeric scores or decisions. Unsupported or unavailable propositions remain `UNKNOWN` and unsupplied aspects remain missing. The module is the normative source for this behavior; the broader brand and content methodology remains guidance for explicitly declared propositions.

## Risk and Compliance

Evaluate safety, regulatory, certification, intellectual property, product-liability, dangerous-goods, and transport-restriction exposure before treating aggregate commercial attractiveness as actionable. Applicability is caller-owned: the analyst decides which Risk Areas apply to this product and declares them as the required-area contract for the run; no unlisted area is presumed applicable.

The current executable boundary is `product_research/risk_compliance.py`. It consumes existing normalized Evidence by caller-supplied `EvidenceId` together with explicit propositions in the six closed Risk Areas (`REGULATION`, `CERTIFICATION`, `IP`, `PRODUCT_LIABILITY`, `DANGEROUS_GOODS`, `TRANSPORT_RESTRICTION`), each proposing one classification (`NORMAL`, `REVIEWABLE`, or `FATAL`). It reuses the existing Evidence Policy and Evidence Assessment contracts, preserves original Evidence-ID traceability in every finding, reports required-area coverage conservatively, and aggregates into the existing decision-facing `RiskGateState`. Missing, stale, conflicting, rejected, or materially incomplete support stays `UNKNOWN` with no classification: missing evidence never becomes `NORMAL`, and missing information alone never becomes `FATAL`. The module is the normative source for this behavior; it does not acquire evidence, search regulations, patents, or trademarks, infer legal conclusions or applicability, or generate scores. The risk-assessment guidance above remains methodology for explicitly declared propositions.

## Red Team

After initial scoring, separately seek evidence that demand is overstated, commerce signals are weak, interest is hype, competition or incumbent concentration is understated, cost/CAC/returns are optimistic, VOC is biased, differentiation is copyable, or IP/compliance/liability risks are hidden. Objections require evidence. Revise scores or confidence only when warranted and identify what changed, why, and which evidence caused it.

The Agent/caller owns this adversarial reasoning and any upstream Risk or Unit Economics re-evaluation. Once those explicit normalized values exist, pass canonical baseline/current-run Evidence IDs, findings, per-dimension proposals, and complete authoritative before/after results to `product_research/red_team_revision.py` through the Stage 14/15 boundary of the end-to-end coordinator. The deterministic boundary validates current-run authorization, applies accepted changes, and preserves immutable history; it does not generate objections, interpret Evidence, rerun analysis, recalculate economics, or make the final decision. Stage 16 resolves the final authoritative state and invokes the existing scoring-decision executor; readable report and Evidence Appendix generation remains downstream.
