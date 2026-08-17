import ast
import copy
import dataclasses
import importlib
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)


class CompetitionTestBase(unittest.TestCase):
    def setUp(self):
        self.c = importlib.import_module("product_research.competition")
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
                ("Example Marketplace", "marketplace_listing"): self.p.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
                ("Example Review Hub", "customer_reviews"): self.p.SourceClass(
                    "CONSUMER_REVIEW_DISCUSSION"
                ),
            },
            "max_current_verification_age": 365,
        }
        values.update(overrides)
        return self.p.EvidencePolicy(**values)

    def build_evidence(self, value="E001", **overrides):
        values = {
            "id": self.eid(value),
            "claim": f"Explicit competition claim for {value}.",
            "evidence": f"Observed competition basis for {value}.",
            "source": self.e.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference=f"https://example.test/items/{value}",
                title=f"Listing {value}",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.e.Tier("Tier 2"),
            "status": self.e.Status("Observed"),
            "confidence": self.e.Confidence("High"),
            "metadata": {
                "policy": {"kind": "competition", "source_date": AS_OF.date().isoformat()}
            },
        }
        values.update(overrides)
        return self.e.Evidence(**values)

    def sample(self, identity, tags=("HEAD",), band="mid", evidence_id="E001"):
        return self.c.CompetitorSample(
            competitor_identity=identity,
            tags=tuple(self.c.SampleTag(value) for value in tags),
            price_band=band,
            evidence_ids=(self.eid(evidence_id),),
        )

    def proposition(
        self,
        dimension="POSITIONING",
        proposition="The competitor has an explicit position.",
        evidence_ids=("E001",),
        relations=None,
        independence=None,
        missing_information=(),
        context=None,
    ):
        ids = tuple(self.eid(value) for value in evidence_ids)
        if relations is None:
            relations = tuple(
                self.a.EvidenceRelation(evidence_id, self.a.Stance("SUPPORTS"))
                for evidence_id in ids
            )
        if independence is None:
            independence = tuple(
                self.a.IndependenceAssignment(evidence_id, f"group-{evidence_id.value}")
                for evidence_id in ids
            )
        if context is None:
            context = self.build_assessment_context()
        return self.c.CompetitionPropositionInput(
            dimension=self.c.CompetitionDimension(dimension),
            proposition=proposition,
            evidence_ids=ids,
            relations=tuple(relations),
            independence=tuple(independence),
            missing_information=tuple(missing_information),
            assessment_context=context,
        )

    def valid_samples(self, count, start=1, include_low_review=True):
        samples = []
        evidences = []
        tags = ("HEAD", "MIDDLE", "NEW_ENTRANT", "LOW_REVIEW")
        for offset in range(count):
            number = start + offset
            evidence_id = f"E{number:03d}"
            tag = tags[offset % len(tags)] if include_low_review else tags[offset % 3]
            band = "low" if offset % 2 == 0 else "high"
            samples.append(self.sample(f"competitor-{number:03d}", (tag,), band, evidence_id))
            evidences.append(self.build_evidence(evidence_id))
        return samples, {value.id: value for value in evidences}

    def analyze(self, samples=(), propositions=(), evidence_index=None, context=None, policy=None):
        if evidence_index is None:
            evidence_index = {}
        return self.c.analyze_competition(
            samples,
            propositions,
            evidence_index,
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def values(self, collection):
        return tuple(value.value for value in collection)


class CompetitionModulePresenceTests(unittest.TestCase):
    def test_competition_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("product_research.competition"))


