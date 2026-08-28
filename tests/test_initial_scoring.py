"""Contract tests for the evidence-grounded Initial Scoring boundary."""

import decimal
import importlib
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal


DIMENSIONS = (
    "Market Demand",
    "Competition",
    "Price & Profitability",
    "Pain Points & Differentiation",
    "Supply Chain & Fulfillment",
    "Brand Potential",
    "Content Potential",
    "Risk & Compliance",
)
QUALITATIVE_FIELDS = (
    "market_demand",
    "competition",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)


def _module_or_none(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return None


class InitialScoringTestBase(unittest.TestCase):
    def setUp(self):
        self.initial = _module_or_none("product_research.initial_scoring")
        self.score = importlib.import_module("product_research.scoring_decision")
        self.economics = importlib.import_module("product_research.unit_economics")
        self.evidence = importlib.import_module("product_research.evidence")
        self.assessment = importlib.import_module("product_research.evidence_assessment")
        self.market = importlib.import_module("product_research.market_demand")
        self.competition = importlib.import_module("product_research.competition")
        self.voc = importlib.import_module("product_research.voc")
        self.supply = importlib.import_module("product_research.supply_chain")
        self.brand = importlib.import_module("product_research.brand_content")
        self.risk = importlib.import_module("product_research.risk_compliance")

    def require_initial(self):
        if self.initial is None:
            self.fail("product_research.initial_scoring has not been implemented")
        return self.initial

    def eid(self, value):
        return self.evidence.EvidenceId(value)

    def assessment_result(
        self,
        evidence_id="E001",
        *,
        confidence="High",
        outcome="SUPPORTED",
        conflict="NONE",
        factors=(),
        missing_information=(),
    ):
        evidence_id = self.eid(evidence_id)
        return self.assessment.EvidenceAssessmentResult(
            outcome=self.assessment.AssessmentOutcome(outcome),
            confidence=self.evidence.Confidence(confidence),
            conflict_state=self.assessment.ConflictState(conflict),
            source_count=1,
            independent_source_count=1,
            supporting_ids=(evidence_id,) if outcome == "SUPPORTED" else (),
            usable_ids=(evidence_id,) if outcome == "SUPPORTED" else (),
            missing_information=tuple(missing_information),
            factors=tuple(self.assessment.AssessmentFactor(value) for value in factors),
        )

    def market_result(self, evidence_id="E001", *, conclusion="POSITIVE", **kwargs):
        return self.market.MarketDemandResult(
            conclusion=self.market.DemandConclusion(conclusion),
            temporal_state=self.market.TemporalDemandState("STABLE" if conclusion == "POSITIVE" else "UNKNOWN"),
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supported_categories=(self.market.DemandSignalCategory("SEARCH"),) if conclusion == "POSITIVE" else (),
            missing_categories=tuple(
                self.market.DemandSignalCategory(value)
                for value in ("COMMERCE", "SOCIAL")
            ) if conclusion == "POSITIVE" else tuple(
                self.market.DemandSignalCategory(value)
                for value in ("SEARCH", "COMMERCE", "SOCIAL")
            ),
            supporting_ids=(self.eid(evidence_id),) if conclusion == "POSITIVE" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop("assessment", self.assessment_result(evidence_id)),
            factors=(),
        )

    def competition_finding(self, dimension="POSITIONING", evidence_id="E002", **kwargs):
        outcome = kwargs.pop("outcome", "SUPPORTED")
        return self.competition.CompetitionFinding(
            dimension=self.competition.CompetitionDimension(dimension),
            proposition="A structured competition proposition.",
            outcome=self.competition.CompetitionFindingOutcome(outcome),
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supporting_ids=(self.eid(evidence_id),) if outcome == "SUPPORTED" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop(
                "assessment",
                self.assessment_result(
                    evidence_id,
                    outcome="SUPPORTED" if outcome == "SUPPORTED" else "INSUFFICIENT",
                ),
            ),
            factors=(),
        )

    def competition_result(self, findings=(), adequacy="ADEQUATE"):
        return self.competition.CompetitionResult(
            total_sample_count=10,
            valid_sample_count=10,
            target_min=10,
            target_max=15,
            sample_adequacy=self.competition.SampleAdequacy(adequacy),
            covered_strata=(),
            missing_strata=(),
            covered_price_bands=(),
            sample_limitations=(),
            sample_results=(),
            findings=tuple(findings),
            factors=(),
        )

    def voc_finding(self, evidence_id="E003", **kwargs):
        outcome = kwargs.pop("outcome", "SUPPORTED")
        return self.voc.VOCFinding(
            category=self.voc.VOCCategory("PAIN_POINT"),
            proposition="Customers report a relevant pain point.",
            outcome=self.voc.VOCFindingOutcome(outcome),
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supporting_ids=(self.eid(evidence_id),) if outcome == "SUPPORTED" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop(
                "assessment",
                self.assessment_result(
                    evidence_id,
                    outcome="SUPPORTED" if outcome == "SUPPORTED" else "INSUFFICIENT",
                ),
            ),
            prevalence=self.voc.ComplaintPrevalence("UNKNOWN"),
            prevalence_supporting_ids=(),
            scope=self.voc.ComplaintScope("UNKNOWN"),
            scope_supporting_ids=(),
            factors=(),
        )

    def voc_result(self, findings=()):
        return self.voc.VOCResult(
            supported_categories=(self.voc.VOCCategory("PAIN_POINT"),) if findings else (),
            unknown_categories=(),
            missing_categories=tuple(
                self.voc.VOCCategory(value)
                for value in (
                    "PURCHASE_MOTIVATION",
                    "COMPLAINT",
                    "UNMET_NEED",
                    "USE_CASE",
                    "PURCHASE_BARRIER",
                    "CUSTOMER_LANGUAGE",
                    "SEGMENT",
                )
            ) if findings else tuple(
                self.voc.VOCCategory(value)
                for value in (
                    "PURCHASE_MOTIVATION",
                    "PAIN_POINT",
                    "COMPLAINT",
                    "UNMET_NEED",
                    "USE_CASE",
                    "PURCHASE_BARRIER",
                    "CUSTOMER_LANGUAGE",
                    "SEGMENT",
                )
            ),
            findings=tuple(findings),
            duplicate_proposition_keys=(),
            factors=(),
        )

    def supply_finding(self, evidence_id="E004", **kwargs):
        outcome = kwargs.pop("outcome", "SUPPORTED")
        return self.supply.SupplyChainFinding(
            dimension=self.supply.SupplyChainDimension("MOQ"),
            proposition="The supplier has a declared minimum order quantity.",
            outcome=self.supply.SupplyChainFindingOutcome(outcome),
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supporting_ids=(self.eid(evidence_id),) if outcome == "SUPPORTED" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop("assessment", self.assessment_result(evidence_id, outcome=outcome)),
            factors=(),
        )

    def supply_result(self, findings=()):
        return self.supply.SupplyChainResult(
            supported_dimensions=(self.supply.SupplyChainDimension("MOQ"),) if findings else (),
            unknown_dimensions=(),
            missing_dimensions=tuple(
                self.supply.SupplyChainDimension(value)
                for value in (
                    "SUPPLIER_LANDSCAPE",
                    "SOURCING_COST",
                    "CUSTOMIZATION",
                    "QUALITY",
                    "WEIGHT_VOLUME",
                    "TRANSPORTATION",
                    "RETURNS_AFTER_SALES",
                )
            ) if findings else tuple(
                self.supply.SupplyChainDimension(value)
                for value in (
                    "SUPPLIER_LANDSCAPE",
                    "MOQ",
                    "SOURCING_COST",
                    "CUSTOMIZATION",
                    "QUALITY",
                    "WEIGHT_VOLUME",
                    "TRANSPORTATION",
                    "RETURNS_AFTER_SALES",
                )
            ),
            findings=tuple(findings),
            duplicate_proposition_keys=(),
            factors=(),
        )

    def brand_finding(self, dimension="BRAND_POTENTIAL", evidence_id="E005", **kwargs):
        outcome = kwargs.pop("outcome", "SUPPORTED")
        return self.brand.BrandContentFinding(
            dimension=self.brand.BrandContentDimension(dimension),
            aspect=self.brand.BrandContentAspect("BRAND_PREMIUM" if dimension == "BRAND_POTENTIAL" else "DEMO_POTENTIAL"),
            proposition="The product supports a declared brand or content proposition.",
            outcome=self.brand.BrandContentFindingOutcome(outcome),
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supporting_ids=(self.eid(evidence_id),) if outcome == "SUPPORTED" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop("assessment", self.assessment_result(evidence_id, outcome=outcome)),
            factors=(),
        )

    def brand_result(self, findings=()):
        aspects = (self.brand.BrandContentAspect("BRAND_PREMIUM"), self.brand.BrandContentAspect("DEMO_POTENTIAL"))
        return self.brand.BrandContentResult(
            supported_aspects=aspects if findings else (),
            unknown_aspects=(),
            missing_aspects=tuple(
                self.brand.BrandContentAspect(value)
                for value in ("STORYTELLING", "VISUAL_EXPRESSION", "UGC_PROPAGATION")
            ) if findings else tuple(
                self.brand.BrandContentAspect(value)
                for value in (
                    "BRAND_PREMIUM",
                    "STORYTELLING",
                    "VISUAL_EXPRESSION",
                    "DEMO_POTENTIAL",
                    "UGC_PROPAGATION",
                )
            ),
            findings=tuple(sorted(findings, key=lambda finding: (finding.dimension.value, finding.aspect.value))),
            duplicate_proposition_keys=(),
            factors=(),
        )

    def risk_finding(self, evidence_id="E006", **kwargs):
        outcome = kwargs.pop("outcome", "SUPPORTED")
        return self.risk.RiskFinding(
            area=self.risk.RiskArea("REGULATION"),
            proposition="The regulatory status is explicitly supported.",
            outcome=self.risk.RiskFindingOutcome(outcome),
            supported_classification=self.risk.RiskClassification("NORMAL") if outcome == "SUPPORTED" else None,
            confidence=self.evidence.Confidence(kwargs.pop("confidence", "High")),
            supporting_ids=(self.eid(evidence_id),) if outcome == "SUPPORTED" else (),
            adverse_ids=tuple(self.eid(value) for value in kwargs.pop("adverse_ids", ())),
            excluded_ids=tuple(self.eid(value) for value in kwargs.pop("excluded_ids", ())),
            assessment=kwargs.pop("assessment", self.assessment_result(evidence_id, outcome=outcome)),
            diagnostics=(),
        )

    def risk_result(self, findings=(), complete=True, gate="CLEAR"):
        required = (self.risk.RiskArea("REGULATION"),)
        return self.risk.RiskComplianceResult(
            required_areas=required,
            supported_required_areas=required if complete and findings else (),
            unresolved_required_areas=() if complete else required,
            missing_required_areas=(),
            findings=tuple(findings),
            duplicate_proposition_keys=(),
            risk_gate=self.risk.RiskGateState(gate),
            diagnostics=(),
        )

    def judgment(self, dimension, score="70", evidence_ids=("E001",), confidence="Medium", rationale=None):
        initial = self.require_initial()
        return initial.QualitativeJudgment(
            dimension=self.score.Dimension(dimension),
            score=Decimal(score),
            confidence=self.evidence.Confidence(confidence),
            evidence_ids=tuple(self.eid(value) for value in evidence_ids),
            rationale=rationale,
        )

    def economics_result(
        self,
        margin=Decimal("0.50"),
        minimum=Decimal("0.20"),
        dynamic=Decimal("0.80"),
        *,
        outcome="MEETS_TARGET",
        evidence_ids=("E900",),
        contribution_ids=None,
        minimum_actual=None,
        dynamic_actual=None,
    ):
        ids = tuple(self.eid(value) for value in evidence_ids)
        contribution_ids = ids if contribution_ids is None else tuple(self.eid(value) for value in contribution_ids)
        minimum_actual = margin if minimum_actual is None else minimum_actual
        dynamic_actual = margin if dynamic_actual is None else dynamic_actual
        return self.economics.UnitEconomicsResult(
            contribution_profit=self.economics.ContributionProfit(
                Decimal("50"), "USD", self.economics.Status("Calculated"), self.evidence.Confidence("High"), ids
            ),
            contribution_margin=self.economics.ContributionMargin(
                margin, self.economics.Status("Calculated"), self.evidence.Confidence("High"), contribution_ids
            ),
            minimum_viability_gate=self.economics.GateResult(
                self.economics.GateOutcome("PASS"), minimum_actual, minimum, ()
            ),
            dynamic_target_gate=self.economics.GateResult(
                self.economics.GateOutcome("PASS"), dynamic_actual, dynamic, ()
            ),
            outcome=self.economics.EconomicsOutcome(outcome),
            unresolved_inputs=(),
            evidence_ids=ids,
            reasons=(),
        )

    def evaluate(self, *, judgments=(), economics=None, **results):
        initial = self.require_initial()
        return initial.evaluate_initial_scoring(
            market_demand=results.get("market_demand"),
            competition=results.get("competition"),
            voc=results.get("voc"),
            supply_chain=results.get("supply_chain"),
            brand_content=results.get("brand_content"),
            risk_compliance=results.get("risk_compliance"),
            unit_economics=economics,
            qualitative_judgments=judgments,
        )


class InitialScoringBoundaryTests(InitialScoringTestBase):
    def test_module_exposes_one_public_evaluator_and_immutable_judgment(self):
        initial = self.require_initial()
        self.assertTrue(callable(initial.evaluate_initial_scoring))
        judgment = self.judgment(DIMENSIONS[0], evidence_ids=("E002", "E001"))
        self.assertEqual(tuple(item.value for item in judgment.evidence_ids), ("E001", "E002"))
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            judgment.score = Decimal("1")

    def test_judgment_rejects_coercion_unsupported_dimension_and_duplicate_ids(self):
        initial = self.require_initial()
        for value in (80, 80.0, "80", True, Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("101")):
            with self.subTest(value=repr(value)), self.assertRaises((TypeError, ValueError)):
                initial.QualitativeJudgment(
                    self.score.Dimension("Market Demand"),
                    value,
                    self.evidence.Confidence("High"),
                    (self.eid("E001"),),
                )
        with self.assertRaises((TypeError, ValueError)):
            initial.QualitativeJudgment(
                self.score.Dimension("Price & Profitability"),
                Decimal("50"),
                self.evidence.Confidence("High"),
                (self.eid("E001"),),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.judgment("Market Demand", evidence_ids=("E001", "E001"))

    def test_empty_or_partial_inputs_always_return_the_exact_eight_slot_contract(self):
        result = self.evaluate()
        self.assertIs(type(result), self.score.DimensionScores)
        self.assertEqual(tuple(field for field in result.__dataclass_fields__), (
            "market_demand", "competition", "price_profitability", "pain_points_differentiation",
            "supply_chain_fulfillment", "brand_potential", "content_potential", "risk_compliance",
        ))
        slots = self.score.iter_dimension_scores(result)
        self.assertEqual(len(slots), 8)
        self.assertEqual(tuple(slot.score for slot in slots), (None,) * 8)
        self.assertEqual(tuple(slot.confidence for slot in slots), (self.evidence.Confidence("Low"),) * 8)
        self.assertEqual(tuple(slot.evidence_ids for slot in slots), ((),) * 8)

    def test_concrete_judgment_preserves_decimal_score_and_reaches_decision_executor(self):
        judgment = self.judgment("Market Demand", score="80", evidence_ids=("E001",), confidence="Medium")
        result = self.evaluate(judgments=(judgment,), market_demand=self.market_result())
        self.assertEqual(result.market_demand.score, Decimal("80"))
        self.assertEqual(result.market_demand.confidence, self.evidence.Confidence("Medium"))
        weights = self.score.WeightAdjustments(*(Decimal("0"),) * 8)
        decision = self.score.evaluate_scoring_decision(
            result,
            weights,
            self.score.RiskGateState("CLEAR"),
            self.economics_result(),
            self.score.DecisionPolicy(Decimal("70")),
            required_research_ready=True,
        )
        self.assertIs(type(decision), self.score.DecisionResult)

    def test_valid_risk_score_preserves_fatal_gate_precedence_downstream(self):
        result = self.evaluate(
            judgments=(self.judgment("Risk & Compliance", "76", ("E007",), "High"),),
            risk_compliance=self.risk_result(
                (self.risk_finding("E007"),),
                gate="FATAL",
            ),
        )
        self.assertEqual(result.risk_compliance.score, Decimal("76"))
        decision = self.score.evaluate_scoring_decision(
            result,
            self.score.WeightAdjustments(*(Decimal("0"),) * 8),
            self.score.RiskGateState("FATAL"),
            self.economics_result(),
            self.score.DecisionPolicy(Decimal("70")),
            required_research_ready=True,
        )
        self.assertEqual(decision.risk_gate, self.score.RiskGateState("FATAL"))
        self.assertEqual(decision.label.value, "NO-GO")

    def test_rationale_is_non_normative_and_cannot_substitute_for_evidence_ids(self):
        first = self.judgment("Market Demand", "80", ("E001",), "Medium", "positive rationale")
        second = self.judgment("Market Demand", "80", ("E001",), "Medium", "different rationale")
        first_result = self.evaluate(judgments=(first,), market_demand=self.market_result())
        second_result = self.evaluate(judgments=(second,), market_demand=self.market_result())
        self.assertEqual(first_result.market_demand, second_result.market_demand)
        with self.assertRaises((TypeError, ValueError)):
            self.judgment("Market Demand", "80", (), "Medium", "rationale only")


class InitialScoringGroundingTests(InitialScoringTestBase):
    def all_judgments(self):
        return (
            self.judgment("Market Demand", "70", ("E001",), "High"),
            self.judgment("Competition", "71", ("E002",), "High"),
            self.judgment("Pain Points & Differentiation", "72", ("E003",), "High"),
            self.judgment("Supply Chain & Fulfillment", "73", ("E004",), "High"),
            self.judgment("Brand Potential", "74", ("E005",), "High"),
            self.judgment("Content Potential", "75", ("E006",), "High"),
            self.judgment("Risk & Compliance", "76", ("E007",), "High"),
        )

    def all_results(self):
        return {
            "market_demand": self.market_result("E001"),
            "competition": self.competition_result((self.competition_finding("MARKET_STRUCTURE", "E002"),)),
            "voc": self.voc_result((self.voc_finding("E003"),)),
            "supply_chain": self.supply_result((self.supply_finding("E004"),)),
            "brand_content": self.brand_result((
                self.brand_finding("BRAND_POTENTIAL", "E005"),
                self.brand_finding("CONTENT_POTENTIAL", "E006"),
            )),
            "risk_compliance": self.risk_result((self.risk_finding("E007"),)),
        }

    def test_exact_ownership_routes_all_seven_qualitative_dimensions(self):
        result = self.evaluate(judgments=self.all_judgments(), economics=self.economics_result(), **self.all_results())
        self.assertEqual(
            tuple(slot.score for slot in self.score.iter_dimension_scores(result)),
            (Decimal("70"), Decimal("71"), Decimal("50"), Decimal("72"), Decimal("73"), Decimal("74"), Decimal("75"), Decimal("76")),
        )

    def test_unrelated_excluded_unknown_and_cross_dimension_ids_are_not_traceable(self):
        results = self.all_results()
        invalid = (
            self.judgment("Brand Potential", evidence_ids=("E006",)),
            self.judgment("Competition", evidence_ids=("E001",)),
        )
        results["market_demand"] = self.market_result("E001", excluded_ids=("E099",))
        invalid += (self.judgment("Market Demand", evidence_ids=("E099",)),)
        results["voc"] = self.voc_result((self.voc_finding("E003", outcome="UNKNOWN"),))
        invalid += (self.judgment("Pain Points & Differentiation", evidence_ids=("E003",)),)
        result = self.evaluate(judgments=invalid, **results)
        self.assertIsNone(result.market_demand.score)
        self.assertIsNone(result.competition.score)
        self.assertIsNone(result.pain_points_differentiation.score)
        self.assertIsNone(result.brand_potential.score)

    def test_duplicate_judgments_are_unresolved_only_for_their_owned_dimension(self):
        results = self.all_results()
        judgments = self.all_judgments() + (self.judgment("Brand Potential", "90", ("E005",)),)
        result = self.evaluate(judgments=judgments, **results)
        self.assertIsNone(result.brand_potential.score)
        self.assertEqual(result.content_potential.score, Decimal("75"))
        self.assertEqual(result.market_demand.score, Decimal("70"))

    def test_malformed_top_level_collection_withholds_all_qualitative_slots_not_economics(self):
        result = self.evaluate(
            judgments="not-a-collection",
            economics=self.economics_result(),
            **self.all_results(),
        )
        self.assertEqual(tuple(slot.score for slot in self.score.iter_dimension_scores(result)[:2]), (None, None))
        self.assertEqual(result.price_profitability.score, Decimal("50"))

    def test_prerequisites_and_nested_uncertainty_fail_closed(self):
        result = self.evaluate(
            judgments=(
                self.judgment("Market Demand", evidence_ids=("E001",)),
                self.judgment("Competition", evidence_ids=("E002",)),
                self.judgment("Supply Chain & Fulfillment", evidence_ids=("E004",)),
                self.judgment("Risk & Compliance", evidence_ids=("E007",)),
            ),
            market_demand=self.market_result("E001", conclusion="UNKNOWN"),
            competition=self.competition_result((self.competition_finding("POSITIONING", "E002"),), adequacy="LIMITED"),
            supply_chain=self.supply_result((self.supply_finding(
                "E004",
                assessment=self.assessment_result("E004", factors=("CRITICAL_INFORMATION_MISSING",)),
            ),)),
            risk_compliance=self.risk_result((self.risk_finding("E007"),), complete=False),
        )
        self.assertIsNone(result.market_demand.score)
        self.assertIsNone(result.competition.score)
        self.assertIsNone(result.supply_chain_fulfillment.score)
        self.assertIsNone(result.risk_compliance.score)

    def test_confidence_ceiling_rejects_inflation_and_preserves_lower_declared_confidence(self):
        low_market = self.market_result("E001", confidence="Low")
        high_claim = self.judgment("Market Demand", "70", ("E001",), "Medium")
        low_claim = self.judgment("Market Demand", "70", ("E001",), "Low")
        self.assertIsNone(self.evaluate(judgments=(high_claim,), market_demand=low_market).market_demand.score)
        accepted = self.evaluate(judgments=(low_claim,), market_demand=low_market)
        self.assertEqual(accepted.market_demand.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(accepted.market_demand.score, Decimal("70"))

    def test_relevant_ids_may_span_sources_and_confidence_uses_the_weakest_source(self):
        results = self.all_results()
        results["competition"] = self.competition_result((
            self.competition_finding("POSITIONING", "E008", confidence="Low"),
        ))
        medium_claim = self.judgment(
            "Pain Points & Differentiation", "72", ("E003", "E008"), "Medium"
        )
        low_claim = self.judgment(
            "Pain Points & Differentiation", "72", ("E003", "E008"), "Low"
        )
        self.assertIsNone(
            self.evaluate(
                judgments=(medium_claim,),
                voc=results["voc"],
                competition=results["competition"],
            ).pain_points_differentiation.score
        )
        accepted = self.evaluate(
            judgments=(low_claim,),
            voc=results["voc"],
            competition=results["competition"],
        )
        self.assertEqual(accepted.pain_points_differentiation.score, Decimal("72"))

    def test_malformed_single_judgment_and_owned_result_fail_closed_without_erasing_independent_slots(self):
        valid_judgment = self.judgment("Brand Potential", "74", ("E005",), "High")
        malformed_judgment = self.judgment("Market Demand", "70", ("E001",), "High")
        object.__setattr__(malformed_judgment, "score", "70")
        malformed_market = self.market_result("E001")
        object.__setattr__(malformed_market, "conclusion", None)
        result = self.evaluate(
            judgments=(malformed_judgment, valid_judgment),
            market_demand=malformed_market,
            brand_content=self.brand_result((self.brand_finding("BRAND_POTENTIAL", "E005"),)),
            economics=self.economics_result(),
        )
        self.assertIsNone(result.market_demand.score)
        self.assertEqual(result.brand_potential.score, Decimal("74"))
        self.assertEqual(result.price_profitability.score, Decimal("50"))

    def test_malformed_confidence_values_fail_closed_without_leaking_exceptions(self):
        malformed_judgment = self.judgment("Market Demand", "70", ("E001",), "High")
        object.__setattr__(malformed_judgment.confidence, "_value", "BROKEN")
        result = self.evaluate(
            judgments=(malformed_judgment,),
            market_demand=self.market_result("E001"),
        )
        self.assertIsNone(result.market_demand.score)
        self.assertEqual(result.market_demand.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.market_demand.evidence_ids, ())

        malformed_market = self.market_result("E001")
        object.__setattr__(malformed_market.confidence, "_value", "BROKEN")
        result = self.evaluate(
            judgments=(self.judgment("Market Demand", evidence_ids=("E001",)),),
            market_demand=malformed_market,
        )
        self.assertIsNone(result.market_demand.score)
        self.assertEqual(result.market_demand.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.market_demand.evidence_ids, ())

    def test_materially_unresolved_relevant_source_blocks_shared_evidence_id(self):
        competition = self.competition_result((
            self.competition_finding(
                "POSITIONING",
                "E003",
                assessment=self.assessment_result(
                    "E003",
                    factors=("MATERIAL_INFORMATION_MISSING",),
                ),
            ),
        ))
        result = self.evaluate(
            judgments=(self.judgment("Pain Points & Differentiation", evidence_ids=("E003",)),),
            voc=self.voc_result((self.voc_finding("E003"),)),
            competition=competition,
        )
        self.assertIsNone(result.pain_points_differentiation.score)
        self.assertEqual(result.pain_points_differentiation.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.pain_points_differentiation.evidence_ids, ())

    def test_repeated_evaluation_is_replay_stable(self):
        arguments = dict(
            judgments=self.all_judgments(),
            economics=self.economics_result(),
            **self.all_results(),
        )
        first = self.evaluate(**arguments)
        second = self.evaluate(**arguments)
        self.assertEqual(first, second)
        self.assertEqual(
            tuple(
                (slot.score, slot.confidence, slot.evidence_ids)
                for slot in self.score.iter_dimension_scores(first)
            ),
            tuple(
                (slot.score, slot.confidence, slot.evidence_ids)
                for slot in self.score.iter_dimension_scores(second)
            ),
        )

    def test_finding_must_be_declared_supported_by_its_own_result_coverage(self):
        voc = self.voc_result((self.voc_finding("E003"),))
        object.__setattr__(voc, "supported_categories", ())
        object.__setattr__(voc, "missing_categories", tuple(
            self.voc.VOCCategory(value)
            for value in (
                "PURCHASE_MOTIVATION",
                "PAIN_POINT",
                "COMPLAINT",
                "UNMET_NEED",
                "USE_CASE",
                "PURCHASE_BARRIER",
                "CUSTOMER_LANGUAGE",
                "SEGMENT",
            )
        ))
        risk = self.risk_result((self.risk_finding("E007"),))
        object.__setattr__(risk, "supported_required_areas", ())
        object.__setattr__(risk, "missing_required_areas", (self.risk.RiskArea("REGULATION"),))
        result = self.evaluate(
            judgments=(
                self.judgment("Pain Points & Differentiation", evidence_ids=("E003",)),
                self.judgment("Risk & Compliance", evidence_ids=("E007",)),
            ),
            voc=voc,
            risk_compliance=risk,
        )
        self.assertIsNone(result.pain_points_differentiation.score)
        self.assertIsNone(result.risk_compliance.score)


class InitialScoringProfitabilityTests(InitialScoringTestBase):
    def score_for(self, economics):
        return self.evaluate(economics=economics).price_profitability

    def test_valid_economics_input_is_unchanged_after_scoring(self):
        economics = self.economics_result()
        original = economics
        self.score_for(economics)
        self.assertEqual(economics, original)
        self.assertEqual(economics.contribution_margin.evidence_ids, (self.eid("E900"),))

    def test_profitability_rubric_boundaries_midpoint_and_clamping(self):
        cases = (
            (Decimal("0.20"), Decimal("0")),
            (Decimal("0.50"), Decimal("50")),
            (Decimal("0.80"), Decimal("100")),
            (Decimal("0.10"), Decimal("0")),
            (Decimal("0.90"), Decimal("100")),
        )
        for margin, expected in cases:
            with self.subTest(margin=margin):
                self.assertEqual(self.score_for(self.economics_result(margin=margin)).score, expected)

    def test_profitability_uses_fresh_34_digit_decimal_context_without_quantizing(self):
        economics = self.economics_result(margin=Decimal("0.3333333333333333333333333333333333"))
        with decimal.localcontext() as context:
            context.prec = 3
            context.rounding = decimal.ROUND_UP
            first = self.score_for(economics).score
        with decimal.localcontext() as context:
            context.prec = 60
            context.rounding = decimal.ROUND_DOWN
            second = self.score_for(economics).score
        self.assertEqual(first, second)
        self.assertEqual(first, Decimal("22.22222222222222222222222222222222"))

    def test_profitability_leaves_process_global_decimal_context_unchanged(self):
        with decimal.localcontext() as context:
            context.prec = 17
            context.rounding = decimal.ROUND_FLOOR
            before = context.copy()
            self.score_for(self.economics_result(
                margin=Decimal("0.3333333333333333333333333333333333"),
            ))
            after = decimal.getcontext()
            self.assertEqual(after.prec, before.prec)
            self.assertEqual(after.rounding, before.rounding)

    def test_profitability_requires_coherent_retained_economics_and_traceability(self):
        invalid = (
            self.economics_result(dynamic=Decimal("0.20")),
            self.economics_result(outcome="UNRESOLVED"),
            self.economics_result(contribution_ids=()),
            self.economics_result(evidence_ids=("E900",), contribution_ids=("E901",)),
            self.economics_result(minimum_actual=Decimal("0.40")),
            self.economics_result(dynamic_actual=Decimal("0.40")),
        )
        for economics in invalid:
            with self.subTest(economics=economics):
                slot = self.score_for(economics)
                self.assertIsNone(slot.score)
                self.assertEqual(slot.confidence, self.evidence.Confidence("Low"))
                self.assertEqual(slot.evidence_ids, ())

    def test_profitability_does_not_use_qualitative_fallback_or_gate_label_alone(self):
        known_ids = (self.eid("E900"),)
        economics = self.economics_result()
        economics = self.economics.UnitEconomicsResult(
            contribution_profit=economics.contribution_profit,
            contribution_margin=self.economics.ContributionMargin(
                None,
                self.economics.Status("Unknown"),
                self.evidence.Confidence("High"),
                known_ids,
            ),
            minimum_viability_gate=self.economics.GateResult(
                self.economics.GateOutcome("UNRESOLVED"), None, None, ()
            ),
            dynamic_target_gate=self.economics.GateResult(
                self.economics.GateOutcome("UNRESOLVED"), None, None, ()
            ),
            outcome=self.economics.EconomicsOutcome("MEETS_TARGET"),
            unresolved_inputs=(),
            evidence_ids=known_ids,
            reasons=(),
        )
        result = self.evaluate(
            judgments=(self.judgment("Market Demand", evidence_ids=("E001",)),),
            market_demand=self.market_result("E001"),
            economics=economics,
        )
        self.assertIsNone(result.price_profitability.score)
        self.assertEqual(result.market_demand.score, Decimal("70"))

    def test_malformed_economics_result_is_unresolved_without_an_exception(self):
        economics = self.economics_result()
        object.__setattr__(economics, "outcome", None)
        result = self.evaluate(economics=economics)
        self.assertIsNone(result.price_profitability.score)
        self.assertEqual(result.price_profitability.confidence, self.evidence.Confidence("Low"))


if __name__ == "__main__":
    unittest.main()
