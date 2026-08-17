import ast
import copy
import dataclasses
import importlib
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
CATEGORIES = (
    "PURCHASE_MOTIVATION",
    "PAIN_POINT",
    "COMPLAINT",
    "UNMET_NEED",
    "USE_CASE",
    "PURCHASE_BARRIER",
    "CUSTOMER_LANGUAGE",
    "SEGMENT",
)


class VOCTestBase(unittest.TestCase):
    def setUp(self):
        self.voc = importlib.import_module("product_research.voc")
        self.e = importlib.import_module("product_research.evidence")
        self.p = importlib.import_module("product_research.evidence_policy")
        self.a = importlib.import_module("product_research.evidence_assessment")

    def eid(self, value):
        return self.e.EvidenceId(value)

    def build_context(self, **overrides):
        values = {
            "as_of": AS_OF,
            "claim_mode": self.p.ClaimMode("OBSERVED_FACT"),
            "temporal_scope": self.p.TemporalScope("CURRENT"),
            "material": True,
            "critical": False,
        }
        values.update(overrides)
        return self.p.ValidationContext(**values)

    def build_assessment_context(self, minimum=1, **overrides):
        values = {
            "validation_context": self.build_context(),
            "minimum_independent_sources": minimum,
        }
        values.update(overrides)
        return self.a.AssessmentContext(**values)

    def build_policy(self, **overrides):
        values = {
            "source_registry": {
                ("Example Review Hub", "customer_reviews"): self.p.SourceClass(
                    "CONSUMER_REVIEW_DISCUSSION"
                ),
                ("Example Marketplace", "marketplace_listing"): self.p.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
            },
            "max_current_verification_age": 365,
        }
        values.update(overrides)
        return self.p.EvidencePolicy(**values)

    def build_evidence(self, value="E001", **overrides):
        values = {
            "id": self.eid(value),
            "claim": f"Explicit VOC proposition support for {value}.",
            "evidence": f"Observed customer language for {value}.",
            "source": self.e.Source(
                provider="Example Review Hub",
                source_type="customer_reviews",
                reference=f"https://example.test/reviews/{value}",
                title=f"Review {value}",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.e.Tier("Tier 3"),
            "status": self.e.Status("Observed"),
            "confidence": self.e.Confidence("High"),
            "metadata": {
                "provider_metadata": {"record_count": 1},
                "provenance": "review-page",
                "source_family": "social",
                "policy": {"kind": "voc", "source_date": AS_OF.date().isoformat()},
            },
        }
        values.update(overrides)
        return self.e.Evidence(**values)

    def relation(self, evidence_id, stance="SUPPORTS"):
        return self.a.EvidenceRelation(self.eid(evidence_id), self.a.Stance(stance))

    def independence(self, evidence_id, group_id=None):
        if group_id is None:
            group_id = f"group-{evidence_id}"
        return self.a.IndependenceAssignment(self.eid(evidence_id), group_id)

    def missing(self, key, severity="MATERIAL"):
        return self.a.MissingInformation(key, self.a.MissingSeverity(severity))

    def proposition(
        self,
        category="PAIN_POINT",
        proposition="Customers struggle with setup.",
        evidence_ids=("E001",),
        relations=None,
        independence=None,
        missing_information=(),
        context=None,
        complaint_characterization=None,
    ):
        ids = tuple(self.eid(value) for value in evidence_ids)
        if relations is None:
            relations = tuple(self.relation(value.value) for value in ids)
        if independence is None:
            independence = tuple(self.independence(value.value) for value in ids)
        if context is None:
            context = self.build_assessment_context()
        return self.voc.VOCPropositionInput(
            category=self.voc.VOCCategory(category),
            proposition=proposition,
            evidence_ids=ids,
            relations=tuple(relations),
            independence=tuple(independence),
            missing_information=tuple(missing_information),
            assessment_context=context,
            complaint_characterization=complaint_characterization,
        )

    def complaint_characterization(
        self,
        prevalence="COMMON",
        prevalence_evidence_ids=("E001",),
        scope="CATEGORY_WIDE",
        scope_evidence_ids=("E001",),
    ):
        return self.voc.ComplaintCharacterizationInput(
            prevalence=self.voc.ComplaintPrevalence(prevalence),
            prevalence_evidence_ids=tuple(self.eid(value) for value in prevalence_evidence_ids),
            scope=self.voc.ComplaintScope(scope),
            scope_evidence_ids=tuple(self.eid(value) for value in scope_evidence_ids),
        )

    def analyze(self, propositions=(), evidence_index=None, policy=None):
        if evidence_index is None:
            evidence_index = {}
        return self.voc.analyze_voc(
            propositions,
            evidence_index,
            policy or self.build_policy(),
        )

    def values(self, collection):
        return tuple(value.value for value in collection)


class VOCModulePresenceTests(unittest.TestCase):
    def test_voc_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("product_research.voc"))


