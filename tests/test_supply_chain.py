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
DIMENSIONS = (
    "SUPPLIER_LANDSCAPE",
    "MOQ",
    "SOURCING_COST",
    "CUSTOMIZATION",
    "QUALITY",
    "WEIGHT_VOLUME",
    "TRANSPORTATION",
    "RETURNS_AFTER_SALES",
)
FACTORS = (
    "SUPPLY_CHAIN_INPUT_ERROR",
    "DUPLICATE_PROPOSITION",
    "ASSESSMENT_INPUT_ERROR",
    "ASSESSMENT_NOT_SUPPORTED",
    "MATERIAL_INFORMATION_UNRESOLVED",
)


class SupplyChainTestBase(unittest.TestCase):
    def setUp(self):
        self.supply = importlib.import_module("product_research.supply_chain")
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
        kind="supplier_quotation",
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
            "claim": f"Explicit supply chain proposition support for {value}.",
            "evidence": f"Caller-declared operational support for {value}.",
            "source": self.e.Source(
                provider=provider,
                source_type=source_type,
                reference=f"https://example.test/quote/{value}",
                title=f"Quote {value}",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.e.Tier(tier),
            "status": self.e.Status(status),
            "confidence": self.e.Confidence(confidence),
            "metadata": {
                "provider_metadata": {"record_count": 1},
                "provenance": "explicit-supplier-quote",
                "source_family": "SUPPLIER",
                "policy": {"kind": kind, "source_date": source_date},
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
        dimension="MOQ",
        proposition="Supplier MOQ is 100 units.",
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
        return self.supply.SupplyChainPropositionInput(
            dimension=self.supply.SupplyChainDimension(dimension),
            proposition=proposition,
            evidence_ids=ids,
            relations=tuple(relations),
            independence=tuple(independence),
            missing_information=tuple(missing_information),
            assessment_context=context,
        )

    def analyze(self, propositions=(), evidence_index=None, policy=None):
        return self.supply.analyze_supply_chain(
            propositions,
            {} if evidence_index is None else evidence_index,
            self.build_policy() if policy is None else policy,
        )

    def values(self, collection):
        return tuple(value.value for value in collection)


class SupplyChainModulePresenceTests(unittest.TestCase):
    def test_supply_chain_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("product_research.supply_chain"))


class SupplyChainVocabularyTests(SupplyChainTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        expected = {
            "SupplyChainDimension": DIMENSIONS,
            "SupplyChainFindingOutcome": ("SUPPORTED", "UNKNOWN"),
            "SupplyChainFactor": FACTORS,
        }
        for name, allowed in expected.items():
            value_type = getattr(self.supply, name)
            self.assertEqual(value_type._allowed, allowed)
            value = value_type(allowed[0])
            with self.assertRaises(AttributeError):
                value._value = "OTHER"
            with self.assertRaises(AttributeError):
                del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        for name in ("SupplyChainDimension", "SupplyChainFindingOutcome", "SupplyChainFactor"):
            value_type = getattr(self.supply, name)
            for invalid in ("MOQ ", "moq", "Moq", "OTHER", 1, None):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises((TypeError, ValueError)):
                        value_type(invalid)

    def test_module_has_one_public_analysis_entry_point_and_no_generic_framework(self):
        self.assertTrue(callable(self.supply.analyze_supply_chain))
        self.assertFalse(hasattr(self.supply, "StructuredAnalysis"))
        self.assertFalse(hasattr(self.supply, "RawFinding"))


class SupplyChainInputValueTests(SupplyChainTestBase):
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
        proposition = self.proposition(proposition="  原始 MOQ 断言  ")
        self.assertEqual(proposition.proposition, "  原始 MOQ 断言  ")
        for invalid in ("", "\ud800", 1, None):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises((TypeError, ValueError)):
                    self.proposition(proposition=invalid)

    def test_duplicate_ids_and_assignments_are_rejected_without_normalization(self):
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(evidence_ids=("E001", "E001"))
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                relations=(self.relation("E001"), self.relation("E001")),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(
                independence=(self.independence("E001"), self.independence("E001")),
            )

    def test_key_finding_and_result_values_are_frozen_typed_and_non_numeric(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        key = self.supply.SupplyChainPropositionKey(
            self.supply.SupplyChainDimension("MOQ"), "exact key"
        )
        self.assertEqual(key.proposition, "exact key")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            key.proposition = "changed"
        self.assertIs(type(result), self.supply.SupplyChainResult)
        for field in (
            "supported_dimensions",
            "unknown_dimensions",
            "missing_dimensions",
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
            result.findings[0].outcome = self.supply.SupplyChainFindingOutcome("UNKNOWN")


class SupplyChainFindingAnalysisTests(SupplyChainTestBase):
    def test_every_dimension_can_produce_an_independently_assessed_finding(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 9))
        propositions = tuple(
            self.proposition(
                dimension=dimension,
                proposition=f"explicit {dimension} proposition",
                evidence_ids=(evidence.id.value,),
            )
            for dimension, evidence in zip(DIMENSIONS, evidences)
        )
        result = self.analyze(propositions, {evidence.id: evidence for evidence in evidences})
        self.assertEqual(self.values(result.supported_dimensions), DIMENSIONS)
        self.assertEqual(result.unknown_dimensions, ())
        self.assertEqual(result.missing_dimensions, ())
        self.assertEqual(
            tuple((finding.dimension.value, finding.proposition) for finding in result.findings),
            tuple((dimension, f"explicit {dimension} proposition") for dimension in DIMENSIONS),
        )
        for finding in result.findings:
            self.assertEqual(finding.outcome.value, "SUPPORTED")
            self.assertIs(type(finding.assessment), self.a.EvidenceAssessmentResult)
            self.assertEqual(finding.supporting_ids, finding.assessment.usable_ids)

    def test_evidence_text_metadata_and_supplier_family_do_not_create_a_proposition(self):
        evidence = self.build_evidence(
            claim="MOQ, cost, supplier concentration, and transportation are all obvious.",
            evidence="The page contains every supply-chain fact.",
            metadata={
                "record_count": 10000,
                "source_family": "SUPPLIER",
                "policy": {"kind": "supplier_quotation", "source_date": AS_OF.date().isoformat()},
            },
        )
        result = self.analyze(evidence_index={evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertEqual(result.supported_dimensions, ())
        self.assertEqual(self.values(result.missing_dimensions), DIMENSIONS)

    def test_each_unique_proposition_is_assessed_once_and_stays_isolated(self):
        evidences = tuple(self.build_evidence(f"E{i:03d}") for i in range(1, 4))
        propositions = (
            self.proposition("QUALITY", "first", ("E001",), context=self.build_assessment_context(1)),
            self.proposition("QUALITY", "second", ("E002",), context=self.build_assessment_context(1)),
            self.proposition("MOQ", "third", ("E003",), context=self.build_assessment_context(1)),
        )
        original = self.supply.assess_evidence
        calls = []

        def record(*args):
            calls.append(args)
            return original(*args)

        with mock.patch.object(self.supply, "assess_evidence", side_effect=record) as assessed:
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

    def test_conflict_and_policy_exclusion_remain_unknown_with_traceability(self):
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
        self.assertEqual(
            tuple(value.value for value in finding.factors), ("ASSESSMENT_NOT_SUPPORTED",)
        )

    def test_material_or_critical_missing_information_downgrades_supported_finding(self):
        evidence = self.build_evidence()
        for severity in ("MATERIAL", "CRITICAL"):
            with self.subTest(severity=severity):
                missing = self.missing("unresolved_operational_input", severity)
                finding = self.analyze(
                    (self.proposition(missing_information=(missing,)),),
                    {evidence.id: evidence},
                ).findings[0]
                self.assertEqual(finding.assessment.outcome.value, "SUPPORTED")
                self.assertEqual(finding.outcome.value, "UNKNOWN")
                self.assertEqual(finding.confidence.value, "Low")
                self.assertIn("MATERIAL_INFORMATION_UNRESOLVED", self.values(finding.factors))

    def test_non_material_missing_information_is_preserved_without_extra_downgrade(self):
        evidence = self.build_evidence()
        missing = self.missing("non_material_gap", "NON_MATERIAL")
        finding = self.analyze(
            (self.proposition(missing_information=(missing,)),), {evidence.id: evidence}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "SUPPORTED")
        self.assertEqual(finding.confidence, finding.assessment.confidence)
        self.assertEqual(finding.assessment.missing_information, (missing,))
        self.assertNotIn("MATERIAL_INFORMATION_UNRESOLVED", self.values(finding.factors))

    def test_material_missing_factor_is_retained_when_support_is_also_unusable(self):
        evidence = self.build_evidence()
        missing = self.missing("material_gap", "MATERIAL")
        proposition = self.proposition(
            missing_information=(missing,),
            relations=(self.relation("E001", "NEUTRAL"),),
        )
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertIn("MATERIAL_INFORMATION_UNRESOLVED", self.values(finding.factors))

    def test_incomplete_assignments_fail_closed_without_fabricated_support(self):
        evidence = self.build_evidence()
        proposition = self.proposition(relations=(), independence=())
        finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.supporting_ids, ())
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(finding.assessment.factors))

    def test_assessment_input_error_cannot_support_an_operational_finding(self):
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

        with mock.patch.object(self.supply, "assess_evidence", return_value=assessment):
            finding = self.analyze((proposition,), {evidence.id: evidence}).findings[0]

        self.assertIs(finding.assessment, assessment)
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(self.values(finding.factors), ("ASSESSMENT_INPUT_ERROR",))

    def test_traceability_preserves_lexical_support_adverse_and_excluded_ids(self):
        evidences = (
            self.build_evidence("E001"),
            self.build_evidence("E002"),
            self.build_evidence("E003", source_date=(AS_OF.date() - timedelta(days=91)).isoformat()),
        )
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
            (proposition,), {value.id: value for value in evidences}
        ).findings[0]
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002", "E003"))
        self.assertEqual(self.values(finding.excluded_ids), ("E003",))
        self.assertEqual(finding.assessment.usable_ids, finding.supporting_ids)
        self.assertEqual(finding.assessment.contradicting_ids, finding.adverse_ids)
        self.assertEqual(finding.assessment.excluded_ids, finding.excluded_ids)


class SupplyChainCoverageDuplicateReplayTests(SupplyChainTestBase):
    def test_coverage_is_fixed_order_exhaustive_and_mutually_exclusive(self):
        evidence = self.build_evidence()
        result = self.analyze((self.proposition(),), {evidence.id: evidence})
        self.assertEqual(self.values(result.supported_dimensions), ("MOQ",))
        self.assertEqual(self.values(result.unknown_dimensions), ())
        self.assertEqual(
            self.values(result.missing_dimensions),
            tuple(value for value in DIMENSIONS if value != "MOQ"),
        )
        sets = (
            set(self.values(result.supported_dimensions)),
            set(self.values(result.unknown_dimensions)),
            set(self.values(result.missing_dimensions)),
        )
        self.assertFalse(any(left & right for index, left in enumerate(sets) for right in sets[index + 1 :]))
        self.assertEqual(set.union(*sets), set(DIMENSIONS))

    def test_supported_unknown_and_mixed_dimensions_preserve_each_finding(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        propositions = (
            self.proposition("QUALITY", "supported", ("E001",)),
            self.proposition(
                "QUALITY",
                "unknown",
                ("E002",),
                relations=(self.relation("E002", "NEUTRAL"),),
            ),
            self.proposition(
                "TRANSPORTATION",
                "unsupported",
                ("E002",),
                relations=(self.relation("E002", "NEUTRAL"),),
            ),
        )
        result = self.analyze(propositions, {value.id: value for value in evidences})
        self.assertIn("QUALITY", self.values(result.supported_dimensions))
        self.assertIn("TRANSPORTATION", self.values(result.unknown_dimensions))
        self.assertEqual(len(result.findings), 3)
        self.assertEqual(
            tuple(value.proposition for value in result.findings),
            ("supported", "unknown", "unsupported"),
        )

    def test_duplicate_keys_have_no_assessment_or_winner_and_unique_key_survives(self):
        evidence = self.build_evidence()
        first = self.proposition("MOQ", "same exact proposition", ("E001",))
        second = self.proposition("MOQ", "same exact proposition", ("E001",))
        unique = self.proposition("MOQ", "different exact proposition", ("E001",))
        with mock.patch.object(self.supply, "assess_evidence", wraps=self.supply.assess_evidence) as assessed:
            result = self.analyze((second, unique, first), {evidence.id: evidence})
        self.assertEqual(assessed.call_count, 1)
        self.assertEqual(len(result.duplicate_proposition_keys), 1)
        self.assertEqual(result.duplicate_proposition_keys[0].proposition, "same exact proposition")
        self.assertEqual(
            tuple(value.proposition for value in result.findings), ("different exact proposition",)
        )
        self.assertEqual(self.values(result.factors), ("DUPLICATE_PROPOSITION",))

    def test_duplicate_permutations_replay_identically(self):
        evidence = self.build_evidence()
        values = (
            self.proposition("TRANSPORTATION", "duplicate", ("E001",)),
            self.proposition("MOQ", "unique", ("E001",)),
            self.proposition("TRANSPORTATION", "duplicate", ("E001",)),
        )
        first = self.analyze(values, {evidence.id: evidence})
        second = self.analyze(tuple(reversed(values)), {evidence.id: evidence})
        self.assertEqual(first, second)

    def test_supplier_quotation_freshness_is_owned_by_existing_policy(self):
        fresh = self.build_evidence("E001", source_date=(AS_OF.date() - timedelta(days=90)).isoformat())
        stale = self.build_evidence("E002", source_date=(AS_OF.date() - timedelta(days=91)).isoformat())
        propositions = (
            self.proposition("SOURCING_COST", "fresh quote", ("E001",)),
            self.proposition("SOURCING_COST", "stale quote", ("E002",)),
        )
        result = self.analyze(propositions, {fresh.id: fresh, stale.id: stale})
        findings = {value.proposition: value for value in result.findings}
        self.assertEqual(findings["fresh quote"].outcome.value, "SUPPORTED")
        self.assertEqual(findings["stale quote"].outcome.value, "UNKNOWN")
        self.assertTrue(
            any(
                issue.reason_code.value == "STALE_EVIDENCE"
                for issue in findings["stale quote"].assessment.policy_results[0].issues
            )
        )

    def test_estimated_status_requires_explicit_compatible_claim_mode(self):
        estimated = self.build_evidence("E001", status="Estimated")
        observed_context = self.build_assessment_context()
        estimate_context = self.build_assessment_context(
            validation_context=self.build_context(claim_mode=self.p.ClaimMode("ESTIMATE"))
        )
        propositions = (
            self.proposition("MOQ", "observed mode", context=observed_context),
            self.proposition("MOQ", "estimate mode", context=estimate_context),
        )
        result = self.analyze(propositions, {estimated.id: estimated})
        findings = {value.proposition: value for value in result.findings}
        self.assertEqual(findings["observed mode"].outcome.value, "UNKNOWN")
        self.assertEqual(findings["estimate mode"].outcome.value, "SUPPORTED")

    def test_unknown_status_never_becomes_zero_or_supported(self):
        unknown = self.build_evidence("E001", status="Unknown")
        finding = self.analyze(
            (self.proposition(),), {unknown.id: unknown}
        ).findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.confidence.value, "Low")
        self.assertEqual(finding.supporting_ids, ())
        self.assertEqual(finding.assessment.policy_results[0].outcome.value, "REJECT")

    def test_equivalent_permutations_replay_identically(self):
        evidences = (self.build_evidence("E001"), self.build_evidence("E002"))
        first = self.proposition(
            "QUALITY",
            "replay",
            ("E002", "E001"),
            relations=(self.relation("E002"), self.relation("E001")),
            independence=(self.independence("E002"), self.independence("E001")),
            missing_information=(self.missing("z", "NON_MATERIAL"), self.missing("a", "NON_MATERIAL")),
        )
        second = self.proposition(
            "QUALITY",
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
        self.assertEqual(proposition.evidence_ids, (self.eid("E001"), self.eid("E002")))


class SupplyChainFailureAndScopeTests(SupplyChainTestBase):
    def test_malformed_proposition_collection_has_no_placeholder_and_is_input_error(self):
        result = self.analyze(["not a proposition"])
        self.assertEqual(result.findings, ())
        self.assertEqual(result.duplicate_proposition_keys, ())
        self.assertEqual(self.values(result.missing_dimensions), DIMENSIONS)
        self.assertEqual(self.values(result.factors), ("SUPPLY_CHAIN_INPUT_ERROR",))

    def test_malformed_shared_index_or_policy_keeps_well_formed_proposition_unknown(self):
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
                self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")
                self.assertEqual(result.findings[0].confidence.value, "Low")
                self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(result.findings[0].factors))

    def test_unresolved_evidence_id_is_a_traceable_unknown(self):
        proposition = self.proposition(evidence_ids=("E999",))
        result = self.analyze((proposition,), {})
        finding = result.findings[0]
        self.assertEqual(finding.outcome.value, "UNKNOWN")
        self.assertEqual(finding.assessment.outcome.value, "INSUFFICIENT")
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(finding.assessment.factors))

    def test_unexpected_ordinary_assessment_error_is_structured_but_base_exception_escapes(self):
        evidence = self.build_evidence()
        proposition = self.proposition()
        with mock.patch.object(self.supply, "assess_evidence", side_effect=RuntimeError("boom")):
            result = self.analyze((proposition,), {evidence.id: evidence})
        self.assertEqual(result.findings[0].outcome.value, "UNKNOWN")
        self.assertEqual(result.findings[0].confidence.value, "Low")
        with mock.patch.object(self.supply, "assess_evidence", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self.analyze((proposition,), {evidence.id: evidence})

    def test_absence_of_numeric_or_operational_declarations_does_not_create_facts(self):
        evidence = self.build_evidence(
            claim="MOQ 100, $10, 2kg, 0.5m3, supplier A, returns easy.",
            evidence="All facts appear in this record.",
        )
        result = self.analyze(evidence_index={evidence.id: evidence})
        self.assertEqual(result.findings, ())
        self.assertFalse(any("numeric" in field.name.lower() for field in dataclasses.fields(result)))

    def test_static_scope_and_import_audit(self):
        source = inspect.getsource(self.supply)
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
        self.assertEqual(public_functions, ("analyze_supply_chain",))
        self.assertEqual(
            public_classes,
            (
                "SupplyChainDimension",
                "SupplyChainFindingOutcome",
                "SupplyChainFactor",
                "SupplyChainPropositionInput",
                "SupplyChainPropositionKey",
                "SupplyChainFinding",
                "SupplyChainResult",
            ),
        )
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        imported = {
            (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
            for node in imports
            for alias in node.names
        }
        self.assertTrue(imported.issubset({"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy"}))
        forbidden = (
            "requests",
            "urllib",
            "httpx",
            "playwright",
            "scraper",
            "network",
            "browser",
            "random",
            "asyncio",
            "UnitEconomics",
            "fx",
            "score",
            "threshold",
            "recommendation",
            "RedTeam",
            "persistence",
            "reporting",
        )
        lowered = source.lower()
        for term in forbidden:
            self.assertNotIn(term.lower(), lowered, term)


if __name__ == "__main__":
    unittest.main()
