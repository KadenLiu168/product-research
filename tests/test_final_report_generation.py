"""Contract tests for the downstream ECO-38 final report boundary."""

import ast
import dataclasses
import importlib
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock


class FinalReportTestBase(unittest.TestCase):
    def setUp(self):
        self.evidence = importlib.import_module("product_research.evidence")
        self.research = importlib.import_module("product_research.research_orchestration")
        self.workflow = importlib.import_module("product_research.end_to_end_workflow")
        self.risk = importlib.import_module("product_research.risk_compliance")
        self.risk_gate = importlib.import_module("product_research.risk_gate")
        self.economics = importlib.import_module("product_research.unit_economics")
        self.scoring = importlib.import_module("product_research.scoring_decision")
        self.red_team = importlib.import_module("product_research.red_team_revision")
        self.assessment = importlib.import_module("product_research.evidence_assessment")
        self.brand_content = importlib.import_module("product_research.brand_content")
        try:
            self.report = importlib.import_module("product_research.final_report_generation")
        except ModuleNotFoundError as exc:
            self.fail(
                "ECO-38 reporting capability is missing: "
                "product_research.final_report_generation"
            )

    def eid(self, value):
        return self.evidence.EvidenceId(value)

    def evidence_records(self):
        source = self.evidence.Source(
            "Example Source", "listing", "https://example.test/item", "Example"
        )
        return tuple(
            self.evidence.Evidence(
                self.eid(identifier),
                claim,
                content,
                source,
                "2026-08-14T08:30:00Z",
                self.evidence.Tier(tier),
                self.evidence.Status(status),
                self.evidence.Confidence(confidence),
                {},
            )
            for identifier, claim, content, tier, status, confidence in (
                ("E001", "Demand claim", "Observed demand", "Tier 1", "Observed", "High"),
                (
                    "E002",
                    "Adverse claim",
                    "Adverse\nvalue | Ω\x1b",
                    "Tier 3",
                    "Unknown",
                    "Low",
                ),
                ("E003", "Unreferenced claim", "Appendix only", "Tier 4", "Estimated", "Medium"),
            )
        )

    def research_run(self, evidence):
        objective = self.research.ResearchObjective("objective-01", "Assess the product.")
        task = self.research.ResearchTask(
            "task-01",
            "What is known?",
            self.research.SourceFamily("SEARCH"),
            "market demand",
            importlib.import_module("product_research.evidence_policy").EvidenceKind("market"),
            True,
        )
        plan = self.research.ResearchPlan(objective.objective_id, (task,))
        task_result = self.research.TaskResult(
            task,
            self.research.TaskStatus("SUCCESS"),
            ("finding-01", "finding-02", "finding-03"),
            tuple(value.id for value in evidence),
            (),
        )
        return self.research.ResearchRunResult(
            objective,
            plan,
            (task_result,),
            evidence,
            (),
            (task.task_id,),
            (task.task_id,),
            (),
            (),
            self.research.RunStatus("COMPLETE"),
        ), plan

    def scores(self, revised=False):
        score = self.scoring.DimensionScore(
            Decimal("80"), self.evidence.Confidence("High"), (self.eid("E001"),)
        )
        values = {field: score for field in (
            "market_demand",
            "competition",
            "price_profitability",
            "pain_points_differentiation",
            "supply_chain_fulfillment",
            "brand_potential",
            "content_potential",
            "risk_compliance",
        )}
        if revised:
            values["price_profitability"] = self.scoring.DimensionScore(
                Decimal("90"), self.evidence.Confidence("High"), (self.eid("E002"),)
            )
        return self.scoring.DimensionScores(**values)

    def economics_result(self, ids):
        status = self.economics.Status("Observed")
        confidence = self.economics.Confidence("High")
        def field(amount):
            return self.economics.EconomicInput(
                Decimal(amount), "USD", status, confidence, ids
            )

        inputs = self.economics.UnitEconomicsInputs(
            *(field(value) for value in ("100", "10", "10", "5", "5", "5", "10", "5"))
        )
        return self.economics.evaluate_unit_economics(
            inputs,
            self.economics.UnitEconomicsPolicy(Decimal("0.20"), Decimal("0.40")),
        )

    def complete_result(self):
        evidence = self.evidence_records()
        research_run, plan = self.research_run(evidence)
        risk = self.risk.RiskComplianceResult(
            (), (), (), (), (), (), self.risk_gate.RiskGateState("CLEAR"), ()
        )
        economics = self.economics_result((self.eid("E001"),))
        initial_scores = self.scores()
        revised_scores = self.scores(revised=True)
        finding = self.red_team.RedTeamFinding(
            "Adverse challenge\nwith | pipe and Ω\x1b", (self.eid("E002"),)
        )
        proposal = self.red_team.ScoreRevisionProposal(
            self.scoring.Dimension("Price & Profitability"),
            revised_scores.price_profitability,
            "Accepted after adverse evidence.",
            (self.eid("E002"),),
        )
        review = self.workflow.RedTeamReviewInputs(
            (self.eid("E001"),),
            (self.eid("E002"),),
            (finding,),
            (proposal,),
        )
        revision = self.red_team.evaluate_red_team_revision(
            initial_scores,
            review.baseline_evidence_ids,
            review.red_team_evidence_ids,
            review.findings,
            review.score_proposals,
        )
        decision = self.scoring.evaluate_scoring_decision(
            revised_scores,
            self.scoring.WeightAdjustments(*([Decimal("0")] * 8)),
            risk.risk_gate,
            economics,
            self.scoring.DecisionPolicy(Decimal("60")),
        )
        final_state = self.workflow.WorkflowFinalState(
            revised_scores, risk, economics, decision
        )
        outputs = {
            self.workflow.WorkflowStage.SUBJECT_VALIDATION: self.workflow.WorkflowSubject(
                "portable blender", "United States"
            ),
            self.workflow.WorkflowStage.RESEARCH_PLAN: plan,
            self.workflow.WorkflowStage.RESEARCH_EVIDENCE: research_run,
            self.workflow.WorkflowStage.RISK_COMPLIANCE: risk,
            self.workflow.WorkflowStage.UNIT_ECONOMICS: economics,
            self.workflow.WorkflowStage.INITIAL_SCORING: initial_scores,
            self.workflow.WorkflowStage.INITIAL_DECISION: decision,
            self.workflow.WorkflowStage.RED_TEAM_ROUTING: review,
            self.workflow.WorkflowStage.RED_TEAM_REVISION: revision,
            self.workflow.WorkflowStage.FINAL_DECISION: final_state,
        }
        records = tuple(
            self.workflow.WorkflowStageResult(
                stage,
                self.workflow.WorkflowStageStatus.COMPLETE,
                output=outputs.get(stage),
            )
            for stage in self.workflow.WorkflowStage
        )
        return self.workflow.EndToEndWorkflowResult(outputs[self.workflow.WorkflowStage.SUBJECT_VALIDATION], records)

    def incomplete_result(self, status):
        result = self.complete_result()
        records = list(result.stages)
        records[-1] = self.workflow.WorkflowStageResult(
            self.workflow.WorkflowStage.FINAL_DECISION,
            status,
            failure_kind=(
                self.workflow.WorkflowFailureKind.EXECUTION_ERROR
                if status is self.workflow.WorkflowStageStatus.FAILED
                else None
            ),
            blocked_by=(
                (self.workflow.WorkflowStage.RED_TEAM_REVISION,)
                if status is self.workflow.WorkflowStageStatus.BLOCKED
                else ()
            ),
        )
        return self.workflow.EndToEndWorkflowResult(result.subject, tuple(records))

    def empty_result(self):
        subject = self.workflow.WorkflowSubject("portable blender", "United States")
        records = tuple(
            self.workflow.WorkflowStageResult(
                stage,
                self.workflow.WorkflowStageStatus.COMPLETE
                if stage is self.workflow.WorkflowStage.SUBJECT_VALIDATION
                else self.workflow.WorkflowStageStatus.BLOCKED,
                output=subject if stage is self.workflow.WorkflowStage.SUBJECT_VALIDATION else None,
                blocked_by=()
                if stage is self.workflow.WorkflowStage.SUBJECT_VALIDATION
                else (self.workflow.WorkflowStage.SUBJECT_VALIDATION,),
            )
            for stage in self.workflow.WorkflowStage
        )
        return self.workflow.EndToEndWorkflowResult(subject, records)


