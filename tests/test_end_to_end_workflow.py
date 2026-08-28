"""Contract tests for the ECO-37 deterministic workflow boundary."""

import dataclasses
import importlib
import unittest
from contextlib import ExitStack
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest import mock


class WorkflowTestBase(unittest.TestCase):
    def setUp(self):
        self.workflow = importlib.import_module("product_research.end_to_end_workflow")
        self.evidence = importlib.import_module("product_research.evidence")
        self.research = importlib.import_module("product_research.research_orchestration")
        self.policy = importlib.import_module("product_research.evidence_policy")
        self.economics = importlib.import_module("product_research.unit_economics")

    def subject(self):
        return self.workflow.WorkflowSubject("portable blender", "United States")

    def research_inputs(
        self,
        *,
        with_evidence=True,
        with_two_evidence=False,
        partial_coverage=False,
    ):
        objective = self.research.ResearchObjective("objective-01", "Assess the candidate.")
        task = self.research.ResearchTask(
            "task-01",
            "What is known?",
            self.research.SourceFamily("MARKETPLACE"),
            "listed_current_price",
            self.policy.EvidenceKind("marketplace_price"),
            True,
        )
        second_task = self.research.ResearchTask(
            "task-02",
            "What remains unknown?",
            self.research.SourceFamily("SEARCH"),
            "missing_required_coverage",
            self.policy.EvidenceKind("market"),
            True,
        )

        def planner(value):
            self.assertIs(value, objective)
            tasks = (task, second_task) if partial_coverage else (task,)
            return self.research.ResearchPlan(objective.objective_id, tasks)

        def acquire(value):
            if value.task_id == second_task.task_id:
                return self.research.AcquisitionResult(
                    value.task_id,
                    self.research.TaskStatus("UNAVAILABLE"),
                    (),
                )
            findings = ()
            if with_evidence:
                findings = [
                    self.research.RawFinding(
                        "finding-01",
                        "The source reported a value.",
                        self.evidence.Source(
                            "Example Marketplace",
                            "marketplace_listing",
                            "https://example.test/products/portable-blender",
                            "Listing",
                        ),
                        "2026-08-14T08:30:00Z",
                        {"adapter": "test"},
                    ),
                ]
                if with_two_evidence:
                    findings.append(
                        self.research.RawFinding(
                            "finding-02",
                            "A second source reported a value.",
                            self.evidence.Source(
                                "Example Marketplace",
                                "marketplace_listing",
                                "https://example.test/products/portable-blender-2",
                                "Listing 2",
                            ),
                            "2026-08-14T08:30:00Z",
                            {"adapter": "test"},
                        )
                    )
                findings = tuple(findings)
            return self.research.AcquisitionResult(
                task.task_id,
                self.research.TaskStatus("SUCCESS"),
                findings,
            )

        def normalize(task_value, finding, evidence_id):
            return self.evidence.Evidence(
                evidence_id,
                "A test claim.",
                finding.content,
                finding.source,
                finding.observed_at,
                self.evidence.Tier("Tier 2"),
                self.evidence.Status("Observed"),
                self.evidence.Confidence("Medium"),
                {"policy": {"kind": "marketplace_price", "source_date": "2026-08-14"}},
            )

        return objective, planner, acquire, normalize

    def economics_inputs(self):
        status = self.economics.Status("Observed")
        confidence = self.economics.Confidence("High")
        ids = (self.evidence.EvidenceId("E001"),)

        def field(amount):
            return self.economics.EconomicInput(
                Decimal(amount), "USD", status, confidence, ids
            )

        return self.economics.UnitEconomicsInputs(
            *(field(value) for value in ("100", "10", "10", "5", "5", "5", "10", "5"))
        )

    def complete_scores(self, evidence_id="E001", value="80"):
        scoring = importlib.import_module("product_research.scoring_decision")
        ids = (self.evidence.EvidenceId(evidence_id),)
        score = scoring.DimensionScore(
            Decimal(value), self.evidence.Confidence("High"), ids
        )
        return scoring.DimensionScores(
            market_demand=score,
            competition=score,
            price_profitability=score,
            pain_points_differentiation=score,
            supply_chain_fulfillment=score,
            brand_potential=score,
            content_potential=score,
            risk_compliance=score,
        )

    def execute_workflow(self, **overrides):
        objective, planner, acquire, normalize = self.research_inputs(
            with_evidence=overrides.pop("with_evidence", True),
            with_two_evidence=overrides.pop("with_two_evidence", False),
            partial_coverage=overrides.pop("partial_coverage", False),
        )
        values = {
            "subject": self.subject(),
            "objective": objective,
            "planner": planner,
            "acquire": acquire,
            "normalize": normalize,
            "risk_required_areas": (),
            "risk_policy": self.policy.EvidencePolicy({}, 0),
            "unit_economics_inputs": self.economics_inputs(),
            "unit_economics_policy": self.economics.UnitEconomicsPolicy(
                Decimal("0.20"), Decimal("0.40")
            ),
            "market_demand_policy": self.policy.EvidencePolicy({}, 0),
            "competition_policy": self.policy.EvidencePolicy({}, 0),
            "voc_policy": self.policy.EvidencePolicy({}, 0),
            "supply_chain_policy": self.policy.EvidencePolicy({}, 0),
            "brand_content_policy": self.policy.EvidencePolicy({}, 0),
            "qualitative_judgments": (),
            "weight_adjustments": importlib.import_module(
                "product_research.scoring_decision"
            ).WeightAdjustments(
                Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
                Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
            ),
            "decision_policy": importlib.import_module(
                "product_research.scoring_decision"
            ).DecisionPolicy(Decimal("60")),
            "required_research_semantically_satisfied": True,
            "red_team_inputs": self.workflow.RedTeamReviewInputs((), (), (), ()),
        }
        values.update(overrides)
        return self.workflow.run_end_to_end_workflow(**values)

    def execute_with_captured_research(self, **overrides):
        captured = []
        run_research = self.research.run_research

        def capture(*args):
            result = run_research(*args)
            captured.append(result)
            return result

        with mock.patch.object(
            self.workflow.research_orchestration,
            "run_research",
            side_effect=capture,
        ):
            result = self.execute_workflow(**overrides)
        self.assertEqual(len(captured), 1)
        return result, captured[0]


