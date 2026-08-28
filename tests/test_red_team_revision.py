import ast
import dataclasses
import importlib
import unittest
from pathlib import Path
from decimal import Decimal


DIMENSION_FIELDS = (
    "market_demand",
    "competition",
    "price_profitability",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)


class _ForgedPayload:
    """Invalid non-string payload that compares like one valid closed value."""

    def __init__(self, equal_value):
        self.equal_value = equal_value

    def __hash__(self):
        return hash(self.equal_value)

    def __eq__(self, other):
        if type(other) is str:
            return other == self.equal_value
        return NotImplemented


def _module():
    return importlib.import_module("product_research.red_team_revision")


class RedTeamRevisionTestBase(unittest.TestCase):
    def setUp(self):
        self.m = _module()
        self.e = importlib.import_module("product_research.evidence")
        self.sd = importlib.import_module("product_research.scoring_decision")
        self.risk = importlib.import_module("product_research.risk_compliance")
        self.economics = importlib.import_module("product_research.unit_economics")

    def eid(self, value):
        return self.e.EvidenceId(value)

    def ids(self, *values):
        return tuple(self.eid(value) for value in values)

    def forged_value(self, value_type, value):
        forged = object.__new__(value_type)
        object.__setattr__(forged, "_value", value)
        return forged

    def forged_dataclass(self, value, **overrides):
        forged = object.__new__(type(value))
        for field in dataclasses.fields(value):
            replacement = overrides[field.name] if field.name in overrides else getattr(value, field.name)
            object.__setattr__(forged, field.name, replacement)
        return forged

    def forged_eid(self, equal_value):
        return self.forged_value(self.e.EvidenceId, _ForgedPayload(equal_value))

    def score(self, value=Decimal("70"), confidence="Medium", evidence_ids=("E001",)):
        return self.sd.DimensionScore(
            score=value,
            confidence=self.e.Confidence(confidence),
            evidence_ids=self.ids(*evidence_ids),
        )

    def unresolved(self):
        return self.sd.DimensionScore(None, self.e.Confidence("Low"), ())

    def scores(self, overrides=None):
        values = {
            field: self.score(evidence_ids=(f"E{index:03d}",))
            for index, field in enumerate(DIMENSION_FIELDS, 1)
        }
        values.update(overrides or {})
        return self.sd.DimensionScores(**values)

    def risk_result(self, gate="CLEAR"):
        return self.risk.RiskComplianceResult(
            required_areas=(),
            supported_required_areas=(),
            unresolved_required_areas=(),
            missing_required_areas=(),
            findings=(),
            duplicate_proposition_keys=(),
            risk_gate=self.risk.RiskGateState(gate),
            diagnostics=(),
        )

    def risk_finding(self):
        return self.risk.RiskFinding(
            area=self.risk.RiskArea("REGULATION"),
            proposition="regulatory claim",
            outcome=self.risk.RiskFindingOutcome("SUPPORTED"),
            supported_classification=self.risk.RiskClassification("NORMAL"),
            confidence=self.e.Confidence("High"),
            supporting_ids=self.ids("E101"),
            adverse_ids=(),
            excluded_ids=(),
            assessment=self.risk._empty_assessment(),
            diagnostics=(),
        )

    def risk_result_with_finding(self, finding, gate="CLEAR"):
        area = finding.area
        return self.risk.RiskComplianceResult(
            required_areas=(area,),
            supported_required_areas=(area,),
            unresolved_required_areas=(),
            missing_required_areas=(),
            findings=(finding,),
            duplicate_proposition_keys=(),
            risk_gate=self.risk.RiskGateState(gate),
            diagnostics=(),
        )

    def economics_result(self, minimum=Decimal("0.20"), dynamic=Decimal("0.40"), outcome="MEETS_TARGET"):
        status = self.economics.Status("Calculated")
        confidence = self.economics.Confidence("High")
        ids = self.ids("E900")
        profit = self.economics.ContributionProfit(
            Decimal("40"), "USD", status, confidence, ids
        )
        margin = self.economics.ContributionMargin(
            Decimal("0.40"), status, confidence, ids
        )
        minimum_gate = self.economics.GateResult(
            self.economics.GateOutcome("PASS" if minimum is not None else "UNRESOLVED"),
            Decimal("0.40") if minimum is not None else None,
            minimum,
            (),
        )
        dynamic_gate = self.economics.GateResult(
            self.economics.GateOutcome("PASS" if dynamic is not None else "UNRESOLVED"),
            Decimal("0.40") if dynamic is not None else None,
            dynamic,
            (),
        )
        return self.economics.UnitEconomicsResult(
            contribution_profit=profit,
            contribution_margin=margin,
            minimum_viability_gate=minimum_gate,
            dynamic_target_gate=dynamic_gate,
            outcome=self.economics.EconomicsOutcome(outcome),
            unresolved_inputs=(),
            evidence_ids=ids,
            reasons=(),
        )

    def evaluate(
        self,
        initial_scores=None,
        baseline=("E001",),
        red_team=("E101",),
        findings=(),
        score_proposals=(),
        risk_proposal=None,
        economics_proposal=None,
    ):
        return self.m.evaluate_red_team_revision(
            self.scores() if initial_scores is None else initial_scores,
            self.ids(*baseline),
            self.ids(*red_team),
            findings,
            score_proposals,
            risk_proposal,
            economics_proposal,
        )


