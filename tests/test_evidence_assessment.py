"""Focused contract tests for the Evidence Assessment boundary.

These tests pin the ``evidence-confidence-conflict`` capability contract:
closed vocabularies, immutable explicit inputs and results, strict
fail-closed boundary validation, reuse of the existing Evidence Policy
eligibility results, known-group independence counting, the three claim
outcomes, the fixed Confidence ceiling table, and deterministic ordering.
"""

import importlib
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)

_UNSET = object()


def _assessment_module():
    try:
        return importlib.import_module("product_research.evidence_assessment")
    except ModuleNotFoundError as exc:
        raise AssertionError("Evidence assessment module has not been implemented") from exc


def _policy_module():
    try:
        return importlib.import_module("product_research.evidence_policy")
    except ModuleNotFoundError as exc:
        raise AssertionError("Evidence policy module has not been implemented") from exc


def _evidence_module():
    try:
        return importlib.import_module("product_research.evidence")
    except ModuleNotFoundError as exc:
        raise AssertionError("Evidence contract module has not been implemented") from exc


class AssessmentTestBase(unittest.TestCase):
    def setUp(self):
        self.assessment = _assessment_module()
        self.policy = _policy_module()
        self.evidence = _evidence_module()

    def date_days_before(self, days):
        return (AS_OF.date() - timedelta(days=days)).isoformat()

    def build_evidence(self, evidence_id="E001", **overrides):
        values = {
            "id": self.evidence.EvidenceId(evidence_id),
            "claim": f"Proposition detail for {evidence_id}.",
            "evidence": f"Observed basis text for {evidence_id}.",
            "source": self.evidence.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference=f"https://example.test/items/{evidence_id}",
                title="Example product listing",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.evidence.Tier("Tier 2"),
            "status": self.evidence.Status("Observed"),
            "confidence": self.evidence.Confidence("High"),
            "metadata": {
                "policy": {"kind": "marketplace_price", "source_date": self.date_days_before(0)}
            },
        }
        values.update(overrides)
        return self.evidence.Evidence(**values)

    def build_validation_context(self, **overrides):
        values = {
            "as_of": AS_OF,
            "claim_mode": self.policy.ClaimMode("OBSERVED_FACT"),
            "temporal_scope": self.policy.TemporalScope("CURRENT"),
            "material": True,
            "critical": False,
        }
        values.update(overrides)
        return self.policy.ValidationContext(**values)

    def build_assessment_context(self, minimum_independent_sources=1, **overrides):
        values = {
            "validation_context": self.build_validation_context(),
            "minimum_independent_sources": minimum_independent_sources,
        }
        values.update(overrides)
        return self.assessment.AssessmentContext(**values)

    def build_policy(self, extra_sources=None):
        registry = {
            ("Example Marketplace", "marketplace_listing"): self.policy.SourceClass(
                "FIRST_PARTY_MARKETPLACE_SUPPLIER"
            ),
            ("Regulatory Agency", "official_regulation"): self.policy.SourceClass(
                "OFFICIAL_AUTHORITATIVE"
            ),
            ("Consumer Review Hub", "customer_reviews"): self.policy.SourceClass(
                "CONSUMER_REVIEW_DISCUSSION"
            ),
            ("Industry Journal", "secondary_articles"): self.policy.SourceClass(
                "SECONDARY_INDUSTRY"
            ),
        }
        registry.update(extra_sources or {})
        return self.policy.EvidencePolicy(source_registry=registry, max_current_verification_age=365)

    def build_index(self, *evidences):
        return {evidence.id: evidence for evidence in evidences}

    def relation(self, evidence_id, stance):
        return self.assessment.EvidenceRelation(
            self.evidence.EvidenceId(evidence_id), self.assessment.Stance(stance)
        )

    def independence(self, evidence_id, group_id):
        return self.assessment.IndependenceAssignment(
            self.evidence.EvidenceId(evidence_id), group_id
        )

    def missing(self, key, severity):
        return self.assessment.MissingInformation(
            key, self.assessment.MissingSeverity(severity)
        )

    def run_assessment(
        self,
        evidence_ids,
        relations=None,
        independence=None,
        missing_information=(),
        context=_UNSET,
        policy=_UNSET,
        evidence_index=None,
    ):
        ids = [self.evidence.EvidenceId(value) for value in evidence_ids]
        if evidence_index is None:
            evidence_index = self.build_index(
                *[self.build_evidence(value) for value in evidence_ids]
            )
        if relations is None:
            relations = [self.relation(value, "SUPPORTS") for value in evidence_ids]
        if independence is None:
            independence = [self.independence(value, f"group-{value}") for value in evidence_ids]
        if context is _UNSET:
            context = self.build_assessment_context(minimum_independent_sources=1)
        if policy is _UNSET:
            policy = self.build_policy()
        return self.assessment.assess_evidence(
            ids, evidence_index, relations, independence, missing_information, context, policy
        )

    def ids(self, result, field):
        return tuple(evidence_id.value for evidence_id in getattr(result, field))

    def assert_fail_closed(self, result):
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(result.source_count, 0)
        self.assertEqual(result.independent_source_count, 0)
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),)
        )
        for field in (
            "supporting_ids",
            "contradicting_ids",
            "neutral_ids",
            "unknown_ids",
            "current_accepted_ids",
            "context_only_ids",
            "usable_ids",
            "excluded_ids",
        ):
            self.assertEqual(getattr(result, field), ())
        self.assertEqual(result.policy_results, ())
        self.assertIsNone(result.claim_support_result)


