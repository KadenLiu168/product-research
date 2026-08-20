import ast
import copy
import dataclasses
import importlib
import importlib.util
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
RISK_AREAS = (
    "REGULATION",
    "CERTIFICATION",
    "IP",
    "PRODUCT_LIABILITY",
    "DANGEROUS_GOODS",
    "TRANSPORT_RESTRICTION",
)
CLASSIFICATIONS = ("NORMAL", "REVIEWABLE", "FATAL")
OUTCOMES = ("SUPPORTED", "UNKNOWN")
DIAGNOSTICS = (
    "RISK_ANALYSIS_INPUT_ERROR",
    "DUPLICATE_PROPOSITION",
    "ASSESSMENT_INPUT_ERROR",
    "ASSESSMENT_NOT_SUPPORTED",
    "MATERIAL_INFORMATION_UNRESOLVED",
    "MISSING_REQUIRED_AREA",
    "UNRESOLVED_REQUIRED_AREA",
)


class RiskComplianceTestBase(unittest.TestCase):
    def setUp(self):
        self.risk = importlib.import_module("product_research.risk_compliance")
        self.e = importlib.import_module("product_research.evidence")
        self.p = importlib.import_module("product_research.evidence_policy")
        self.a = importlib.import_module("product_research.evidence_assessment")
        self.sd = importlib.import_module("product_research.scoring_decision")

    def eid(self, value):
        return self.e.EvidenceId(value)

    def area(self, value="REGULATION"):
        return self.risk.RiskArea(value)

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
                ("Regulatory Agency", "official_regulation"): self.p.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
                ),
                ("Patent Office", "official_patent"): self.p.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
                ),
                ("Trademark Office", "official_trademark"): self.p.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
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
        kind="regulation",
        effective_from="2026-01-01",
        verified_current_at="2026-08-01T00:00:00Z",
        provider="Regulatory Agency",
        source_type="official_regulation",
        tier="Tier 1",
        **overrides,
    ):
        values = {
            "id": self.eid(value),
            "claim": f"Explicit risk and compliance proposition support for {value}.",
            "evidence": f"Caller-declared authoritative record for {value}.",
            "source": self.e.Source(
                provider=provider,
                source_type=source_type,
                reference=f"https://example.test/record/{value}",
                title=f"Official record {value}",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.e.Tier(tier),
            "status": self.e.Status(status),
            "confidence": self.e.Confidence(confidence),
            "metadata": {
                "provider_metadata": {"record_count": 1},
                "provenance": "explicit-authoritative-record",
                "source_family": "RISK",
                "policy": {
                    "kind": kind,
                    "effective_from": effective_from,
                    "verified_current_at": verified_current_at,
                },
            },
        }
        values.update(overrides)
        return self.e.Evidence(**values)

    def build_ip_evidence(self, value="E001", **overrides):
        overrides.setdefault("kind", "ip_authoritative_record")
        overrides.setdefault("provider", "Patent Office")
        overrides.setdefault("source_type", "official_patent")
        return self.build_evidence(value, **overrides)

    def build_stale_evidence(self, value="E001", **overrides):
        overrides["verified_current_at"] = (AS_OF - timedelta(days=400)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        overrides.setdefault("effective_from", "2025-01-01")
        return self.build_evidence(value, **overrides)

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
        area="REGULATION",
        proposition="The product is subject to the cited mandatory safety regulation.",
        classification="NORMAL",
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
        return self.risk.RiskPropositionInput(
            area=self.area(area),
            proposition=proposition,
            classification=self.risk.RiskClassification(classification),
            evidence_ids=ids,
            relations=tuple(relations),
            independence=tuple(independence),
            missing_information=tuple(missing_information),
            assessment_context=context,
        )

    def analyze(
        self,
        propositions=(),
        required_areas=("REGULATION",),
        evidence_index=None,
        policy=None,
    ):
        return self.risk.analyze_risk_compliance(
            propositions,
            tuple(self.area(value) for value in required_areas),
            {} if evidence_index is None else evidence_index,
            self.build_policy() if policy is None else policy,
        )

    def values(self, collection):
        return tuple(value.value for value in collection)


class RiskComplianceModulePresenceTests(unittest.TestCase):
    def test_risk_compliance_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("product_research.risk_compliance"))


class RiskComplianceVocabularyTests(RiskComplianceTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        expected = {
            "RiskArea": RISK_AREAS,
            "RiskClassification": CLASSIFICATIONS,
            "RiskFindingOutcome": OUTCOMES,
            "RiskAnalysisDiagnostic": DIAGNOSTICS,
        }
        for name, allowed in expected.items():
            value_type = getattr(self.risk, name)
            self.assertEqual(value_type._allowed, allowed)
            value = value_type(allowed[0])
            with self.assertRaises(AttributeError):
                value._value = "OTHER"
            with self.assertRaises(AttributeError):
                del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        for name in ("RiskArea", "RiskClassification", "RiskFindingOutcome", "RiskAnalysisDiagnostic"):
            value_type = getattr(self.risk, name)
            for invalid in ("REGULATION ", "regulation", "Regulation", "OTHER", "IP_RISK", 1, None):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises((TypeError, ValueError)):
                        value_type(invalid)

    def test_module_has_one_public_analysis_entry_point_and_no_generic_framework(self):
        self.assertTrue(callable(self.risk.analyze_risk_compliance))
        self.assertFalse(hasattr(self.risk, "StructuredAnalysis"))
        self.assertFalse(hasattr(self.risk, "RawFinding"))
        self.assertFalse(hasattr(self.risk, "RiskGate"))

    def test_module_reuses_the_existing_decision_facing_gate_vocabulary(self):
        self.assertTrue(hasattr(self.sd, "RiskGateState"))
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), ("REGULATION",), {evidence.id: evidence})
        self.assertIs(type(result.risk_gate), self.sd.RiskGateState)