class PublicValueContractTests(RedTeamRevisionTestBase):
    def test_public_values_are_frozen_and_have_no_runtime_metadata(self):
        finding = self.m.RedTeamFinding("challenge", self.ids("E101"))
        proposal = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Market Demand"),
            self.score(Decimal("60"), evidence_ids=("E101",)),
            "new evidence weakens demand",
            self.ids("E101"),
        )
        risk = self.m.RiskRevisionProposal(
            self.risk_result(), self.risk_result("REVIEW_REQUIRED"), "risk changed", self.ids("E101")
        )
        economics = self.m.EconomicsRevisionProposal(
            self.economics_result(),
            self.economics_result(outcome="BELOW_TARGET"),
            "economics changed",
            self.ids("E101"),
        )
        values = (
            finding,
            proposal,
            risk,
            economics,
            self.m.ScoreRevisionRecord(
                self.sd.Dimension("Market Demand"),
                self.score(),
                proposal.revised_score,
                proposal.reason,
                proposal.causal_evidence_ids,
            ),
            self.m.RiskGateRevisionRecord(
                risk.initial_result,
                risk.revised_result,
                risk.reason,
                risk.causal_evidence_ids,
            ),
            self.m.EconomicsGateRevisionRecord(
                economics.initial_result,
                economics.revised_result,
                economics.reason,
                economics.causal_evidence_ids,
            ),
            self.evaluate(),
        )
        for value in values:
            self.assertTrue(dataclasses.is_dataclass(value))
            for field in dataclasses.fields(value):
                with self.subTest(value=type(value).__name__, field=field.name):
                    with self.assertRaises(dataclasses.FrozenInstanceError):
                        setattr(value, field.name, None)
            self.assertNotIn("timestamp", {field.name for field in dataclasses.fields(value)})
            self.assertNotIn("id", {field.name for field in dataclasses.fields(value)})
            self.assertNotIn("run_id", {field.name for field in dataclasses.fields(value)})

    def test_public_values_reject_wrong_types_empty_text_and_noncanonical_ids(self):
        with self.assertRaises((TypeError, ValueError)):
            self.m.RedTeamFinding("", self.ids("E101"))
        with self.assertRaises((TypeError, ValueError)):
            self.m.RedTeamFinding("challenge", [self.eid("E101")])
        with self.assertRaises((TypeError, ValueError)):
            self.m.RedTeamFinding("challenge", self.ids("E102", "E101"))
        with self.assertRaises((TypeError, ValueError)):
            self.m.ScoreRevisionProposal(
                self.sd.Dimension("Market Demand"),
                self.score(),
                "",
                self.ids("E101"),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.m.ScoreRevisionProposal(
                self.sd.Dimension("Market Demand"),
                self.score(),
                "reason",
                self.ids("E101", "E101"),
            )

    def test_result_constructor_requires_deterministic_nested_record_order(self):
        first = self.m.RedTeamFinding("first", self.ids("E101"))
        second = self.m.RedTeamFinding("second", self.ids("E101"))
        with self.assertRaises((TypeError, ValueError)):
            self.m.RedTeamRevisionResult(
                self.scores(), self.scores(), (second, first), (), None, None
            )

    def test_no_change_retains_initial_and_builds_distinct_scorecard(self):
        initial = self.scores()
        result = self.evaluate(initial_scores=initial, red_team=())
        self.assertIs(result.initial_scores, initial)
        self.assertIs(type(result.revised_scores), self.sd.DimensionScores)
        self.assertIsNot(result.revised_scores, initial)
        self.assertEqual(result.revised_scores, initial)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.score_revisions, ())
        self.assertIsNone(result.risk_revision)
        self.assertIsNone(result.economics_revision)

    def test_whole_scorecard_replacement_is_not_a_public_input(self):
        self.assertFalse(hasattr(self.m, "RevisedDimensionScores"))
        result = self.evaluate(score_proposals=(self.scores(),))
        self.assertEqual(result.revised_scores, result.initial_scores)