class AssessmentVocabularyContractTests(AssessmentTestBase):
    def test_stance_values_are_closed(self):
        for value in ("SUPPORTS", "CONTRADICTS", "NEUTRAL", "UNKNOWN"):
            with self.subTest(value=value):
                self.assertEqual(str(self.assessment.Stance(value)), value)

    def test_stance_rejects_unknown_values(self):
        for invalid in ("AGREES", "supports", 1, None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.assessment.Stance(invalid)

    def test_missing_severity_values_are_closed(self):
        for value in ("NON_MATERIAL", "MATERIAL", "CRITICAL"):
            with self.subTest(value=value):
                self.assertEqual(str(self.assessment.MissingSeverity(value)), value)

    def test_missing_severity_rejects_unknown_values(self):
        for invalid in ("IMPORTANT", "material", None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.assessment.MissingSeverity(invalid)

    def test_assessment_outcome_values_are_closed(self):
        for value in ("SUPPORTED", "CONFLICTED", "INSUFFICIENT"):
            with self.subTest(value=value):
                self.assertEqual(str(self.assessment.AssessmentOutcome(value)), value)

    def test_assessment_outcome_rejects_unknown_values(self):
        for invalid in ("RESOLVED", "CONTRADICTED", None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.assessment.AssessmentOutcome(invalid)

    def test_conflict_state_values_are_closed(self):
        for value in ("NONE", "PRESENT"):
            with self.subTest(value=value):
                self.assertEqual(str(self.assessment.ConflictState(value)), value)

    def test_conflict_state_rejects_unknown_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.ConflictState("RESOLVED")

    def test_assessment_factor_values_are_closed(self):
        for value in (
            "ASSESSMENT_INPUT_ERROR",
            "NO_USABLE_SUPPORT",
            "CONFLICTING_EVIDENCE",
            "CRITICAL_INFORMATION_MISSING",
            "MATERIAL_INFORMATION_MISSING",
            "ONLY_LOW_TIER_SUPPORT",
            "LOW_BASE_CONFIDENCE",
            "INDEPENDENCE_UNKNOWN",
            "INSUFFICIENT_INDEPENDENT_SOURCES",
            "UNKNOWN_RELATIONSHIP",
            "MEDIUM_BASE_CONFIDENCE",
        ):
            with self.subTest(value=value):
                self.assertEqual(str(self.assessment.AssessmentFactor(value)), value)

    def test_assessment_factor_rejects_unknown_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.AssessmentFactor("NUMERIC_SCORE")

    def test_evidence_relation_constructs_and_freezes(self):
        relation = self.assessment.EvidenceRelation(
            self.evidence.EvidenceId("E001"), self.assessment.Stance("SUPPORTS")
        )
        self.assertEqual(relation.evidence_id, self.evidence.EvidenceId("E001"))
        self.assertEqual(relation.stance, self.assessment.Stance("SUPPORTS"))
        with self.assertRaises(AttributeError):
            relation.stance = self.assessment.Stance("NEUTRAL")

    def test_evidence_relation_rejects_wrong_types(self):
        class ExtendedStance(self.assessment.Stance):
            _allowed = ("AGREES",)

        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceRelation("E001", self.assessment.Stance("SUPPORTS"))
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceRelation(self.evidence.EvidenceId("E001"), "SUPPORTS")
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceRelation(
                self.evidence.EvidenceId("E001"), ExtendedStance("AGREES")
            )

    def test_independence_assignment_accepts_known_group(self):
        assignment = self.assessment.IndependenceAssignment(
            self.evidence.EvidenceId("E001"), "supplier-record-a"
        )
        self.assertEqual(assignment.group_id, "supplier-record-a")

    def test_independence_assignment_accepts_explicit_unknown(self):
        assignment = self.assessment.IndependenceAssignment(self.evidence.EvidenceId("E001"), None)
        self.assertIsNone(assignment.group_id)

    def test_independence_assignment_rejects_empty_group(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.IndependenceAssignment(self.evidence.EvidenceId("E001"), "")

    def test_independence_assignment_rejects_non_string_group(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.IndependenceAssignment(self.evidence.EvidenceId("E001"), 7)

    def test_independence_assignment_rejects_wrong_evidence_id(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.IndependenceAssignment("E001", "group")

    def test_independence_assignment_freezes(self):
        assignment = self.assessment.IndependenceAssignment(
            self.evidence.EvidenceId("E001"), "group-a"
        )
        with self.assertRaises(AttributeError):
            assignment.group_id = "group-b"

    def test_missing_information_constructs_and_freezes(self):
        entry = self.assessment.MissingInformation(
            "supplier_price", self.assessment.MissingSeverity("MATERIAL")
        )
        self.assertEqual(entry.key, "supplier_price")
        self.assertEqual(entry.severity, self.assessment.MissingSeverity("MATERIAL"))
        with self.assertRaises(AttributeError):
            entry.key = "other"

    def test_missing_information_rejects_empty_or_non_string_key(self):
        for invalid in ("", None, 3):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.assessment.MissingInformation(
                    invalid, self.assessment.MissingSeverity("MATERIAL")
                )

    def test_missing_information_rejects_invalid_severity(self):
        class ExtendedSeverity(self.assessment.MissingSeverity):
            _allowed = ("IGNORABLE",)

        with self.assertRaises((TypeError, ValueError)):
            self.assessment.MissingInformation("supplier_price", "MATERIAL")
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.MissingInformation(
                "supplier_price", ExtendedSeverity("IGNORABLE")
            )

    def test_assessment_context_requires_explicit_positive_minimum(self):
        for invalid in (0, -1, 1.5, True, None, "2"):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.assessment.AssessmentContext(
                    validation_context=self.build_validation_context(),
                    minimum_independent_sources=invalid,
                )

    def test_assessment_context_has_no_default_minimum(self):
        with self.assertRaises(TypeError):
            self.assessment.AssessmentContext(validation_context=self.build_validation_context())

    def test_assessment_context_rejects_wrong_validation_context(self):
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.AssessmentContext(
                validation_context=None, minimum_independent_sources=1
            )

    def test_assessment_context_freezes(self):
        context = self.build_assessment_context(minimum_independent_sources=2)
        with self.assertRaises(AttributeError):
            context.minimum_independent_sources = 3

    def test_result_constructs_and_freezes(self):
        result = self.assessment.EvidenceAssessmentResult(
            outcome=self.assessment.AssessmentOutcome("SUPPORTED"),
            confidence=self.evidence.Confidence("High"),
            conflict_state=self.assessment.ConflictState("NONE"),
            source_count=2,
            independent_source_count=2,
            supporting_ids=(self.evidence.EvidenceId("E001"), self.evidence.EvidenceId("E002")),
            usable_ids=(self.evidence.EvidenceId("E001"), self.evidence.EvidenceId("E002")),
        )
        self.assertEqual(result.source_count, 2)
        with self.assertRaises(AttributeError):
            result.confidence = self.evidence.Confidence("Low")

    def test_result_rejects_wrong_field_types(self):
        class ExtendedOutcome(self.assessment.AssessmentOutcome):
            _allowed = ("MAYBE",)

        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceAssessmentResult(
                outcome="SUPPORTED",
                confidence=self.evidence.Confidence("High"),
                conflict_state=self.assessment.ConflictState("NONE"),
                source_count=1,
                independent_source_count=1,
            )
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceAssessmentResult(
                outcome=self.assessment.AssessmentOutcome("SUPPORTED"),
                confidence=self.evidence.Confidence("High"),
                conflict_state=self.assessment.ConflictState("NONE"),
                source_count=1,
                independent_source_count=1,
                supporting_ids=("E001",),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.assessment.EvidenceAssessmentResult(
                outcome=ExtendedOutcome("MAYBE"),
                confidence=self.evidence.Confidence("High"),
                conflict_state=self.assessment.ConflictState("NONE"),
                source_count=0,
                independent_source_count=0,
            )


class AssessmentInputFailureTests(AssessmentTestBase):
    def test_extended_stance_assignment_fails_closed(self):
        class ExtendedStance(self.assessment.Stance):
            _allowed = ("AGREES",)

        class ExtendedRelation(self.assessment.EvidenceRelation):
            def __post_init__(self):
                pass

        result = self.run_assessment(
            ["E001"],
            relations=[
                ExtendedRelation(
                    self.evidence.EvidenceId("E001"), ExtendedStance("AGREES")
                )
            ],
        )

        self.assert_fail_closed(result)

    def test_extended_missing_severity_fails_closed(self):
        class ExtendedSeverity(self.assessment.MissingSeverity):
            _allowed = ("IGNORABLE",)

        class ExtendedMissingInformation(self.assessment.MissingInformation):
            def __post_init__(self):
                pass

        result = self.run_assessment(
            ["E001"],
            missing_information=(
                ExtendedMissingInformation("supplier_price", ExtendedSeverity("IGNORABLE")),
            ),
        )

        self.assert_fail_closed(result)

    def test_duplicate_requested_ids_fail_closed(self):
        result = self.run_assessment(["E001", "E001"])
        self.assert_fail_closed(result)

    def test_unknown_requested_id_fails_closed(self):
        result = self.run_assessment(
            ["E001", "E002"], evidence_index=self.build_index(self.build_evidence("E001"))
        )
        self.assert_fail_closed(result)

    def test_mismatched_index_key_fails_closed(self):
        index = self.build_index(self.build_evidence("E002"))
        index[self.evidence.EvidenceId("E001")] = self.build_evidence("E002")
        result = self.run_assessment(["E001", "E002"], evidence_index=index)
        self.assert_fail_closed(result)

    def test_non_evidence_id_index_key_fails_closed(self):
        index = self.build_index(self.build_evidence("E001"))
        index["E002"] = self.build_evidence("E002")
        result = self.run_assessment(["E001"], evidence_index=index)
        self.assert_fail_closed(result)

    def test_non_evidence_index_value_fails_closed(self):
        index = self.build_index(self.build_evidence("E001"))
        index[self.evidence.EvidenceId("E002")] = "not evidence"
        result = self.run_assessment(["E001"], evidence_index=index)
        self.assert_fail_closed(result)

    def test_incomplete_relation_coverage_fails_closed(self):
        result = self.run_assessment(
            ["E001", "E002"], relations=[self.relation("E001", "SUPPORTS")]
        )
        self.assert_fail_closed(result)

    def test_extra_relation_fails_closed(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
        )
        self.assert_fail_closed(result)

    def test_duplicate_relation_assignment_fails_closed(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E001", "NEUTRAL")],
        )
        self.assert_fail_closed(result)

    def test_incomplete_independence_coverage_fails_closed(self):
        result = self.run_assessment(
            ["E001", "E002"], independence=[self.independence("E001", "group-a")]
        )
        self.assert_fail_closed(result)

    def test_duplicate_independence_assignment_fails_closed(self):
        result = self.run_assessment(
            ["E001"],
            independence=[
                self.independence("E001", "group-a"),
                self.independence("E001", "group-b"),
            ],
        )
        self.assert_fail_closed(result)

    def test_malformed_missing_information_fails_closed(self):
        result = self.run_assessment(
            ["E001"], missing_information=("supplier_price",)
        )
        self.assert_fail_closed(result)

    def test_wrong_type_relation_entry_fails_closed(self):
        result = self.run_assessment(["E001"], relations=[("E001", "SUPPORTS")])
        self.assert_fail_closed(result)

    def test_wrong_type_independence_entry_fails_closed(self):
        result = self.run_assessment(["E001"], independence=[("E001", None)])
        self.assert_fail_closed(result)

    def test_duplicate_missing_information_keys_fail_closed(self):
        result = self.run_assessment(
            ["E001"],
            missing_information=(
                self.missing("supplier_price", "MATERIAL"),
                self.missing("supplier_price", "CRITICAL"),
            ),
        )
        self.assert_fail_closed(result)

    def test_invalid_context_fails_closed(self):
        result = self.run_assessment(["E001"], context=None)
        self.assert_fail_closed(result)

    def test_policy_context_instead_of_assessment_context_fails_closed(self):
        result = self.run_assessment(
            ["E001"], context=self.build_validation_context()
        )
        self.assert_fail_closed(result)

    def test_invalid_policy_fails_closed(self):
        result = self.run_assessment(["E001"], policy=None)
        self.assert_fail_closed(result)

    def test_none_requested_ids_fail_closed(self):
        result = self.assessment.assess_evidence(
            None, {}, [], [], (), self.build_assessment_context(), self.build_policy()
        )
        self.assert_fail_closed(result)

    def test_unexpected_validation_failure_fails_closed(self):
        with mock.patch.object(
            self.assessment, "validate_evidence", side_effect=RuntimeError("boom")
        ):
            result = self.run_assessment(["E001", "E002"])
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.source_count, 2)
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001", "E002"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),)
        )

    def test_structured_record_validation_error_fails_closed(self):
        original_validate = self.policy._validate_evidence_inner

        def fail_one_record(evidence, context, policy):
            if evidence.id == self.evidence.EvidenceId("E002"):
                raise RuntimeError("boom")
            return original_validate(evidence, context, policy)

        with mock.patch.object(
            self.policy, "_validate_evidence_inner", side_effect=fail_one_record
        ):
            result = self.run_assessment(["E001", "E002"])

        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.source_count, 2)
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001", "E002"))
        self.assertEqual(result.policy_results[1].issues[0].reason_code.value, "VALIDATION_ERROR")
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),)
        )

    def test_structured_claim_support_validation_error_fails_closed(self):
        original_validate = self.policy._validate_evidence_inner
        calls = 0

        def fail_claim_support(evidence, context, policy):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("boom")
            return original_validate(evidence, context, policy)

        with mock.patch.object(
            self.policy, "_validate_evidence_inner", side_effect=fail_claim_support
        ):
            result = self.run_assessment(["E001"])

        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.source_count, 1)
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001",))
        self.assertEqual(
            result.claim_support_result.issues[0].reason_code.value, "VALIDATION_ERROR"
        )
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),)
        )

    def test_unexpected_failure_preserves_completed_diagnostics(self):
        index = self.build_index(
            self.build_evidence("E001"),
            self.build_evidence(
                "E002",
                metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
            ),
        )
        with mock.patch.object(
            self.assessment, "validate_claim_support", side_effect=RuntimeError("boom")
        ):
            result = self.run_assessment(
                ["E002", "E001"],
                relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
                independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
                missing_information=(self.missing("weight", "MATERIAL"),),
                evidence_index=index,
            )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),)
        )
        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.independent_source_count, 0)
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001", "E002"))
        self.assertEqual(self.ids(result, "current_accepted_ids"), ("E001",))
        self.assertEqual(self.ids(result, "excluded_ids"), ("E002",))
        self.assertEqual(self.ids(result, "usable_ids"), ())
        stale_issue = result.policy_results[1].issues[0]
        self.assertEqual(stale_issue.reason_code.value, "STALE_EVIDENCE")
        self.assertEqual(
            tuple(entry.key for entry in result.missing_information), ("weight",)
        )