class RiskComplianceInputValueTests(RiskComplianceTestBase):
    def test_proposition_is_frozen_and_canonicalizes_explicit_inputs(self):
        value = self.proposition(
            evidence_ids=("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z", "NON_MATERIAL"), self.missing("a", "NON_MATERIAL")),
        )
        self.assertEqual(self.values(value.evidence_ids), ("E001", "E002"))
        self.assertEqual(
            self.values(relation.evidence_id for relation in value.relations), ("E001", "E002")
        )
        self.assertEqual(tuple(entry.key for entry in value.missing_information), ("a", "z"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.proposition = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.classification = self.risk.RiskClassification("FATAL")

    def test_proposition_preserves_exact_non_empty_utf8_text(self):
        proposition = self.proposition(proposition="  原始风险断言：产品需通过 UL 认证  ")
        self.assertEqual(proposition.proposition, "  原始风险断言：产品需通过 UL 认证  ")
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
            self.proposition(independence=(self.independence("E001"), self.independence("E001")))
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(missing_information=(self.missing("k"), self.missing("k")))

    def test_proposition_requires_exact_public_types_and_material_context(self):
        with self.assertRaises((TypeError, ValueError)):
            self.risk.RiskPropositionInput(
                area="REGULATION",
                proposition="text",
                classification=self.risk.RiskClassification("NORMAL"),
                evidence_ids=(),
                relations=(),
                independence=(),
                missing_information=(),
                assessment_context=self.build_assessment_context(),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(context=self.build_assessment_context(
                validation_context=self.build_context(material=False)
            ))

    def test_key_ignores_classification_and_is_frozen(self):
        first = self.risk.RiskPropositionKey(self.area("IP"), "same text")
        second = self.risk.RiskPropositionKey(self.area("IP"), "same text")
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.proposition = "changed"

    def test_result_values_are_frozen_typed_and_non_numeric(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), ("REGULATION",), {evidence.id: evidence})
        self.assertIs(type(result), self.risk.RiskComplianceResult)
        for field in (
            "required_areas",
            "supported_required_areas",
            "unresolved_required_areas",
            "missing_required_areas",
            "findings",
            "duplicate_proposition_keys",
            "risk_gate",
            "diagnostics",
        ):
            self.assertIn(field, result.__dataclass_fields__)
        self.assertFalse(
            any(
                name in result.__dataclass_fields__
                for name in ("score", "weight", "threshold", "recommendation", "decision")
            )
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.findings = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.findings[0].outcome = self.risk.RiskFindingOutcome("UNKNOWN")

    def test_required_areas_are_canonical_set_semantics(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        first = self.analyze(
            (proposition,),
            ("IP", "REGULATION", "IP", "CERTIFICATION", "REGULATION"),
            {evidence.id: evidence},
        )
        second = self.analyze(
            (proposition,),
            ("CERTIFICATION", "REGULATION", "IP"),
            {evidence.id: evidence},
        )
        self.assertEqual(self.values(first.required_areas), ("REGULATION", "CERTIFICATION", "IP"))
        self.assertEqual(first, second)


class RiskComplianceFindingAnalysisTests(RiskComplianceTestBase):
    def test_every_risk_area_can_produce_an_independently_assessed_finding(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 7))
        propositions = tuple(
            self.proposition(
                area=area,
                proposition=f"explicit {area} proposition",
                evidence_ids=(evidence.id.value,),
            )
            for area, evidence in zip(RISK_AREAS, evidences)
        )
        result = self.analyze(propositions, RISK_AREAS, {value.id: value for value in evidences})
        self.assertEqual(self.values(result.required_areas), RISK_AREAS)
        self.assertEqual(self.values(result.supported_required_areas), RISK_AREAS)
        self.assertEqual(result.unresolved_required_areas, ())
        self.assertEqual(result.missing_required_areas, ())
        self.assertEqual(
            tuple((finding.area.value, finding.proposition) for finding in result.findings),
            tuple((area, f"explicit {area} proposition") for area in RISK_AREAS),
        )
        for finding in result.findings:
            self.assertEqual(finding.outcome.value, "SUPPORTED")
            self.assertIs(type(finding.assessment), self.a.EvidenceAssessmentResult)
            self.assertEqual(finding.supporting_ids, finding.assessment.usable_ids)
        self.assertEqual(result.risk_gate.value, "CLEAR")

    def test_current_authoritative_regulation_supports_proposition(self):
        evidence = self.build_evidence()
        finding = self.analyze(
            (self.proposition(),), ("REGULATION",), {evidence.id: evidence}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.supported_classification, self.risk.RiskClassification("NORMAL"))
        self.assertEqual(finding.confidence, finding.assessment.confidence)
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))

    def test_current_authoritative_patent_record_supports_ip_proposition(self):
        evidence = self.build_ip_evidence()
        finding = self.analyze(
            (self.proposition(area="IP", classification="REVIEWABLE"),),
            ("IP",),
            {evidence.id: evidence},
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.supported_classification.value, "REVIEWABLE")
        self.assertEqual(finding.assessment.policy_results[0].outcome.value, "ACCEPT_CURRENT")

    def test_stale_regulation_remains_unknown_with_trace(self):
        stale = self.build_stale_evidence()
        finding = self.analyze(
            (self.proposition(),), ("REGULATION",), {stale.id: stale}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(finding.supporting_ids, ())
        self.assertEqual(
            finding.assessment.policy_results[0].issues[0].reason_code.value, "STALE_EVIDENCE"
        )
        self.assertEqual(self.values(finding.diagnostics), ("ASSESSMENT_NOT_SUPPORTED",))

    def test_non_authoritative_regulation_remains_unknown(self):
        secondary = self.build_evidence(
            provider="Example Marketplace",
            source_type="marketplace_listing",
            tier="Tier 2",
        )
        finding = self.analyze(
            (self.proposition(),), ("REGULATION",), {secondary.id: secondary}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(
            finding.assessment.policy_results[0].issues[0].reason_code.value, "TIER_MISMATCH"
        )

    def test_caller_declared_one_source_minimum_is_honored(self):
        evidence = self.build_evidence()
        proposition = self.proposition(context=self.build_assessment_context(minimum=1))
        finding = self.analyze(
            (proposition,), ("REGULATION",), {evidence.id: evidence}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.assessment.independent_source_count, 1)

    def test_unsupported_evidence_remains_unknown_without_classification(self):
        evidence = self.build_evidence(status="Unknown")
        finding = self.analyze(
            (self.proposition(),), ("REGULATION",), {evidence.id: evidence}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(finding.supporting_ids, ())
        self.assertEqual(finding.assessment.policy_results[0].outcome.value, "REJECT")

    def test_conflict_remains_unknown_and_does_not_choose_a_side(self):
        support = self.build_evidence("E001")
        adverse = self.build_evidence("E002")
        proposition = self.proposition(
            evidence_ids=("E001", "E002"),
            relations=(self.relation("E001"), self.relation("E002", "CONTRADICTS")),
            independence=(self.independence("E001"), self.independence("E002")),
        )
        finding = self.analyze(
            (proposition,), ("REGULATION",), {value.id: value for value in (support, adverse)}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(finding.assessment.outcome.value, "CONFLICTED")
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002",))

    def test_material_or_critical_missing_information_withholds_classification(self):
        evidence = self.build_evidence()
        for severity in ("MATERIAL", "CRITICAL"):
            with self.subTest(severity=severity):
                missing = self.missing("unresolved_compliance_input", severity)
                finding = self.analyze(
                    (self.proposition(missing_information=(missing,)),),
                    ("REGULATION",),
                    {evidence.id: evidence},
                ).findings[0]
                self.assertEqual(finding.assessment.outcome.value, "SUPPORTED")
                self.assertEqual(finding.outcome.value, "UNKNOWN")
                self.assertEqual(finding.confidence.value, "Low")
                self.assertIsNone(finding.supported_classification)
                self.assertIn("MATERIAL_INFORMATION_UNRESOLVED", self.values(finding.diagnostics))

    def test_non_material_missing_information_does_not_downgrade(self):
        evidence = self.build_evidence()
        missing = self.missing("non_material_gap", "NON_MATERIAL")
        finding = self.analyze(
            (self.proposition(missing_information=(missing,)),),
            ("REGULATION",),
            {evidence.id: evidence},
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.confidence, finding.assessment.confidence)
        self.assertNotIn("MATERIAL_INFORMATION_UNRESOLVED", self.values(finding.diagnostics))

    def test_missing_evidence_cannot_fabricate_fatal(self):
        proposition = self.proposition(
            classification="FATAL",
            evidence_ids=(),
            relations=(),
            independence=(),
        )
        result = self.analyze((proposition,), ("REGULATION",))
        finding = result.findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertNotEqual(result.risk_gate.value, "FATAL")

    def test_unresolved_evidence_id_is_a_traceable_unknown(self):
        proposition = self.proposition(evidence_ids=("E999",))
        result = self.analyze((proposition,), ("REGULATION",))
        finding = result.findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(finding.diagnostics))
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_assessment_input_error_cannot_support_a_risk_classification(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
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
        with mock.patch.object(self.risk, "assess_evidence", return_value=assessment):
            finding = self.analyze(
                (proposition,), ("REGULATION",), {evidence.id: evidence}
            ).findings[0]
        self.assertIs(finding.assessment, assessment)
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertIsNone(finding.supported_classification)
        self.assertEqual(self.values(finding.diagnostics), ("ASSESSMENT_INPUT_ERROR",))

    def test_each_unique_proposition_is_assessed_exactly_once(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 4))
        propositions = (
            self.proposition("REGULATION", "first", "NORMAL", ("E001",)),
            self.proposition("REGULATION", "second", "NORMAL", ("E002",)),
            self.proposition("CERTIFICATION", "third", "NORMAL", ("E003",)),
        )
        original = self.risk.assess_evidence
        calls = []

        def record(*args):
            calls.append(args)
            return original(*args)

        with mock.patch.object(self.risk, "assess_evidence", side_effect=record) as assessed:
            self.analyze(
                propositions,
                ("REGULATION", "CERTIFICATION"),
                {value.id: value for value in evidences},
            )
        self.assertEqual(assessed.call_count, 3)
        self.assertEqual(
            [tuple(value.value for value in call[0]) for call in calls],
            [("E001",), ("E002",), ("E003",)],
        )

    def test_traceability_preserves_lexical_support_adverse_and_excluded_ids(self):
        current = self.build_evidence("E001")
        adverse = self.build_evidence("E002")
        stale = self.build_stale_evidence("E003")
        proposition = self.proposition(
            evidence_ids=("E003", "E001", "E002"),
            relations=(
                self.relation("E003", "CONTRADICTS"),
                self.relation("E002", "CONTRADICTS"),
                self.relation("E001"),
            ),
            independence=(
                self.independence("E003"),
                self.independence("E002"),
                self.independence("E001"),
            ),
        )
        finding = self.analyze(
            (proposition,),
            ("REGULATION",),
            {value.id: value for value in (current, adverse, stale)},
        ).findings[0]
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002", "E003"))
        self.assertEqual(self.values(finding.excluded_ids), ("E003",))
        self.assertEqual(finding.assessment.usable_ids, finding.supporting_ids)
        self.assertEqual(finding.assessment.contradicting_ids, finding.adverse_ids)
        self.assertEqual(finding.assessment.excluded_ids, finding.excluded_ids)
        for evidence_id in finding.supporting_ids + finding.adverse_ids + finding.excluded_ids:
            self.assertIs(type(evidence_id), self.e.EvidenceId)

    def test_evidence_text_does_not_create_propositions_or_coverage(self):
        evidence = self.build_evidence(
            claim="Regulation, certification, patent, liability, dangerous goods, and transport restrictions are all mentioned.",
            evidence="The record text mentions every risk topic.",
        )
        result = self.analyze(evidence_index={evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertEqual(result.supported_required_areas, ())
        self.assertEqual(self.values(result.missing_required_areas), ("REGULATION",))
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")


class RiskComplianceCoverageTests(RiskComplianceTestBase):
    def test_coverage_is_mutually_exclusive_and_exhaustive_over_required_areas_only(self):
        evidence = self.build_evidence()
        unsupported = self.proposition(
            "CERTIFICATION",
            "unsupported certification proposition",
            "NORMAL",
            ("E001",),
            relations=(self.relation("E001", "NEUTRAL"),),
        )
        result = self.analyze(
            (unsupported,),
            ("REGULATION", "CERTIFICATION", "IP"),
            {evidence.id: evidence},
        )
        self.assertEqual(self.values(result.required_areas), ("REGULATION", "CERTIFICATION", "IP"))
        self.assertEqual(self.values(result.supported_required_areas), ())
        self.assertEqual(self.values(result.unresolved_required_areas), ("CERTIFICATION",))
        self.assertEqual(self.values(result.missing_required_areas), ("REGULATION", "IP"))
        sets = (
            set(self.values(result.supported_required_areas)),
            set(self.values(result.unresolved_required_areas)),
            set(self.values(result.missing_required_areas)),
        )
        self.assertFalse(any(left & right for index, left in enumerate(sets) for right in sets[index + 1 :]))
        self.assertEqual(set.union(*sets), {"REGULATION", "CERTIFICATION", "IP"})

    def test_non_required_absent_areas_are_not_missing(self):
        evidence = self.build_evidence()
        result = self.analyze(
            (self.proposition(),), ("REGULATION",), {evidence.id: evidence}
        )
        self.assertEqual(self.values(result.missing_required_areas), ())
        self.assertEqual(self.values(result.supported_required_areas), ("REGULATION",))

    def test_supported_area_with_additional_material_unknown_keeps_both_signals(self):
        evidence = self.build_evidence()
        propositions = (
            self.proposition("REGULATION", "supported proposition", "NORMAL", ("E001",)),
            self.proposition(
                "REGULATION",
                "materially incomplete proposition",
                "NORMAL",
                ("E001",),
                missing_information=(self.missing("gap"),),
            ),
        )
        result = self.analyze(propositions, ("REGULATION",), {evidence.id: evidence})
        self.assertEqual(self.values(result.supported_required_areas), ("REGULATION",))
        self.assertEqual(result.unresolved_required_areas, ())
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_required_area_addressed_only_by_duplicates_is_missing(self):
        evidence = self.build_evidence()
        duplicate = self.proposition("IP", "ambiguous ip proposition", "NORMAL", ("E001",))
        result = self.analyze(
            (duplicate, duplicate), ("IP",), {evidence.id: evidence}
        )
        self.assertEqual(result.findings, ())
        self.assertEqual(self.values(result.missing_required_areas), ("IP",))
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_non_required_supplied_findings_remain_visible_and_participate_in_precedence(self):
        evidence = self.build_evidence()
        fatal = self.proposition(
            "PRODUCT_LIABILITY", "non-required liability fatal proposition", "FATAL", ("E001",)
        )
        result = self.analyze((fatal,), (), {evidence.id: evidence})
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].outcome.value, "SUPPORTED")
        self.assertEqual(result.findings[0].supported_classification.value, "FATAL")
        self.assertEqual(result.risk_gate.value, "FATAL")

    def test_empty_required_areas_with_supported_normal_clears(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), (), {evidence.id: evidence})
        self.assertEqual(result.required_areas, ())
        self.assertEqual(result.risk_gate.value, "CLEAR")


class RiskComplianceGateAggregationTests(RiskComplianceTestBase):
    def gate_for(self, propositions, required_areas=("REGULATION",), evidences=None):
        evidences = evidences or (self.build_evidence(),)
        return self.analyze(
            propositions,
            required_areas,
            {value.id: value for value in evidences},
        ).risk_gate.value

    def test_supported_fatal_produces_fatal_gate(self):
        proposition = self.proposition(classification="FATAL")
        self.assertEqual(self.gate_for((proposition,)), "FATAL")

    def test_supported_reviewable_requires_review(self):
        proposition = self.proposition(classification="REVIEWABLE")
        self.assertEqual(self.gate_for((proposition,)), "REVIEW_REQUIRED")

    def test_supported_fatal_precedes_reviewable(self):
        propositions = (
            self.proposition("REGULATION", "fatal proposition", "FATAL", ("E001",)),
            self.proposition("CERTIFICATION", "reviewable proposition", "REVIEWABLE", ("E002",)),
        )
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        result = self.analyze(
            propositions, ("REGULATION", "CERTIFICATION"), {value.id: value for value in evidences}
        )
        self.assertEqual(result.risk_gate.value, "FATAL")
        self.assertEqual(len(result.findings), 2)
        classifications = {
            finding.proposition: finding.supported_classification.value
            for finding in result.findings
        }
        self.assertEqual(
            classifications,
            {"fatal proposition": "FATAL", "reviewable proposition": "REVIEWABLE"},
        )

    def test_complete_supported_normal_coverage_clears(self):
        evidences = (
            self.build_evidence("E001"),
            self.build_evidence("E002", kind="certification"),
        )
        propositions = (
            self.proposition("REGULATION", "regulation normal", "NORMAL", ("E001",)),
            self.proposition("CERTIFICATION", "certification normal", "NORMAL", ("E002",)),
        )
        result = self.analyze(
            propositions, ("REGULATION", "CERTIFICATION"), {value.id: value for value in evidences}
        )
        self.assertEqual(self.values(result.supported_required_areas), ("REGULATION", "CERTIFICATION"))
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(result.risk_gate.value, "CLEAR")

    def test_material_unknown_requires_review(self):
        evidence = self.build_evidence()
        proposition = self.proposition(missing_information=(self.missing("material_gap"),))
        self.assertEqual(self.gate_for((proposition,), evidences=(evidence,)), "REVIEW_REQUIRED")

    def test_missing_or_unresolved_required_area_requires_review(self):
        evidence = self.build_evidence()
        missing = self.gate_for((), ("REGULATION",), (evidence,))
        self.assertEqual(missing, "REVIEW_REQUIRED")
        unresolved_proposition = self.proposition(
            relations=(self.relation("E001", "NEUTRAL"),)
        )
        unresolved = self.gate_for(
            (unresolved_proposition,), ("REGULATION",), (evidence,)
        )
        self.assertEqual(unresolved, "REVIEW_REQUIRED")

    def test_supported_normal_never_overrides_higher_precedence_conditions(self):
        evidence = self.build_evidence()
        propositions = (
            self.proposition("REGULATION", "normal proposition", "NORMAL", ("E001",)),
            self.proposition(
                "REGULATION",
                "materially incomplete proposition",
                "NORMAL",
                ("E001",),
                missing_information=(self.missing("gap"),),
            ),
        )
        result = self.analyze((propositions[0],), ("REGULATION",), {evidence.id: evidence})
        self.assertEqual(result.risk_gate.value, "CLEAR")
        result = self.analyze(propositions, ("REGULATION",), {evidence.id: evidence})
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_non_material_non_required_unknown_does_not_block_clear(self):
        evidence = self.build_evidence()
        propositions = (
            self.proposition("REGULATION", "required normal", "NORMAL", ("E001",)),
            self.proposition(
                "IP",
                "optional unknown proposition",
                "REVIEWABLE",
                ("E001",),
                relations=(self.relation("E001", "NEUTRAL"),),
            ),
        )
        result = self.analyze(propositions, ("REGULATION",), {evidence.id: evidence})
        outcomes = {finding.proposition: finding.outcome.value for finding in result.findings}
        self.assertEqual(outcomes["optional unknown proposition"], "UNKNOWN")
        self.assertIn("ASSESSMENT_NOT_SUPPORTED", self.values(result.diagnostics))
        self.assertEqual(result.risk_gate.value, "CLEAR")

    def test_result_diagnostics_use_declared_order_with_duplicates_removed(self):
        evidence = self.build_evidence()
        unsupported = self.proposition(
            "CERTIFICATION",
            "unsupported certification proposition",
            "NORMAL",
            ("E001",),
            relations=(self.relation("E001", "NEUTRAL"),),
        )
        result = self.analyze((unsupported,), ("CERTIFICATION", "IP"), {evidence.id: evidence})
        self.assertEqual(
            self.values(result.diagnostics),
            ("ASSESSMENT_NOT_SUPPORTED", "MISSING_REQUIRED_AREA", "UNRESOLVED_REQUIRED_AREA"),
        )


class RiskComplianceDuplicateReplayTests(RiskComplianceTestBase):
    def test_duplicate_keys_have_no_assessment_or_winner_and_unique_key_survives(self):
        evidence = self.build_evidence()
        first = self.proposition("REGULATION", "same exact proposition", "NORMAL", ("E001",))
        second = self.proposition("REGULATION", "same exact proposition", "FATAL", ("E001",))
        unique = self.proposition("REGULATION", "different exact proposition", "NORMAL", ("E001",))
        with mock.patch.object(
            self.risk, "assess_evidence", wraps=self.risk.assess_evidence
        ) as assessed:
            result = self.analyze(
                (second, unique, first), ("REGULATION",), {evidence.id: evidence}
            )
        self.assertEqual(assessed.call_count, 1)
        self.assertEqual(len(result.duplicate_proposition_keys), 1)
        self.assertEqual(result.duplicate_proposition_keys[0].proposition, "same exact proposition")
        self.assertEqual(
            tuple(value.proposition for value in result.findings), ("different exact proposition",)
        )
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")
        self.assertIn("DUPLICATE_PROPOSITION", self.values(result.diagnostics))

    def test_duplicate_with_unique_fatal_keeps_fatal_gate_and_duplicate_diagnostic(self):
        evidence = self.build_evidence()
        duplicate_a = self.proposition("REGULATION", "ambiguous", "NORMAL", ("E001",))
        duplicate_b = self.proposition("REGULATION", "ambiguous", "REVIEWABLE", ("E001",))
        fatal = self.proposition("CERTIFICATION", "unique fatal", "FATAL", ("E001",))
        result = self.analyze(
            (duplicate_a, fatal, duplicate_b), ("REGULATION",), {evidence.id: evidence}
        )
        self.assertEqual(result.risk_gate.value, "FATAL")
        self.assertIn("DUPLICATE_PROPOSITION", self.values(result.diagnostics))
        self.assertEqual(
            tuple(value.proposition for value in result.findings), ("unique fatal",)
        )

    def test_equivalent_reordered_inputs_replay_identically(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002", kind="certification"))
        first = self.proposition(
            "REGULATION",
            "replay",
            "NORMAL",
            ("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z", "NON_MATERIAL"), self.missing("a", "NON_MATERIAL")),
        )
        second = self.proposition(
            "CERTIFICATION",
            "replay two",
            "NORMAL",
            ("E001",),
        )
        result_one = self.analyze(
            (first, second),
            ("IP", "REGULATION", "CERTIFICATION"),
            {value.id: value for value in evidences},
        )
        result_two = self.analyze(
            (second, first),
            ("CERTIFICATION", "REGULATION", "IP"),
            {value.id: value for value in reversed(evidences)},
        )
        self.assertEqual(result_one, result_two)
        self.assertEqual(result_one.risk_gate.value, "REVIEW_REQUIRED")

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
        self.analyze((proposition,), ("REGULATION",), index, policy)
        self.assertEqual(index, before[0])
        self.assertEqual(policy, before[1])
        self.assertEqual(proposition.evidence_ids, (self.eid("E001"), self.eid("E002")))


class RiskComplianceFailureAndScopeTests(RiskComplianceTestBase):
    def test_malformed_proposition_collection_is_structured_input_error(self):
        result = self.analyze(["not a proposition"], ("REGULATION",))
        self.assertEqual(result.findings, ())
        self.assertEqual(result.duplicate_proposition_keys, ())
        self.assertEqual(self.values(result.missing_required_areas), ("REGULATION",))
        self.assertEqual(
            self.values(result.diagnostics),
            ("RISK_ANALYSIS_INPUT_ERROR", "MISSING_REQUIRED_AREA"),
        )
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_malformed_required_areas_fail_closed_with_empty_coverage(self):
        evidence = self.build_evidence()
        for required_areas in ("REGULATION", ("REGULATION", "IP"), ("REGULATION", "nope"), 1):
            with self.subTest(required_areas=repr(required_areas)):
                result = self.risk.analyze_risk_compliance(
                    (self.proposition(),),
                    required_areas,
                    {evidence.id: evidence},
                    self.build_policy(),
                )
                self.assertEqual(result.findings, ())
                self.assertEqual(result.required_areas, ())
                self.assertEqual(result.supported_required_areas, ())
                self.assertEqual(result.unresolved_required_areas, ())
                self.assertEqual(result.missing_required_areas, ())
                self.assertEqual(self.values(result.diagnostics), ("RISK_ANALYSIS_INPUT_ERROR",))
                self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_forged_frozen_values_fail_closed_at_the_boundary(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        object.__setattr__(proposition, "proposition", "")
        result = self.analyze((proposition,), ("REGULATION",), {evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertIn("RISK_ANALYSIS_INPUT_ERROR", self.values(result.diagnostics))
        self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

        area_value = self.area("REGULATION")
        object.__setattr__(area_value, "_value", "FORGED")
        result = self.risk.analyze_risk_compliance(
            (self.proposition(),),
            (area_value,),
            {evidence.id: evidence},
            self.build_policy(),
        )
        self.assertEqual(result.findings, ())
        self.assertEqual(self.values(result.diagnostics), ("RISK_ANALYSIS_INPUT_ERROR",))

    def test_malformed_shared_index_or_policy_keeps_propositions_unknown(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        for index, policy in (
            ({self.eid("E001"): "not evidence"}, self.build_policy()),
            ({evidence.id: evidence}, object()),
            ({self.eid("E999"): evidence}, self.build_policy()),
        ):
            with self.subTest(index=index, policy=policy):
                result = self.analyze((proposition,), ("REGULATION",), index, policy)
                self.assertEqual(len(result.findings), 1)
                self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")
                self.assertEqual(result.findings[0].confidence.value, "Low")
                self.assertIsNone(result.findings[0].supported_classification)
                self.assertIn("RISK_ANALYSIS_INPUT_ERROR", self.values(result.diagnostics))
                self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(result.diagnostics))
                self.assertEqual(result.risk_gate.value, "REVIEW_REQUIRED")

    def test_unexpected_ordinary_assessment_error_is_structured_but_base_exception_escapes(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        with mock.patch.object(self.risk, "assess_evidence", side_effect=RuntimeError("boom")):
            result = self.analyze((proposition,), ("REGULATION",), {evidence.id: evidence})
        self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")
        self.assertEqual(result.findings[0].confidence.value, "Low")
        with mock.patch.object(self.risk, "assess_evidence", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self.analyze((proposition,), ("REGULATION",), {evidence.id: evidence})

    def test_module_does_not_define_a_second_gate_or_numeric_contract(self):
        source = inspect.getsource(self.risk)
        self.assertNotIn("class RiskGate", source)
        for field in dataclasses.fields(self.risk.RiskComplianceResult):
            self.assertNotIn("score", field.name.lower())
            self.assertNotIn("weight", field.name.lower())

    def test_static_scope_and_import_audit(self):
        source = inspect.getsource(self.risk)
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
        self.assertEqual(public_functions, ("analyze_risk_compliance",))
        self.assertEqual(
            public_classes,
            (
                "RiskArea",
                "RiskClassification",
                "RiskFindingOutcome",
                "RiskAnalysisDiagnostic",
                "RiskPropositionInput",
                "RiskPropositionKey",
                "RiskFinding",
                "RiskComplianceResult",
            ),
        )
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        imported = {
            (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
            for node in imports
            for alias in node.names
        }
        self.assertTrue(
            imported.issubset(
                {"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy", "risk_gate"}
            )
        )
        forbidden = (
            "requests",
            "urllib",
            "httpx",
            "playwright",
            "selenium",
            "scraper",
            "network",
            "browser",
            "random",
            "asyncio",
            "llm",
            "supply_chain",
            "supplychain",
            "unit_economics",
            "uniteconomics",
            "evaluate_scoring_decision",
            "weightadjustments",
            "dimensionscore",
            "decimal",
            "redteam",
            "persistence",
            "reporting",
            "recommendation",
            "orchestration",
            "open(",
            "__import__",
        )
        lowered = source.lower()
        for term in forbidden:
            self.assertNotIn(term.lower(), lowered, term)


if __name__ == "__main__":
    unittest.main()