class ProvenanceAndFindingTests(RedTeamRevisionTestBase):
    def test_canonical_disjoint_provenance_is_accepted_even_when_current_run_is_empty(self):
        result = self.evaluate(baseline=("E001", "E002"), red_team=())
        self.assertEqual(result.revised_scores, result.initial_scores)

    def test_malformed_provenance_fails_closed_without_reordering_or_deduplicating(self):
        initial = self.scores()
        cases = (
            ([self.eid("E001")], ()),
            ((self.eid("E002"), self.eid("E001")), ()),
            ((self.eid("E001"), self.eid("E001")), ()),
            ((self.eid("E001"),), (self.eid("E001"),)),
            (("E001",), ()),
        )
        for baseline, red_team in cases:
            with self.subTest(baseline=baseline, red_team=red_team):
                result = self.m.evaluate_red_team_revision(
                    initial, baseline, red_team, (), (), None, None
                )
                self.assertEqual(result.revised_scores, initial)
                self.assertEqual(result.findings, ())
                self.assertEqual(result.score_revisions, ())

    def test_forged_evidence_id_cannot_escape_fail_closed_provenance_or_finding_validation(self):
        forged_id = object.__new__(self.e.EvidenceId)
        finding = object.__new__(self.m.RedTeamFinding)
        object.__setattr__(finding, "text", "forged id")
        object.__setattr__(finding, "evidence_ids", (forged_id,))
        result = self.m.evaluate_red_team_revision(
            self.scores(), (self.eid("E001"),), (self.eid("E101"),), (finding,), ()
        )
        self.assertEqual(result.revised_scores, result.initial_scores)
        self.assertEqual(result.findings, ())

    def test_forged_evidence_id_payload_rejects_baseline_and_red_team_provenance(self):
        initial = self.scores()
        economics = self.economics_result(outcome="BELOW_TARGET")
        proposal = self.m.EconomicsRevisionProposal(
            self.economics_result(), economics, "economics changed", self.ids("E101")
        )
        cases = (
            (self.ids("E001"), (self.forged_eid("E101"),)),
            ((self.forged_eid("E001"),), self.ids("E101")),
        )
        for baseline, red_team in cases:
            with self.subTest(baseline=baseline, red_team=red_team):
                result = self.m.evaluate_red_team_revision(
                    initial,
                    baseline,
                    red_team,
                    (),
                    (),
                    None,
                    proposal,
                )
                self.assertEqual(result.revised_scores, initial)
                self.assertIsNone(result.economics_revision)

    def test_forged_finding_evidence_id_is_local_and_valid_finding_survives(self):
        forged = object.__new__(self.m.RedTeamFinding)
        object.__setattr__(forged, "text", "forged finding")
        object.__setattr__(forged, "evidence_ids", (self.forged_eid("E101"),))
        valid = self.m.RedTeamFinding("valid finding", self.ids("E101"))
        result = self.evaluate(findings=(forged, valid))
        self.assertEqual(result.findings, (valid,))

    def test_forged_score_proposal_causal_id_is_local_and_valid_target_survives(self):
        forged = object.__new__(self.m.ScoreRevisionProposal)
        object.__setattr__(forged, "dimension", self.sd.Dimension("Market Demand"))
        object.__setattr__(forged, "revised_score", self.score(Decimal("60"), evidence_ids=("E101",)))
        object.__setattr__(forged, "reason", "forged causal id")
        object.__setattr__(forged, "causal_evidence_ids", (self.forged_eid("E101"),))
        valid = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Competition"),
            self.score(Decimal("90"), evidence_ids=("E101",)),
            "valid independent revision",
            self.ids("E101"),
        )
        result = self.evaluate(score_proposals=(forged, valid))
        self.assertEqual(result.revised_scores.market_demand, result.initial_scores.market_demand)
        self.assertEqual(result.revised_scores.competition.score, Decimal("90"))

    def test_forged_concrete_score_trace_is_local_and_valid_target_survives(self):
        forged_score = object.__new__(self.sd.DimensionScore)
        object.__setattr__(forged_score, "score", Decimal("60"))
        object.__setattr__(forged_score, "confidence", self.e.Confidence("Medium"))
        object.__setattr__(forged_score, "evidence_ids", (self.forged_eid("E101"),))
        forged = object.__new__(self.m.ScoreRevisionProposal)
        object.__setattr__(forged, "dimension", self.sd.Dimension("Market Demand"))
        object.__setattr__(forged, "revised_score", forged_score)
        object.__setattr__(forged, "reason", "forged score trace")
        object.__setattr__(forged, "causal_evidence_ids", self.ids("E101"))
        valid = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Competition"),
            self.score(Decimal("90"), evidence_ids=("E101",)),
            "valid independent revision",
            self.ids("E101"),
        )
        result = self.evaluate(score_proposals=(forged, valid))
        self.assertEqual(result.revised_scores.market_demand, result.initial_scores.market_demand)
        self.assertEqual(result.revised_scores.competition.score, Decimal("90"))

    def test_invalid_initial_scorecard_is_rejected_not_fabricated(self):
        invalid_scorecard = object.__new__(self.sd.DimensionScores)
        object.__setattr__(invalid_scorecard, "market_demand", "invalid")
        for field in DIMENSION_FIELDS[1:]:
            object.__setattr__(invalid_scorecard, field, self.score())
        for invalid in (None, object(), invalid_scorecard):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises((TypeError, ValueError)):
                    self.m.evaluate_red_team_revision(
                        invalid, self.ids("E001"), self.ids("E101"), (), (), None, None
                    )

    def test_findings_require_declared_current_run_evidence(self):
        valid = self.m.RedTeamFinding("challenge", self.ids("E001", "E101"))
        cases = (
            valid,
            self.m.RedTeamFinding("baseline only", self.ids("E001")),
            self.m.RedTeamFinding("undeclared", self.ids("E999")),
        )
        result = self.evaluate(findings=cases)
        self.assertEqual(result.findings, (valid,))

    def test_duplicate_findings_are_rejected_without_erasing_independent_findings(self):
        duplicate = self.m.RedTeamFinding("same", self.ids("E101"))
        other = self.m.RedTeamFinding("other", self.ids("E101"))
        result = self.evaluate(findings=(duplicate, other, duplicate))
        self.assertEqual(result.findings, (other,))

    def test_finding_ordering_is_independent_of_caller_order(self):
        first = self.m.RedTeamFinding("alpha", self.ids("E101"))
        second = self.m.RedTeamFinding("beta", self.ids("E101", "E102"))
        left = self.evaluate(findings=(second, first), red_team=("E101", "E102"))
        right = self.evaluate(findings=(first, second), red_team=("E101", "E102"))
        self.assertEqual(left, right)
        self.assertEqual(left.findings, (first, second))

    def test_finding_with_unchanged_state_is_retained_without_fake_revision(self):
        finding = self.m.RedTeamFinding("challenge without state change", self.ids("E101"))
        result = self.evaluate(findings=(finding,))
        self.assertEqual(result.findings, (finding,))
        self.assertEqual(result.score_revisions, ())
        self.assertIsNone(result.risk_revision)
        self.assertIsNone(result.economics_revision)

    def test_malformed_top_level_collections_authorize_nothing(self):
        proposal = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Market Demand"),
            self.score(Decimal("60"), evidence_ids=("E101",)),
            "weakens demand",
            self.ids("E101"),
        )
        for field in ("findings", "score_proposals"):
            kwargs = {field: [proposal] if field == "score_proposals" else []}
            result = self.evaluate(**kwargs)
            self.assertEqual(result.revised_scores, result.initial_scores)
            self.assertEqual(result.findings, ())
            self.assertEqual(result.score_revisions, ())

    def test_invalid_finding_members_are_isolated_from_valid_members(self):
        valid = self.m.RedTeamFinding("valid", self.ids("E101"))
        forged = object.__new__(self.m.RedTeamFinding)
        object.__setattr__(forged, "text", "forged")
        object.__setattr__(forged, "evidence_ids", (self.eid("E999"),))
        result = self.evaluate(findings=(forged, valid, object()))
        self.assertEqual(result.findings, (valid,))