class AssessmentClassificationTests(AssessmentTestBase):
    def test_two_independent_agreeing_sources_are_high(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
            context=self.build_assessment_context(minimum_independent_sources=2),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(result.confidence, self.evidence.Confidence("High"))
        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.independent_source_count, 2)
        self.assertEqual(self.ids(result, "usable_ids"), ("E001", "E002"))
        self.assertEqual(result.factors, ())

    def test_duplicate_upstream_group_counts_once(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[
                self.independence("E001", "shared-upstream"),
                self.independence("E002", "shared-upstream"),
            ],
            context=self.build_assessment_context(minimum_independent_sources=2),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.independent_source_count, 1)
        self.assertEqual(
            result.factors,
            (self.assessment.AssessmentFactor("INSUFFICIENT_INDEPENDENT_SOURCES"),),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("Medium"))

    def test_current_evidence_is_preserved_and_usable(self):
        result = self.run_assessment(["E001"])
        self.assertEqual(self.ids(result, "current_accepted_ids"), ("E001",))
        self.assertEqual(self.ids(result, "context_only_ids"), ())
        self.assertEqual(self.ids(result, "usable_ids"), ("E001",))
        self.assertEqual(self.ids(result, "excluded_ids"), ())
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("High"))
        self.assertEqual(result.factors, ())

    def test_context_only_eligibility_follows_declared_scope(self):
        context = self.build_assessment_context(
            minimum_independent_sources=1,
            validation_context=self.build_validation_context(
                temporal_scope=self.policy.TemporalScope("HISTORICAL")
            ),
        )
        index = self.build_index(
            self.build_evidence("E001"),
            self.build_evidence(
                "E002",
                metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
            ),
        )
        result = self.run_assessment(
            ["E002", "E001"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
            context=context,
            evidence_index=index,
        )
        self.assertEqual(self.ids(result, "current_accepted_ids"), ("E001",))
        self.assertEqual(self.ids(result, "context_only_ids"), ("E002",))
        self.assertEqual(self.ids(result, "usable_ids"), ("E001", "E002"))
        self.assertEqual(self.ids(result, "excluded_ids"), ())
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))

    def test_eligible_contradiction_produces_conflict(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "CONTRADICTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("CONFLICTED"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("PRESENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("CONFLICTING_EVIDENCE"),)
        )
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001",))
        self.assertEqual(self.ids(result, "contradicting_ids"), ("E002",))
        self.assertEqual(self.ids(result, "usable_ids"), ("E001",))
        self.assertEqual(self.ids(result, "excluded_ids"), ())

    def test_stale_contradiction_remains_visible_without_conflict(self):
        index = self.build_index(
            self.build_evidence("E001"),
            self.build_evidence(
                "E002",
                metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
            ),
        )
        result = self.run_assessment(
            ["E002", "E001"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "CONTRADICTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
            evidence_index=index,
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(self.ids(result, "contradicting_ids"), ("E002",))
        self.assertEqual(self.ids(result, "excluded_ids"), ("E002",))
        self.assertEqual(self.ids(result, "usable_ids"), ("E001",))
        stale_result = result.policy_results[1]
        self.assertEqual(stale_result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(stale_result.fact_eligible)
        self.assertEqual(stale_result.issues[0].reason_code.value, "STALE_EVIDENCE")

    def test_claim_support_reuse_rejects_critical_tier4_only(self):
        context = self.build_assessment_context(
            minimum_independent_sources=1,
            validation_context=self.build_validation_context(critical=True),
        )
        tier4 = self.build_evidence(
            "E001",
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://industry.test/articles/1",
                title="Secondary article",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            context=context,
            evidence_index=self.build_index(tier4),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(self.ids(result, "usable_ids"), ())
        self.assertEqual(result.policy_results[0].outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.policy_results[0].fact_eligible)
        self.assertEqual(result.claim_support_result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            result.claim_support_result.issues[0].reason_code.value,
            "TIER4_SOLE_CRITICAL_SUPPORT",
        )
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("NO_USABLE_SUPPORT"),)
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))

    def test_tier4_only_support_is_low_without_policy_change(self):
        tier4 = self.build_evidence(
            "E001",
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://industry.test/articles/1",
                title="Secondary article",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            evidence_index=self.build_index(tier4),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("ONLY_LOW_TIER_SUPPORT"),)
        )
        self.assertEqual(result.policy_results[0].outcome, self.policy.Outcome("ACCEPT_CURRENT"))

    def test_no_usable_support_is_insufficient(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "CONTRADICTS")],
            independence=[self.independence("E001", "group-a")],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("NO_USABLE_SUPPORT"),)
        )
        self.assertEqual(self.ids(result, "contradicting_ids"), ("E001",))
        self.assertEqual(self.ids(result, "usable_ids"), ())

    def test_material_claim_without_support_preserves_missing_citation(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "CONTRADICTS")],
            independence=[self.independence("E001", "group-a")],
            context=self.build_assessment_context(
                validation_context=self.build_validation_context(material=True)
            ),
        )

        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertIsNotNone(result.claim_support_result)
        self.assertEqual(result.claim_support_result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            result.claim_support_result.issues[0].reason_code.value, "MISSING_CITATION"
        )

    def test_neutral_only_collection_is_insufficient(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "NEUTRAL")],
            independence=[self.independence("E001", "group-a")],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("NO_USABLE_SUPPORT"),)
        )
        self.assertEqual(self.ids(result, "neutral_ids"), ("E001",))
        self.assertEqual(self.ids(result, "usable_ids"), ())

    def test_unknown_only_collection_is_insufficient(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "UNKNOWN")],
            independence=[self.independence("E001", "group-a")],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.conflict_state, self.assessment.ConflictState("NONE"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors,
            (
                self.assessment.AssessmentFactor("NO_USABLE_SUPPORT"),
                self.assessment.AssessmentFactor("UNKNOWN_RELATIONSHIP"),
            ),
        )
        self.assertEqual(self.ids(result, "unknown_ids"), ("E001",))
        self.assertEqual(self.ids(result, "usable_ids"), ())

    def test_empty_collection_is_insufficient(self):
        result = self.run_assessment(
            [],
            relations=[],
            independence=[],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("INSUFFICIENT"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("NO_USABLE_SUPPORT"),)
        )
        self.assertEqual(result.source_count, 0)

    def test_stance_and_eligibility_collections_are_separately_ordered(self):
        index = self.build_index(
            self.build_evidence("E001"),
            self.build_evidence("E0010"),
            self.build_evidence("E002", metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}),
            self.build_evidence("E003"),
            self.build_evidence("E004"),
            self.build_evidence("E005"),
        )
        result = self.run_assessment(
            ["E005", "E0010", "E003", "E004", "E002", "E001"],
            relations=[
                self.relation("E001", "CONTRADICTS"),
                self.relation("E0010", "SUPPORTS"),
                self.relation("E002", "SUPPORTS"),
                self.relation("E003", "NEUTRAL"),
                self.relation("E004", "UNKNOWN"),
                self.relation("E005", "CONTRADICTS"),
            ],
            independence=[
                self.independence("E001", "group-a"),
                self.independence("E0010", "group-b"),
                self.independence("E002", "group-c"),
                self.independence("E003", "group-d"),
                self.independence("E004", "group-e"),
                self.independence("E005", "group-f"),
            ],
            evidence_index=index,
        )
        # Lexical (not numeric) Evidence-ID order: "E0010" < "E002".
        self.assertEqual(self.ids(result, "supporting_ids"), ("E0010", "E002"))
        self.assertEqual(self.ids(result, "contradicting_ids"), ("E001", "E005"))
        self.assertEqual(self.ids(result, "neutral_ids"), ("E003",))
        self.assertEqual(self.ids(result, "unknown_ids"), ("E004",))
        self.assertEqual(
            self.ids(result, "current_accepted_ids"),
            ("E001", "E0010", "E003", "E004", "E005"),
        )
        self.assertEqual(self.ids(result, "context_only_ids"), ())
        self.assertEqual(self.ids(result, "excluded_ids"), ("E002",))
        self.assertEqual(self.ids(result, "usable_ids"), ("E0010",))
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("CONFLICTED"))


