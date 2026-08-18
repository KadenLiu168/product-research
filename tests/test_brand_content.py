import ast
import copy
import dataclasses
import importlib
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
DIMENSIONS = ("BRAND_POTENTIAL", "CONTENT_POTENTIAL")
ASPECTS = (
    "BRAND_PREMIUM",
    "STORYTELLING",
    "VISUAL_EXPRESSION",
    "DEMO_POTENTIAL",
    "UGC_PROPAGATION",
)
FACTORS = (
    "BRAND_CONTENT_INPUT_ERROR",
    "DUPLICATE_PROPOSITION",
    "ASSESSMENT_INPUT_ERROR",
    "ASSESSMENT_NOT_SUPPORTED",
)


class BrandContentTestBase(unittest.TestCase):
    def setUp(self):
        self.brand = importlib.import_module("product_research.brand_content")
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
                ("Example Supplier", "supplier_quote"): self.p.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
                ("Example Marketplace", "marketplace_listing"): self.p.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
            },
            "max_current_verification_age": 365,
        }
        values.update(overrides)
        return self.p.EvidencePolicy(**values)

    def build_evidence(
        self,
        value="E001",
        *,
        status="Observed",
        confidence="High",
        source_date=None,
        provider="Example Supplier",
        source_type="supplier_quote",
        tier="Tier 2",
        **overrides,
    ):
        if source_date is None:
            source_date = AS_OF.date().isoformat()
        values = {
            "id": self.eid(value),
            "claim": f"Explicit Brand Content support for {value}.",
            "evidence": f"Caller-declared support for {value}.",
            "source": self.e.Source(
                provider=provider,
                source_type=source_type,
                reference=f"https://example.test/record/{value}",
                title=f"Record {value}",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.e.Tier(tier),
            "status": self.e.Status(status),
            "confidence": self.e.Confidence(confidence),
            "metadata": {
                "provider_metadata": {"record_count": 1},
                "provenance": "explicit-caller-record",
                "source_family": "SUPPLIER",
                "policy": {"kind": "supplier_quotation", "source_date": source_date},
            },
        }
        values.update(overrides)
        return self.e.Evidence(**values)

    def relation(self, evidence_id, stance="SUPPORTS"):
        return self.a.EvidenceRelation(self.eid(evidence_id), self.a.Stance(stance))

    def independence(self, evidence_id, group_id=None):
        return self.a.IndependenceAssignment(
            self.eid(evidence_id), group_id if group_id is not None else f"group-{evidence_id}"
        )

    def missing(self, key, severity="MATERIAL"):
        return self.a.MissingInformation(key, self.a.MissingSeverity(severity))

    def proposition(
        self,
        dimension="BRAND_POTENTIAL",
        aspect="BRAND_PREMIUM",
        proposition="The product supports a premium brand position.",
        evidence_ids=("E001",),
        relations=None,
        independence=None,
        missing_information=(),
        context=None,
    ):
        ids = tuple(self.eid(value) for value in evidence_ids)
        if relations is None:
            relations = tuple(self.relation(value.value) for value in ids)
        if independence is None:
            independence = tuple(self.independence(value.value) for value in ids)
        if context is None:
            context = self.build_assessment_context()
        return self.brand.BrandContentPropositionInput(
            dimension=self.brand.BrandContentDimension(dimension),
            aspect=self.brand.BrandContentAspect(aspect),
            proposition=proposition,
            evidence_ids=ids,
            relations=tuple(relations),
            independence=tuple(independence),
            missing_information=tuple(missing_information),
            assessment_context=context,
        )

    def analyze(self, propositions=(), evidence_index=None, policy=None):
        return self.brand.analyze_brand_content(
            propositions,
            {} if evidence_index is None else evidence_index,
            self.build_policy() if policy is None else policy,
        )

    def values(self, collection):
        return tuple(value.value for value in collection)


class BrandContentVocabularyTests(BrandContentTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        expected = {
            "BrandContentDimension": DIMENSIONS,
            "BrandContentAspect": ASPECTS,
            "BrandContentFindingOutcome": ("SUPPORTED", "UNKNOWN"),
            "BrandContentFactor": FACTORS,
        }
        for name, allowed in expected.items():
            value_type = getattr(self.brand, name)
            self.assertEqual(value_type._allowed, allowed)
            value = value_type(allowed[0])
            with self.assertRaises(AttributeError):
                value._value = "OTHER"
            with self.assertRaises(AttributeError):
                del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        for name in (
            "BrandContentDimension",
            "BrandContentAspect",
            "BrandContentFindingOutcome",
            "BrandContentFactor",
        ):
            value_type = getattr(self.brand, name)
            for invalid in ("BRAND_PREMIUM ", "brand_premium", "BrandPremium", "OTHER", 1, None):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises((TypeError, ValueError)):
                        value_type(invalid)

    def test_module_has_one_public_analysis_entry_point_and_no_generic_framework(self):
        self.assertTrue(callable(self.brand.analyze_brand_content))
        self.assertFalse(hasattr(self.brand, "StructuredAnalysis"))
        self.assertFalse(hasattr(self.brand, "RawFinding"))


class BrandContentInputValueTests(BrandContentTestBase):
    def test_proposition_is_frozen_and_canonicalizes_explicit_inputs(self):
        value = self.proposition(
            evidence_ids=("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z"), self.missing("a")),
        )
        self.assertEqual(self.values(value.evidence_ids), ("E001", "E002"))
        self.assertEqual(
            self.values(relation.evidence_id for relation in value.relations), ("E001", "E002")
        )
        self.assertEqual(tuple(entry.key for entry in value.missing_information), ("a", "z"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.proposition = "changed"

    def test_proposition_preserves_exact_non_empty_utf8_text(self):
        proposition = self.proposition(proposition="  原始 Brand 命题  ")
        self.assertEqual(proposition.proposition, "  原始 Brand 命题  ")
        for invalid in ("", "\ud800", 1, None):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises((TypeError, ValueError)):
                    self.proposition(proposition=invalid)

    def test_duplicate_ids_and_assignments_are_rejected_without_normalization(self):
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(evidence_ids=("E001", "E001"))
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(relations=(self.relation("E001"), self.relation("E001")))
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                independence=(self.independence("E001"), self.independence("E001"))
            )
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                missing_information=(self.missing("same"), self.missing("same"))
            )

    def test_invalid_context_and_non_tuple_inputs_are_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(context=object())
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                context=self.build_assessment_context(
                    validation_context=self.build_context(material=False)
                )
            )
        with self.assertRaises((TypeError, ValueError)):
            self.brand.BrandContentPropositionInput(
                dimension=self.brand.BrandContentDimension("BRAND_POTENTIAL"),
                aspect=self.brand.BrandContentAspect("BRAND_PREMIUM"),
                proposition="valid",
                evidence_ids=[self.eid("E001")],
                relations=(),
                independence=(),
                missing_information=(),
                assessment_context=self.build_assessment_context(),
            )

    def test_key_finding_and_result_values_are_frozen_typed_and_non_numeric(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        key = self.brand.BrandContentPropositionKey(
            self.brand.BrandContentDimension("BRAND_POTENTIAL"),
            self.brand.BrandContentAspect("BRAND_PREMIUM"),
            "exact key",
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            key.proposition = "changed"
        self.assertIs(type(result), self.brand.BrandContentResult)
        for field in (
            "supported_aspects",
            "unknown_aspects",
            "missing_aspects",
            "findings",
            "duplicate_proposition_keys",
            "factors",
        ):
            self.assertIs(type(getattr(result, field)), tuple)
        self.assertFalse(
            any(
                name in result.__dataclass_fields__
                for name in ("score", "weight", "threshold", "recommendation", "decision")
            )
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.findings = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.findings[0].outcome = self.brand.BrandContentFindingOutcome("UNKNOWN")

    def test_all_explicit_pairs_are_representable_without_a_compatibility_matrix(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 11))
        propositions = tuple(
            self.proposition(
                dimension=DIMENSIONS[index // 5],
                aspect=aspect,
                proposition=f"explicit {DIMENSIONS[index // 5]} {aspect}",
                evidence_ids=(evidences[index].id.value,),
            )
            for index, aspect in enumerate(ASPECTS * 2)
        )
        result = self.analyze(propositions, {e.id: e for e in evidences})
        self.assertEqual(self.values(result.supported_aspects), ASPECTS)
        self.assertEqual(
            tuple((finding.dimension.value, finding.aspect.value) for finding in result.findings),
            tuple((dimension, aspect) for dimension in DIMENSIONS for aspect in ASPECTS),
        )

    def test_same_text_and_evidence_under_two_dimensions_stays_distinct(self):
        evidence = self.build_evidence()
        propositions = (
            self.proposition("BRAND_POTENTIAL", "STORYTELLING", "same text"),
            self.proposition("CONTENT_POTENTIAL", "STORYTELLING", "same text"),
        )
        result = self.analyze(propositions, {evidence.id: evidence})
        self.assertEqual(
            tuple((f.dimension.value, f.aspect.value, f.proposition) for f in result.findings),
            (("BRAND_POTENTIAL", "STORYTELLING", "same text"),
             ("CONTENT_POTENTIAL", "STORYTELLING", "same text")),
        )


class BrandContentFindingAnalysisTests(BrandContentTestBase):
    def test_evidence_text_metadata_and_voc_values_do_not_create_a_finding(self):
        evidence = self.build_evidence(
            claim="premium storytelling visual demo UGC",
            evidence="Every creative fact is in this record.",
            metadata={"keywords": ["premium", "story"], "policy": {
                "kind": "supplier_quotation", "source_date": AS_OF.date().isoformat()
            }},
        )
        result = self.analyze(evidence_index={evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertEqual(self.values(result.missing_aspects), ASPECTS)

    def test_each_unique_proposition_is_assessed_once_and_stays_isolated(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 4))
        propositions = (
            self.proposition("BRAND_POTENTIAL", "BRAND_PREMIUM", "first", ("E001",)),
            self.proposition("BRAND_POTENTIAL", "BRAND_PREMIUM", "second", ("E002",)),
            self.proposition("CONTENT_POTENTIAL", "DEMO_POTENTIAL", "third", ("E003",)),
        )
        original = self.brand.assess_evidence
        calls = []

        def record(*args):
            calls.append(args)
            return original(*args)

        with mock.patch.object(self.brand, "assess_evidence", side_effect=record) as assessed:
            result = self.analyze(propositions, {value.id: value for value in evidences})
        self.assertEqual(assessed.call_count, 3)
        self.assertEqual(
            [tuple(value.value for value in call[0]) for call in calls],
            [("E001",), ("E002",), ("E003",)],
        )
        by_proposition = {value.proposition: value for value in result.findings}
        self.assertEqual(by_proposition["first"].assessment.source_count, 1)
        self.assertEqual(by_proposition["second"].assessment.source_count, 1)
        self.assertEqual(by_proposition["third"].assessment.source_count, 1)

    def test_supported_finding_keeps_existing_confidence_without_upgrade(self):
        for confidence in ("High", "Medium", "Low"):
            with self.subTest(confidence=confidence):
                evidence = self.build_evidence(confidence=confidence)
                finding = self.analyze(
                    (self.proposition(),), {evidence.id: evidence}
                ).findings[0]
                self.assertEqual(finding.outcome.value, "SUPPORTED")
                self.assertEqual(finding.confidence, finding.assessment.confidence)
                self.assertEqual(finding.confidence.value, confidence)
                self.assertEqual(evidence.confidence.value, confidence)

    def test_conflict_is_unknown_and_keeps_complete_traceability(self):
        support = self.build_evidence("E001")
        adverse = self.build_evidence("E002")
        stale = self.build_evidence(
            "E003", source_date=(AS_OF.date() - timedelta(days=91)).isoformat()
        )
        proposition = self.proposition(
            evidence_ids=("E001", "E002", "E003"),
            relations=(
                self.relation("E001"),
                self.relation("E002", "CONTRADICTS"),
                self.relation("E003", "CONTRADICTS"),
            ),
            independence=(
                self.independence("E001"),
                self.independence("E002"),
                self.independence("E003"),
            ),
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
        self.assertEqual(self.values(finding.factors), ("ASSESSMENT_NOT_SUPPORTED",))

    def test_non_material_missing_information_follows_existing_assessment(self):
        evidence = self.build_evidence()
        missing = self.missing("non_material_gap", "NON_MATERIAL")
        finding = self.analyze(
            (self.proposition(missing_information=(missing,)),), {evidence.id: evidence}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.confidence, finding.assessment.confidence)
        self.assertEqual(finding.assessment.missing_information, (missing,))

    def test_insufficient_and_policy_rejected_evidence_remain_unknown(self):
        evidence = self.build_evidence("E001", status="Unknown")
        proposition = self.proposition(
            relations=(self.relation("E001", "NEUTRAL"),)
        )
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.supporting_ids, ())
        self.assertTrue(finding.assessment.policy_results)
        self.assertEqual(finding.assessment.claim_support_result.outcome.value, "REJECT")

    def test_assessment_input_error_cannot_support_a_finding(self):
        evidence = self.build_evidence()
        assessment = self.a.EvidenceAssessmentResult(
            outcome=self.a.AssessmentOutcome("SUPPORTED"),
            confidence=self.e.Confidence("High"),
            conflict_state=self.a.ConflictState("NONE"),
            source_count=1,
            independent_source_count=1,
            supporting_ids=(evidence.id,),
            current_accepted_ids=(evidence.id,),
            usable_ids=(evidence.id,),
            factors=(self.a.AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
        )
        with mock.patch.object(self.brand, "assess_evidence", return_value=assessment):
            finding = self.analyze(
                (self.proposition(),), {evidence.id: evidence}
            ).findings[0]
        self.assertIs(finding.assessment, assessment)
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")

    def test_finding_preserves_dimension_aspect_ids_assessment_and_fixed_factors(self):
        evidence = self.build_evidence()
        finding = self.analyze(
            (self.proposition("CONTENT_POTENTIAL", "UGC_PROPAGATION"),),
            {evidence.id: evidence},
        ).findings[0]
        self.assertEqual(finding.dimension.value, "CONTENT_POTENTIAL")
        self.assertEqual(finding.aspect.value, "UGC_PROPAGATION")
        self.assertEqual(finding.proposition, "The product supports a premium brand position.")
        self.assertIs(finding.assessment, finding.assessment)
        self.assertEqual(finding.supporting_ids, finding.assessment.usable_ids)
        self.assertEqual(tuple(value.value for value in finding.factors), ())


class BrandContentCoverageDuplicateReplayTests(BrandContentTestBase):
    def test_coverage_is_fixed_order_exhaustive_and_mutually_exclusive(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        self.assertEqual(self.values(result.supported_aspects), ("BRAND_PREMIUM",))
        self.assertEqual(result.unknown_aspects, ())
        self.assertEqual(
            self.values(result.missing_aspects), tuple(value for value in ASPECTS if value != "BRAND_PREMIUM")
        )
        sets = (
            set(self.values(result.supported_aspects)),
            set(self.values(result.unknown_aspects)),
            set(self.values(result.missing_aspects)),
        )
        self.assertFalse(any(left & right for index, left in enumerate(sets) for right in sets[index + 1:]))
        self.assertEqual(set.union(*sets), set(ASPECTS))

    def test_mixed_supported_and_unknown_aspects_keep_both_dimensions_visible(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        propositions = (
            self.proposition("BRAND_POTENTIAL", "STORYTELLING", "supported", ("E001",)),
            self.proposition(
                "CONTENT_POTENTIAL", "STORYTELLING", "unknown", ("E002",),
                relations=(self.relation("E002", "NEUTRAL"),),
            ),
        )
        result = self.analyze(propositions, {value.id: value for value in evidences})
        self.assertEqual(self.values(result.supported_aspects), ("STORYTELLING",))
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(
            tuple((value.dimension.value, value.aspect.value) for value in result.findings),
            (("BRAND_POTENTIAL", "STORYTELLING"), ("CONTENT_POTENTIAL", "STORYTELLING")),
        )

    def test_duplicate_keys_have_no_assessment_or_winner(self):
        evidence = self.build_evidence()
        first = self.proposition("BRAND_POTENTIAL", "STORYTELLING", "same", ("E001",))
        second = self.proposition("BRAND_POTENTIAL", "STORYTELLING", "same", ("E001",))
        unique = self.proposition("BRAND_POTENTIAL", "STORYTELLING", "unique", ("E001",))
        with mock.patch.object(self.brand, "assess_evidence", wraps=self.brand.assess_evidence) as assessed:
            result = self.analyze((second, unique, first), {evidence.id: evidence})
        self.assertEqual(assessed.call_count, 1)
        self.assertEqual(len(result.duplicate_proposition_keys), 1)
        self.assertEqual(result.duplicate_proposition_keys[0].proposition, "same")
        self.assertEqual(tuple(value.proposition for value in result.findings), ("unique",))
        self.assertEqual(self.values(result.factors), ("DUPLICATE_PROPOSITION",))
        self.assertEqual(self.values(result.supported_aspects), ("STORYTELLING",))

    def test_duplicate_permutations_replay_identically_and_count_as_supplied(self):
        evidence = self.build_evidence()
        values = (
            self.proposition("CONTENT_POTENTIAL", "DEMO_POTENTIAL", "duplicate", ("E001",)),
            self.proposition("BRAND_POTENTIAL", "BRAND_PREMIUM", "unique", ("E001",)),
            self.proposition("CONTENT_POTENTIAL", "DEMO_POTENTIAL", "duplicate", ("E001",)),
        )
        first = self.analyze(values, {evidence.id: evidence})
        second = self.analyze(tuple(reversed(values)), {evidence.id: evidence})
        self.assertEqual(first, second)
        self.assertEqual(self.values(first.unknown_aspects), ("DEMO_POTENTIAL",))

    def test_same_text_under_different_aspect_is_independently_assessed(self):
        evidence = self.build_evidence()
        propositions = (
            self.proposition("BRAND_POTENTIAL", "BRAND_PREMIUM", "same text"),
            self.proposition("BRAND_POTENTIAL", "VISUAL_EXPRESSION", "same text"),
        )
        with mock.patch.object(self.brand, "assess_evidence", wraps=self.brand.assess_evidence) as assessed:
            result = self.analyze(propositions, {evidence.id: evidence})
        self.assertEqual(assessed.call_count, 2)
        self.assertEqual(len(result.findings), 2)

    def test_equivalent_permutations_replay_identically(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        first = self.proposition(
            "CONTENT_POTENTIAL",
            "VISUAL_EXPRESSION",
            "replay",
            ("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z", "NON_MATERIAL"), self.missing("a", "NON_MATERIAL")),
        )
        second = self.proposition(
            "CONTENT_POTENTIAL",
            "VISUAL_EXPRESSION",
            "replay",
            ("E001", "E002"),
            relations=(self.relation("E001"), self.relation("E002")),
            independence=(self.independence("E001"), self.independence("E002")),
            missing_information=(self.missing("a", "NON_MATERIAL"), self.missing("z", "NON_MATERIAL")),
        )
        result_one = self.analyze((first,), {e.id: e for e in evidences})
        result_two = self.analyze((second,), {e.id: e for e in reversed(evidences)})
        self.assertEqual(result_one, result_two)

    def test_analysis_does_not_mutate_inputs_or_policy(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        proposition = self.proposition(
            evidence_ids=("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
        )
        index = {evidence.id: evidence for evidence in evidences}
        policy = self.build_policy()
        before = (copy.deepcopy(index), policy)
        self.analyze((proposition,), index, policy)
        self.assertEqual(index, before[0])
        self.assertEqual(policy, before[1])


class BrandContentFailureAndScopeTests(BrandContentTestBase):
    def test_malformed_proposition_collection_has_no_placeholder_and_is_input_error(self):
        result = self.analyze(["not a proposition"])
        self.assertEqual(result.findings, ())
        self.assertEqual(result.duplicate_proposition_keys, ())
        self.assertEqual(self.values(result.missing_aspects), ASPECTS)
        self.assertEqual(self.values(result.factors), ("BRAND_CONTENT_INPUT_ERROR",))

    def test_uninterpretable_proposition_collection_fails_closed(self):
        class ExplodingList(list):
            def __iter__(self):
                raise RuntimeError("cannot iterate")

        result = self.analyze(ExplodingList())
        self.assertEqual(result.findings, ())
        self.assertEqual(self.values(result.missing_aspects), ASPECTS)
        self.assertEqual(self.values(result.factors), ("BRAND_CONTENT_INPUT_ERROR",))

    def test_malformed_shared_index_or_policy_keeps_propositions_unknown(self):
        proposition = self.proposition()
        evidence = self.build_evidence()
        for index, policy in (
            ({self.eid("E001"): "not evidence"}, self.build_policy()),
            ({evidence.id: evidence}, object()),
            ({self.eid("E999"): evidence}, self.build_policy()),
        ):
            with self.subTest(index=index, policy=policy):
                result = self.analyze((proposition,), index, policy)
                self.assertEqual(len(result.findings), 1)
                self.assertEqual(self.values(result.unknown_aspects), ("BRAND_PREMIUM",))
                self.assertEqual(self.values(result.factors), ("BRAND_CONTENT_INPUT_ERROR",))
                self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")

    def test_unresolved_evidence_id_is_a_traceable_unknown(self):
        proposition = self.proposition(evidence_ids=("E999",))
        finding = self.analyze((proposition,), {}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(finding.assessment.factors))

    def test_incomplete_assignments_fail_closed_without_fabricated_support(self):
        evidence = self.build_evidence()
        proposition = self.proposition(relations=(), independence=())
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.supporting_ids, ())
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(finding.assessment.factors))

    def test_unexpected_ordinary_error_is_structured_but_base_exception_escapes(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        with mock.patch.object(self.brand, "assess_evidence", side_effect=RuntimeError("boom")):
            result = self.analyze((proposition,), {evidence.id: evidence})
        self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")
        self.assertEqual(result.findings[0].confidence.value, "Low")
        self.assertEqual(self.values(result.findings[0].assessment.factors), ("ASSESSMENT_INPUT_ERROR",))
        with mock.patch.object(self.brand, "assess_evidence", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self.analyze((proposition,), {evidence.id: evidence})

    def test_wrong_assessment_return_type_is_structured_and_local(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        propositions = (
            self.proposition("BRAND_POTENTIAL", "BRAND_PREMIUM", "first", ("E001",)),
            self.proposition("CONTENT_POTENTIAL", "STORYTELLING", "second", ("E002",)),
        )
        original = self.brand.assess_evidence

        def return_wrong_type(*args):
            return "not an assessment" if args[0] == (self.eid("E001"),) else original(*args)

        with mock.patch.object(self.brand, "assess_evidence", side_effect=return_wrong_type):
            result = self.analyze(propositions, {e.id: e for e in evidences})
        findings = {value.proposition: value for value in result.findings}
        self.assertEqual(findings["first"].outcome.value, "UNKNOWN")
        self.assertEqual(findings["second"].outcome.value, "SUPPORTED")
        self.assertEqual(self.values(findings["first"].assessment.factors), ("ASSESSMENT_INPUT_ERROR",))

    def test_voc_values_are_not_accepted_as_evidence_or_confidence(self):
        evidence = self.build_evidence()
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(evidence_ids=(object(),))
        voc_result = importlib.import_module("product_research.voc").VOCResult
        self.assertNotIn(voc_result, self.brand.BrandContentPropositionInput.__annotations__.values())
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        self.assertEqual(result.findings[0].confidence, result.findings[0].assessment.confidence)

    def test_static_scope_and_import_audit(self):
        source = inspect.getsource(self.brand)
        tree = ast.parse(source)
        public_functions = tuple(
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        )
        public_classes = tuple(
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
        )
        self.assertEqual(public_functions, ("analyze_brand_content",))
        self.assertEqual(
            public_classes,
            (
                "BrandContentDimension",
                "BrandContentAspect",
                "BrandContentFindingOutcome",
                "BrandContentFactor",
                "BrandContentPropositionInput",
                "BrandContentPropositionKey",
                "BrandContentFinding",
                "BrandContentResult",
            ),
        )
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        imported = {
            (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
            for node in imports
            for alias in node.names
        }
        self.assertTrue(
            imported.issubset({"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy"})
        )
        forbidden = (
            "requests", "urllib", "httpx", "playwright", "scraper", "network", "browser",
            "random", "asyncio", "voc", "market_demand", "competition", "supply_chain",
            "unit_economics", "scoring_decision", "score", "threshold", "recommendation",
            "redteam", "persistence", "reporting", "provider", "normalization", "embedding",
            "clustering", "llm",
        )
        lowered = source.lower()
        for term in forbidden:
            self.assertNotIn(term.lower(), lowered, term)


if __name__ == "__main__":
    unittest.main()