class CompetitionVocabularyTests(CompetitionTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        expected = {
            "SampleTag": ("HEAD", "MIDDLE", "NEW_ENTRANT", "LOW_REVIEW"),
            "CompetitionDimension": ("POSITIONING", "DIFFERENTIATION", "MARKET_STRUCTURE"),
            "SampleAdequacy": ("ADEQUATE", "LIMITED", "UNKNOWN"),
            "CompetitionFindingOutcome": ("SUPPORTED", "UNKNOWN"),
        }
        for name, allowed in expected.items():
            value_type = getattr(self.c, name)
            self.assertEqual(value_type._allowed, allowed)
            value = value_type(allowed[0])
            with self.assertRaises(AttributeError):
                value._value = "OTHER"
            with self.assertRaises(AttributeError):
                del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        for name in (
            "SampleTag",
            "CompetitionDimension",
            "SampleAdequacy",
            "CompetitionFindingOutcome",
        ):
            value_type = getattr(self.c, name)
            for invalid in ("head", "Head", "UNKNOWN_VALUE", 1, None):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises((TypeError, ValueError)):
                        value_type(invalid)


class CompetitionInputValueTests(CompetitionTestBase):
    def test_sample_requires_exact_fields_and_canonicalizes_tags_and_ids(self):
        value = self.c.CompetitorSample(
            "Exact Identity",
            (self.c.SampleTag("LOW_REVIEW"), self.c.SampleTag("HEAD")),
            "opaque band 20-30",
            (self.eid("E002"), self.eid("E001")),
        )
        self.assertEqual(self.values(value.tags), ("HEAD", "LOW_REVIEW"))
        self.assertEqual(self.values(value.evidence_ids), ("E001", "E002"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.price_band = "other"
        for kwargs in (
            {"competitor_identity": "", "tags": (self.c.SampleTag("HEAD"),), "price_band": "x", "evidence_ids": (self.eid("E001"),)},
            {"competitor_identity": "x", "tags": (), "price_band": "x", "evidence_ids": (self.eid("E001"),)},
            {"competitor_identity": "x", "tags": (self.c.SampleTag("HEAD"),), "price_band": "", "evidence_ids": (self.eid("E001"),)},
            {"competitor_identity": "x", "tags": (self.c.SampleTag("HEAD"),), "price_band": "x", "evidence_ids": ()},
        ):
            with self.assertRaises((TypeError, ValueError)):
                self.c.CompetitorSample(**kwargs)
        with self.assertRaises((TypeError, ValueError)):
            self.c.CompetitorSample("x", [self.c.SampleTag("HEAD")], "x", (self.eid("E001"),))
        with self.assertRaises((TypeError, ValueError)):
            self.c.CompetitorSample(
                "x", (self.c.SampleTag("HEAD"), self.c.SampleTag("HEAD")), "x", (self.eid("E001"),)
            )
        with self.assertRaises((TypeError, ValueError)):
            self.c.CompetitorSample("x", (self.c.SampleTag("HEAD"),), "x", (self.eid("E001"), self.eid("E001")))

    def test_proposition_preserves_explicit_inputs_and_requires_material_context(self):
        relation = self.a.EvidenceRelation(self.eid("E002"), self.a.Stance("CONTRADICTS"))
        independence = self.a.IndependenceAssignment(self.eid("E002"), "source-2")
        missing = self.a.MissingInformation("unresolved_position", self.a.MissingSeverity("MATERIAL"))
        value = self.proposition(
            evidence_ids=("E002",),
            relations=(relation,),
            independence=(independence,),
            missing_information=(missing,),
        )
        self.assertEqual(value.evidence_ids, (self.eid("E002"),))
        self.assertEqual(value.relations, (relation,))
        self.assertEqual(value.independence, (independence,))
        self.assertEqual(value.missing_information, (missing,))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.proposition = "changed"
        non_material = self.build_assessment_context(
            validation_context=self.build_context(material=False)
        )
        with self.assertRaises((TypeError, ValueError)):
            self.proposition(context=non_material)

    def test_result_values_are_frozen_typed_and_have_no_numeric_decision_fields(self):
        samples, index = self.valid_samples(1)
        result = self.analyze(samples=samples, evidence_index=index)
        self.assertIs(type(result), self.c.CompetitionResult)
        self.assertIs(type(result.sample_results[0]), self.c.CompetitorSampleResult)
        for field in (
            "total_sample_count",
            "valid_sample_count",
            "target_min",
            "target_max",
            "sample_adequacy",
            "covered_strata",
            "missing_strata",
            "covered_price_bands",
            "sample_limitations",
            "sample_results",
            "findings",
            "factors",
        ):
            self.assertTrue(hasattr(result, field))
        self.assertFalse(
            any(name in result.__dataclass_fields__ for name in ("score", "threshold", "weight", "recommendation"))
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.target_min = 11
        with self.assertRaises(TypeError):
            self.c.CompetitionResult(
                0, 0, 10, 15, self.c.SampleAdequacy("UNKNOWN"), [], (), (), (), (), (), ()
            )

    def test_malformed_collections_fail_closed_without_fabrication(self):
        result = self.analyze(samples=[object()], propositions=[object()])
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("UNKNOWN"))
        self.assertEqual(result.valid_sample_count, 0)
        self.assertEqual(result.sample_results, ())
        self.assertEqual(result.findings, ())
        self.assertIn("COMPETITION_INPUT_ERROR", self.values(result.factors))


class CompetitionSampleAnalysisTests(CompetitionTestBase):
    def test_ten_to_fifteen_valid_samples_are_adequate_and_report_target(self):
        for count in (10, 15):
            samples, index = self.valid_samples(count)
            result = self.analyze(samples=samples, evidence_index=index)
            with self.subTest(count=count):
                self.assertEqual(result.total_sample_count, count)
                self.assertEqual(result.valid_sample_count, count)
                self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("ADEQUATE"))
                self.assertEqual((result.target_min, result.target_max), (10, 15))
                self.assertEqual(self.values(result.missing_strata), ())

    def test_nine_samples_are_retained_and_limited(self):
        samples, index = self.valid_samples(9)
        result = self.analyze(samples=samples, evidence_index=index)
        self.assertEqual(len(result.sample_results), 9)
        self.assertEqual(result.valid_sample_count, 9)
        self.assertEqual(self.values(result.sample_limitations), ("SAMPLE_SIZE_LIMITATION",))
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("LIMITED"))

    def test_more_than_fifteen_samples_are_all_retained(self):
        samples, index = self.valid_samples(16)
        result = self.analyze(samples=samples, evidence_index=index)
        self.assertEqual(result.valid_sample_count, 16)
        self.assertEqual(len(result.sample_results), 16)
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("ADEQUATE"))

    def test_duplicate_identity_invalidates_every_occurrence_order_independently(self):
        duplicate_a = self.sample("same", ("HEAD",), "zzz", "E001")
        duplicate_b = self.sample("same", ("NEW_ENTRANT",), "aaa", "E002")
        unique_samples, unique_index = self.valid_samples(10, start=3)
        index = {
            self.eid("E001"): self.build_evidence("E001"),
            self.eid("E002"): self.build_evidence("E002"),
            **unique_index,
        }
        first = self.analyze(samples=(duplicate_a, duplicate_b, *unique_samples), evidence_index=index)
        second = self.analyze(samples=(*unique_samples, duplicate_b, duplicate_a), evidence_index=index)
        self.assertEqual(first, second)
        self.assertEqual(first.valid_sample_count, 10)
        duplicate_results = [
            item for item in first.sample_results if item.sample.competitor_identity == "same"
        ]
        self.assertEqual(len(duplicate_results), 2)
        self.assertTrue(all(not item.valid for item in duplicate_results))
        self.assertTrue(
            all("DUPLICATE_COMPETITOR_IDENTITY" in self.values(item.factors) for item in duplicate_results)
        )
        self.assertNotIn("aaa", first.covered_price_bands)
        self.assertNotIn("zzz", first.covered_price_bands)

    def test_required_strata_are_fixed_and_low_review_is_optional(self):
        samples, index = self.valid_samples(10, include_low_review=False)
        result = self.analyze(samples=samples, evidence_index=index)
        self.assertEqual(self.values(result.covered_strata), ("HEAD", "MIDDLE", "NEW_ENTRANT"))
        self.assertEqual(self.values(result.missing_strata), ())
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("ADEQUATE"))

        missing_samples = [self.sample(f"head-{i}", ("HEAD",), "low", f"E{i:03d}") for i in range(1, 11)]
        missing_index = {self.eid(f"E{i:03d}"): self.build_evidence(f"E{i:03d}") for i in range(1, 11)}
        missing = self.analyze(samples=missing_samples, evidence_index=missing_index)
        self.assertEqual(self.values(missing.covered_strata), ("HEAD",))
        self.assertEqual(self.values(missing.missing_strata), ("MIDDLE", "NEW_ENTRANT"))
        self.assertIn("MISSING_REQUIRED_STRATUM", self.values(missing.sample_limitations))

    def test_price_bands_are_opaque_lexical_and_need_two_distinct_labels(self):
        samples, index = self.valid_samples(10)
        samples[0] = self.sample("competitor-001", ("HEAD",), "$100+", "E001")
        samples[1] = self.sample("competitor-002", ("MIDDLE",), "under-20", "E002")
        result = self.analyze(samples=samples, evidence_index=index)
        self.assertEqual(result.covered_price_bands, ("$100+", "high", "low", "under-20"))
        one_band = [self.sample(f"competitor-{i:03d}", ("HEAD", "MIDDLE", "NEW_ENTRANT"), "opaque", f"E{i:03d}") for i in range(1, 11)]
        one_index = {self.eid(f"E{i:03d}"): self.build_evidence(f"E{i:03d}") for i in range(1, 11)}
        limited = self.analyze(samples=one_band, evidence_index=one_index)
        self.assertEqual(limited.covered_price_bands, ("opaque",))
        self.assertIn("INSUFFICIENT_PRICE_BAND_COVERAGE", self.values(limited.sample_limitations))

    def test_policy_rejected_sample_is_local_and_preserves_policy_result(self):
        good = self.build_evidence("E001")
        stale = self.build_evidence(
            "E002",
            metadata={"policy": {"kind": "competition", "source_date": (AS_OF.date() - timedelta(days=366)).isoformat()}},
        )
        samples = (self.sample("good", ("HEAD",), "low", "E001"), self.sample("stale", ("MIDDLE",), "high", "E002"))
        index = {good.id: good, stale.id: stale}
        result = self.analyze(samples=samples, evidence_index=index)
        by_identity = {item.sample.competitor_identity: item for item in result.sample_results}
        self.assertTrue(by_identity["good"].valid)
        self.assertFalse(by_identity["stale"].valid)
        expected = self.p.validate_claim_support(
            (self.eid("E002"),), index, self.build_context(), self.build_policy()
        )
        self.assertEqual(by_identity["stale"].policy_result, expected)
        self.assertEqual(result.valid_sample_count, 1)
        self.assertEqual(self.values(result.covered_strata), ("HEAD",))

    def test_unknown_evidence_id_invalidates_only_its_sample_without_placeholder(self):
        good = self.build_evidence("E001")
        samples = (
            self.sample("good", ("HEAD",), "low", "E001"),
            self.sample("unresolved", ("MIDDLE",), "high", "E999"),
        )
        evidence_index = {good.id: good}

        result = self.analyze(samples=samples, evidence_index=evidence_index)

        by_identity = {item.sample.competitor_identity: item for item in result.sample_results}
        self.assertTrue(by_identity["good"].valid)
        self.assertFalse(by_identity["unresolved"].valid)
        self.assertEqual(
            by_identity["unresolved"].policy_result.issues[0].reason_code,
            self.p.ReasonCode("UNKNOWN_EVIDENCE_ID"),
        )
        self.assertEqual(result.valid_sample_count, 1)
        self.assertEqual(evidence_index, {good.id: good})

    def test_every_declared_sample_evidence_id_must_be_policy_usable(self):
        good = self.build_evidence("E001")
        stale = self.build_evidence(
            "E002",
            metadata={"policy": {"kind": "competition", "source_date": (AS_OF.date() - timedelta(days=366)).isoformat()}},
        )
        sample = self.c.CompetitorSample(
            "mixed", (self.c.SampleTag("HEAD"),), "low", (good.id, stale.id)
        )
        result = self.analyze(
            samples=(sample,), evidence_index={good.id: good, stale.id: stale}
        )
        value = result.sample_results[0]
        self.assertFalse(value.valid)
        self.assertEqual(value.policy_result.issues[0].reason_code.value, "STALE_EVIDENCE")
        self.assertEqual(result.valid_sample_count, 0)

    def test_unsupported_source_status_context_and_indeterminate_policy_are_local(self):
        unsupported = self.build_evidence(
            "E001",
            source=self.e.Source("Unknown", "listing", "ref", "Unknown"),
        )
        status_ineligible = self.build_evidence("E002", status=self.e.Status("Estimated"))
        malformed = object.__new__(self.e.Evidence)
        object.__setattr__(malformed, "id", self.eid("E003"))
        samples = (
            self.sample("unsupported", ("HEAD",), "a", "E001"),
            self.sample("status", ("MIDDLE",), "b", "E002"),
            self.sample("malformed", ("NEW_ENTRANT",), "c", "E003"),
        )
        result = self.analyze(
            samples=samples,
            evidence_index={unsupported.id: unsupported, status_ineligible.id: status_ineligible, malformed.id: malformed},
        )
        self.assertEqual(result.valid_sample_count, 0)
        self.assertTrue(all(not value.valid for value in result.sample_results))
        issue_values = {
            issue.reason_code.value
            for value in result.sample_results
            for issue in value.policy_result.issues
        }
        self.assertIn("UNSUPPORTED_SOURCE", issue_values)
        self.assertIn("STATUS_NOT_FACT_ELIGIBLE", issue_values)
        self.assertIn("VALIDATION_ERROR", issue_values)

        with mock.patch.object(self.c, "validate_claim_support", side_effect=RuntimeError):
            indeterminate = self.analyze(
                samples=(self.sample("indeterminate", ("HEAD",), "a", "E001"),),
                evidence_index={self.eid("E001"): self.build_evidence("E001")},
            )
        self.assertFalse(indeterminate.sample_results[0].valid)
        self.assertEqual(
            indeterminate.sample_results[0].policy_result.issues[0].reason_code,
            self.p.ReasonCode("VALIDATION_ERROR"),
        )