class FinalReportContractTests(FinalReportTestBase):
    def test_complete_report_has_exact_canonical_sections_and_final_scorecard(self):
        report = self.report.render_final_report(self.complete_result())
        expected = [
            "Executive Summary", "Market Demand", "Competition", "Price & Profitability",
            "VOC & Differentiation", "Supply Chain & Fulfillment", "Brand Potential",
            "Content Potential", "Risk & Compliance", "Scorecard", "Key Evidence",
            "Key Uncertainties", "Red Team Findings", "Final Analysis Label", "Evidence Appendix",
        ]
        headings = [line[3:] for line in report.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [f"{index}. {title}" for index, title in enumerate(expected, 1)])
        self.assertEqual(report.count("| Price & Profitability |"), 1)
        self.assertIn("| Price & Profitability | 90", report)
        self.assertIn("Final Analysis Label: GO", report)
        self.assertIn("| Dimension | Score | Base Weight | Final Weight | Contribution | Confidence | Evidence IDs |", report)
        self.assertIn("| Price & Profitability | 90 | 20 | 20 | 18 | High | E002 |", report)
        self.assertIn("Confidence: High", report)
        self.assertIn("Evidence IDs: E002", report)
        self.assertIn("Aggregate: 82", report)

    def test_weighted_contribution_is_decimal_exact_and_never_creates_missing_aggregate(self):
        complete = self.complete_result()
        report = self.report.render_final_report(complete)
        self.assertIn("| Price & Profitability | 90 | 20 | 20 | 18 | High | E002 |", report)
        final_stage = complete.stage(self.workflow.WorkflowStage.FINAL_DECISION)
        missing_aggregate = dataclasses.replace(
            final_stage.output.decision, aggregate_score=None
        )
        missing_state = dataclasses.replace(final_stage.output, decision=missing_aggregate)
        missing = dataclasses.replace(complete, stages=(*complete.stages[:-1], dataclasses.replace(final_stage, output=missing_state)))
        missing_report = self.report.render_final_report(missing)
        self.assertIn("Aggregate: UNAVAILABLE", missing_report)
        self.assertNotIn("Aggregate: 82", missing_report)

        inconsistent = dataclasses.replace(final_stage.output.decision, aggregate_score=Decimal("81"))
        inconsistent_state = dataclasses.replace(final_stage.output, decision=inconsistent)
        invalid = dataclasses.replace(complete, stages=(*complete.stages[:-1], dataclasses.replace(final_stage, output=inconsistent_state)))
        with self.assertRaises(self.report.ReportInputError):
            self.report.render_final_report(invalid)

        unresolved_score = self.scoring.DimensionScore(
            None, self.evidence.Confidence("Low"), ()
        )
        partial_scores = dataclasses.replace(
            final_stage.output.scores, market_demand=unresolved_score
        )
        partial_decision = dataclasses.replace(
            final_stage.output.decision, scores=partial_scores
        )
        partial_state = dataclasses.replace(
            final_stage.output, scores=partial_scores, decision=partial_decision
        )
        partial = dataclasses.replace(
            complete,
            stages=(
                *complete.stages[:-1],
                dataclasses.replace(final_stage, output=partial_state),
            ),
        )
        with self.assertRaises(self.report.ReportInputError):
            self.report.render_final_report(partial)

    def test_evidence_projection_is_current_run_non_ranked_and_appendix_is_lossless(self):
        report = self.report.render_final_report(self.complete_result())
        key_section = report.split("## 12. Key Uncertainties", 1)[0].split("## 11. Key Evidence", 1)[1]
        self.assertIn("E001", key_section)
        self.assertIn("E002", key_section)
        self.assertNotIn("E003", key_section)
        self.assertNotIn("strongest", key_section.lower())
        appendix = report.split("## 15. Evidence Appendix", 1)[1]
        self.assertLess(appendix.index("E001"), appendix.index("E002"))
        self.assertLess(appendix.index("E002"), appendix.index("E003"))
        self.assertEqual(appendix.count("| E001 |"), 1)
        self.assertEqual(appendix.count("| E002 |"), 1)
        self.assertEqual(appendix.count("| E003 |"), 1)
        self.assertIn("Adverse\\nvalue \\| Ω\\x1b", appendix)

        final_stage = self.complete_result().stage(self.workflow.WorkflowStage.FINAL_DECISION)
        scores = dataclasses.replace(
            final_stage.output.scores,
            market_demand=self.scoring.DimensionScore(
                Decimal("80"), self.evidence.Confidence("High"), (self.eid("E999"),)
            ),
        )
        invalid_decision = dataclasses.replace(final_stage.output.decision, scores=scores)
        invalid_state = dataclasses.replace(final_stage.output, scores=scores, decision=invalid_decision)
        invalid = dataclasses.replace(
            self.complete_result(),
            stages=(*self.complete_result().stages[:-1], dataclasses.replace(final_stage, output=invalid_state)),
        )
        with self.assertRaises(self.report.EvidenceTraceabilityError):
            self.report.render_final_report(invalid)

    def test_accepted_red_team_finding_evidence_is_selected_and_validated(self):
        complete = self.complete_result()
        revision_stage = complete.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION)
        unique_finding = self.red_team.RedTeamFinding(
            "Unique accepted challenge", (self.eid("E003"),)
        )
        revision = dataclasses.replace(revision_stage.output, findings=(unique_finding,))
        with_unique_finding = dataclasses.replace(
            complete,
            stages=(
                *complete.stages[:-2],
                dataclasses.replace(revision_stage, output=revision),
                complete.stages[-1],
            ),
        )
        report = self.report.render_final_report(with_unique_finding)
        key_section = report.split("## 12. Key Uncertainties", 1)[0].split(
            "## 11. Key Evidence", 1
        )[1]
        self.assertIn("E003", key_section)

        foreign_finding = self.red_team.RedTeamFinding(
            "Foreign accepted challenge", (self.eid("E999"),)
        )
        foreign_revision = dataclasses.replace(
            revision_stage.output, findings=(foreign_finding,)
        )
        invalid = dataclasses.replace(
            complete,
            stages=(
                *complete.stages[:-2],
                dataclasses.replace(revision_stage, output=foreign_revision),
                complete.stages[-1],
            ),
        )
        with self.assertRaises(self.report.EvidenceTraceabilityError):
            self.report.render_final_report(invalid)

    def test_explicit_risk_and_economics_uncertainty_is_preserved(self):
        complete = self.complete_result()
        final_stage = complete.stage(self.workflow.WorkflowStage.FINAL_DECISION)
        unresolved_economics = self.economics.evaluate_unit_economics(None, None)
        unresolved_risk = dataclasses.replace(
            final_stage.output.risk_result,
            diagnostics=(self.risk.RiskAnalysisDiagnostic("MISSING_REQUIRED_AREA"),),
        )
        decision = dataclasses.replace(
            final_stage.output.decision,
            risk_gate=unresolved_risk.risk_gate,
            unit_economics=unresolved_economics,
        )
        final_state = dataclasses.replace(
            final_stage.output,
            risk_result=unresolved_risk,
            economics_result=unresolved_economics,
            decision=decision,
        )
        result = dataclasses.replace(
            complete,
            stages=(
                *complete.stages[:-1],
                dataclasses.replace(final_stage, output=final_state),
            ),
        )

        report = self.report.render_final_report(result)
        uncertainty = report.split("## 13. Red Team Findings", 1)[0].split(
            "## 12. Key Uncertainties", 1
        )[1]
        self.assertIn("MISSING_REQUIRED_AREA", uncertainty)
        self.assertIn("ECONOMICS_INPUT_ERROR", uncertainty)
        economics = report.split("## 5. VOC & Differentiation", 1)[0].split(
            "## 4. Price & Profitability", 1
        )[1]
        self.assertIn("- Reasons: ECONOMICS_INPUT_ERROR", economics)

    def test_final_risk_finding_preserves_full_authoritative_detail(self):
        complete = self.complete_result()
        final_stage = complete.stage(self.workflow.WorkflowStage.FINAL_DECISION)
        assessment = self.assessment.EvidenceAssessmentResult(
            outcome=self.assessment.AssessmentOutcome("SUPPORTED"),
            confidence=self.evidence.Confidence("High"),
            conflict_state=self.assessment.ConflictState("NONE"),
            source_count=1,
            independent_source_count=1,
            supporting_ids=(self.eid("E001"),),
            usable_ids=(self.eid("E001"),),
            excluded_ids=(self.eid("E003"),),
        )
        finding = self.risk.RiskFinding(
            area=self.risk.RiskArea("REGULATION"),
            proposition="Regulatory status is supported.",
            outcome=self.risk.RiskFindingOutcome("SUPPORTED"),
            supported_classification=self.risk.RiskClassification("NORMAL"),
            confidence=self.evidence.Confidence("High"),
            supporting_ids=(self.eid("E001"),),
            adverse_ids=(self.eid("E002"),),
            excluded_ids=(self.eid("E003"),),
            assessment=assessment,
            diagnostics=(self.risk.RiskAnalysisDiagnostic("ASSESSMENT_NOT_SUPPORTED"),),
        )
        area = self.risk.RiskArea("REGULATION")
        risk = self.risk.RiskComplianceResult(
            (area,), (area,), (), (), (finding,), (), self.risk.RiskGateState("CLEAR"), ()
        )
        decision = dataclasses.replace(final_stage.output.decision, risk_gate=risk.risk_gate)
        final_state = dataclasses.replace(
            final_stage.output, risk_result=risk, decision=decision
        )
        result = dataclasses.replace(
            complete,
            stages=(
                *complete.stages[:-1],
                dataclasses.replace(final_stage, output=final_state),
            ),
        )

        risk_section = self.report.render_final_report(result).split(
            "## 10. Scorecard", 1
        )[0].split("## 9. Risk & Compliance", 1)[1]
        for expected in (
            "area=REGULATION",
            "proposition=Regulatory status is supported.",
            "excluded=E003",
            "diagnostics=ASSESSMENT_NOT_SUPPORTED",
        ):
            self.assertIn(expected, risk_section)

    def test_brand_and_content_sections_do_not_leak_findings_across_dimensions(self):
        complete = self.complete_result()
        assessment = self.assessment.EvidenceAssessmentResult(
            outcome=self.assessment.AssessmentOutcome("SUPPORTED"),
            confidence=self.evidence.Confidence("High"),
            conflict_state=self.assessment.ConflictState("NONE"),
            source_count=1,
            independent_source_count=1,
            supporting_ids=(self.eid("E001"),),
            usable_ids=(self.eid("E001"),),
        )
        findings = (
            self.brand_content.BrandContentFinding(
                self.brand_content.BrandContentDimension("BRAND_POTENTIAL"),
                self.brand_content.BrandContentAspect("BRAND_PREMIUM"),
                "Brand-only proposition",
                self.brand_content.BrandContentFindingOutcome("UNKNOWN"),
                self.evidence.Confidence("Low"),
                (),
                (),
                (),
                assessment,
                (self.brand_content.BrandContentFactor("ASSESSMENT_NOT_SUPPORTED"),),
            ),
            self.brand_content.BrandContentFinding(
                self.brand_content.BrandContentDimension("CONTENT_POTENTIAL"),
                self.brand_content.BrandContentAspect("DEMO_POTENTIAL"),
                "Content-only proposition",
                self.brand_content.BrandContentFindingOutcome("SUPPORTED"),
                self.evidence.Confidence("High"),
                (self.eid("E001"),),
                (),
                (),
                assessment,
            ),
        )
        aspects = tuple(
            self.brand_content.BrandContentAspect(value)
            for value in self.brand_content.BrandContentAspect._allowed
        )
        output = self.brand_content.BrandContentResult(aspects, (), (), findings, ())
        stages = list(complete.stages)
        for stage in (
            self.workflow.WorkflowStage.BRAND_POTENTIAL,
            self.workflow.WorkflowStage.CONTENT_POTENTIAL,
        ):
            index = tuple(self.workflow.WorkflowStage).index(stage)
            stages[index] = dataclasses.replace(stages[index], output=output)
        report = self.report.render_final_report(
            dataclasses.replace(complete, stages=tuple(stages))
        )
        brand_section = report.split("## 8. Content Potential", 1)[0].split(
            "## 7. Brand Potential", 1
        )[1]
        content_section = report.split("## 9. Risk & Compliance", 1)[0].split(
            "## 8. Content Potential", 1
        )[1]
        uncertainty_section = report.split("## 13. Red Team Findings", 1)[0].split(
            "## 12. Key Uncertainties", 1
        )[1]

        self.assertIn("Brand-only proposition", brand_section)
        self.assertNotIn("Content-only proposition", brand_section)
        self.assertIn("Content-only proposition", content_section)
        self.assertNotIn("Brand-only proposition", content_section)
        self.assertIn("Brand Potential finding 1: UNKNOWN", uncertainty_section)
        self.assertNotIn("Content Potential finding 1: UNKNOWN", uncertainty_section)

    def test_incomplete_states_remain_explicit_and_latest_known_is_not_final(self):
        for status in (
            self.workflow.WorkflowStageStatus.UNRESOLVED,
            self.workflow.WorkflowStageStatus.BLOCKED,
            self.workflow.WorkflowStageStatus.FAILED,
        ):
            with self.subTest(status=status):
                report = self.report.render_final_report(self.incomplete_result(status))
                self.assertIn(status.value, report)
                self.assertIn("Final Analysis Label: UNAVAILABLE", report)
                self.assertNotIn("| Market Demand | 0", report)
        empty = self.report.render_final_report(self.empty_result())
        self.assertIn("No normalized Evidence records retained", empty)
        self.assertIn("Evidence Appendix", empty)
        latest = self.complete_result()
        final_stage = latest.stage(self.workflow.WorkflowStage.FINAL_DECISION)
        latest = dataclasses.replace(
            latest,
            stages=(*latest.stages[:-1], self.workflow.WorkflowStageResult(
                self.workflow.WorkflowStage.FINAL_DECISION,
                self.workflow.WorkflowStageStatus.BLOCKED,
                blocked_by=(self.workflow.WorkflowStage.RED_TEAM_REVISION,),
            )),
        )
        report = self.report.render_final_report(latest)
        self.assertIn("State Source: LATEST-KNOWN", report)
        self.assertIn("Final Analysis Label: UNAVAILABLE", report)
        self.assertIn(
            "| Market Demand | 80 | 20 | UNAVAILABLE | UNAVAILABLE | High | E001 |",
            report,
        )
        self.assertNotIn("Overall Confidence", report)

        unchanged_revision = self.red_team.evaluate_red_team_revision(
            self.scores(), (self.eid("E001"),), (), (), ()
        )
        revision_stage = latest.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION)
        without_accepted_revision = dataclasses.replace(
            latest,
            stages=(
                *latest.stages[:-2],
                dataclasses.replace(revision_stage, output=unchanged_revision),
                latest.stages[-1],
            ),
        )
        initial_report = self.report.render_final_report(without_accepted_revision)
        self.assertIn("State Source: INITIAL", initial_report)
        self.assertNotIn("State Source: LATEST-KNOWN", initial_report)

    def test_rendering_is_deterministic_and_does_not_reverse_dependency_direction(self):
        first = self.complete_result()
        self.assertEqual(
            self.report.render_final_report(first), self.report.render_final_report(first)
        )
        module = ast.parse(Path("product_research/end_to_end_workflow.py").read_text())
        imports = [node for node in ast.walk(module) if isinstance(node, (ast.Import, ast.ImportFrom))]
        imported_names = ast.unparse(imports)
        self.assertNotIn("final_report_generation", imported_names)
        self.assertNotIn("final_report_generation", Path("product_research/scoring_decision.py").read_text())
        self.assertNotIn("final_report_generation", Path("product_research/evidence.py").read_text())
        with mock.patch.object(
            self.scoring,
            "evaluate_scoring_decision",
            side_effect=AssertionError("reporting must not execute scoring policy"),
        ):
            self.report.render_final_report(first)
        with self.assertRaises(TypeError):
            self.report.render_final_report(object())