class ScoreRevisionBehaviorTests(RedTeamRevisionTestBase):
    def proposal(self, dimension="Market Demand", value=Decimal("60"), confidence="Medium", ids=("E101",), reason="revision"):
        return self.m.ScoreRevisionProposal(
            self.sd.Dimension(dimension),
            self.score(value, confidence, ids),
            reason,
            self.ids(*ids),
        )

    def test_downward_upward_and_confidence_only_revisions_are_recorded(self):
        initial = self.scores({"market_demand": self.score(Decimal("70"), "Medium")})
        downward = self.proposal(value=Decimal("60"), reason="downward")
        upward = self.proposal(
            dimension="Competition", value=Decimal("90"), reason="upward disproves concern"
        )
        confidence_only = self.proposal(
            dimension="Brand Potential",
            value=Decimal("70"),
            confidence="High",
            ids=("E101", "E102"),
            reason="confidence improves",
        )
        result = self.evaluate(
            initial_scores=initial,
            red_team=("E101", "E102"),
            score_proposals=(confidence_only, upward, downward),
        )
        self.assertEqual(
            tuple(record.dimension.value for record in result.score_revisions),
            ("Market Demand", "Competition", "Brand Potential"),
        )
        self.assertEqual(result.revised_scores.market_demand.score, Decimal("60"))
        self.assertEqual(result.revised_scores.competition.score, Decimal("90"))
        self.assertEqual(result.revised_scores.brand_potential.confidence.value, "High")
        for record in result.score_revisions:
            self.assertIsNotNone(record.initial_score)
            self.assertIsNotNone(record.revised_score)
            self.assertNotEqual(record.initial_score, record.revised_score)
            self.assertTrue(record.reason)
            self.assertTrue(record.causal_evidence_ids)

    def test_revision_requires_current_run_causal_evidence_and_reason(self):
        cases = (
            self.proposal(ids=("E001",), reason="baseline only"),
            self.proposal(ids=("E999",), reason="undeclared"),
        )
        result = self.evaluate(score_proposals=cases)
        self.assertEqual(result.revised_scores, result.initial_scores)
        self.assertEqual(result.score_revisions, ())
        no_new_evidence = self.evaluate(
            red_team=(),
            score_proposals=(self.proposal(ids=("E001",), reason="empty current run"),),
        )
        self.assertEqual(no_new_evidence.revised_scores, no_new_evidence.initial_scores)

        with self.assertRaises((TypeError, ValueError)):
            self.proposal(reason="")

    def test_same_score_and_confidence_with_new_score_ids_is_evidence_only(self):
        proposal = self.proposal(value=Decimal("70"), confidence="Medium", ids=("E101",))
        initial = self.scores({"market_demand": self.score(Decimal("70"), "Medium")})
        result = self.evaluate(initial_scores=initial, score_proposals=(proposal,))
        self.assertEqual(result.revised_scores.market_demand, initial.market_demand)
        self.assertEqual(result.score_revisions, ())

    def test_concrete_revisions_must_share_current_run_id_with_score_trace(self):
        proposal = self.proposal(value=Decimal("60"), ids=("E101",))
        proposal_without_grounding = self.m.ScoreRevisionProposal(
            proposal.dimension,
            self.score(Decimal("60"), evidence_ids=("E001",)),
            proposal.reason,
            proposal.causal_evidence_ids,
        )
        result = self.evaluate(score_proposals=(proposal_without_grounding,))
        self.assertEqual(result.revised_scores, result.initial_scores)

    def test_unresolved_to_concrete_and_concrete_to_unresolved_are_canonical(self):
        initial = self.scores({"market_demand": self.unresolved()})
        to_concrete = self.proposal(value=Decimal("60"), ids=("E101",))
        result = self.evaluate(initial_scores=initial, score_proposals=(to_concrete,))
        self.assertEqual(result.revised_scores.market_demand.score, Decimal("60"))

        concrete_initial = self.scores({"market_demand": self.score(Decimal("70"))})
        to_unresolved = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Market Demand"),
            self.unresolved(),
            "adverse evidence invalidates conclusion",
            self.ids("E101"),
        )
        result = self.evaluate(initial_scores=concrete_initial, score_proposals=(to_unresolved,))
        self.assertIsNone(result.revised_scores.market_demand.score)
        self.assertEqual(result.revised_scores.market_demand.confidence.value, "Low")
        self.assertEqual(result.revised_scores.market_demand.evidence_ids, ())
        self.assertEqual(result.score_revisions[0].causal_evidence_ids, self.ids("E101"))

    def test_noncanonical_unresolved_proposal_shapes_are_rejected(self):
        for confidence, evidence_ids in (
            ("High", ()),
            ("Low", ("E101",)),
            ("Medium", ("E101",)),
        ):
            with self.subTest(confidence=confidence, evidence_ids=evidence_ids):
                proposal = self.m.ScoreRevisionProposal(
                    self.sd.Dimension("Market Demand"),
                    self.sd.DimensionScore(
                        None, self.e.Confidence(confidence), self.ids(*evidence_ids)
                    ),
                    "adverse evidence",
                    self.ids("E101"),
                )
                result = self.evaluate(score_proposals=(proposal,))
                self.assertEqual(result.revised_scores, result.initial_scores)
                self.assertEqual(result.score_revisions, ())

    def test_duplicate_targets_reject_all_proposals_without_winner_selection(self):
        first = self.proposal(value=Decimal("60"), reason="first")
        second = self.proposal(value=Decimal("90"), reason="second")
        result = self.evaluate(score_proposals=(second, first))
        self.assertEqual(result.revised_scores, result.initial_scores)
        self.assertEqual(result.score_revisions, ())

    def test_invalid_target_is_local_and_independent_target_still_revises(self):
        valid = self.proposal(dimension="Competition", value=Decimal("90"))
        forged = object.__new__(self.m.ScoreRevisionProposal)
        object.__setattr__(forged, "dimension", self.sd.Dimension("Market Demand"))
        object.__setattr__(forged, "revised_score", self.score(Decimal("60"), evidence_ids=("E101",)))
        object.__setattr__(forged, "reason", "forged")
        object.__setattr__(forged, "causal_evidence_ids", self.ids("E101"))
        duplicate = self.proposal(dimension="Market Demand", value=Decimal("50"))
        result = self.evaluate(score_proposals=(forged, duplicate, valid))
        self.assertEqual(result.revised_scores.market_demand, result.initial_scores.market_demand)
        self.assertEqual(result.revised_scores.competition.score, Decimal("90"))

    def test_forged_invalid_proposal_for_one_target_does_not_block_another_target(self):
        forged_score = object.__new__(self.sd.DimensionScore)
        object.__setattr__(forged_score, "score", None)
        object.__setattr__(forged_score, "confidence", self.e.Confidence("High"))
        object.__setattr__(forged_score, "evidence_ids", ())
        forged = object.__new__(self.m.ScoreRevisionProposal)
        object.__setattr__(forged, "dimension", self.sd.Dimension("Market Demand"))
        object.__setattr__(forged, "revised_score", forged_score)
        object.__setattr__(forged, "reason", "forged unresolved")
        object.__setattr__(forged, "causal_evidence_ids", self.ids("E101"))
        valid = self.proposal(dimension="Competition", value=Decimal("90"))
        result = self.evaluate(score_proposals=(forged, valid))
        self.assertEqual(result.revised_scores.market_demand, result.initial_scores.market_demand)
        self.assertEqual(result.revised_scores.competition.score, Decimal("90"))

    def test_forged_empty_causal_trace_cannot_authorize_a_score_revision(self):
        forged = object.__new__(self.m.ScoreRevisionProposal)
        object.__setattr__(forged, "dimension", self.sd.Dimension("Market Demand"))
        object.__setattr__(forged, "revised_score", self.score(Decimal("60"), evidence_ids=("E101",)))
        object.__setattr__(forged, "reason", "missing trace")
        object.__setattr__(forged, "causal_evidence_ids", ())
        result = self.evaluate(score_proposals=(forged,))
        self.assertEqual(result.revised_scores, result.initial_scores)

    def test_reordering_and_replay_are_equal_and_unchanged_slots_are_exact(self):
        initial = self.scores()
        proposals = (
            self.proposal("Content Potential", Decimal("90")),
            self.proposal("Market Demand", Decimal("60")),
        )
        left = self.evaluate(initial_scores=initial, score_proposals=proposals)
        right = self.evaluate(initial_scores=initial, score_proposals=tuple(reversed(proposals)))
        self.assertEqual(left, right)
        for field in DIMENSION_FIELDS:
            if field not in ("content_potential", "market_demand"):
                self.assertIs(getattr(left.revised_scores, field), getattr(initial, field))