class AssessmentConfidenceCeilingTests(AssessmentTestBase):
    def test_material_missing_information_is_low_and_preserved(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            missing_information=(self.missing("supplier_price", "MATERIAL"),),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors,
            (self.assessment.AssessmentFactor("MATERIAL_INFORMATION_MISSING"),),
        )
        self.assertEqual(
            tuple((entry.key, entry.severity.value) for entry in result.missing_information),
            (("supplier_price", "MATERIAL"),),
        )

    def test_non_material_missing_information_is_preserved_without_ceiling(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            missing_information=(
                self.missing("supplier_price", "NON_MATERIAL"),
                self.missing("notes", "NON_MATERIAL"),
            ),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("High"))
        self.assertEqual(result.factors, ())
        self.assertEqual(
            tuple(entry.key for entry in result.missing_information),
            ("notes", "supplier_price"),
        )

    def test_critical_missing_information_is_low(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            missing_information=(self.missing("certification", "CRITICAL"),),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors,
            (self.assessment.AssessmentFactor("CRITICAL_INFORMATION_MISSING"),),
        )

    def test_single_source_obeys_explicit_minimum(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            context=self.build_assessment_context(minimum_independent_sources=2),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Medium"))
        self.assertEqual(
            result.factors,
            (self.assessment.AssessmentFactor("INSUFFICIENT_INDEPENDENT_SOURCES"),),
        )

    def test_canonical_source_may_require_only_one(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            context=self.build_assessment_context(minimum_independent_sources=1),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("High"))
        self.assertEqual(result.factors, ())

    def test_unknown_independence_does_not_manufacture_cross_validation(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[self.independence("E001", None), self.independence("E002", None)],
            context=self.build_assessment_context(minimum_independent_sources=2),
        )
        self.assertEqual(result.independent_source_count, 0)
        self.assertEqual(result.confidence, self.evidence.Confidence("Medium"))
        self.assertEqual(
            result.factors,
            (
                self.assessment.AssessmentFactor("INDEPENDENCE_UNKNOWN"),
                self.assessment.AssessmentFactor("INSUFFICIENT_INDEPENDENT_SOURCES"),
            ),
        )

    def test_unknown_stance_caps_at_medium(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "UNKNOWN")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Medium"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("UNKNOWN_RELATIONSHIP"),)
        )
        self.assertEqual(self.ids(result, "unknown_ids"), ("E002",))

    def test_all_low_support_caps_at_low(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            evidence_index=self.build_index(
                self.build_evidence("E001", confidence=self.evidence.Confidence("Low"))
            ),
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("SUPPORTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("LOW_BASE_CONFIDENCE"),)
        )

    def test_medium_base_without_high_caps_at_medium(self):
        result = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            evidence_index=self.build_index(
                self.build_evidence("E001", confidence=self.evidence.Confidence("Medium"))
            ),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("Medium"))
        self.assertEqual(
            result.factors, (self.assessment.AssessmentFactor("MEDIUM_BASE_CONFIDENCE"),)
        )

    def test_strongest_high_suppresses_medium_base_ceiling(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
            evidence_index=self.build_index(
                self.build_evidence("E001", confidence=self.evidence.Confidence("High")),
                self.build_evidence("E002", confidence=self.evidence.Confidence("Medium")),
            ),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("High"))
        self.assertEqual(result.factors, ())

    def test_strictest_cap_wins_with_fixed_factor_order(self):
        index = self.build_index(
            self.build_evidence("E001", confidence=self.evidence.Confidence("Low")),
            self.build_evidence("E002", confidence=self.evidence.Confidence("Low")),
            self.build_evidence("E003", confidence=self.evidence.Confidence("High")),
        )
        result = self.run_assessment(
            ["E003", "E002", "E001"],
            relations=[
                self.relation("E001", "SUPPORTS"),
                self.relation("E002", "SUPPORTS"),
                self.relation("E003", "CONTRADICTS"),
            ],
            independence=[
                self.independence("E001", "group-a"),
                self.independence("E002", None),
                self.independence("E003", "group-b"),
            ],
            evidence_index=index,
        )
        self.assertEqual(result.outcome, self.assessment.AssessmentOutcome("CONFLICTED"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors,
            (
                self.assessment.AssessmentFactor("CONFLICTING_EVIDENCE"),
                self.assessment.AssessmentFactor("LOW_BASE_CONFIDENCE"),
                self.assessment.AssessmentFactor("INDEPENDENCE_UNKNOWN"),
            ),
        )

    def test_missing_information_factors_are_deduplicated_and_ordered(self):
        result = self.run_assessment(
            ["E001", "E002"],
            relations=[self.relation("E001", "SUPPORTS"), self.relation("E002", "SUPPORTS")],
            independence=[self.independence("E001", "group-a"), self.independence("E002", "group-b")],
            missing_information=(
                self.missing("weight", "MATERIAL"),
                self.missing("supplier_price", "MATERIAL"),
                self.missing("certification", "CRITICAL"),
            ),
            context=self.build_assessment_context(minimum_independent_sources=2),
        )
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(
            result.factors,
            (
                self.assessment.AssessmentFactor("CRITICAL_INFORMATION_MISSING"),
                self.assessment.AssessmentFactor("MATERIAL_INFORMATION_MISSING"),
            ),
        )
        self.assertEqual(
            tuple(entry.key for entry in result.missing_information),
            ("certification", "supplier_price", "weight"),
        )


class AssessmentReplayAndImmutabilityTests(AssessmentTestBase):
    def build_mixed_inputs(self):
        index = self.build_index(
            self.build_evidence("E001"),
            self.build_evidence("E002", confidence=self.evidence.Confidence("Medium")),
            self.build_evidence("E003", metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}),
        )
        return index

    def run_mixed(self, order, missing_order):
        index = self.build_mixed_inputs()
        relations_by_id = {
            "E001": self.relation("E001", "SUPPORTS"),
            "E002": self.relation("E002", "SUPPORTS"),
            "E003": self.relation("E003", "CONTRADICTS"),
        }
        independence_by_id = {
            "E001": self.independence("E001", "group-a"),
            "E002": self.independence("E002", "group-b"),
            "E003": self.independence("E003", "group-c"),
        }
        return self.run_assessment(
            order,
            relations=[relations_by_id[value] for value in order],
            independence=[independence_by_id[value] for value in order],
            missing_information=missing_order,
            evidence_index=index,
        )

    def test_reordered_equivalent_inputs_replay_identically(self):
        missing_forward = (
            self.missing("supplier_price", "MATERIAL"),
            self.missing("certification", "CRITICAL"),
        )
        missing_reversed = (missing_forward[1], missing_forward[0])
        result_a = self.run_mixed(["E001", "E002", "E003"], missing_forward)
        result_b = self.run_mixed(["E003", "E001", "E002"], missing_reversed)
        self.assertEqual(result_a, result_b)
        self.assertEqual(result_a.confidence, result_b.confidence)
        self.assertEqual(result_a.factors, result_b.factors)
        self.assertEqual(result_a.supporting_ids, result_b.supporting_ids)
        self.assertEqual(result_a.contradicting_ids, result_b.contradicting_ids)
        self.assertEqual(result_a.excluded_ids, result_b.excluded_ids)
        self.assertEqual(
            tuple(entry.key for entry in result_a.missing_information),
            tuple(entry.key for entry in result_b.missing_information),
        )

    def test_repeated_assessment_is_stable(self):
        missing = (self.missing("supplier_price", "MATERIAL"),)
        result_a = self.run_mixed(["E001", "E002", "E003"], missing)
        result_b = self.run_mixed(["E001", "E002", "E003"], missing)
        self.assertEqual(result_a, result_b)
        self.assertEqual(result_a.factors, result_b.factors)
        self.assertEqual(result_a.policy_results, result_b.policy_results)

    def test_assessment_preserves_evidence_values_and_serialization(self):
        evidence = self.build_evidence("E001")
        serialized_before = evidence.to_json()
        self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            evidence_index=self.build_index(evidence),
        )
        self.assertEqual(evidence.to_json(), serialized_before)
        self.assertEqual(
            evidence,
            self.build_evidence("E001"),
        )
        self.assertEqual(evidence.confidence, self.evidence.Confidence("High"))

    def test_provider_url_domain_claim_and_text_do_not_influence_stance(self):
        baseline = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
        )
        variant_evidence = self.build_evidence(
            "E001",
            claim="A completely different claim about a different proposition.",
            evidence="Different free text with no shared wording.",
            source=self.evidence.Source(
                provider="Other Marketplace",
                source_type="marketplace_listing",
                reference="https://other-domain.test/other/path",
                title="Other listing",
            ),
        )
        variant = self.run_assessment(
            ["E001"],
            relations=[self.relation("E001", "SUPPORTS")],
            independence=[self.independence("E001", "group-a")],
            policy=self.build_policy(
                extra_sources={
                    ("Other Marketplace", "marketplace_listing"): self.policy.SourceClass(
                        "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                    )
                }
            ),
            evidence_index=self.build_index(variant_evidence),
        )
        self.assertEqual(baseline.outcome, variant.outcome)
        self.assertEqual(baseline.confidence, variant.confidence)
        self.assertEqual(baseline.factors, variant.factors)
        self.assertEqual(baseline.independent_source_count, variant.independent_source_count)
        self.assertEqual(baseline.supporting_ids, variant.supporting_ids)
        self.assertEqual(baseline.contradicting_ids, variant.contradicting_ids)


if __name__ == "__main__":
    unittest.main()
