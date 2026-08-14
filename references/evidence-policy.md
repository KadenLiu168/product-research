# Evidence Policy

## Shared Evidence Representation

Evidence producers use the shared [`Evidence` contract](../product_research/evidence.py) for the structural record and [`EvidenceId`](../product_research/evidence.py) for downstream references. Its JSON boundary is deterministic and its `observed_at` value identifies when the Evidence content was observed or confirmed; it does not replace source publication or effective dates in policy analysis.

The contract validates representational shape only. The separate [`Evidence Policy validation`](../product_research/evidence_policy.py) boundary validates Tier/source eligibility, freshness, and citation integrity. Source independence, conflict handling, confidence assessment, and semantic support remain governed by this document and later capabilities; consumers reference an Evidence record by ID rather than defining a second Evidence shape.

## Core Discipline

`No evidence → no factual claim.` Research before conclusions. Every material claim must be traceable to evidence; critical commercial judgments should use at least two independent sources where practical.

## Evidence Tiers

| Tier | Source class | Typical use |
|---|---|---|
| Tier 1 | Official / authoritative sources | Regulation, compliance, safety, customs, IP, and official specifications |
| Tier 2 | First-party market / commerce data | Pricing, availability, competition, supplier data, and demand proxies |
| Tier 3 | Consumer evidence | Reviews, discussions, complaints, motivations, use cases, and customer language |
| Tier 4 | Secondary industry sources | Supporting context when stronger sources are unavailable |

Tier 4 must not independently justify a critical conclusion when better evidence should exist.

## Evidence Status

| Status | Meaning |
|---|---|
| `Observed` | Directly obtained from an identified source. |
| `Estimated` | A bounded inference supported by comparables, public data, or explicit assumptions. |
| `Calculated` | Deterministically derived from stated inputs. |
| `Unknown` | No sufficiently reliable value is available. |

Never convert `Estimated` or `Unknown` into `Observed`. User-provided facts take precedence over inference unless credible evidence shows inconsistency; if not independently verified, retain them with an appropriate status and confidence.

## Freshness

- Market, price, and competition: prefer the most recent 3–12 months.
- VOC: prefer the most recent 12–24 months; older evidence may support persistent issues when dated.
- Supply-chain quotations: prefer the most recent 3 months.
- Regulation, certification, and tariffs: verify the currently effective authoritative version.
- Long-term industry data may be older, but state its year and continuing relevance.

## Cross-Validation and Conflict

Use `>= 2 independent sources` for key commercial judgments where practical. Independence means the sources do not merely repeat the same underlying claim.

When credible sources conflict:

1. Preserve and surface both.
2. Compare tier, directness, methodology, and freshness.
3. Explain a working assumption only when justified.
4. Mark unresolved facts `Unknown` or preserve a bounded range.
5. Reduce confidence as appropriate.

Do not selectively hide adverse evidence.

## Confidence

Assign `High`, `Medium`, or `Low` to major conclusions using source count, tier, freshness, independence, agreement, sample size, estimate share, and overall data quality. A high score based on low-confidence evidence remains low confidence.

## Minimum Evidence Record

Record an ID, claim, evidence, source, evidence date, tier, status, and confidence. A citation is valid only when the source actually supports the claim.

If a required source or research capability is unavailable, say so. Do not invent sales, keyword volumes, prices, certifications, regulations, patents, reviews, citations, or source access.