class AuthoritativeGateTests(RedTeamRevisionTestBase):
    def test_risk_revision_requires_complete_authoritative_results_and_new_evidence(self):
        proposal = self.m.RiskRevisionProposal(
            self.risk_result("CLEAR"),
            self.risk_result("REVIEW_REQUIRED"),
            "new risk evidence changes gate",
            self.ids("E101"),
        )
        result = self.evaluate(risk_proposal=proposal)
        self.assertIsInstance(result.risk_revision, self.m.RiskGateRevisionRecord)
        self.assertEqual(result.risk_revision.initial_result.risk_gate.value, "CLEAR")
        self.assertEqual(result.risk_revision.revised_result.risk_gate.value, "REVIEW_REQUIRED")

        baseline_only = self.m.RiskRevisionProposal(
            proposal.initial_result,
            proposal.revised_result,
            proposal.reason,
            self.ids("E001"),
        )
        self.assertIsNone(self.evaluate(risk_proposal=baseline_only).risk_revision)

    def test_raw_risk_gate_and_malformed_authoritative_result_are_rejected(self):
        raw = self.risk.RiskGateState("REVIEW_REQUIRED")
        result = self.evaluate(risk_proposal=raw)
        self.assertIsNone(result.risk_revision)
        forged_gate = object.__new__(self.risk.RiskGateState)
        object.__setattr__(forged_gate, "_value", "INVALID")
        forged = object.__new__(self.risk.RiskComplianceResult)
        for field in (
            "required_areas",
            "supported_required_areas",
            "unresolved_required_areas",
            "missing_required_areas",
            "findings",
            "duplicate_proposition_keys",
            "diagnostics",
        ):
            object.__setattr__(forged, field, ())
        object.__setattr__(forged, "risk_gate", forged_gate)
        forged_proposal = self.m.RiskRevisionProposal(
            self.risk_result(), forged, "forged result", self.ids("E101")
        )
        self.assertIsNone(self.evaluate(risk_proposal=forged_proposal).risk_revision)

    def test_risk_change_requires_declared_current_run_causal_ids(self):
        proposal = self.m.RiskRevisionProposal(
            self.risk_result(),
            self.risk_result("REVIEW_REQUIRED"),
            "changed",
            self.ids("E001"),
        )
        self.assertIsNone(self.evaluate(risk_proposal=proposal).risk_revision)
        forged = object.__new__(self.m.RiskRevisionProposal)
        object.__setattr__(forged, "initial_result", proposal.initial_result)
        object.__setattr__(forged, "revised_result", proposal.revised_result)
        object.__setattr__(forged, "reason", proposal.reason)
        object.__setattr__(forged, "causal_evidence_ids", ())
        self.assertIsNone(self.evaluate(risk_proposal=forged).risk_revision)

    def test_unchanged_risk_gate_has_no_fake_record_but_finding_survives(self):
        finding = self.m.RedTeamFinding("risk challenge", self.ids("E101"))
        proposal = self.m.RiskRevisionProposal(
            self.risk_result(), self.risk_result(), "unchanged", self.ids("E101")
        )
        result = self.evaluate(findings=(finding,), risk_proposal=proposal)
        self.assertEqual(result.findings, (finding,))
        self.assertIsNone(result.risk_revision)

    def test_forged_risk_closed_values_are_local_and_valid_score_survives(self):
        initial_finding = self.risk_finding()
        initial = self.risk_result_with_finding(initial_finding)
        valid_score = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Competition"),
            self.score(Decimal("90"), evidence_ids=("E101",)),
            "valid independent revision",
            self.ids("E101"),
        )
        cases = (
            self.forged_dataclass(
                initial_finding,
                outcome=self.forged_value(self.risk.RiskFindingOutcome, "INVALID"),
                supported_classification=None,
            ),
            self.forged_dataclass(
                initial_finding,
                supported_classification=self.forged_value(
                    self.risk.RiskClassification, "INVALID"
                ),
            ),
            self.forged_dataclass(
                initial_finding,
                area=self.forged_value(
                    self.risk.RiskArea, _ForgedPayload("REGULATION")
                ),
            ),
            self.forged_dataclass(
                initial_finding,
                supporting_ids=(self.forged_eid("E101"),),
            ),
        )
        for finding in cases:
            with self.subTest(finding=finding):
                revised = self.risk_result_with_finding(finding, gate="REVIEW_REQUIRED")
                proposal = self.m.RiskRevisionProposal(
                    initial,
                    revised,
                    "forged risk result",
                    self.ids("E101"),
                )
                result = self.evaluate(
                    score_proposals=(valid_score,), risk_proposal=proposal
                )
                self.assertIsNone(result.risk_revision)
                self.assertEqual(result.revised_scores.competition.score, Decimal("90"))
                self.assertEqual(result.revised_scores.risk_compliance, result.initial_scores.risk_compliance)

    def test_economics_revision_requires_equal_thresholds_and_authoritative_values(self):
        proposal = self.m.EconomicsRevisionProposal(
            self.economics_result(),
            self.economics_result(outcome="BELOW_TARGET"),
            "new economics evidence changes outcome",
            self.ids("E101"),
        )
        result = self.evaluate(economics_proposal=proposal)
        self.assertIsInstance(result.economics_revision, self.m.EconomicsGateRevisionRecord)
        self.assertEqual(result.economics_revision.revised_result.outcome.value, "BELOW_TARGET")

        threshold_changed = self.m.EconomicsRevisionProposal(
            proposal.initial_result,
            self.economics_result(minimum=Decimal("0.10"), outcome="BELOW_TARGET"),
            proposal.reason,
            proposal.causal_evidence_ids,
        )
        self.assertIsNone(self.evaluate(economics_proposal=threshold_changed).economics_revision)

        dynamic_threshold_changed = self.m.EconomicsRevisionProposal(
            proposal.initial_result,
            self.economics_result(dynamic=Decimal("0.30"), outcome="BELOW_TARGET"),
            proposal.reason,
            proposal.causal_evidence_ids,
        )
        self.assertIsNone(self.evaluate(economics_proposal=dynamic_threshold_changed).economics_revision)

    def test_economics_revision_ignores_non_state_result_changes_but_keeps_findings(self):
        initial = self.economics_result()
        changed_profit = dataclasses.replace(
            initial,
            contribution_profit=dataclasses.replace(
                initial.contribution_profit, amount=Decimal("41")
            ),
        )
        changed_margin = dataclasses.replace(
            initial,
            contribution_margin=dataclasses.replace(
                initial.contribution_margin, value=Decimal("0.41")
            ),
        )
        changed_actual_margin = dataclasses.replace(
            initial,
            minimum_viability_gate=dataclasses.replace(
                initial.minimum_viability_gate, actual_margin=Decimal("0.35")
            ),
        )
        changed_reasons = dataclasses.replace(
            initial,
            dynamic_target_gate=dataclasses.replace(
                initial.dynamic_target_gate,
                reasons=(self.economics.ReasonCode("CALCULATION_ERROR"),),
            ),
        )
        finding = self.m.RedTeamFinding("independent challenge", self.ids("E101"))
        for revised in (changed_profit, changed_margin, changed_actual_margin, changed_reasons):
            with self.subTest(revised=revised):
                proposal = self.m.EconomicsRevisionProposal(
                    initial, revised, "non-state economics change", self.ids("E101")
                )
                result = self.evaluate(findings=(finding,), economics_proposal=proposal)
                self.assertEqual(result.findings, (finding,))
                self.assertIsNone(result.economics_revision)

    def test_each_authoritative_economics_state_transition_is_accepted_whole(self):
        initial = self.economics_result()
        revised_results = (
            dataclasses.replace(
                initial,
                minimum_viability_gate=dataclasses.replace(
                    initial.minimum_viability_gate,
                    outcome=self.economics.GateOutcome("FAIL"),
                    actual_margin=Decimal("0.10"),
                ),
            ),
            dataclasses.replace(
                initial,
                dynamic_target_gate=dataclasses.replace(
                    initial.dynamic_target_gate,
                    outcome=self.economics.GateOutcome("FAIL"),
                    actual_margin=Decimal("0.30"),
                ),
            ),
            dataclasses.replace(
                initial,
                outcome=self.economics.EconomicsOutcome("BELOW_TARGET"),
            ),
        )
        for revised in revised_results:
            with self.subTest(revised=revised):
                reason = "authoritative economics state changed"
                causal_ids = self.ids("E101")
                proposal = self.m.EconomicsRevisionProposal(
                    initial, revised, reason, causal_ids
                )
                result = self.evaluate(economics_proposal=proposal)
                record = result.economics_revision
                self.assertIsInstance(record, self.m.EconomicsGateRevisionRecord)
                self.assertIs(record.initial_result, initial)
                self.assertIs(record.revised_result, revised)
                self.assertEqual(record.reason, reason)
                self.assertEqual(record.causal_evidence_ids, causal_ids)

    def test_economics_missing_to_concrete_threshold_change_is_rejected(self):
        initial = self.economics_result(minimum=None, dynamic=None, outcome="UNRESOLVED")
        revised = self.economics_result(outcome="MEETS_TARGET")
        proposal = self.m.EconomicsRevisionProposal(
            initial, revised, "policy changed", self.ids("E101")
        )
        self.assertIsNone(self.evaluate(economics_proposal=proposal).economics_revision)

    def test_raw_economics_overrides_and_forged_results_are_rejected(self):
        for raw in (
            self.economics.GateOutcome("PASS"),
            self.economics.EconomicsOutcome("BELOW_TARGET"),
            Decimal("0.20"),
        ):
            with self.subTest(raw=repr(raw)):
                result = self.evaluate(economics_proposal=raw)
                self.assertIsNone(result.economics_revision)
        forged_outcome = object.__new__(self.economics.EconomicsOutcome)
        object.__setattr__(forged_outcome, "_value", "INVALID")
        forged = object.__new__(self.economics.UnitEconomicsResult)
        real = self.economics_result()
        for field in (
            "contribution_profit",
            "contribution_margin",
            "minimum_viability_gate",
            "dynamic_target_gate",
            "unresolved_inputs",
            "evidence_ids",
            "reasons",
        ):
            object.__setattr__(forged, field, getattr(real, field))
        object.__setattr__(forged, "outcome", forged_outcome)
        forged_proposal = self.m.EconomicsRevisionProposal(
            real, forged, "forged economics result", self.ids("E101")
        )
        self.assertIsNone(self.evaluate(economics_proposal=forged_proposal).economics_revision)

    def test_forged_economics_closed_values_are_local_and_valid_score_survives(self):
        initial = self.economics_result()
        valid_score = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Competition"),
            self.score(Decimal("90"), evidence_ids=("E101",)),
            "valid independent revision",
            self.ids("E101"),
        )
        revised = self.economics_result(outcome="BELOW_TARGET")
        cases = []

        for field_name in ("minimum_viability_gate", "dynamic_target_gate"):
            gate = getattr(revised, field_name)
            forged_reason = self.forged_value(self.economics.ReasonCode, "INVALID")
            forged_gate = self.forged_dataclass(gate, reasons=(forged_reason,))
            cases.append(self.forged_dataclass(revised, **{field_name: forged_gate}))

        forged_gate_outcome = self.forged_value(self.economics.GateOutcome, "INVALID")
        cases.append(
            self.forged_dataclass(
                revised,
                minimum_viability_gate=self.forged_dataclass(
                    revised.minimum_viability_gate, outcome=forged_gate_outcome
                ),
            )
        )
        cases.append(
            self.forged_dataclass(
                revised,
                outcome=self.forged_value(self.economics.EconomicsOutcome, "INVALID"),
            )
        )
        cases.append(
            self.forged_dataclass(
                revised,
                contribution_profit=self.forged_dataclass(
                    revised.contribution_profit,
                    status=self.forged_value(self.economics.Status, "INVALID"),
                ),
            )
        )
        cases.append(
            self.forged_dataclass(
                revised,
                contribution_margin=self.forged_dataclass(
                    revised.contribution_margin,
                    confidence=self.forged_value(self.economics.Confidence, "INVALID"),
                ),
            )
        )

        for revised_with_forgery in cases:
            with self.subTest(revised=revised_with_forgery):
                proposal = self.m.EconomicsRevisionProposal(
                    initial,
                    revised_with_forgery,
                    "forged economics result",
                    self.ids("E101"),
                )
                result = self.evaluate(
                    score_proposals=(valid_score,), economics_proposal=proposal
                )
                self.assertIsNone(result.economics_revision)
                self.assertEqual(result.revised_scores.competition.score, Decimal("90"))

    def test_economics_change_requires_declared_current_run_causal_ids(self):
        proposal = self.m.EconomicsRevisionProposal(
            self.economics_result(),
            self.economics_result(outcome="BELOW_TARGET"),
            "changed",
            self.ids("E001"),
        )
        self.assertIsNone(self.evaluate(economics_proposal=proposal).economics_revision)

    def test_equal_none_thresholds_are_not_policy_mutation_by_themselves(self):
        initial = self.economics_result(minimum=None, dynamic=None, outcome="UNRESOLVED")
        revised = self.economics_result(minimum=None, dynamic=None, outcome="BELOW_TARGET")
        proposal = self.m.EconomicsRevisionProposal(
            initial, revised, "outcome changed", self.ids("E101")
        )
        self.assertIsNotNone(self.evaluate(economics_proposal=proposal).economics_revision)

    def test_unchanged_economics_state_has_no_fake_record_but_finding_survives(self):
        finding = self.m.RedTeamFinding("economics challenge", self.ids("E101"))
        result_value = self.economics_result()
        proposal = self.m.EconomicsRevisionProposal(
            result_value, result_value, "unchanged", self.ids("E101")
        )
        result = self.evaluate(findings=(finding,), economics_proposal=proposal)
        self.assertEqual(result.findings, (finding,))
        self.assertIsNone(result.economics_revision)