class WorkflowControlPlaneTests(WorkflowTestBase):
    def test_fixed_stage_vocabulary_is_ordered_and_results_are_immutable(self):
        self.assertEqual(
            tuple(stage.value for stage in self.workflow.WorkflowStage),
            (
                "SUBJECT_VALIDATION", "RESEARCH_PLAN", "RESEARCH_EVIDENCE",
                "RISK_COMPLIANCE", "UNIT_ECONOMICS", "MARKET_DEMAND",
                "COMPETITION", "VOICE_OF_CUSTOMER", "SUPPLY_CHAIN",
                "BRAND_POTENTIAL", "CONTENT_POTENTIAL", "INITIAL_SCORING",
                "INITIAL_DECISION", "RED_TEAM_ROUTING", "RED_TEAM_REVISION",
                "FINAL_DECISION",
            ),
        )
        subject = self.subject()
        records = tuple(
            self.workflow.WorkflowStageResult(stage, self.workflow.WorkflowStageStatus.BLOCKED)
            for stage in self.workflow.WorkflowStage
        )
        result = self.workflow.EndToEndWorkflowResult(subject, records)

        self.assertEqual(result.stages, records)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            subject.candidate_product = "other"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.stages = ()

    def test_subject_rejects_missing_or_non_normalized_values_without_repair(self):
        for candidate, market in (
            ("", "United States"),
            ("portable blender", ""),
            (None, "United States"),
        ):
            with self.subTest(candidate=candidate, market=market):
                with self.assertRaises((TypeError, ValueError)):
                    self.workflow.WorkflowSubject(candidate, market)

    def test_replay_has_equal_ordered_trace_without_runtime_metadata(self):
        first = self.execute_workflow()
        second = self.execute_workflow()
        self.assertEqual(first, second)
        self.assertNotIn("timestamp", repr(first).lower())
        self.assertNotIn("runtime", repr(first).lower())
        self.assertEqual(tuple(record.stage for record in first.stages), tuple(self.workflow.WorkflowStage))

    def test_invalid_subject_fails_narrowly_and_blocks_without_calling_research(self):
        calls = []
        objective, planner, acquire, normalize = self.research_inputs()

        def counted_planner(value):
            calls.append(value)
            return planner(value)

        result = self.workflow.run_end_to_end_workflow(
            candidate_product="",
            target_market="United States",
            objective=objective,
            planner=counted_planner,
            acquire=acquire,
            normalize=normalize,
            required_research_semantically_satisfied=True,
        )
        self.assertIsNone(result.subject)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.SUBJECT_VALIDATION).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertEqual(calls, [])
        for stage in tuple(self.workflow.WorkflowStage)[1:]:
            record = result.stage(stage)
            self.assertEqual(record.status, self.workflow.WorkflowStageStatus.BLOCKED)
            self.assertEqual(record.blocked_by, (self.workflow.WorkflowStage.SUBJECT_VALIDATION,))


