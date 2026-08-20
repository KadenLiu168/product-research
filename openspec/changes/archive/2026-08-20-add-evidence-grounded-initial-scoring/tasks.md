## 1. Establish RED contracts

- [x] 1.1 Add focused `unittest` fixtures that construct real existing Phase 6 results, `UnitEconomicsResult`, qualitative judgments, and the existing `DimensionScores` values without bypassing domain validation.
- [x] 1.2 Add RED tests for exactly eight output slots, existing dimension order and value types, canonical unresolved slots, valid `Decimal 0..100` scores, immutable/canonical Evidence-ID tuples, and direct `evaluate_scoring_decision(...)` compatibility.
- [x] 1.3 Add RED tests for the seven qualitative ownership routes, including relevant supported/adverse IDs, unrelated IDs, excluded IDs, unknown/unsupported findings, duplicate or malformed judgments, malformed collections, and per-owned-dimension fail-closed isolation.
- [x] 1.4 Add RED tests for material/critical missing information, conflicted or insufficient assessments, Competition sample adequacy, Market Demand positivity, complete Risk required-area coverage, and conservative Confidence ceiling behavior.
- [x] 1.5 Add RED tests for the profitability formula at lower/upper boundaries, midpoint, below/above clamping, non-terminating Decimal behavior, missing/equal/malformed thresholds, mismatched retained actual margins or Evidence-ID tuples, unresolved economics, missing Evidence IDs, and ambient Decimal context independence.
- [x] 1.6 Add Agent-level RED scenarios to `tests/scenarios.md` for explicit qualitative handoff, relevant Evidence selection, withheld unsupported scores, Confidence non-inflation, Risk/economics independence, and no Red Team behavior.

## 2. Add the minimal Initial Scoring boundary

- [x] 2.1 Add one focused module under `product_research/` with the minimum immutable qualitative-judgment/input contract needed to express dimension, Decimal score, Confidence, Evidence IDs, and optional non-normative rationale; reject coercion, unsupported dimensions, and duplicate IDs.
- [x] 2.2 Implement the public fail-closed evaluator that always returns the existing `DimensionScores` with exactly eight ordered `DimensionScore` slots and uses `None`, `Low`, and `()` for every unresolved slot.
- [x] 2.3 Keep imports and dependency direction narrow: reuse existing Phase 6, Evidence, Unit Economics, and score value objects without changing those modules or adding a parallel final score model, external dependency, provider, LLM, clock, network, randomness, persistence, or hidden configuration.

## 3. Implement qualitative grounding and Confidence validation

- [x] 3.1 Build deterministic read-only support routing for Market Demand, Competition, VOC plus relevant Competition differentiation findings, Supply Chain, Brand, Content, and Risk according to the exact dimension ownership table.
- [x] 3.2 Accept only IDs traceable through eligible `supporting_ids` or `adverse_ids`; reject IDs available only through excluded, unknown, unsupported, unrelated, malformed, or materially unresolved sources without reading Evidence text or rerunning Policy/Assessment/analyzers.
- [x] 3.3 Enforce Market Demand `POSITIVE`, Competition `ADEQUATE`, Risk complete required-area coverage, and nested conflict/insufficiency/material-gap rules while leaving uncited out-of-route gaps independent.
- [x] 3.4 Compute the Confidence ceiling as the weakest relevant cited source Confidence, preserve caller Confidence at or below the ceiling, and resolve overconfident judgments without averaging, voting, or automatic repair.
- [x] 3.5 Make judgment and Evidence-ID ordering replay-stable and ensure malformed or duplicate dimension judgments affect only their owned slot except for the specified malformed top-level collection behavior.

## 4. Implement deterministic profitability normalization

- [x] 4.1 Validate one existing immutable `UnitEconomicsResult` without reconstructing inputs or recalculating Contribution Profit, Contribution Margin, gate outcomes, thresholds, reasons, or `EconomicsOutcome`.
- [x] 4.2 Implement `100 * (margin - minimum) / (dynamic - minimum)` under a fresh 34-digit `ROUND_HALF_EVEN` Decimal context, clamp known values to `0..100`, and apply no implicit quantization.
- [x] 4.3 Emit Price & Profitability only when the retained margin, distinct ordered thresholds, matching actual margins, non-unresolved outcome, Contribution Margin Confidence, and equal non-empty result/margin Evidence-ID tuples satisfy the spec; otherwise emit the canonical unresolved slot.
- [x] 4.4 Verify the profitability path never consumes a qualitative fallback and never uses `EconomicsOutcome` or either gate label alone as a numeric score.

## 5. Align Agent and reference contracts

- [x] 5.1 Update `SKILL.md` Stage 12 routing and capability text so Agent/caller qualitative judgments cross the explicit deterministic validation boundary and unsupported judgments remain withheld; do not claim provider-backed, Red Team, report, or end-to-end capabilities.
- [x] 5.2 Update `references/methodology.md` and `references/scoring-policy.md` with the Initial Scoring ownership, exact profitability rubric, Confidence ceiling, traceability, and unresolved rules while retaining existing weights, core thresholds, and analytical decision policy.
- [x] 5.3 Review `references/gates.md`, `docs/product-research-skill-spec.md`, and related living specs for contradictions; make only necessary contract-alignment edits and preserve independent Risk Gate, Unit Economics Gate, and scoring-decision ownership.
- [x] 5.4 Turn the Agent RED scenarios GREEN and confirm rationale never substitutes for Evidence IDs or affects deterministic scoring.

## 6. Verify scope, regressions, and acceptance

- [x] 6.1 Run the focused Initial Scoring test module verbosely and trace every delta-spec scenario to fresh contract evidence, including Decimal-context, relevance, material-gap, Confidence, and malformed-boundary cases.
- [x] 6.2 Run focused regression modules for scoring decision, Unit Economics, Market Demand, Competition, VOC, Supply Chain, Brand / Content, Risk & Compliance, Evidence Assessment, Evidence Policy, and Evidence representation.
- [x] 6.3 Run `python3 -m unittest discover -s tests` and every other repository-wide automated validation present at Apply time; leave the full suite green.
- [x] 6.4 Run `openspec validate add-evidence-grounded-initial-scoring --strict` and `openspec validate --all --strict`, then inspect the final diff for Unknown-to-zero/neutral behavior, hidden score constants, float coercion, irrelevant or excluded traceability, Confidence inflation, analyzer/gate recalculation, LLM/provider calls, decision/Red Team leakage, upstream contract edits, extra dependencies, or unrelated changes.
- [x] 6.5 Obtain an independent acceptance review that traces proposal, design, every requirement/scenario, tasks, implementation, documentation, and fresh command output; resolve all in-scope findings and leave archive, Linear, commit, and push unperformed pending separate authorization.
