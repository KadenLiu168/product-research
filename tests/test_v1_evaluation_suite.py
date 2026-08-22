"""ECO-39 v1 evaluation contract.

This module is the acceptance map for the fixture support below.  Each test
calls the narrowest existing owner; no
evaluation engine, aggregate quality score, policy vocabulary, or second
decision model belongs here.

Dimension -> authoritative oracle -> Agent rubric mapping:

* Evidence Coverage -> Evidence Policy / Assessment and domain traceability;
  Scenario 1 material-claim Evidence rubric and Scenario 2 missing-data rubric.
* Citation Accuracy -> claim-support and final-report reference validation;
  Scenario 1 Evidence rubric and Scenario 3 current-authority rubric.
* Hallucination Resistance -> fail-closed owners and workflow state;
  Scenario 1/2 non-fabrication rubrics and Scenario 3 unresolved-risk rubric.
* Estimate Discipline -> Evidence status/use policy;
  Scenario 1 status taxonomy and Scenario 2 estimate rubric.
* Repeatability -> policy/assessment, workflow trace, and report renderer;
  no Agent prose byte-equality requirement.
* Scoring Stability -> Initial Scoring and scoring/decision.
* Gate Correctness -> scoring/decision with Risk and Unit Economics owners.
* Core Threshold Enforcement -> scoring/decision core results.
* Red Team Effectiveness -> Red Team revision and downstream workflow/report.
* Report Traceability -> final-report renderer over the current workflow result.

The Agent mapping deliberately reuses Scenario 1-3 rather than adding
ECO-39-named duplicates.  Historical RED/GREEN prose is not a current
automated assertion, and no LLM judge is used.
"""

from dataclasses import replace
from decimal import Decimal

import unittest

from product_research import (
    end_to_end_workflow,
    evidence,
    evidence_policy,
    final_report_generation,
    red_team_revision,
    scoring_decision,
)
from tests.v1_evaluation_fixtures import (
    all_fixture_builders,
    claim_support,
    conflicting_assessment,
    core_threshold_fixture,
    normal_fixture,
    policy_result,
    run_workflow,
    score_revision_fixture,
)