class CompetitionFindingAnalysisTests(CompetitionTestBase):
    def test_each_dimension_and_same_dimension_proposition_is_assessed_separately(self):
        samples, index = self.valid_samples(0)
        index = {self.eid(f"E{i:03d}"): self.build_evidence(f"E{i:03d}") for i in range(1, 4)}
        propositions = (
            self.proposition("POSITIONING", "position", ("E001",)),
            self.proposition("DIFFERENTIATION", "copyability", ("E002",)),
            self.proposition("MARKET_STRUCTURE", "concentration", ("E003",)),
            self.proposition("POSITIONING", "audience", ("E001",)),
        )
        assessments = []
        original_assess = self.c.assess_evidence

        def record_assessment(*args):
            assessment = original_assess(*args)
            assessments.append(assessment)
            return assessment

        with mock.patch.object(self.c, "assess_evidence", side_effect=record_assessment) as assessed:
            result = self.analyze(propositions=propositions, evidence_index=index)
        self.assertEqual(assessed.call_count, 4)
        self.assertEqual(
            tuple((finding.dimension.value, finding.proposition) for finding in result.findings),
            (("POSITIONING", "audience"), ("POSITIONING", "position"), ("DIFFERENTIATION", "copyability"), ("MARKET_STRUCTURE", "concentration")),
        )
        self.assertEqual(len({finding.assessment for finding in result.findings}), 3)
        assessment_by_proposition = {
            proposition.proposition: assessment
            for proposition, assessment in zip(propositions, assessments)
        }
        for finding in result.findings:
            self.assertIs(finding.assessment, assessment_by_proposition[finding.proposition])

    def test_supported_finding_copies_existing_outcome_confidence_and_ids(self):
        for confidence in ("High", "Medium", "Low"):
            evidence = self.build_evidence("E001", confidence=self.e.Confidence(confidence))
            result = self.analyze(
                propositions=(self.proposition(),), evidence_index={evidence.id: evidence}
            )
            finding = result.findings[0]
            self.assertEqual(finding.outcome, self.c.CompetitionFindingOutcome("SUPPORTED"))
            self.assertEqual(finding.confidence, finding.assessment.confidence)
            self.assertEqual(finding.confidence.value, confidence)
            self.assertEqual(finding.supporting_ids, (self.eid("E001"),))

    def test_conflict_is_unknown_and_retains_adverse_and_excluded_ids(self):
        support = self.build_evidence("E001")
        adverse = self.build_evidence(
            "E002",
            source=self.e.Source(
                provider="Example Review Hub",
                source_type="customer_reviews",
                reference="https://example.test/reviews/E002",
                title="Review E002",
            ),
            tier=self.e.Tier("Tier 3"),
        )
        stale = self.build_evidence(
            "E003",
            metadata={"policy": {"kind": "competition", "source_date": (AS_OF.date() - timedelta(days=400)).isoformat()}},
        )
        proposition = self.proposition(
            evidence_ids=("E001", "E002", "E003"),
            relations=(
                self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("SUPPORTS")),
                self.a.EvidenceRelation(self.eid("E002"), self.a.Stance("CONTRADICTS")),
                self.a.EvidenceRelation(self.eid("E003"), self.a.Stance("CONTRADICTS")),
            ),
        )
        result = self.analyze(
            propositions=(proposition,),
            evidence_index={item.id: item for item in (support, adverse, stale)},
        )
        finding = result.findings[0]
        self.assertEqual(finding.outcome, self.c.CompetitionFindingOutcome("UNKNOWN"))
        self.assertEqual(finding.confidence, self.e.Confidence("Low"))
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002", "E003"))
        self.assertEqual(self.values(finding.excluded_ids), ("E003",))
        self.assertIs(finding.assessment, finding.assessment)

    def test_insufficient_finding_preserves_missing_information_and_assessment(self):
        missing = self.a.MissingInformation("unresolved_claim", self.a.MissingSeverity("MATERIAL"))
        evidence = self.build_evidence("E001")
        proposition = self.proposition(
            evidence_ids=("E001",),
            relations=(self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("NEUTRAL")),),
            missing_information=(missing,),
        )
        result = self.analyze(propositions=(proposition,), evidence_index={evidence.id: evidence})
        finding = result.findings[0]
        self.assertEqual(finding.outcome, self.c.CompetitionFindingOutcome("UNKNOWN"))
        self.assertEqual(finding.confidence, self.e.Confidence("Low"))
        self.assertEqual(finding.assessment.missing_information, (missing,))
        self.assertEqual(finding.supporting_ids, ())
        self.assertEqual(finding.excluded_ids, ())

    def test_incomplete_assignments_fail_only_that_finding(self):
        index = {self.eid(f"E{i:03d}"): self.build_evidence(f"E{i:03d}") for i in range(1, 4)}
        invalid = self.proposition(
            dimension="POSITIONING",
            proposition="incomplete",
            evidence_ids=("E001", "E002"),
            relations=(self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("SUPPORTS")),),
            independence=(self.a.IndependenceAssignment(self.eid("E001"), "group-1"),),
        )
        valid = self.proposition("DIFFERENTIATION", "valid", ("E003",))
        result = self.analyze(propositions=(invalid, valid), evidence_index=index)
        findings = {finding.proposition: finding for finding in result.findings}
        self.assertEqual(findings["incomplete"].outcome, self.c.CompetitionFindingOutcome("UNKNOWN"))
        self.assertIn("ASSESSMENT_INPUT_ERROR", self.values(findings["incomplete"].factors))
        self.assertEqual(findings["valid"].outcome, self.c.CompetitionFindingOutcome("SUPPORTED"))

    def test_duplicate_relations_or_independence_fail_only_that_finding(self):
        evidence = self.build_evidence("E001")
        relation = self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("SUPPORTS"))
        independence = self.a.IndependenceAssignment(self.eid("E001"), "group-1")
        duplicate_relation = self.proposition(
            proposition="duplicate relation",
            relations=(relation, relation),
            independence=(independence,),
        )
        duplicate_independence = self.proposition(
            proposition="duplicate independence",
            relations=(relation,),
            independence=(independence, independence),
        )
        result = self.analyze(
            propositions=(duplicate_relation, duplicate_independence),
            evidence_index={evidence.id: evidence},
        )
        self.assertEqual(len(result.findings), 2)
        self.assertTrue(
            all(
                finding.outcome == self.c.CompetitionFindingOutcome("UNKNOWN")
                and "ASSESSMENT_INPUT_ERROR" in self.values(finding.factors)
                for finding in result.findings
            )
        )

    def test_missing_citation_and_unknown_id_remain_unknown_without_placeholder_support(self):
        missing = self.analyze(
            propositions=(self.proposition(evidence_ids=(), relations=(), independence=()),),
            evidence_index={},
        ).findings[0]
        self.assertEqual(missing.outcome, self.c.CompetitionFindingOutcome("UNKNOWN"))
        self.assertEqual(missing.supporting_ids, ())
        self.assertEqual(
            missing.assessment.claim_support_result.issues[0].reason_code,
            self.p.ReasonCode("MISSING_CITATION"),
        )

        unknown = self.analyze(
            propositions=(self.proposition(evidence_ids=("E999",)),), evidence_index={}
        ).findings[0]
        self.assertEqual(unknown.outcome, self.c.CompetitionFindingOutcome("UNKNOWN"))
        self.assertEqual(unknown.supporting_ids, ())

    def test_malformed_shared_policy_or_context_cannot_produce_a_finding(self):
        evidence = self.build_evidence("E001")
        samples = (self.sample("one", ("HEAD",), "a", "E001"),)
        proposition = self.proposition()
        result = self.analyze(
            samples=samples,
            propositions=(proposition,),
            evidence_index={evidence.id: evidence},
            context="not a context",
            policy="not a policy",
        )
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("UNKNOWN"))
        self.assertEqual(result.valid_sample_count, 0)
        self.assertEqual(result.findings, ())
        self.assertNotIn(self.c.CompetitionFindingOutcome("SUPPORTED"), result.findings)

    def test_duplicate_dimension_and_proposition_fails_collection_closed(self):
        evidence = self.build_evidence("E001")
        first = self.proposition("POSITIONING", "same", ("E001",))
        second = self.proposition("POSITIONING", "same", ("E001",))
        result = self.analyze(
            propositions=(second, first), evidence_index={evidence.id: evidence}
        )
        self.assertEqual(result.findings, ())
        self.assertIn("COMPETITION_INPUT_ERROR", self.values(result.factors))

    def test_traceability_keeps_each_evidence_id_class_and_nested_assessment(self):
        support = self.build_evidence("E001")
        adverse = self.build_evidence("E002")
        excluded = self.build_evidence(
            "E003",
            metadata={"policy": {"kind": "competition", "source_date": (AS_OF.date() - timedelta(days=400)).isoformat()}},
        )
        proposition = self.proposition(
            evidence_ids=("E003", "E002", "E001"),
            relations=(
                self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("SUPPORTS")),
                self.a.EvidenceRelation(self.eid("E002"), self.a.Stance("CONTRADICTS")),
                self.a.EvidenceRelation(self.eid("E003"), self.a.Stance("CONTRADICTS")),
            ),
        )
        result = self.analyze(
            propositions=(proposition,),
            evidence_index={item.id: item for item in (support, adverse, excluded)},
        )
        finding = result.findings[0]
        self.assertEqual(self.values(finding.supporting_ids), ("E001",))
        self.assertEqual(self.values(finding.adverse_ids), ("E002", "E003"))
        self.assertEqual(self.values(finding.excluded_ids), ("E003",))
        self.assertEqual(finding.assessment, result.findings[0].assessment)