class WorkflowCompositionTests(WorkflowTestBase):
    def test_real_research_and_downstream_boundaries_cross_without_conversion(self):
        subject = self.subject()
        result, research_run = self.execute_with_captured_research(subject=subject)
        self.assertIs(result.subject, subject)
        self.assertIs(
            result.subject,
            result.stage(self.workflow.WorkflowStage.SUBJECT_VALIDATION).output,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        research_record = result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE)
        self.assertEqual(research_record.status, self.workflow.WorkflowStageStatus.COMPLETE)
        self.assertIs(result.research_plan, research_run.plan)
        self.assertIs(research_record.output, research_run)
        self.assertIs(result.research_run, research_run)
        self.assertEqual(result.research_run.evidence[0].id.value, "E001")
        self.assertIs(result.evidence[0], result.research_run.evidence[0])
        for stage, result_value in (
            (self.workflow.WorkflowStage.RISK_COMPLIANCE, result.risk_result),
            (self.workflow.WorkflowStage.UNIT_ECONOMICS, result.economics_result),
            (self.workflow.WorkflowStage.MARKET_DEMAND, result.market_demand),
            (self.workflow.WorkflowStage.COMPETITION, result.competition),
            (self.workflow.WorkflowStage.VOICE_OF_CUSTOMER, result.voc),
            (self.workflow.WorkflowStage.SUPPLY_CHAIN, result.supply_chain),
        ):
            with self.subTest(stage=stage):
                self.assertIs(result_value, result.stage(stage).output)
        self.assertIs(result.brand_content, result.stage(self.workflow.WorkflowStage.BRAND_POTENTIAL).output)
        self.assertIs(result.brand_content, result.stage(self.workflow.WorkflowStage.CONTENT_POTENTIAL).output)
        self.assertIs(result.initial_decision, result.stage(self.workflow.WorkflowStage.INITIAL_DECISION).output)
        self.assertIs(result.final_decision, result.stage(self.workflow.WorkflowStage.FINAL_DECISION).output.decision)

    def test_missing_evidence_blocks_evidence_dependent_analyzers_but_economics_can_run(self):
        boundaries = (
            (self.workflow.risk_compliance, "analyze_risk_compliance"),
            (self.workflow.market_demand, "analyze_market_demand"),
            (self.workflow.competition, "analyze_competition"),
            (self.workflow.voc, "analyze_voc"),
            (self.workflow.supply_chain, "analyze_supply_chain"),
            (self.workflow.brand_content, "analyze_brand_content"),
        )
        with ExitStack() as stack:
            analyzers = tuple(
                stack.enter_context(mock.patch.object(module, name, wraps=getattr(module, name)))
                for module, name in boundaries
            )
            result = self.execute_workflow(with_evidence=False)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RISK_COMPLIANCE).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.UNIT_ECONOMICS).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.INITIAL_SCORING).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )
        self.assertTrue(all(analyzer.call_count == 0 for analyzer in analyzers))

    def test_planner_exception_retains_the_exact_failed_research_run(self):
        def planner(_):
            raise RuntimeError("planner exploded")

        result, research_run = self.execute_with_captured_research(planner=planner)
        plan_record = result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN)
        research_record = result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE)

        self.assertEqual(plan_record.status, self.workflow.WorkflowStageStatus.UNRESOLVED)
        self.assertIsNone(plan_record.output)
        self.assertIsNone(plan_record.failure_kind)
        self.assertEqual(research_record.status, self.workflow.WorkflowStageStatus.UNRESOLVED)
        self.assertIsNone(research_record.failure_kind)
        self.assertIs(research_record.output, research_run)
        self.assertIs(result.research_run, research_run)
        self.assertEqual(research_run.status, self.research.RunStatus("FAILED"))
        self.assertEqual(
            tuple(failure.reason for failure in research_run.failures),
            (self.research.FailureReason("PLANNER_EXCEPTION"),),
        )

    def test_invalid_plan_retains_the_exact_failed_research_run(self):
        def planner(_):
            return None

        result, research_run = self.execute_with_captured_research(planner=planner)
        plan_record = result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN)
        research_record = result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE)

        self.assertEqual(plan_record.status, self.workflow.WorkflowStageStatus.UNRESOLVED)
        self.assertIsNone(plan_record.output)
        self.assertIsNone(plan_record.failure_kind)
        self.assertEqual(research_record.status, self.workflow.WorkflowStageStatus.UNRESOLVED)
        self.assertIsNone(research_record.failure_kind)
        self.assertIs(research_record.output, research_run)
        self.assertIs(result.research_run, research_run)
        self.assertEqual(research_run.status, self.research.RunStatus("FAILED"))
        self.assertEqual(
            tuple(failure.reason for failure in research_run.failures),
            (self.research.FailureReason("INVALID_PLAN"),),
        )

    def test_planner_failure_blocks_only_evidence_dependent_stages_and_keeps_economics_running(self):
        def planner(_):
            raise RuntimeError("planner exploded")

        boundaries = (
            (self.workflow.risk_compliance, "analyze_risk_compliance"),
            (self.workflow.market_demand, "analyze_market_demand"),
            (self.workflow.competition, "analyze_competition"),
            (self.workflow.voc, "analyze_voc"),
            (self.workflow.supply_chain, "analyze_supply_chain"),
            (self.workflow.brand_content, "analyze_brand_content"),
        )
        with ExitStack() as stack:
            analyzers = tuple(
                stack.enter_context(mock.patch.object(module, name, wraps=getattr(module, name)))
                for module, name in boundaries
            )
            economics = stack.enter_context(
                mock.patch.object(
                    self.workflow.unit_economics,
                    "evaluate_unit_economics",
                    wraps=self.workflow.unit_economics.evaluate_unit_economics,
                )
            )
            result = self.execute_workflow(planner=planner)

        self.assertEqual(result.evidence, ())
        self.assertEqual(economics.call_count, 1)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.UNIT_ECONOMICS).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertTrue(all(analyzer.call_count == 0 for analyzer in analyzers))
        for stage in (
            self.workflow.WorkflowStage.RISK_COMPLIANCE,
            self.workflow.WorkflowStage.MARKET_DEMAND,
            self.workflow.WorkflowStage.COMPETITION,
            self.workflow.WorkflowStage.VOICE_OF_CUSTOMER,
            self.workflow.WorkflowStage.SUPPLY_CHAIN,
            self.workflow.WorkflowStage.BRAND_POTENTIAL,
            self.workflow.WorkflowStage.CONTENT_POTENTIAL,
        ):
            with self.subTest(stage=stage):
                record = result.stage(stage)
                self.assertEqual(record.status, self.workflow.WorkflowStageStatus.BLOCKED)
                self.assertIsNone(record.output)

    def test_research_exception_and_invalid_return_remain_workflow_execution_failures(self):
        cases = (
            ("exception", {"side_effect": RuntimeError("research exploded")}),
            ("invalid return", {"return_value": object()}),
        )
        for label, patch_kwargs in cases:
            with self.subTest(case=label), mock.patch.object(
                self.workflow.research_orchestration,
                "run_research",
                **patch_kwargs,
            ):
                result = self.execute_workflow()

            plan_record = result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN)
            research_record = result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE)
            self.assertEqual(plan_record.status, self.workflow.WorkflowStageStatus.FAILED)
            self.assertEqual(
                plan_record.failure_kind,
                self.workflow.WorkflowFailureKind.EXECUTION_ERROR,
            )
            self.assertEqual(research_record.status, self.workflow.WorkflowStageStatus.BLOCKED)
            self.assertEqual(
                research_record.blocked_by,
                (self.workflow.WorkflowStage.RESEARCH_PLAN,),
            )
            self.assertIsNone(result.research_run)

    def test_missing_economics_input_retains_the_existing_fail_closed_result(self):
        result = self.execute_workflow(unit_economics_inputs=None)
        economics_record = result.stage(self.workflow.WorkflowStage.UNIT_ECONOMICS)

        self.assertEqual(
            economics_record.status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )
        self.assertIsInstance(economics_record.output, self.economics.UnitEconomicsResult)
        self.assertEqual(economics_record.output.outcome.value, "UNRESOLVED")
        self.assertIsNotNone(result.initial_scores)
        self.assertIsNotNone(result.initial_decision)

    def test_partial_research_coverage_remains_visible_while_later_analysis_runs(self):
        result, research_run = self.execute_with_captured_research(partial_coverage=True)
        self.assertEqual(result.research_run.status.value, "PARTIAL")
        self.assertEqual(result.research_run.missing_required_task_ids, ("task-02",))
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )
        self.assertIs(result.research_plan, research_run.plan)
        self.assertIs(result.research_run, research_run)
        self.assertIsNotNone(result.market_demand)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.MARKET_DEMAND).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )

    def test_failed_research_run_with_plan_remains_retained_and_blocks_evidence_analysis(self):
        result, research_run = self.execute_with_captured_research(with_evidence=False)
        research_record = result.stage(self.workflow.WorkflowStage.RESEARCH_EVIDENCE)

        self.assertEqual(result.research_run.status, self.research.RunStatus("FAILED"))
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RESEARCH_PLAN).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(research_record.status, self.workflow.WorkflowStageStatus.UNRESOLVED)
        self.assertIs(research_record.output, research_run)
        self.assertIs(result.research_run, research_run)
        self.assertIs(result.research_plan, research_run.plan)
        self.assertEqual(result.evidence, ())
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RISK_COMPLIANCE).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )

    def test_adverse_domain_results_are_not_workflow_failures(self):
        risk = importlib.import_module("product_research.risk_compliance")
        fatal = risk.RiskComplianceResult(
            (), (), (), (), (), (), risk.RiskGateState("FATAL"), ()
        )
        result = self.execute_workflow(
            unit_economics_policy=self.economics.UnitEconomicsPolicy(
                Decimal("0.80"), Decimal("0.90")
            ),
        )
        economics = result.economics_result
        self.assertIsNotNone(economics)
        with mock.patch.object(
            self.workflow.risk_compliance,
            "analyze_risk_compliance",
            return_value=fatal,
        ):
            result = self.execute_workflow(
                unit_economics_policy=self.economics.UnitEconomicsPolicy(
                    Decimal("0.80"), Decimal("0.90")
                ),
            )
        self.assertEqual(result.risk_result.risk_gate.value, "FATAL")
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.UNIT_ECONOMICS).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(result.economics_result.outcome.value, "UNVIABLE")
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RISK_COMPLIANCE).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.INITIAL_SCORING).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )

    def test_core_threshold_failure_is_a_complete_decision_outcome(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        scores = self.complete_scores()
        scores = dataclasses.replace(
            scores,
            market_demand=scoring.DimensionScore(
                Decimal("10"), self.evidence.Confidence("High"),
                (self.evidence.EvidenceId("E001"),),
            ),
        )
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            result = self.execute_workflow()
        self.assertTrue(result.initial_decision.failed_core_dimensions)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.INITIAL_DECISION).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )

    def test_invalid_decision_policy_inputs_keep_both_decisions_unresolved(self):
        scores = self.complete_scores()
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            result = self.execute_workflow(weight_adjustments=None)

        for stage in (
            self.workflow.WorkflowStage.INITIAL_DECISION,
            self.workflow.WorkflowStage.FINAL_DECISION,
        ):
            with self.subTest(stage=stage):
                self.assertEqual(
                    result.stage(stage).status,
                    self.workflow.WorkflowStageStatus.UNRESOLVED,
                )

    def test_brand_and_content_stage_statuses_are_classified_by_their_own_facets(self):
        brand = importlib.import_module("product_research.brand_content")
        assessment = importlib.import_module("product_research.evidence_assessment")
        policy = self.policy.EvidencePolicy(
            {
                ("Example Marketplace", "marketplace_listing"):
                    self.policy.SourceClass("FIRST_PARTY_MARKETPLACE_SUPPLIER")
            },
            365,
        )
        validation_context = self.policy.ValidationContext(
            datetime.fromisoformat("2026-08-15T12:00:00+00:00"),
            self.policy.ClaimMode("OBSERVED_FACT"),
            self.policy.TemporalScope("CURRENT"),
            True,
            False,
        )
        evidence_id = self.evidence.EvidenceId("E001")
        propositions = tuple(
            brand.BrandContentPropositionInput(
                brand.BrandContentDimension("BRAND_POTENTIAL"),
                brand.BrandContentAspect(aspect),
                f"Supported Brand proposition for {aspect}.",
                (evidence_id,),
                (assessment.EvidenceRelation(evidence_id, assessment.Stance("SUPPORTS")),),
                (assessment.IndependenceAssignment(evidence_id, "source-1"),),
                (),
                assessment.AssessmentContext(validation_context, 1),
            )
            for aspect in (
                "BRAND_PREMIUM",
                "STORYTELLING",
                "VISUAL_EXPRESSION",
                "DEMO_POTENTIAL",
                "UGC_PROPAGATION",
            )
        )

        result = self.execute_workflow(
            brand_content_propositions=propositions,
            brand_content_policy=policy,
        )

        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.BRAND_POTENTIAL).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.CONTENT_POTENTIAL).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )

    def test_failed_analysis_does_not_stop_an_independent_later_analysis(self):
        with mock.patch.object(
            self.workflow.risk_compliance,
            "analyze_risk_compliance",
            side_effect=RuntimeError("control-plane failure"),
        ), mock.patch.object(
            self.workflow.market_demand,
            "analyze_market_demand",
            wraps=self.workflow.market_demand.analyze_market_demand,
        ) as market_mock:
            result = self.execute_workflow()
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RISK_COMPLIANCE).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertEqual(market_mock.call_count, 1)
        self.assertIsNotNone(result.market_demand)

    def test_invalid_authoritative_analysis_outputs_fail_their_stage(self):
        boundaries = (
            (self.workflow.WorkflowStage.RISK_COMPLIANCE,
             self.workflow.risk_compliance, "analyze_risk_compliance"),
            (self.workflow.WorkflowStage.UNIT_ECONOMICS,
             self.workflow.unit_economics, "evaluate_unit_economics"),
            (self.workflow.WorkflowStage.MARKET_DEMAND,
             self.workflow.market_demand, "analyze_market_demand"),
            (self.workflow.WorkflowStage.COMPETITION,
             self.workflow.competition, "analyze_competition"),
            (self.workflow.WorkflowStage.VOICE_OF_CUSTOMER,
             self.workflow.voc, "analyze_voc"),
            (self.workflow.WorkflowStage.SUPPLY_CHAIN,
             self.workflow.supply_chain, "analyze_supply_chain"),
        )

        for stage, module, function_name in boundaries:
            with self.subTest(stage=stage), mock.patch.object(
                module, function_name, return_value=object()
            ):
                result = self.execute_workflow()

            record = result.stage(stage)
            self.assertEqual(record.status, self.workflow.WorkflowStageStatus.FAILED)
            self.assertEqual(
                record.failure_kind,
                self.workflow.WorkflowFailureKind.EXECUTION_ERROR,
            )
            self.assertIsNone(record.output)

    def test_empty_explicit_red_team_review_reaches_final_structured_state(self):
        result = self.execute_workflow()
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.FINAL_DECISION).status,
            self.workflow.WorkflowStageStatus.UNRESOLVED,
        )
        self.assertIs(result.revised_scores, result.red_team_result.revised_scores)
        self.assertIs(result.final_risk_result, result.risk_result)
        self.assertIs(result.final_economics_result, result.economics_result)

    def test_conflicting_red_team_input_forms_fail_instead_of_dropping_values(self):
        review = self.workflow.RedTeamReviewInputs((), (), (), ())
        result = self.execute_workflow(
            red_team_inputs=review,
            red_team_evidence_ids=(self.evidence.EvidenceId("E999"),),
        )

        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )

    def test_missing_explicit_red_team_input_is_invalid_not_blocked_by_existing_decision(self):
        result = self.execute_workflow(red_team_inputs=None)
        routing = result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING)

        self.assertIsNotNone(result.initial_decision)
        self.assertEqual(routing.status, self.workflow.WorkflowStageStatus.FAILED)
        self.assertEqual(routing.failure_kind, self.workflow.WorkflowFailureKind.INVALID_INPUT)
        self.assertEqual(routing.blocked_by, ())
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).blocked_by,
            (self.workflow.WorkflowStage.RED_TEAM_ROUTING,),
        )

    def test_final_state_rejects_parallel_authoritative_values(self):
        risk = importlib.import_module("product_research.risk_compliance")
        scores = self.complete_scores()
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            result = self.execute_workflow()

        final_state = result.stage(self.workflow.WorkflowStage.FINAL_DECISION).output
        mismatches = (
            {"scores": dataclasses.replace(final_state.scores)},
            {
                "risk_result": dataclasses.replace(
                    final_state.risk_result,
                    risk_gate=risk.RiskGateState("FATAL"),
                ),
            },
            {
                "economics_result": dataclasses.replace(final_state.economics_result),
                "decision": dataclasses.replace(
                    final_state.decision,
                    unit_economics=dataclasses.replace(final_state.economics_result),
                ),
            },
        )
        for changes in mismatches:
            with self.subTest(changes=tuple(changes)):
                with self.assertRaises(ValueError):
                    self.workflow.WorkflowFinalState(
                        changes.get("scores", final_state.scores),
                        changes.get("risk_result", final_state.risk_result),
                        changes.get("economics_result", final_state.economics_result),
                        changes.get("decision", final_state.decision),
                    )

    def test_incoherent_final_decision_fails_stage_16_without_escaping(self):
        scores = self.complete_scores()
        evaluate = self.workflow.scoring_decision.evaluate_scoring_decision
        call_count = 0

        def incoherent_final_decision(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            decision = evaluate(*args, **kwargs)
            if call_count == 2:
                return dataclasses.replace(
                    decision,
                    scores=dataclasses.replace(decision.scores),
                )
            return decision

        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ), mock.patch.object(
            self.workflow.scoring_decision,
            "evaluate_scoring_decision",
            side_effect=incoherent_final_decision,
        ):
            result = self.execute_workflow()

        final_record = result.stage(self.workflow.WorkflowStage.FINAL_DECISION)
        self.assertEqual(final_record.status, self.workflow.WorkflowStageStatus.FAILED)
        self.assertEqual(
            final_record.failure_kind,
            self.workflow.WorkflowFailureKind.EXECUTION_ERROR,
        )
        self.assertIsNone(final_record.output)

    def test_foreign_evidence_id_fails_stage_14_and_does_not_invoke_red_team(self):
        red_team = self.workflow.RedTeamReviewInputs(
            (self.evidence.EvidenceId("E001"),),
            (self.evidence.EvidenceId("E999"),),
            (),
            (),
        )
        with mock.patch.object(
            self.workflow.red_team_revision,
            "evaluate_red_team_revision",
            wraps=self.workflow.red_team_revision.evaluate_red_team_revision,
        ) as revision_mock:
            result = self.execute_workflow(red_team_inputs=red_team)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.FINAL_DECISION).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )
        self.assertIs(result.red_team_inputs, red_team)
        self.assertEqual(revision_mock.call_count, 0)

    def test_malformed_red_team_baseline_fails_stage_14_without_escaping(self):
        class MalformedRiskProposal:
            @property
            def initial_result(self):
                raise RuntimeError("malformed caller-owned proposal")

        review = self.workflow.RedTeamReviewInputs(
            (), (), (), (), MalformedRiskProposal()
        )
        result = self.execute_workflow(red_team_inputs=review)

        routing = result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING)
        self.assertEqual(routing.status, self.workflow.WorkflowStageStatus.FAILED)
        self.assertEqual(
            routing.failure_kind,
            self.workflow.WorkflowFailureKind.INVALID_INPUT,
        )
        self.assertIs(routing.output, review)
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )
        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.FINAL_DECISION).status,
            self.workflow.WorkflowStageStatus.BLOCKED,
        )

    def test_initial_and_final_decisions_use_the_same_existing_executor_and_policy(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        scores = self.complete_scores()
        weights = scoring.WeightAdjustments(
            Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
            Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
        )
        policy = scoring.DecisionPolicy(Decimal("60"))
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ) as initial_mock, mock.patch.object(
            self.workflow.scoring_decision,
            "evaluate_scoring_decision",
            wraps=self.workflow.scoring_decision.evaluate_scoring_decision,
        ) as decision_mock:
            result = self.execute_workflow(
                weight_adjustments=weights,
                decision_policy=policy,
            )

        self.assertEqual(initial_mock.call_count, 1)
        self.assertEqual(decision_mock.call_count, 2)
        self.assertIs(result.initial_scores, scores)
        self.assertIs(result.initial_decision, result.stage(self.workflow.WorkflowStage.INITIAL_DECISION).output)
        self.assertIs(result.final_decision, result.stage(self.workflow.WorkflowStage.FINAL_DECISION).output.decision)
        self.assertIs(decision_mock.call_args_list[0].args[1], weights)
        self.assertIs(decision_mock.call_args_list[1].args[1], weights)
        self.assertIs(decision_mock.call_args_list[0].args[4], policy)
        self.assertIs(decision_mock.call_args_list[1].args[4], policy)

    def test_initial_and_final_decisions_reuse_derived_required_research_readiness(self):
        scores = self.complete_scores()
        cases = (
            ({}, True, True),
            ({"partial_coverage": True}, True, False),
            ({}, False, False),
            ({}, None, None),
            ({}, "true", None),
        )
        for fixture_overrides, semantic, expected in cases:
            with self.subTest(semantic=semantic, fixture_overrides=fixture_overrides):
                with mock.patch.object(
                    self.workflow.initial_scoring,
                    "evaluate_initial_scoring",
                    return_value=scores,
                ), mock.patch.object(
                    self.workflow.scoring_decision,
                    "evaluate_scoring_decision",
                    wraps=self.workflow.scoring_decision.evaluate_scoring_decision,
                ) as decision_mock:
                    result = self.execute_workflow(
                        **fixture_overrides,
                        required_research_semantically_satisfied=semantic,
                    )

                self.assertEqual(decision_mock.call_count, 2)
                readiness_values = tuple(
                    call.kwargs["required_research_ready"]
                    for call in decision_mock.call_args_list
                )
                self.assertEqual(readiness_values, (expected, expected))
                self.assertIs(result.final_decision.required_research_ready, expected)
                if expected is None:
                    self.assertIn(
                        "RESEARCH_READINESS_INPUT_ERROR",
                        tuple(reason.value for reason in result.final_decision.reasons),
                    )
                else:
                    self.assertEqual(
                        result.final_decision.label.value,
                        "GO" if expected else "CONDITIONAL GO",
                    )

    def test_failed_research_execution_never_derives_ready(self):
        def planner(_):
            raise RuntimeError("planned failure")

        _, research_run = self.execute_with_captured_research(planner=planner)

        self.assertEqual(research_run.status.value, "FAILED")
        self.assertIs(
            self.workflow._derive_required_research_readiness(research_run, True),
            False,
        )
        self.assertIs(
            self.workflow._derive_required_research_readiness(research_run, False),
            False,
        )

    def test_invalid_retained_research_result_never_derives_ready(self):
        _, valid_run = self.execute_with_captured_research()
        invalid_run = object.__new__(self.research.ResearchRunResult)
        for field in dataclasses.fields(valid_run):
            object.__setattr__(invalid_run, field.name, getattr(valid_run, field.name))
        object.__setattr__(
            invalid_run,
            "required_task_ids",
            (*valid_run.required_task_ids, "ghost-required"),
        )

        with mock.patch.object(
            self.workflow.research_orchestration,
            "run_research",
            return_value=invalid_run,
        ):
            result = self.execute_workflow()

        self.assertIs(result.final_decision.required_research_ready, False)
        self.assertEqual(result.final_decision.label.value, "CONDITIONAL GO")

    def test_accepted_score_revision_changes_only_final_scores_and_keeps_initial_decision(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        red_team = importlib.import_module("product_research.red_team_revision")
        scores = self.complete_scores()
        revised_score = scoring.DimensionScore(
            Decimal("95"), self.evidence.Confidence("High"),
            (self.evidence.EvidenceId("E002"),),
        )
        proposal = red_team.ScoreRevisionProposal(
            scoring.Dimension("Market Demand"),
            revised_score,
            "The current-run second source changes this dimension.",
            (self.evidence.EvidenceId("E002"),),
        )
        review = self.workflow.RedTeamReviewInputs(
            (self.evidence.EvidenceId("E001"),),
            (self.evidence.EvidenceId("E002"),),
            (),
            (proposal,),
        )
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ), mock.patch.object(
            self.workflow.red_team_revision,
            "evaluate_red_team_revision",
            wraps=self.workflow.red_team_revision.evaluate_red_team_revision,
        ) as revision_mock:
            result = self.execute_workflow(with_two_evidence=True, red_team_inputs=review)

        self.assertEqual(
            result.stage(self.workflow.WorkflowStage.RED_TEAM_REVISION).status,
            self.workflow.WorkflowStageStatus.COMPLETE,
        )
        self.assertEqual(result.initial_scores.market_demand.score, Decimal("80"))
        self.assertEqual(result.revised_scores.market_demand.score, Decimal("95"))
        self.assertEqual(result.final_decision.scores.market_demand, revised_score)
        self.assertIsNot(result.initial_decision, result.final_decision)
        call = revision_mock.call_args.args
        self.assertIs(call[1], review.baseline_evidence_ids)
        self.assertIs(call[2], review.red_team_evidence_ids)
        self.assertIs(call[3], review.findings)
        self.assertIs(call[4], review.score_proposals)

    def test_duplicate_or_unsupported_red_team_proposals_remain_fail_closed(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        red_team = importlib.import_module("product_research.red_team_revision")
        scores = self.complete_scores()
        proposal = red_team.ScoreRevisionProposal(
            scoring.Dimension("Market Demand"),
            scoring.DimensionScore(
                Decimal("95"), self.evidence.Confidence("High"),
                (self.evidence.EvidenceId("E002"),),
            ),
            "Duplicate proposal target.",
            (self.evidence.EvidenceId("E002"),),
        )
        review = self.workflow.RedTeamReviewInputs(
            (self.evidence.EvidenceId("E001"),),
            (self.evidence.EvidenceId("E002"),),
            (),
            (proposal, proposal, object()),
        )
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            result = self.execute_workflow(
                with_two_evidence=True,
                red_team_inputs=review,
            )
        self.assertEqual(result.red_team_result.score_revisions, ())
        self.assertEqual(result.revised_scores, result.initial_scores)

    def test_value_equal_risk_baseline_binds_but_value_different_baseline_fails(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        red_team = importlib.import_module("product_research.red_team_revision")
        risk = importlib.import_module("product_research.risk_compliance")
        scores = self.complete_scores()
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            baseline_run = self.execute_workflow(with_two_evidence=True)
            equal_initial = dataclasses.replace(baseline_run.risk_result)
            revised = dataclasses.replace(
                equal_initial,
                risk_gate=risk.RiskGateState("FATAL"),
            )
            equal_review = self.workflow.RedTeamReviewInputs(
                (self.evidence.EvidenceId("E001"),),
                (self.evidence.EvidenceId("E002"),),
                (),
                (),
                red_team.RiskRevisionProposal(
                    equal_initial,
                    revised,
                    "A current-run red team revision.",
                    (self.evidence.EvidenceId("E002"),),
                ),
            )
            equal_result = self.execute_workflow(
                with_two_evidence=True,
                red_team_inputs=equal_review,
            )
            self.assertEqual(
                equal_result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
                self.workflow.WorkflowStageStatus.COMPLETE,
            )
            self.assertIs(equal_result.final_risk_result, revised)
            self.assertEqual(equal_result.final_risk_result.risk_gate.value, "FATAL")

            foreign = dataclasses.replace(equal_initial, risk_gate=risk.RiskGateState("FATAL"))
            foreign_review = self.workflow.RedTeamReviewInputs(
                (self.evidence.EvidenceId("E001"),),
                (self.evidence.EvidenceId("E002"),),
                (),
                (),
                red_team.RiskRevisionProposal(
                    foreign,
                    baseline_run.risk_result,
                    "A foreign baseline must not be repaired.",
                    (self.evidence.EvidenceId("E002"),),
                ),
            )
            foreign_result = self.execute_workflow(
                with_two_evidence=True,
                red_team_inputs=foreign_review,
            )

        self.assertEqual(
            foreign_result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertIs(foreign_result.red_team_inputs, foreign_review)
        self.assertIs(foreign_result.red_team_inputs.risk_proposal, foreign_review.risk_proposal)


class WorkflowArchitectureTests(WorkflowTestBase):
    def test_workflow_is_the_only_new_composition_layer_and_does_not_render(self):
        root = Path(__file__).resolve().parents[1]
        workflow_source = (root / "product_research" / "end_to_end_workflow.py").read_text()
        self.assertNotIn("sqlite", workflow_source.lower())
        self.assertNotIn("report", workflow_source.lower())
        self.assertNotIn("evidence appendix", workflow_source.lower())
        self.assertNotIn("provider", workflow_source.lower())
        self.assertNotIn("llm", workflow_source.lower())
        self.assertNotIn("async", workflow_source.lower())
        for path in (root / "product_research").glob("*.py"):
            if path.name not in ("end_to_end_workflow.py", "final_report_generation.py"):
                self.assertNotIn("end_to_end_workflow", path.read_text())
        report_source = (root / "product_research" / "final_report_generation.py").read_text()
        self.assertIn("end_to_end_workflow", report_source)
        self.assertNotIn("final_report_generation", workflow_source)

    def test_research_orchestration_remains_the_only_research_to_evidence_boundary(self):
        root = Path(__file__).resolve().parents[1]
        workflow_source = (root / "product_research" / "end_to_end_workflow.py").read_text()

        self.assertEqual(workflow_source.count("research_orchestration.run_research("), 1)
        for constructor in (
            "ResearchRunResult(",
            "ResearchFailure(",
            "FailureReason(",
            "RunStatus(",
            "ResearchPlan(",
            "EvidenceId(",
        ):
            self.assertNotIn(constructor, workflow_source)
        self.assertNotIn("_validate_plan(", workflow_source)

    def test_workflow_public_surface_has_no_generic_executor_or_second_policy_engine(self):
        workflow = importlib.import_module("product_research.end_to_end_workflow")
        public_names = tuple(
            name for name in vars(workflow)
            if not name.startswith("_") and name not in workflow.__all__
        )
        self.assertNotIn("dispatch", public_names)
        self.assertNotIn("execute_stage", public_names)
        self.assertEqual(workflow.__all__[-1], "run_end_to_end_workflow")

    def test_value_equal_economics_baseline_binds_and_foreign_one_is_not_repaired(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        red_team = importlib.import_module("product_research.red_team_revision")
        economics = importlib.import_module("product_research.unit_economics")
        scores = self.complete_scores()
        with mock.patch.object(
            self.workflow.initial_scoring,
            "evaluate_initial_scoring",
            return_value=scores,
        ):
            baseline_run = self.execute_workflow(with_two_evidence=True)
            equal_initial = dataclasses.replace(baseline_run.economics_result)
            revised = dataclasses.replace(
                equal_initial,
                outcome=economics.EconomicsOutcome("BELOW_TARGET"),
                dynamic_target_gate=dataclasses.replace(
                    equal_initial.dynamic_target_gate,
                    outcome=economics.GateOutcome("FAIL"),
                ),
            )
            equal_review = self.workflow.RedTeamReviewInputs(
                (self.evidence.EvidenceId("E001"),),
                (self.evidence.EvidenceId("E002"),),
                (),
                (),
                None,
                red_team.EconomicsRevisionProposal(
                    equal_initial,
                    revised,
                    "A current-run economics revision.",
                    (self.evidence.EvidenceId("E002"),),
                ),
            )
            equal_result = self.execute_workflow(
                with_two_evidence=True,
                red_team_inputs=equal_review,
            )
            self.assertEqual(
                equal_result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
                self.workflow.WorkflowStageStatus.COMPLETE,
            )
            self.assertIs(equal_result.final_economics_result, revised)
            self.assertEqual(equal_result.final_economics_result.outcome.value, "BELOW_TARGET")

            foreign = dataclasses.replace(
                equal_initial,
                outcome=economics.EconomicsOutcome("UNVIABLE"),
            )
            foreign_review = self.workflow.RedTeamReviewInputs(
                (self.evidence.EvidenceId("E001"),),
                (self.evidence.EvidenceId("E002"),),
                (),
                (),
                None,
                red_team.EconomicsRevisionProposal(
                    foreign,
                    baseline_run.economics_result,
                    "A foreign economics baseline must not be repaired.",
                    (self.evidence.EvidenceId("E002"),),
                ),
            )
            foreign_result = self.execute_workflow(
                with_two_evidence=True,
                red_team_inputs=foreign_review,
            )
        self.assertEqual(
            foreign_result.stage(self.workflow.WorkflowStage.RED_TEAM_ROUTING).status,
            self.workflow.WorkflowStageStatus.FAILED,
        )
        self.assertIs(foreign_result.red_team_inputs, foreign_review)


if __name__ == "__main__":
    unittest.main()