class V1EvaluationSuiteTests(unittest.TestCase):
    """Acceptance tests for the seven fixtures and ten ECO-39 dimensions."""

    def test_required_fixture_families_are_explicit(self):
        builders = all_fixture_builders()
        self.assertEqual(
            tuple(builders),
            (
                "normal",
                "missing",
                "conflicting",
                "expired",
                "high-risk",
                "economic-failure",
                "evidence-based-score-revision",
            ),
        )
        for name, builder in builders.items():
            with self.subTest(fixture=name):
                fixture = builder()
                self.assertEqual(fixture.name, name)
                self.assertIsNotNone(fixture.workflow_kwargs)
                self.assertIsNotNone(fixture.as_of.tzinfo)

    def test_core_threshold_variant_has_favorable_aggregate_but_failed_core(self):
        fixture = core_threshold_fixture()
        result = scoring_decision.evaluate_scoring_decision(
            fixture.core_threshold_scores,
            scoring_decision.WeightAdjustments(*(Decimal("0"),) * 8),
            scoring_decision.RiskGateState("CLEAR"),
            fixture.economics_result,
            scoring_decision.DecisionPolicy(Decimal("60")),
        )
        self.assertGreaterEqual(result.aggregate_score, result.policy_threshold)
        self.assertNotEqual(result.label.value, "GO")
        self.assertEqual(tuple(value.value for value in result.failed_core_dimensions), ("Market Demand",))

    def test_evidence_coverage_uses_authoritative_support_and_preserves_gaps(self):
        fixture = normal_fixture()
        result = run_workflow(fixture)
        final_state = result.stage(end_to_end_workflow.WorkflowStage.FINAL_DECISION).output
        retained_ids = {
            evidence_id
            for score in scoring_decision.iter_dimension_scores(final_state.scores)
            for evidence_id in score.evidence_ids
        }
        self.assertTrue(retained_ids <= {item.id for item in result.evidence})
        missing = run_workflow(all_fixture_builders()["missing"]())
        self.assertEqual(missing.evidence, ())
        self.assertIsNone(missing.initial_scores)
        self.assertIsNone(missing.final_decision)

    def test_citation_accuracy_is_current_run_and_fail_closed(self):
        fixture = normal_fixture()
        self.assertTrue(claim_support(fixture, ("E001",)).fact_eligible)
        self.assertNotIn(evidence.EvidenceId("E023"), fixture.evidence_index)
        expired = all_fixture_builders()["expired"]()
        self.assertEqual(policy_result(expired, "E023").outcome.value, "REJECT")
        self.assertEqual(
            policy_result(expired, "E023").issues[0].reason_code.value,
            "STALE_EVIDENCE",
        )
        cases = (
            ((), "MISSING_CITATION"),
            (("E999",), "UNKNOWN_EVIDENCE_ID"),
            (("E024",), "STATUS_NOT_FACT_ELIGIBLE"),
            (("E025",), "STATUS_NOT_FACT_ELIGIBLE"),
        )
        for ids, reason in cases:
            with self.subTest(ids=ids):
                result = claim_support(fixture, ids)
                self.assertFalse(result.fact_eligible)
                self.assertEqual(result.issues[0].reason_code.value, reason)
        duplicate = evidence_policy.validate_evidence_set((fixture.evidence[0], fixture.evidence[0]))
        self.assertEqual(duplicate.issues[0].reason_code.value, "DUPLICATE_EVIDENCE_ID")

    def test_hallucination_resistance_preserves_invalid_state(self):
        fixture = normal_fixture()
        conflict = conflicting_assessment(fixture)
        self.assertEqual(conflict.outcome.value, "CONFLICTED")
        self.assertEqual(tuple(item.value for item in conflict.contradicting_ids), ("E022",))
        self.assertEqual(
            policy_result(all_fixture_builders()["expired"](), "E023").outcome.value,
            "REJECT",
        )
        missing = run_workflow(all_fixture_builders()["missing"]())
        self.assertEqual(missing.stage(end_to_end_workflow.WorkflowStage.INITIAL_SCORING).status,
                         end_to_end_workflow.WorkflowStageStatus.BLOCKED)
        self.assertIsNone(missing.final_decision)

    def test_estimate_discipline_preserves_status_and_unknown(self):
        fixture = normal_fixture()
        estimated = fixture.evidence_index[evidence.EvidenceId("E024")]
        unknown = fixture.evidence_index[evidence.EvidenceId("E025")]
        calculated = fixture.evidence_index[evidence.EvidenceId("E026")]
        self.assertEqual(estimated.status.value, "Estimated")
        self.assertEqual(unknown.status.value, "Unknown")
        self.assertEqual(calculated.status.value, "Calculated")
        self.assertEqual(policy_result(fixture, "E024").issues[0].reason_code.value,
                         "STATUS_NOT_FACT_ELIGIBLE")
        self.assertEqual(policy_result(fixture, "E025").issues[0].reason_code.value,
                         "STATUS_NOT_FACT_ELIGIBLE")
        self.assertEqual(
            policy_result(fixture, "E026", claim_mode="DERIVED_VALUE").outcome.value,
            "ACCEPT_CURRENT",
        )

    def test_repeatability_covers_structured_and_report_replay(self):
        first = run_workflow(normal_fixture())
        second = run_workflow(normal_fixture())
        self.assertEqual(first, second)
        self.assertEqual(
            final_report_generation.render_final_report(first),
            final_report_generation.render_final_report(second),
        )

    def test_scoring_stability_compares_exact_authoritative_results(self):
        first = run_workflow(normal_fixture())
        second = run_workflow(normal_fixture())
        for left, right in (
            (first.initial_scores, second.initial_scores),
            (first.initial_decision, second.initial_decision),
            (first.final_decision, second.final_decision),
        ):
            self.assertEqual(left, right)
        self.assertEqual(first.final_decision.final_weights, second.final_decision.final_weights)
        self.assertEqual(first.final_decision.core_results, second.final_decision.core_results)
        self.assertEqual(first.final_decision.reasons, second.final_decision.reasons)
        self.assertEqual(first.final_decision.label, second.final_decision.label)
        self.assertEqual(
            tuple(
                score.score
                for score in scoring_decision.iter_dimension_scores(first.final_decision.scores)
            ),
            tuple(Decimal(value) for value in ("80", "80", "100", "80", "80", "80", "80", "80")),
        )
        self.assertEqual(
            tuple(weight.final_weight for weight in first.final_decision.final_weights),
            tuple(Decimal(value) for value in ("20", "15", "20", "15", "10", "8", "7", "5")),
        )
        self.assertEqual(first.final_decision.aggregate_score, Decimal("84"))
        self.assertEqual(
            tuple(result.outcome.value for result in first.final_decision.core_results),
            ("PASS", "PASS", "PASS", "PASS"),
        )
        self.assertEqual(first.final_decision.failed_core_dimensions, ())
        self.assertEqual(first.final_decision.unresolved_dimensions, ())
        self.assertEqual(first.final_decision.reasons, ())
        self.assertEqual(first.final_decision.label.value, "GO")

    def test_gate_correctness_preserves_risk_and_economics_precedence(self):
        high_risk = run_workflow(all_fixture_builders()["high-risk"]())
        failed_economics_fixture = all_fixture_builders()["economic-failure"]()
        failed_economics = scoring_decision.evaluate_scoring_decision(
            failed_economics_fixture.baseline_scores,
            scoring_decision.WeightAdjustments(*(Decimal("0"),) * 8),
            scoring_decision.RiskGateState("CLEAR"),
            failed_economics_fixture.economics_result,
            scoring_decision.DecisionPolicy(Decimal("60")),
        )
        for result in (high_risk.final_decision, failed_economics):
            self.assertGreaterEqual(
                result.aggregate_score,
                result.policy_threshold,
            )
            self.assertTrue(all(
                core.outcome.value == "PASS"
                for core in result.core_results
            ))
        self.assertEqual(high_risk.final_decision.label.value, "NO-GO")
        self.assertIn("RISK_FATAL", tuple(value.value for value in high_risk.final_decision.reasons))
        self.assertEqual(failed_economics.label.value, "NO-GO")
        self.assertIn(
            "ECONOMICS_UNVIABLE",
            tuple(value.value for value in failed_economics.reasons),
        )

    def test_core_threshold_enforcement_preserves_diagnostics(self):
        fixture = core_threshold_fixture()
        result = scoring_decision.evaluate_scoring_decision(
            fixture.core_threshold_scores,
            scoring_decision.WeightAdjustments(*(Decimal("0") for _ in range(8))),
            scoring_decision.RiskGateState("CLEAR"),
            fixture.economics_result,
            scoring_decision.DecisionPolicy(Decimal("60")),
        )
        self.assertEqual(result.label.value, "CONDITIONAL GO")
        self.assertEqual(result.core_results[0].outcome.value, "FAIL")
        self.assertIn("CORE_THRESHOLD_FAILED", tuple(value.value for value in result.reasons))

    def test_red_team_effectiveness_is_narrow_and_causal(self):
        fixture = score_revision_fixture()
        result = run_workflow(fixture)
        revision = result.red_team_result
        self.assertEqual(len(revision.score_revisions), 1)
        record = revision.score_revisions[0]
        self.assertEqual(record.dimension.value, "Market Demand")
        self.assertEqual(record.before.score, Decimal("80"))
        self.assertEqual(record.after.score, Decimal("65"))
        self.assertEqual(record.reason, "Current-run Evidence changes the market-demand score.")
        self.assertEqual(tuple(item.value for item in record.causal_evidence_ids), ("E019",))
        self.assertEqual(
            scoring_decision.iter_dimension_scores(revision.initial_scores)[1:],
            scoring_decision.iter_dimension_scores(revision.revised_scores)[1:],
        )
        review = result.red_team_inputs
        baseline_only = red_team_revision.evaluate_red_team_revision(
            revision.initial_scores,
            review.baseline_evidence_ids,
            (),
            review.findings,
            review.score_proposals,
        )
        self.assertEqual(baseline_only.score_revisions, ())
        self.assertEqual(baseline_only.revised_scores, baseline_only.initial_scores)
        duplicate = red_team_revision.evaluate_red_team_revision(
            revision.initial_scores,
            review.baseline_evidence_ids,
            review.red_team_evidence_ids,
            review.findings,
            review.score_proposals + review.score_proposals,
        )
        self.assertEqual(duplicate.score_revisions, ())
        self.assertEqual(duplicate.revised_scores, duplicate.initial_scores)
        proposal = review.score_proposals[0]
        conflicting_proposal = replace(
            proposal,
            revised_score=scoring_decision.DimensionScore(
                Decimal("70"),
                proposal.revised_score.confidence,
                proposal.revised_score.evidence_ids,
            ),
            reason="A conflicting proposal targets the same dimension.",
        )
        conflicting = red_team_revision.evaluate_red_team_revision(
            revision.initial_scores,
            review.baseline_evidence_ids,
            review.red_team_evidence_ids,
            review.findings,
            review.score_proposals + (conflicting_proposal,),
        )
        self.assertEqual(conflicting.score_revisions, ())
        self.assertEqual(conflicting.revised_scores, conflicting.initial_scores)

    def test_report_traceability_is_current_run_and_lossless(self):
        fixture = normal_fixture()
        result = run_workflow(fixture)
        report = final_report_generation.render_final_report(result)
        appendix = report.split("## 15. Evidence Appendix", 1)[1]
        for item in result.evidence:
            self.assertEqual(appendix.count(f"| {item.id.value} |"), 1)
        self.assertIn("## 15. Evidence Appendix", report)
        conflicting_report = final_report_generation.render_final_report(
            run_workflow(all_fixture_builders()["conflicting"]())
        )
        self.assertIn("Adverse Evidence: E002", conflicting_report)
        conflicting_appendix = conflicting_report.split("## 15. Evidence Appendix", 1)[1]
        self.assertEqual(conflicting_appendix.count("| E002 |"), 1)
        revision_report = final_report_generation.render_final_report(
            run_workflow(score_revision_fixture())
        )
        self.assertIn(
            "Dimension=Market Demand; Score: 80 -> 65; Confidence: High -> High; "
            "Reason=Current-run Evidence changes the market-demand score.; "
            "Causal Evidence IDs=E019",
            revision_report,
        )

    def test_normal_fixture_crosses_complete_workflow_and_report(self):
        result = run_workflow(normal_fixture())
        self.assertEqual(
            tuple(record.stage.value for record in result.stage_trace),
            (
                "SUBJECT_VALIDATION",
                "RESEARCH_PLAN",
                "RESEARCH_EVIDENCE",
                "RISK_COMPLIANCE",
                "UNIT_ECONOMICS",
                "MARKET_DEMAND",
                "COMPETITION",
                "VOICE_OF_CUSTOMER",
                "SUPPLY_CHAIN",
                "BRAND_POTENTIAL",
                "CONTENT_POTENTIAL",
                "INITIAL_SCORING",
                "INITIAL_DECISION",
                "RED_TEAM_ROUTING",
                "RED_TEAM_REVISION",
                "FINAL_DECISION",
            ),
        )
        self.assertTrue(all(
            record.status is end_to_end_workflow.WorkflowStageStatus.COMPLETE
            for record in result.stage_trace
        ))
        self.assertIsNotNone(result.final_decision)
        self.assertIn("Workflow Status: COMPLETE", final_report_generation.render_final_report(result))

    def test_missing_fixture_crosses_workflow_without_fabrication(self):
        result = run_workflow(all_fixture_builders()["missing"]())
        report = final_report_generation.render_final_report(result)
        self.assertEqual(result.evidence, ())
        self.assertIsNone(result.final_decision)
        self.assertNotIn("Aggregate: 0", report)
        self.assertIn("Workflow Status: INCOMPLETE", report)
        self.assertIn("No normalized Evidence records retained", report)
        self.assertIn("Final Analysis Label: UNAVAILABLE", report)
        self.assertIn("Risk Gate: UNAVAILABLE", report)
        self.assertIn("Aggregate: UNAVAILABLE", report)
        self.assertIn(
            "| Market Demand | UNAVAILABLE | 20 | UNAVAILABLE | UNAVAILABLE | "
            "UNAVAILABLE | NONE |",
            report,
        )

    def test_revision_fixture_crosses_red_team_workflow_and_report(self):
        result = run_workflow(score_revision_fixture())
        self.assertEqual(result.final_scores.market_demand.score, Decimal("65"))
        self.assertEqual(result.final_decision.scores, result.final_scores)
        self.assertEqual(result.final_decision.label.value, "GO")
        self.assertIn(
            "Causal Evidence IDs=E019",
            final_report_generation.render_final_report(result),
        )

    def test_invalid_report_references_fail_closed(self):
        result = run_workflow(normal_fixture())
        final_stage = result.stage(end_to_end_workflow.WorkflowStage.FINAL_DECISION)
        final_state = final_stage.output
        foreign_id = evidence.EvidenceId("E999")
        foreign_score = replace(
            final_state.scores,
            market_demand=replace(
                final_state.scores.market_demand,
                evidence_ids=(foreign_id,),
            ),
        )
        foreign_decision = replace(
            final_state.decision,
            scores=foreign_score,
            evidence_ids=(foreign_id,),
        )
        foreign_state = replace(final_state, scores=foreign_score, decision=foreign_decision)
        stages = list(result.stage_trace)
        stages[-1] = replace(final_stage, output=foreign_state)
        foreign_result = replace(result, stages=tuple(stages))
        with self.assertRaises(final_report_generation.EvidenceTraceabilityError):
            final_report_generation.render_final_report(foreign_result)

    def test_semantically_equivalent_normal_and_revision_inputs_replay_identically(self):
        first_normal = normal_fixture()
        second_normal = normal_fixture()
        self.assertEqual(policy_result(first_normal, "E001"), policy_result(second_normal, "E001"))
        self.assertEqual(conflicting_assessment(first_normal), conflicting_assessment(second_normal))
        first_result = run_workflow(first_normal)
        second_result = run_workflow(second_normal)
        self.assertEqual(first_result, second_result)
        self.assertEqual(
            final_report_generation.render_final_report(first_result),
            final_report_generation.render_final_report(second_result),
        )
        first_revision = run_workflow(score_revision_fixture())
        second_revision = run_workflow(score_revision_fixture())
        self.assertEqual(first_revision, second_revision)
        self.assertEqual(
            final_report_generation.render_final_report(first_revision),
            final_report_generation.render_final_report(second_revision),
        )


if __name__ == "__main__":
    unittest.main()