class ArchitectureAndCompatibilityTests(RedTeamRevisionTestBase):
    def test_revised_scores_are_directly_accepted_by_scoring_decision(self):
        proposal = self.m.ScoreRevisionProposal(
            self.sd.Dimension("Market Demand"),
            self.score(Decimal("90"), evidence_ids=("E101",)),
            "new evidence improves demand",
            self.ids("E101"),
        )
        result = self.evaluate(score_proposals=(proposal,))
        weights = self.sd.WeightAdjustments(*([Decimal("0")] * 8))
        decision = self.sd.evaluate_scoring_decision(
            result.revised_scores,
            weights,
            self.risk.RiskGateState("CLEAR"),
            self.economics_result(),
            self.sd.DecisionPolicy(Decimal("0")),
            required_research_ready=True,
        )
        self.assertIs(decision.scores, result.revised_scores)

    def test_module_has_only_local_domain_and_standard_library_imports(self):
        module_path = Path("product_research/red_team_revision.py")
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        forbidden = {"datetime", "random", "uuid", "requests", "urllib", "subprocess", "socket"}
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            for alias in node.names
        )
        self.assertTrue(imported.isdisjoint(forbidden))
        source = module_path.read_text(encoding="utf-8")
        for forbidden_name in ("requests", "urllib", "datetime", "random", "uuid", "evaluate_initial_scoring", "evaluate_scoring_decision"):
            self.assertNotIn(forbidden_name, source)


if __name__ == "__main__":
    unittest.main()