class VOCVocabularyTests(VOCTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        expected = {
            "VOCCategory": CATEGORIES,
            "VOCFindingOutcome": ("SUPPORTED", "UNKNOWN"),
            "ComplaintPrevalence": ("COMMON", "EDGE_CASE", "UNKNOWN"),
            "ComplaintScope": ("PRODUCT_SPECIFIC", "CATEGORY_WIDE", "UNKNOWN"),
        }
        for name, allowed in expected.items():
            value_type = getattr(self.voc, name)
            self.assertEqual(value_type._allowed, allowed)
            value = value_type(allowed[0])
            with self.assertRaises(AttributeError):
                value._value = "OTHER"
            with self.assertRaises(AttributeError):
                del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        for name in (
            "VOCCategory",
            "VOCFindingOutcome",
            "ComplaintPrevalence",
            "ComplaintScope",
        ):
            value_type = getattr(self.voc, name)
            for invalid in ("pain_point", "Pain Point", "OTHER", 1, None):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises((TypeError, ValueError)):
                        value_type(invalid)


class VOCInputValueTests(VOCTestBase):
    def test_proposition_is_frozen_and_canonicalizes_explicit_inputs(self):
        value = self.proposition(
            evidence_ids=("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z"), self.missing("a")),
        )
        self.assertEqual(self.values(value.evidence_ids), ("E001", "E002"))
        self.assertEqual(self.values(relation.evidence_id for relation in value.relations), ("E001", "E002"))
        self.assertEqual(tuple(entry.key for entry in value.missing_information), ("a", "z"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.proposition = "changed"

    def test_proposition_preserves_exact_non_empty_utf8_text(self):
        proposition = self.proposition(proposition="  原始 VOC 断言  ")
        self.assertEqual(proposition.proposition, "  原始 VOC 断言  ")
        for invalid in ("", "\ud800", 1, None):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises((TypeError, ValueError)):
                    self.proposition(proposition=invalid)

    def test_complaint_characterization_is_frozen_and_requires_axis_support_for_non_unknown(self):
        value = self.complaint_characterization(
            prevalence="COMMON",
            prevalence_evidence_ids=("E002", "E001"),
            scope="CATEGORY_WIDE",
            scope_evidence_ids=("E001",),
        )
        self.assertEqual(self.values(value.prevalence_evidence_ids), ("E001", "E002"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.scope = self.voc.ComplaintScope("UNKNOWN")
        unknown = self.complaint_characterization(
            prevalence="UNKNOWN", prevalence_evidence_ids=(), scope="UNKNOWN", scope_evidence_ids=()
        )
        self.assertEqual(unknown.prevalence.value, "UNKNOWN")
        with self.assertRaises((TypeError, ValueError)):
            self.complaint_characterization(prevalence="UNKNOWN", prevalence_evidence_ids=("E001",))

    def test_complaint_characterization_cannot_attach_to_non_complaint(self):
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                category="PAIN_POINT",
                complaint_characterization=self.complaint_characterization(),
            )

    def test_result_values_are_frozen_typed_and_have_no_scoring_fields(self):
        result = self.analyze()
        self.assertIs(type(result), self.voc.VOCResult)
        self.assertEqual(result.findings, ())
        for field in (
            "supported_categories",
            "unknown_categories",
            "missing_categories",
            "findings",
            "duplicate_proposition_keys",
            "factors",
        ):
            self.assertTrue(hasattr(result, field))
            self.assertIs(type(getattr(result, field)), tuple)
        self.assertFalse(
            any(
                name in result.__dataclass_fields__
                for name in ("score", "threshold", "weight", "recommendation")
            )
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.findings = ()

    def test_proposition_key_and_finding_values_are_frozen_and_typed(self):
        evidence = self.build_evidence("E001")
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        key = self.voc.VOCPropositionKey(self.voc.VOCCategory("PAIN_POINT"), "key")
        self.assertEqual(key.proposition, "key")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            key.proposition = "changed"
        finding = result.findings[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            finding.outcome = self.voc.VOCFindingOutcome("UNKNOWN")

    def test_empty_text_and_duplicate_ids_are_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(evidence_ids=("E001", "E001"))
        with self.assertRaises((TypeError, ValueError)):
            self.complaint_characterization(
                prevalence_evidence_ids=("E001", "E001"), scope_evidence_ids=()
            )


class VOCFindingAnalysisTests(VOCTestBase):
    def test_every_closed_category_can_produce_a_supported_finding(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 9))
        propositions = tuple(
            self.proposition(
                category=category,
                proposition=f"explicit {category}",
                evidence_ids=(evidence.id.value,),
            )
            for category, evidence in zip(CATEGORIES, evidences)
        )
        complaint = self.proposition(
            category="COMPLAINT",
            proposition="explicit complaint",
            evidence_ids=("E003",),
            complaint_characterization=self.complaint_characterization(),
        )
        propositions = propositions[:2] + (complaint,) + propositions[3:]
        result = self.analyze(
            propositions,
            {evidence.id: evidence for evidence in evidences},
        )
        self.assertEqual(self.values(result.supported_categories), CATEGORIES)
        self.assertEqual(result.unknown_categories, ())
        self.assertEqual(result.missing_categories, ())
        self.assertEqual(
            tuple((finding.category.value, finding.proposition) for finding in result.findings),
            tuple((category, f"explicit {category}") for category in CATEGORIES[:2])
            + (("COMPLAINT", "explicit complaint"),)
            + tuple((category, f"explicit {category}") for category in CATEGORIES[3:]),
        )
        for finding in result.findings:
            self.assertEqual(finding.outcome, self.voc.VOCFindingOutcome("SUPPORTED"))
            self.assertIs(type(finding.assessment), self.a.EvidenceAssessmentResult)
            self.assertEqual(finding.supporting_ids, finding.assessment.usable_ids)

    def test_evidence_text_or_metadata_alone_creates_no_proposition(self):
        evidence = self.build_evidence(
            "E001",
            claim="This sounds like a pain point, segment, and purchase motivation.",
            evidence="Customer review says this is a common complaint.",
            metadata={
                "provider": "review-provider",
                "record_count": 1000,
                "provenance": "social",
                "policy": {"kind": "voc", "source_date": AS_OF.date().isoformat()},
            },
        )
        result = self.analyze(evidence_index={evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertEqual(result.supported_categories, ())
        self.assertEqual(self.values(result.missing_categories), CATEGORIES)

    def test_each_unique_proposition_is_assessed_once_and_preserves_its_result(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 4))
        propositions = (
            self.proposition("PAIN_POINT", "first", ("E001",)),
            self.proposition("PAIN_POINT", "second", ("E002",)),
            self.proposition("USE_CASE", "third", ("E003",)),
        )
        original = self.voc.assess_evidence
        assessments = []

        def record(*args):
            value = original(*args)
            assessments.append(value)
            return value

        with mock.patch.object(self.voc, "assess_evidence", side_effect=record) as assessed:
            result = self.analyze(propositions, {value.id: value for value in evidences})
        self.assertEqual(assessed.call_count, 3)
        by_proposition = {
            proposition.proposition: assessment
            for proposition, assessment in zip(propositions, assessments)
        }
        for finding in result.findings:
            self.assertIs(finding.assessment, by_proposition[finding.proposition])

    def test_assessment_minimum_independent_sources_is_proposition_specific(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        one_source = self.proposition(
            proposition="one source",
            evidence_ids=("E001",),
            context=self.build_assessment_context(minimum=1),
        )
        two_sources = self.proposition(
            proposition="two sources",
            evidence_ids=("E001", "E002"),
            context=self.build_assessment_context(minimum=2),
        )
        result = self.analyze((one_source, two_sources), {value.id: value for value in evidences})
        findings = {finding.proposition: finding for finding in result.findings}
        self.assertEqual(findings["one source"].outcome.value, "SUPPORTED")
        self.assertEqual(findings["two sources"].outcome.value, "SUPPORTED")
        self.assertEqual(findings["one source"].assessment.independent_source_count, 1)
        self.assertEqual(findings["two sources"].assessment.independent_source_count, 2)

    def test_supported_confidence_is_identical_to_assessment_without_upgrade(self):
        for confidence in ("High", "Medium", "Low"):
            with self.subTest(confidence=confidence):
                evidence = self.build_evidence("E001", confidence=self.e.Confidence(confidence))
                finding = self.analyze(
                    (self.proposition(),), {evidence.id: evidence}
                ).findings[0]
                self.assertEqual(finding.outcome.value, "SUPPORTED")
                self.assertEqual(finding.confidence, finding.assessment.confidence)
                self.assertEqual(finding.confidence.value, confidence)

    def test_conflict_is_unknown_and_retains_adverse_and_excluded_ids(self):
        support = self.build_evidence("E001")
        adverse = self.build_evidence(
            "E002",
            tier=self.e.Tier("Tier 3"),
        )
        stale = self.build_evidence(
            "E003",
            metadata={"policy": {"kind": "voc", "source_date": (AS_OF.date() - timedelta(days=731)).isoformat()}},
        )
        proposition = self.proposition(
            evidence_ids=("E001", "E002", "E003"),
            relations=(self.relation("E001"), self.relation("E002", "CONTRADICTS"), self.relation("E003", "CONTRADICTS")),
            independence=(self.independence("E001"), self.independence("E002"), self.independence("E003")),
        )
        finding = self.analyze(
            (proposition,), {value.id: value for value in (support, adverse, stale)}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002", "E003"))
        self.assertEqual(self.values(finding.excluded_ids), ("E003",))
        self.assertEqual(finding.assessment.outcome.value, "CONFLICTED")

    def test_insufficient_and_missing_information_preserve_complete_assessment(self):
        evidence = self.build_evidence("E001")
        missing = self.missing("unresolved_customer_need", "MATERIAL")
        proposition = self.proposition(
            evidence_ids=("E001",),
            relations=(self.relation("E001", "NEUTRAL"),),
            missing_information=(missing,),
        )
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.assessment.missing_information, (missing,))
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertEqual(finding.supporting_ids, ())

    def test_material_missing_information_preserves_supported_low_assessment(self):
        evidence = self.build_evidence("E001")
        missing = self.missing("material_gap", "MATERIAL")
        proposition = self.proposition(missing_information=(missing,))
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.confidence, finding.assessment.confidence)
        self.assertEqual(finding.assessment.missing_information, (missing,))

    def test_stale_support_preserves_policy_and_assessment_diagnostics(self):
        stale = self.build_evidence(
            "E001",
            metadata={
                "policy": {
                    "kind": "voc",
                    "source_date": (AS_OF.date() - timedelta(days=731)).isoformat(),
                }
            },
        )
        finding = self.analyze((self.proposition(),), {stale.id: stale}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(self.values(finding.excluded_ids), ("E001",))
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertEqual(
            tuple(issue.reason_code.value for issue in finding.assessment.policy_results[0].issues),
            ("STALE_EVIDENCE",),
        )

    def test_missing_citation_and_unresolved_id_remain_unknown_without_placeholder_support(self):
        missing = self.proposition(evidence_ids=(), relations=(), independence=())
        unresolved = self.proposition(
            proposition="unresolved",
            evidence_ids=("E999",),
            relations=(self.relation("E999"),),
            independence=(self.independence("E999"),),
        )
        result = self.analyze((missing, unresolved), {})
        findings = {finding.proposition: finding for finding in result.findings}
        self.assertEqual(findings["Customers struggle with setup."].outcome.value, "UNKNOWN")
        self.assertEqual(findings["Customers struggle with setup."].supporting_ids, ())
        self.assertEqual(
            findings["Customers struggle with setup."].assessment.claim_support_result.issues[0].reason_code.value,
            "MISSING_CITATION",
        )
        self.assertEqual(findings["unresolved"].outcome.value, "UNKNOWN")
        self.assertEqual(findings["unresolved"].supporting_ids, ())

    def test_critical_missing_information_preserves_existing_low_confidence(self):
        evidence = self.build_evidence("E001")
        proposition = self.proposition(
            missing_information=(self.missing("critical_gap", "CRITICAL"),),
            context=self.build_assessment_context(
                validation_context=self.build_context(critical=True)
            ),
        )
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.assessment.outcome.value, "SUPPORTED")
        self.assertEqual(finding.assessment.confidence.value, "Low")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.assessment.missing_information[0].severity.value, "CRITICAL")

    def test_incomplete_assignments_fail_only_that_proposition(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 3))
        invalid = self.proposition(
            proposition="incomplete",
            evidence_ids=("E001", "E002"),
            relations=(self.relation("E001"),),
            independence=(self.independence("E001"),),
        )
        valid = self.proposition("USE_CASE", "valid", ("E002",))
        result = self.analyze((invalid, valid), {value.id: value for value in evidences})
        findings = {finding.proposition: finding for finding in result.findings}
        self.assertEqual(findings["incomplete"].outcome.value, "UNKNOWN")
        self.assertEqual(findings["incomplete"].assessment.factors[0].value, "ASSESSMENT_INPUT_ERROR")
        self.assertEqual(findings["valid"].outcome.value, "SUPPORTED")


class VOCCoverageAndDuplicateTests(VOCTestBase):
    def test_coverage_is_fixed_order_exhaustive_and_mutually_exclusive(self):
        support = self.build_evidence("E001")
        unknown = self.proposition(
            "PAIN_POINT",
            "unsupported",
            evidence_ids=("E001",),
            relations=(self.relation("E001", "NEUTRAL"),),
        )
        supported = self.proposition("PAIN_POINT", "supported", evidence_ids=("E001",))
        supplied_missing = self.proposition(
            "COMPLAINT", "complaint", evidence_ids=(), relations=(), independence=()
        )
        result = self.analyze(
            (unknown, supported, supplied_missing), {support.id: support}
        )
        self.assertEqual(self.values(result.supported_categories), ("PAIN_POINT",))
        self.assertEqual(self.values(result.unknown_categories), ("COMPLAINT",))
        self.assertEqual(
            tuple((finding.proposition, finding.outcome.value) for finding in result.findings),
            (("supported", "SUPPORTED"), ("unsupported", "UNKNOWN"), ("complaint", "UNKNOWN")),
        )
        self.assertEqual(
            self.values(result.missing_categories),
            ("PURCHASE_MOTIVATION", "UNMET_NEED", "USE_CASE", "PURCHASE_BARRIER", "CUSTOMER_LANGUAGE", "SEGMENT"),
        )
        self.assertEqual(
            set(self.values(result.supported_categories))
            | set(self.values(result.unknown_categories))
            | set(self.values(result.missing_categories)),
            set(CATEGORIES),
        )

    def test_duplicate_keys_have_no_winner_but_other_unique_propositions_are_assessed(self):
        evidence = self.build_evidence("E001")
        duplicate_one = self.proposition("PAIN_POINT", "same", evidence_ids=("E001",))
        duplicate_two = self.proposition("PAIN_POINT", "same", evidence_ids=())
        unique = self.proposition("USE_CASE", "other", evidence_ids=("E001",))
        with mock.patch.object(self.voc, "assess_evidence", wraps=self.voc.assess_evidence) as assessed:
            result = self.analyze(
                (duplicate_two, unique, duplicate_one), {evidence.id: evidence}
            )
        self.assertEqual(assessed.call_count, 1)
        self.assertEqual(len(result.duplicate_proposition_keys), 1)
        self.assertEqual(result.duplicate_proposition_keys[0].proposition, "same")
        self.assertEqual(result.duplicate_proposition_keys[0].category.value, "PAIN_POINT")
        self.assertEqual(tuple(finding.proposition for finding in result.findings), ("other",))
        self.assertEqual(self.values(result.unknown_categories), ("PAIN_POINT",))
        self.assertIn(self.voc.VOCFactor("DUPLICATE_PROPOSITION"), result.factors)

    def test_duplicate_permutations_have_equal_results(self):
        evidence = self.build_evidence("E001")
        first = self.proposition("PAIN_POINT", "same", evidence_ids=("E001",))
        second = self.proposition("PAIN_POINT", "same", evidence_ids=())
        unique = self.proposition("USE_CASE", "other", evidence_ids=("E001",))
        left = self.analyze((first, second, unique), {evidence.id: evidence})
        right = self.analyze((unique, second, first), {evidence.id: evidence})
        self.assertEqual(left, right)


class VOCComplaintTests(VOCTestBase):
    def test_supported_complaint_preserves_independent_explicit_axes(self):
        evidence = self.build_evidence("E001")
        second = self.build_evidence("E002")
        characterization = self.complaint_characterization(
            prevalence="COMMON",
            prevalence_evidence_ids=("E002",),
            scope="CATEGORY_WIDE",
            scope_evidence_ids=("E001",),
        )
        finding = self.analyze(
            (
                self.proposition(
                    "COMPLAINT",
                    "explicit complaint",
                    evidence_ids=("E001", "E002"),
                    complaint_characterization=characterization,
                ),
            ),
            {evidence.id: evidence, second.id: second},
        ).findings[0]
        self.assertEqual(finding.prevalence.value, "COMMON")
        self.assertEqual(finding.scope.value, "CATEGORY_WIDE")
        self.assertEqual(self.values(finding.prevalence_supporting_ids), ("E002",))
        self.assertEqual(self.values(finding.scope_supporting_ids), ("E001",))

    def test_each_unsupported_complaint_axis_downgrades_independently(self):
        evidence = self.build_evidence("E001")
        characterization = self.complaint_characterization(
            prevalence="COMMON",
            prevalence_evidence_ids=("E999",),
            scope="CATEGORY_WIDE",
            scope_evidence_ids=(),
        )
        finding = self.analyze(
            (self.proposition("COMPLAINT", "axis complaint", complaint_characterization=characterization),),
            {evidence.id: evidence},
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.prevalence.value, "UNKNOWN")
        self.assertEqual(finding.prevalence_supporting_ids, ())
        self.assertEqual(finding.scope.value, "UNKNOWN")
        self.assertEqual(finding.scope_supporting_ids, ())
        factor_values = self.values(finding.factors)
        self.assertIn("PREVALENCE_SUPPORT_UNAVAILABLE", factor_values)
        self.assertIn("SCOPE_SUPPORT_UNAVAILABLE", factor_values)

    def test_policy_excluded_axis_evidence_downgrades_only_that_axis(self):
        usable = self.build_evidence("E001")
        stale = self.build_evidence(
            "E002",
            metadata={
                "policy": {
                    "kind": "voc",
                    "source_date": (AS_OF.date() - timedelta(days=731)).isoformat(),
                }
            },
        )
        characterization = self.complaint_characterization(
            prevalence="COMMON",
            prevalence_evidence_ids=("E002",),
            scope="PRODUCT_SPECIFIC",
            scope_evidence_ids=("E001",),
        )
        proposition = self.proposition(
            "COMPLAINT",
            "excluded axis support",
            evidence_ids=("E001", "E002"),
            complaint_characterization=characterization,
        )
        finding = self.analyze(
            (proposition,), {usable.id: usable, stale.id: stale}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.prevalence.value, "UNKNOWN")
        self.assertEqual(finding.prevalence_supporting_ids, ())
        self.assertIn(
            self.voc.VOCFactor("PREVALENCE_SUPPORT_UNAVAILABLE"), finding.factors
        )
        self.assertEqual(finding.scope.value, "PRODUCT_SPECIFIC")
        self.assertEqual(self.values(finding.scope_supporting_ids), ("E001",))
        self.assertNotIn(self.voc.VOCFactor("SCOPE_SUPPORT_UNAVAILABLE"), finding.factors)

    def test_unknown_axes_are_not_inferred_from_text_metadata_or_ordering(self):
        evidence = self.build_evidence(
            "E001",
            claim="Everyone has this complaint across the category.",
            evidence="COMMON CATEGORY_WIDE complaint",
        )
        characterization = self.complaint_characterization(
            prevalence="UNKNOWN", prevalence_evidence_ids=(), scope="UNKNOWN", scope_evidence_ids=()
        )
        finding = self.analyze(
            (self.proposition("COMPLAINT", "unknown complaint", complaint_characterization=characterization),),
            {evidence.id: evidence},
        ).findings[0]
        self.assertEqual(finding.prevalence.value, "UNKNOWN")
        self.assertEqual(finding.scope.value, "UNKNOWN")
        self.assertEqual(finding.prevalence_supporting_ids, ())
        self.assertEqual(finding.scope_supporting_ids, ())

    def test_unknown_finding_cannot_retain_optimistic_complaint_axes(self):
        evidence = self.build_evidence("E001")
        characterization = self.complaint_characterization()
        proposition = self.proposition(
            "COMPLAINT",
            "conflicted complaint",
            evidence_ids=("E001",),
            relations=(self.relation("E001", "CONTRADICTS"),),
            complaint_characterization=characterization,
        )
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.prevalence.value, "UNKNOWN")
        self.assertEqual(finding.scope.value, "UNKNOWN")
        self.assertEqual(finding.prevalence_supporting_ids, ())
        self.assertEqual(finding.scope_supporting_ids, ())
        self.assertIn(
            self.voc.VOCFactor("PREVALENCE_SUPPORT_UNAVAILABLE"), finding.factors
        )
        self.assertIn(self.voc.VOCFactor("SCOPE_SUPPORT_UNAVAILABLE"), finding.factors)


class VOCReplayAndOwnershipTests(VOCTestBase):
    def test_equivalent_input_permutations_replay_identically(self):
        first = self.build_evidence("E001")
        second = self.build_evidence("E002")
        proposition = self.proposition(
            "COMPLAINT",
            "permutation",
            evidence_ids=("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z"), self.missing("a")),
            complaint_characterization=self.complaint_characterization(
                prevalence_evidence_ids=("E002", "E001"), scope_evidence_ids=("E001",)
            ),
        )
        reordered = self.proposition(
            "COMPLAINT",
            "permutation",
            evidence_ids=("E001", "E002"),
            relations=(self.relation("E001"), self.relation("E002")),
            independence=(self.independence("E001"), self.independence("E002")),
            missing_information=(self.missing("a"), self.missing("z")),
            complaint_characterization=self.complaint_characterization(
                prevalence_evidence_ids=("E001", "E002"), scope_evidence_ids=("E001",)
            ),
        )
        index = {first.id: first, second.id: second}
        self.assertEqual(self.analyze((proposition,), index), self.analyze((reordered,), {second.id: second, first.id: first}))

    def test_analysis_does_not_mutate_inputs_or_policy(self):
        evidence = self.build_evidence("E001")
        proposition = self.proposition()
        index = {evidence.id: evidence}
        policy = self.build_policy()
        snapshot = (copy.deepcopy(evidence), copy.deepcopy(proposition), copy.deepcopy(index), policy)
        self.analyze((proposition,), index, policy)
        self.assertEqual(evidence, snapshot[0])
        self.assertEqual(proposition, snapshot[1])
        self.assertEqual(index, snapshot[2])
        self.assertEqual(policy, snapshot[3])

    def test_malformed_shared_index_blocks_all_support_with_stable_input_error(self):
        evidence = self.build_evidence("E001")
        proposition = self.proposition()
        malformed = {self.eid("E001"): self.build_evidence("E002")}
        result = self.analyze((proposition,), malformed)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.factors, (self.voc.VOCFactor("VOC_INPUT_ERROR"),))
        self.assertEqual(self.values(result.unknown_categories), ("PAIN_POINT",))

    def test_malformed_proposition_collection_and_policy_fail_closed(self):
        evidence = self.build_evidence("E001")
        proposition = self.proposition()
        malformed_collection = self.analyze((proposition, object()), {evidence.id: evidence})
        self.assertEqual(malformed_collection.findings, ())
        self.assertEqual(malformed_collection.factors, (self.voc.VOCFactor("VOC_INPUT_ERROR"),))
        malformed_policy = self.analyze((proposition,), {evidence.id: evidence}, policy=object())
        self.assertEqual(malformed_policy.findings, ())
        self.assertEqual(malformed_policy.factors, (self.voc.VOCFactor("VOC_INPUT_ERROR"),))

    def test_programmer_control_base_exception_is_not_swallowed(self):
        evidence = self.build_evidence("E001")
        with mock.patch.object(self.voc, "assess_evidence", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.analyze((self.proposition(),), {evidence.id: evidence})

    def test_static_scope_and_import_audit(self):
        with open(self.voc.__file__, encoding="utf-8") as source_file:
            source = source_file.read()
        tree = ast.parse(source)
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        imported = set()
        for node in imports:
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            else:
                imported.add((node.module or "").split(".")[0])
        self.assertEqual(
            imported,
            {"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy"},
        )
        source_text = source.lower()
        forbidden = (
            "requests",
            "httpx",
            "urllib",
            "browser",
            "network",
            "scrap",
            "provider",
            "retry",
            "cache",
            "clock",
            "environment",
            "rawfinding",
            "acquisitionresult",
            "run_research",
            "normalization",
            "random",
            "asyncio",
            "embedding",
            "nlp",
            "llm",
            "cluster",
            "score",
            "threshold",
            "weight",
            "recommendation",
            "red team",
            "brand analysis",
            "content analysis",
            "supply chain",
            "risk analysis",
            "persistence",
            "report",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source_text)