class CompetitionReplayAndOwnershipTests(CompetitionTestBase):
    def test_equivalent_input_permutations_replay_identically(self):
        samples, index = self.valid_samples(10)
        relations = (
            self.a.EvidenceRelation(self.eid("E001"), self.a.Stance("SUPPORTS")),
            self.a.EvidenceRelation(self.eid("E002"), self.a.Stance("SUPPORTS")),
        )
        independence = (
            self.a.IndependenceAssignment(self.eid("E001"), "group-1"),
            self.a.IndependenceAssignment(self.eid("E002"), "group-2"),
        )
        missing_information = (
            self.a.MissingInformation("zeta", self.a.MissingSeverity("NON_MATERIAL")),
            self.a.MissingInformation("alpha", self.a.MissingSeverity("NON_MATERIAL")),
        )
        first_propositions = (
            self.proposition(
                "MARKET_STRUCTURE",
                "structure",
                ("E002", "E001"),
                relations=relations,
                independence=independence,
                missing_information=missing_information,
            ),
            self.proposition("POSITIONING", "position", ("E003",)),
        )
        second_propositions = (
            self.proposition("POSITIONING", "position", ("E003",)),
            self.proposition(
                "MARKET_STRUCTURE",
                "structure",
                ("E001", "E002"),
                relations=tuple(reversed(relations)),
                independence=tuple(reversed(independence)),
                missing_information=tuple(reversed(missing_information)),
            ),
        )
        first = self.analyze(
            samples=samples,
            propositions=first_propositions,
            evidence_index=index,
        )
        second = self.analyze(
            samples=tuple(reversed(samples)),
            propositions=second_propositions,
            evidence_index=dict(reversed(tuple(index.items()))),
        )
        self.assertEqual(first, second)

    def test_analysis_does_not_mutate_any_supplied_value(self):
        samples, index = self.valid_samples(10)
        propositions = (self.proposition(),)
        context = self.build_context()
        policy = self.build_policy()
        before_index = copy.deepcopy(index)
        before_samples = copy.deepcopy(samples)
        before_props = copy.deepcopy(propositions)
        before_registry = dict(policy.source_registry)
        before_limits = dict(policy.freshness_limits)
        self.analyze(
            samples=samples,
            propositions=propositions,
            evidence_index=index,
            context=context,
            policy=policy,
        )
        self.assertEqual(index, before_index)
        self.assertEqual(samples, before_samples)
        self.assertEqual(propositions, before_props)
        self.assertEqual(context, self.build_context())
        self.assertEqual(dict(policy.source_registry), before_registry)
        self.assertEqual(dict(policy.freshness_limits), before_limits)

    def test_shared_input_mismatch_fails_closed_and_does_not_swallow_control_exceptions(self):
        sample = self.sample("broken", ("HEAD",), "low", "E001")
        mismatched = {self.eid("E001"): self.build_evidence("E002")}
        result = self.analyze(samples=(sample,), evidence_index=mismatched)
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("UNKNOWN"))
        self.assertEqual(result.valid_sample_count, 0)
        self.assertEqual(self.values(result.missing_strata), ("HEAD", "MIDDLE", "NEW_ENTRANT"))
        self.assertEqual(result.covered_price_bands, ())

        with mock.patch.object(self.c, "validate_claim_support", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.analyze(samples=(sample,), evidence_index={self.eid("E001"): self.build_evidence("E001")})

    def test_corrupted_frozen_values_fail_closed_without_leaking_attribute_errors(self):
        evidence = self.build_evidence("E001")
        sample = self.sample("one", ("HEAD",), "a", "E001")
        bad_context = object.__new__(self.p.ValidationContext)
        result = self.analyze(
            samples=(sample,),
            propositions=(),
            evidence_index={evidence.id: evidence},
            context=bad_context,
        )
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("UNKNOWN"))
        self.assertEqual(result.valid_sample_count, 0)

        bad_sample = object.__new__(self.c.CompetitorSample)
        object.__setattr__(bad_sample, "competitor_identity", "bad")
        object.__setattr__(bad_sample, "tags", ())
        result = self.analyze(samples=(bad_sample,), evidence_index={evidence.id: evidence})
        self.assertEqual(result.sample_adequacy, self.c.SampleAdequacy("UNKNOWN"))

        bad_proposition = object.__new__(self.c.CompetitionPropositionInput)
        object.__setattr__(bad_proposition, "dimension", self.c.CompetitionDimension("POSITIONING"))
        result = self.analyze(
            propositions=(bad_proposition,), evidence_index={evidence.id: evidence}
        )
        self.assertEqual(result.findings, ())

    def test_static_scope_and_import_audit(self):
        with open(self.c.__file__, encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
        self.assertTrue(
            set(imports)
            <= {"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy"}
        )
        names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
        forbidden_names = {"Evidence", "RawFinding", "AcquisitionResult", "run_research", "score", "recommendation"}
        self.assertTrue(forbidden_names.isdisjoint(names))
        for marker in ("network", "browser", "scrap", "llm", "persist", "report", "risk", "voc", "supply_chain"):
            self.assertNotIn(marker, source.lower())


if __name__ == "__main__":
    unittest.main()
