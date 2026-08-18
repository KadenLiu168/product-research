import copy
import importlib
import unittest
from datetime import datetime, timedelta, timezone


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)


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


class PolicyTestBase(unittest.TestCase):
    def setUp(self):
        self.policy = _policy_module()
        self.evidence = _evidence_module()

    def date_days_before(self, days):
        return (AS_OF.date() - timedelta(days=days)).isoformat()

    def build_evidence(self, **overrides):
        values = {
            "id": self.evidence.EvidenceId("E001"),
            "claim": "Listed retail price is $39.99.",
            "evidence": "The product page displayed a listed price of $39.99.",
            "source": self.evidence.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference="https://example.test/products/123",
                title="Example product listing",
            ),
            "observed_at": "2026-08-15T11:00:00Z",
            "tier": self.evidence.Tier("Tier 2"),
            "status": self.evidence.Status("Observed"),
            "confidence": self.evidence.Confidence("Medium"),
            "metadata": {"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(0)}},
        }
        values.update(overrides)
        return self.evidence.Evidence(**values)

    def build_context(self, **overrides):
        values = {
            "as_of": AS_OF,
            "claim_mode": self.policy.ClaimMode("OBSERVED_FACT"),
            "temporal_scope": self.policy.TemporalScope("CURRENT"),
            "material": True,
            "critical": False,
        }
        values.update(overrides)
        return self.policy.ValidationContext(**values)

    def build_policy(self, **overrides):
        values = {
            "source_registry": {
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
            },
            "max_current_verification_age": 365,
        }
        values.update(overrides)
        return self.policy.EvidencePolicy(**values)


class PolicyVocabularyContractTests(PolicyTestBase):
    def test_outcome_values_are_closed(self):
        for value in ("ACCEPT_CURRENT", "CONTEXT_ONLY", "REJECT"):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.Outcome(value)), value)

    def test_outcome_rejects_unknown_values(self):
        for invalid in ("MAYBE", "ACCEPT", "reject", 1, None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.policy.Outcome(invalid)

    def test_claim_mode_values_are_closed(self):
        for value in ("OBSERVED_FACT", "ESTIMATE", "DERIVED_VALUE"):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.ClaimMode(value)), value)

    def test_claim_mode_rejects_unknown_values(self):
        for invalid in ("FACT", "observed", None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.policy.ClaimMode(invalid)

    def test_temporal_scope_values_are_closed(self):
        for value in ("CURRENT", "HISTORICAL", "CONTEXT"):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.TemporalScope(value)), value)

    def test_temporal_scope_rejects_unknown_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.policy.TemporalScope("PAST")

    def test_source_class_values_are_closed(self):
        for value in (
            "OFFICIAL_AUTHORITATIVE",
            "FIRST_PARTY_MARKETPLACE_SUPPLIER",
            "CONSUMER_REVIEW_DISCUSSION",
            "SECONDARY_INDUSTRY",
        ):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.SourceClass(value)), value)

    def test_source_class_rejects_unknown_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.policy.SourceClass("BLOG")

    def test_evidence_kind_values_are_closed(self):
        for value in (
            "market",
            "competition",
            "marketplace_price",
            "supplier_quotation",
            "voc",
            "regulation",
            "certification",
            "tariff",
            "ip_authoritative_record",
            "long_term_industry",
        ):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.EvidenceKind(value)), value)

    def test_evidence_kind_vocabulary_is_exact(self):
        self.assertEqual(
            self.policy.EvidenceKind._allowed,
            (
                "market",
                "competition",
                "marketplace_price",
                "supplier_quotation",
                "voc",
                "regulation",
                "certification",
                "tariff",
                "ip_authoritative_record",
                "long_term_industry",
            ),
        )

    def test_evidence_kind_rejects_unknown_values(self):
        for invalid in ("mystery", "ip", "patent", "trademark", "regulation_ip", "IP_AUTHORITATIVE_RECORD"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    self.policy.EvidenceKind(invalid)

    def test_reason_codes_cover_the_contract(self):
        for value in (
            "UNSUPPORTED_SOURCE",
            "TIER_MISMATCH",
            "STALE_EVIDENCE",
            "FUTURE_OBSERVATION",
            "MISSING_FRESHNESS_METADATA",
            "STATUS_NOT_FACT_ELIGIBLE",
            "UNKNOWN_EVIDENCE_ID",
            "DUPLICATE_EVIDENCE_ID",
            "MISSING_CITATION",
            "TIER4_SOLE_CRITICAL_SUPPORT",
            "UNSUPPORTED_EVIDENCE_KIND",
            "INVALID_POLICY_METADATA",
            "VALIDATION_ERROR",
        ):
            with self.subTest(value=value):
                self.assertEqual(str(self.policy.ReasonCode(value)), value)

    def test_reason_code_rejects_unknown_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.policy.ReasonCode("SOME_OTHER_CODE")

    def test_validation_context_is_immutable(self):
        context = self.build_context()

        with self.assertRaises(AttributeError):
            context.as_of = AS_OF

    def test_validation_context_requires_critical_to_be_material(self):
        with self.assertRaises(ValueError):
            self.build_context(critical=True, material=False)

    def test_validation_context_rejects_wrong_field_types(self):
        with self.assertRaises((TypeError, ValueError)):
            self.build_context(as_of="2026-08-15T12:00:00Z")
        with self.assertRaises((TypeError, ValueError)):
            self.build_context(claim_mode="OBSERVED_FACT")
        with self.assertRaises((TypeError, ValueError)):
            self.build_context(temporal_scope="CURRENT")
        with self.assertRaises((TypeError, ValueError)):
            self.build_context(material="yes")

    def test_evidence_policy_is_immutable(self):
        policy = self.build_policy()

        with self.assertRaises(AttributeError):
            policy.max_current_verification_age = 1
        with self.assertRaises(TypeError):
            policy.source_registry[("Example Marketplace", "marketplace_listing")] = self.policy.SourceClass(
                "OFFICIAL_AUTHORITATIVE"
            )

    def test_evidence_policy_requires_explicit_verification_age(self):
        with self.assertRaises(TypeError):
            self.policy.EvidencePolicy(
                source_registry={
                    ("Example Marketplace", "marketplace_listing"): self.policy.SourceClass(
                        "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                    )
                }
            )

    def test_evidence_policy_rejects_invalid_registry_entries(self):
        with self.assertRaises((TypeError, ValueError)):
            self.build_policy(
                source_registry={("provider",): self.policy.SourceClass("OFFICIAL_AUTHORITATIVE")}
            )
        with self.assertRaises((TypeError, ValueError)):
            self.build_policy(source_registry={("provider", "type"): "OFFICIAL_AUTHORITATIVE"})

    def test_policy_issue_and_result_are_immutable(self):
        issue = self.policy.PolicyIssue(self.policy.ReasonCode("STALE_EVIDENCE"))
        result = self.policy.PolicyValidationResult(self.policy.Outcome("REJECT"), False, None, (issue,))

        with self.assertRaises(AttributeError):
            issue.reason_code = self.policy.ReasonCode("TIER_MISMATCH")
        with self.assertRaises(AttributeError):
            result.outcome = self.policy.Outcome("ACCEPT_CURRENT")


class ValidateEvidenceSourceTierTests(PolicyTestBase):
    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_evidence(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_registered_marketplace_source_with_tier2_passes(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)
        self.assertEqual(result.evidence_id, self.evidence.EvidenceId("E001"))
        self.assertEqual(result.issues, ())

    def test_marketplace_source_marked_tier1_rejected(self):
        result = self.validate(evidence=self.build_evidence(tier=self.evidence.Tier("Tier 1")))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER_MISMATCH")],
        )

    def test_unregistered_source_rejected(self):
        evidence = self.build_evidence(
            source=self.evidence.Source(
                provider="Unknown Provider",
                source_type="marketplace_listing",
                reference="https://unknown.test/item",
                title=None,
            )
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("UNSUPPORTED_SOURCE")],
        )
        self.assertEqual(result.issues[0].evidence_id, self.evidence.EvidenceId("E001"))

    def test_exact_registry_key_required(self):
        evidence = self.build_evidence(
            source=self.evidence.Source(
                provider="Example Marketplace",
                source_type="seller_offer",
                reference="https://example.test/offers/7",
                title=None,
            )
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("UNSUPPORTED_SOURCE")],
        )

    def test_each_source_class_maps_to_its_expected_tier(self):
        cases = (
            ("OFFICIAL_AUTHORITATIVE", "Regulatory Agency", "official_regulation", "Tier 1"),
            ("FIRST_PARTY_MARKETPLACE_SUPPLIER", "Example Marketplace", "marketplace_listing", "Tier 2"),
            ("CONSUMER_REVIEW_DISCUSSION", "Consumer Review Hub", "customer_reviews", "Tier 3"),
            ("SECONDARY_INDUSTRY", "Industry Journal", "secondary_articles", "Tier 4"),
        )
        for source_class, provider, source_type, tier in cases:
            with self.subTest(source_class=source_class):
                evidence = self.build_evidence(
                    source=self.evidence.Source(
                        provider=provider,
                        source_type=source_type,
                        reference="https://example.test/reference",
                        title=None,
                    ),
                    tier=self.evidence.Tier(tier),
                )
                result = self.validate(evidence=evidence)

                self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
                self.assertTrue(result.fact_eligible)


class ValidateEvidenceStatusModeTests(PolicyTestBase):
    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_evidence(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_estimated_evidence_cannot_support_observed_fact(self):
        result = self.validate(evidence=self.build_evidence(status=self.evidence.Status("Estimated")))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STATUS_NOT_FACT_ELIGIBLE")],
        )

    def test_status_must_match_claim_mode(self):
        cases = (
            (self.evidence.Status("Observed"), "OBSERVED_FACT", True),
            (self.evidence.Status("Estimated"), "ESTIMATE", True),
            (self.evidence.Status("Calculated"), "DERIVED_VALUE", True),
            (self.evidence.Status("Observed"), "ESTIMATE", False),
            (self.evidence.Status("Observed"), "DERIVED_VALUE", False),
            (self.evidence.Status("Estimated"), "OBSERVED_FACT", False),
            (self.evidence.Status("Estimated"), "DERIVED_VALUE", False),
            (self.evidence.Status("Calculated"), "OBSERVED_FACT", False),
            (self.evidence.Status("Calculated"), "ESTIMATE", False),
        )
        for status, claim_mode, expected_pass in cases:
            with self.subTest(status=status.value, claim_mode=claim_mode):
                result = self.validate(
                    evidence=self.build_evidence(status=status),
                    context=self.build_context(claim_mode=self.policy.ClaimMode(claim_mode)),
                )
                if expected_pass:
                    self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
                else:
                    self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                    self.assertEqual(
                        [issue.reason_code for issue in result.issues],
                        [self.policy.ReasonCode("STATUS_NOT_FACT_ELIGIBLE")],
                    )

    def test_calculated_evidence_retains_derived_semantics(self):
        evidence = self.build_evidence(status=self.evidence.Status("Calculated"))
        result = self.validate(
            evidence=evidence,
            context=self.build_context(claim_mode=self.policy.ClaimMode("DERIVED_VALUE")),
        )

        self.assertEqual(str(evidence.status), "Calculated")
        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_unknown_evidence_never_fact_eligible(self):
        for claim_mode in ("OBSERVED_FACT", "ESTIMATE", "DERIVED_VALUE"):
            with self.subTest(claim_mode=claim_mode):
                result = self.validate(
                    evidence=self.build_evidence(status=self.evidence.Status("Unknown")),
                    context=self.build_context(claim_mode=self.policy.ClaimMode(claim_mode)),
                )

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertFalse(result.fact_eligible)
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("STATUS_NOT_FACT_ELIGIBLE")],
                )


class ValidateEvidenceFutureObservationTests(PolicyTestBase):
    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_evidence(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_observation_after_as_of_rejected(self):
        result = self.validate(evidence=self.build_evidence(observed_at="2026-08-15T13:00:00Z"))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("FUTURE_OBSERVATION")],
        )

    def test_observation_at_as_of_is_not_future(self):
        result = self.validate(evidence=self.build_evidence(observed_at="2026-08-15T12:00:00Z"))

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)


class ValidateEvidenceDeterminismTests(PolicyTestBase):
    def test_replay_with_same_as_of_is_identical(self):
        evidence = self.build_evidence(
            source=self.evidence.Source(
                provider="Unknown Provider",
                source_type="marketplace_listing",
                reference="https://unknown.test/item",
                title=None,
            ),
            status=self.evidence.Status("Estimated"),
            observed_at="2026-08-15T13:00:00Z",
        )
        context = self.build_context()
        policy = self.build_policy()

        results = [self.policy.validate_evidence(evidence, context, policy) for _ in range(3)]

        for result in results[1:]:
            self.assertEqual(result.outcome, results[0].outcome)
            self.assertEqual(result.fact_eligible, results[0].fact_eligible)
            self.assertEqual(
                [issue.reason_code for issue in result.issues],
                [issue.reason_code for issue in results[0].issues],
            )

    def test_multiple_issues_have_deterministic_order(self):
        evidence = self.build_evidence(
            source=self.evidence.Source(
                provider="Unknown Provider",
                source_type="marketplace_listing",
                reference="https://unknown.test/item",
                title=None,
            ),
            status=self.evidence.Status("Estimated"),
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
        )
        context = self.build_context()
        policy = self.build_policy()

        expected_codes = [
            self.policy.ReasonCode("UNSUPPORTED_SOURCE"),
            self.policy.ReasonCode("STALE_EVIDENCE"),
            self.policy.ReasonCode("STATUS_NOT_FACT_ELIGIBLE"),
        ]
        first = self.policy.validate_evidence(evidence, context, policy)
        second = self.policy.validate_evidence(evidence, context, policy)

        self.assertEqual([issue.reason_code for issue in first.issues], expected_codes)
        self.assertEqual([issue.reason_code for issue in second.issues], expected_codes)


class ValidateEvidenceNonMutationTests(PolicyTestBase):
    def test_validation_does_not_mutate_or_repair_evidence(self):
        evidence = self.build_evidence(
            source=self.evidence.Source(
                provider="Unknown Provider",
                source_type="marketplace_listing",
                reference="https://unknown.test/item",
                title=None,
            ),
            metadata={
                "policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)},
                "extra": [1, 2],
            },
        )
        before = evidence.to_json()
        metadata_before = copy.deepcopy(evidence.metadata)
        context = self.build_context()
        policy = self.build_policy()

        result = self.policy.validate_evidence(evidence, context, policy)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(evidence.to_json(), before)
        self.assertEqual(evidence.metadata, metadata_before)
        self.assertEqual(context, self.build_context())
        self.assertEqual(policy, self.build_policy())

    def test_structurally_valid_evidence_still_requires_policy_acceptance(self):
        result = self.policy.validate_evidence(
            self.build_evidence(
                source=self.evidence.Source(
                    provider="Unknown Provider",
                    source_type="marketplace_listing",
                    reference="https://unknown.test/item",
                    title=None,
                )
            ),
            self.build_context(),
            self.build_policy(),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)


class ValidateEvidenceMetadataTests(PolicyTestBase):
    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_evidence(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_dated_kinds_without_source_date_rejected(self):
        for kind in ("market", "competition", "marketplace_price", "supplier_quotation", "voc"):
            with self.subTest(kind=kind):
                result = self.validate(evidence=self.build_evidence(metadata={"policy": {"kind": kind}}))

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
                )

    def test_missing_policy_metadata_rejected(self):
        for metadata in ({}, {"currency": "USD"}):
            with self.subTest(metadata=repr(metadata)):
                result = self.validate(evidence=self.build_evidence(metadata=metadata))

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("UNSUPPORTED_EVIDENCE_KIND")],
                )

    def test_unsupported_kind_rejected(self):
        result = self.validate(
            evidence=self.build_evidence(metadata={"policy": {"kind": "mystery"}})
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("UNSUPPORTED_EVIDENCE_KIND")],
        )

    def test_non_string_kind_rejected(self):
        result = self.validate(evidence=self.build_evidence(metadata={"policy": {"kind": 42}}))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("UNSUPPORTED_EVIDENCE_KIND")],
        )

    def test_non_object_policy_metadata_rejected(self):
        for policy_value in ("marketplace_price", ["marketplace_price"], 42, None, True):
            with self.subTest(policy_value=repr(policy_value)):
                result = self.validate(evidence=self.build_evidence(metadata={"policy": policy_value}))

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("UNSUPPORTED_EVIDENCE_KIND")],
                )

    def test_malformed_source_date_rejected(self):
        for source_date in ("2026-13-01", "2026-2-3", "not-a-date", "20260815", 20260815):
            with self.subTest(source_date=repr(source_date)):
                result = self.validate(
                    evidence=self.build_evidence(
                        metadata={"policy": {"kind": "marketplace_price", "source_date": source_date}}
                    )
                )

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
                )

    def test_future_source_date_rejected(self):
        result = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "marketplace_price", "source_date": "2026-08-16"}}
            )
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_unrelated_metadata_is_preserved_and_ignored(self):
        result = self.validate(
            evidence=self.build_evidence(
                metadata={
                    "policy": {"kind": "marketplace_price", "source_date": self.date_days_before(0)},
                    "currency": "USD",
                    "nested": {"raw": [1, 2.5, None]},
                }
            )
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_observed_at_never_stands_in_for_source_date(self):
        evidence = self.build_evidence(
            observed_at="2026-08-15T11:00:00Z",
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )


class ValidateEvidenceFreshnessTests(PolicyTestBase):
    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_evidence(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_marketplace_price_365_day_boundary_included(self):
        result = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(365)}}
            )
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_thirteen_month_old_price_is_stale(self):
        result = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(366)}}
            )
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_market_and_competition_use_365_day_window(self):
        for kind in ("market", "competition"):
            with self.subTest(kind=kind):
                fresh = self.validate(
                    evidence=self.build_evidence(
                        metadata={"policy": {"kind": kind, "source_date": self.date_days_before(365)}}
                    )
                )
                stale = self.validate(
                    evidence=self.build_evidence(
                        metadata={"policy": {"kind": kind, "source_date": self.date_days_before(366)}}
                    )
                )

                self.assertEqual(fresh.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
                self.assertEqual(stale.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in stale.issues],
                    [self.policy.ReasonCode("STALE_EVIDENCE")],
                )

    def test_supplier_quotation_90_day_boundary(self):
        at_boundary = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "supplier_quotation", "source_date": self.date_days_before(90)}}
            )
        )
        first_stale = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "supplier_quotation", "source_date": self.date_days_before(91)}}
            )
        )

        self.assertEqual(at_boundary.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertEqual(first_stale.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in first_stale.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_voc_730_day_boundary(self):
        at_boundary = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "voc", "source_date": self.date_days_before(730)}}
            )
        )
        first_stale = self.validate(
            evidence=self.build_evidence(
                metadata={"policy": {"kind": "voc", "source_date": self.date_days_before(731)}}
            )
        )

        self.assertEqual(at_boundary.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertEqual(first_stale.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in first_stale.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_old_price_supports_explicitly_historical_statement(self):
        evidence = self.build_evidence(
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(366)}}
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("HISTORICAL")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("CONTEXT_ONLY"))
        self.assertTrue(result.fact_eligible)

    def test_old_price_supports_explicit_context_use(self):
        evidence = self.build_evidence(
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("CONTEXT")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("CONTEXT_ONLY"))
        self.assertTrue(result.fact_eligible)

    def test_old_price_never_supports_current_fact(self):
        evidence = self.build_evidence(
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}
        )
        result = self.validate(evidence=evidence, context=self.build_context())

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_fresh_evidence_accepts_historical_scope(self):
        result = self.validate(
            evidence=self.build_evidence(),
            context=self.build_context(temporal_scope=self.policy.TemporalScope("HISTORICAL")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_persistent_older_voc_is_context_only(self):
        evidence = self.build_evidence(
            metadata={
                "policy": {
                    "kind": "voc",
                    "source_date": self.date_days_before(750),
                    "continuing_relevance_justification": "Review patterns remain representative.",
                }
            }
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("CONTEXT")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("CONTEXT_ONLY"))
        self.assertTrue(result.fact_eligible)

    def test_older_voc_without_justification_rejected(self):
        evidence = self.build_evidence(
            metadata={"policy": {"kind": "voc", "source_date": self.date_days_before(750)}}
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("CONTEXT")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )


class ValidateEvidenceRegulatoryTests(PolicyTestBase):
    def build_regulation(self, **overrides):
        values = {
            "source": self.evidence.Source(
                provider="Regulatory Agency",
                source_type="official_regulation",
                reference="https://agency.test/regulation/42",
                title="Consumer Product Safety Regulation",
            ),
            "tier": self.evidence.Tier("Tier 1"),
            "metadata": {
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            },
        }
        values.update(overrides)
        return self.build_evidence(**values)

    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_regulation(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_current_authoritative_regulation_accepted(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_regulation_accepts_timezone_aware_verification_offset(self):
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-01T08:00:00+08:00",
                }
            }
        )

        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_regulation_without_current_verification_rejected(self):
        evidence = self.build_regulation(
            metadata={"policy": {"kind": "regulation", "effective_from": "2026-01-01"}}
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )

    def test_regulation_without_effective_date_rejected(self):
        evidence = self.build_regulation(
            metadata={"policy": {"kind": "regulation", "verified_current_at": "2026-08-01T00:00:00Z"}}
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )

    def test_regulation_with_malformed_verification_rejected(self):
        for verified_current_at in ("2026-08-01", "2026-13-01T00:00:00Z", "not-a-timestamp", 20260801):
            with self.subTest(verified_current_at=repr(verified_current_at)):
                evidence = self.build_regulation(
                    metadata={
                        "policy": {
                            "kind": "regulation",
                            "effective_from": "2026-01-01",
                            "verified_current_at": verified_current_at,
                        }
                    }
                )
                result = self.validate(evidence=evidence)

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
                )

    def test_regulation_with_expired_verification_rejected(self):
        verified = (AS_OF - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_regulation_verification_at_boundary_accepted(self):
        verified = (AS_OF - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_regulation_verification_one_second_past_boundary_rejected(self):
        verified = (AS_OF - timedelta(days=365, seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )

        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_regulation_verification_age_is_offset_representation_independent(self):
        results = []
        for verified in ("2025-08-14T23:59:59Z", "2025-08-15T13:59:59+14:00"):
            evidence = self.build_regulation(
                metadata={
                    "policy": {
                        "kind": "regulation",
                        "effective_from": "2025-01-01",
                        "verified_current_at": verified,
                    }
                }
            )
            results.append(self.validate(evidence=evidence))

        self.assertEqual(
            [(result.outcome.value, [issue.reason_code.value for issue in result.issues]) for result in results],
            [
                ("REJECT", ["STALE_EVIDENCE"]),
                ("REJECT", ["STALE_EVIDENCE"]),
            ],
        )

    def test_regulation_with_future_effective_date_rejected(self):
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-08-16",
                    "verified_current_at": "2026-08-15T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_regulation_verified_after_as_of_rejected(self):
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-16T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_regulation_with_effective_date_after_verification_rejected(self):
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-09-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_certification_and_tariff_kinds_follow_regulatory_rules(self):
        for kind in ("certification", "tariff"):
            with self.subTest(kind=kind):
                evidence = self.build_regulation(
                    metadata={
                        "policy": {
                            "kind": kind,
                            "effective_from": "2026-01-01",
                            "verified_current_at": "2026-08-01T00:00:00Z",
                        }
                    }
                )
                result = self.validate(evidence=evidence)

                self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))

    def test_regulation_on_non_current_scope_has_no_verification_window(self):
        verified = (AS_OF - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_regulation(
            metadata={
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("HISTORICAL")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_regulation_with_wrong_tier_rejected(self):
        result = self.validate(evidence=self.build_regulation(tier=self.evidence.Tier("Tier 2")))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER_MISMATCH")],
        )

    def test_regulation_from_registered_non_authoritative_source_rejected(self):
        evidence = self.build_regulation(
            source=self.evidence.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference="https://example.test/regulation-summary",
                title="Marketplace regulation summary",
            ),
            tier=self.evidence.Tier("Tier 2"),
        )

        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER_MISMATCH")],
        )


class ValidateEvidenceAuthoritativeRecordTests(PolicyTestBase):
    def build_ip_record(self, **overrides):
        values = {
            "source": self.evidence.Source(
                provider="Patent Office",
                source_type="official_patent",
                reference="https://patents.test/11-222-333",
                title="Granted patent 11-222-333",
            ),
            "tier": self.evidence.Tier("Tier 1"),
            "metadata": {
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            },
        }
        values.update(overrides)
        return self.build_evidence(**values)

    def build_policy(self, **overrides):
        values = {
            "source_registry": {
                ("Patent Office", "official_patent"): self.policy.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
                ),
                ("Trademark Office", "official_trademark"): self.policy.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
                ),
                ("Example Marketplace", "marketplace_listing"): self.policy.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
            },
            "max_current_verification_age": 365,
        }
        values.update(overrides)
        return self.policy.EvidencePolicy(**values)

    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_ip_record(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_current_official_patent_record_accepted(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)
        self.assertEqual(result.issues, ())

    def test_current_official_trademark_record_accepted_without_regulation_kind(self):
        evidence = self.build_ip_record(
            source=self.evidence.Source(
                provider="Trademark Office",
                source_type="official_trademark",
                reference="https://trademarks.test/4-555-666",
                title="Registered trademark 4-555-666",
            ),
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2025-06-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            },
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)
        self.assertEqual(evidence.metadata["policy"]["kind"], "ip_authoritative_record")

    def test_ip_record_without_current_verification_rejected(self):
        evidence = self.build_ip_record(
            metadata={"policy": {"kind": "ip_authoritative_record", "effective_from": "2026-01-01"}}
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )

    def test_ip_record_without_effective_date_rejected(self):
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )

    def test_ip_record_with_expired_verification_rejected(self):
        verified = (AS_OF - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("STALE_EVIDENCE")],
        )

    def test_ip_record_verification_at_boundary_accepted(self):
        verified = (AS_OF - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_ip_record_with_future_effective_date_rejected(self):
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2026-08-16",
                    "verified_current_at": "2026-08-15T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_ip_record_verified_after_as_of_rejected(self):
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-16T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_ip_record_with_effective_date_after_verification_rejected(self):
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2026-09-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_ip_record_with_malformed_metadata_rejected(self):
        for policy_meta in (
            {"kind": "ip_authoritative_record", "effective_from": "2026/01/01", "verified_current_at": "2026-08-01T00:00:00Z"},
            {"kind": "ip_authoritative_record", "effective_from": "2026-01-01", "verified_current_at": "2026-08-01"},
            {"kind": "ip_authoritative_record", "effective_from": "2026-01-01", "verified_current_at": "not-a-timestamp"},
        ):
            with self.subTest(policy_meta=policy_meta):
                result = self.validate(evidence=self.build_ip_record(metadata={"policy": policy_meta}))

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
                )

    def test_ip_record_from_registered_non_authoritative_source_rejected(self):
        evidence = self.build_ip_record(
            source=self.evidence.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference="https://example.test/patent-summary",
                title="Marketplace patent summary",
            ),
            tier=self.evidence.Tier("Tier 2"),
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER_MISMATCH")],
        )

    def test_ip_record_from_official_source_with_wrong_tier_rejected(self):
        result = self.validate(evidence=self.build_ip_record(tier=self.evidence.Tier("Tier 2")))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER_MISMATCH")],
        )

    def test_ip_record_on_non_current_scope_has_no_verification_window(self):
        verified = (AS_OF - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = self.build_ip_record(
            metadata={
                "policy": {
                    "kind": "ip_authoritative_record",
                    "effective_from": "2025-01-01",
                    "verified_current_at": verified,
                }
            }
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("HISTORICAL")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_ip_record_acceptance_infers_no_legal_conclusion(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertEqual(
            [issue.message for issue in result.issues],
            [],
        )

    def test_regulation_certification_and_tariff_behavior_is_unchanged(self):
        for kind in ("regulation", "certification", "tariff"):
            with self.subTest(kind=kind):
                accepted = self.validate(
                    evidence=self.build_ip_record(
                        source=self.evidence.Source(
                            provider="Patent Office",
                            source_type="official_patent",
                            reference="https://patents.test/regulation-like/1",
                            title="Official record",
                        ),
                        metadata={
                            "policy": {
                                "kind": kind,
                                "effective_from": "2026-01-01",
                                "verified_current_at": "2026-08-01T00:00:00Z",
                            }
                        },
                    )
                )
                stale = self.validate(
                    evidence=self.build_ip_record(
                        source=self.evidence.Source(
                            provider="Patent Office",
                            source_type="official_patent",
                            reference="https://patents.test/regulation-like/2",
                            title="Official record",
                        ),
                        metadata={
                            "policy": {
                                "kind": kind,
                                "effective_from": "2025-01-01",
                                "verified_current_at": (AS_OF - timedelta(days=400)).strftime(
                                    "%Y-%m-%dT%H:%M:%SZ"
                                ),
                            }
                        },
                    )
                )

                self.assertEqual(accepted.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
                self.assertEqual(stale.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in stale.issues],
                    [self.policy.ReasonCode("STALE_EVIDENCE")],
                )


class ValidateEvidenceLongTermIndustryTests(PolicyTestBase):
    def build_industry(self, **overrides):
        values = {
            "source": self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/9",
                title="Industry structure report",
            ),
            "tier": self.evidence.Tier("Tier 4"),
            "metadata": {
                "policy": {
                    "kind": "long_term_industry",
                    "source_year": 2026,
                    "continuing_relevance_justification": "Category structure remains unchanged.",
                }
            },
        }
        values.update(overrides)
        return self.build_evidence(**values)

    def validate(self, evidence=None, context=None, policy=None):
        return self.policy.validate_evidence(
            evidence or self.build_industry(),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_current_year_industry_data_accepted(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_older_industry_data_with_justification_is_context_only(self):
        evidence = self.build_industry(
            metadata={
                "policy": {
                    "kind": "long_term_industry",
                    "source_year": 2023,
                    "continuing_relevance_justification": "Category structure remains unchanged.",
                }
            }
        )
        result = self.validate(
            evidence=evidence,
            context=self.build_context(temporal_scope=self.policy.TemporalScope("CONTEXT")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("CONTEXT_ONLY"))
        self.assertTrue(result.fact_eligible)

    def test_older_industry_data_not_current_eligible(self):
        evidence = self.build_industry(
            metadata={
                "policy": {
                    "kind": "long_term_industry",
                    "source_year": 2023,
                    "continuing_relevance_justification": "Category structure remains unchanged.",
                }
            }
        )
        result = self.validate(evidence=evidence, context=self.build_context())

        self.assertEqual(result.outcome, self.policy.Outcome("CONTEXT_ONLY"))
        self.assertFalse(result.fact_eligible)

    def test_industry_data_without_source_year_rejected(self):
        evidence = self.build_industry(
            metadata={"policy": {"kind": "long_term_industry", "continuing_relevance_justification": "Relevant."}}
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )

    def test_industry_data_with_non_integer_year_rejected(self):
        for source_year in ("2023", 2023.5, True):
            with self.subTest(source_year=repr(source_year)):
                evidence = self.build_industry(
                    metadata={
                        "policy": {
                            "kind": "long_term_industry",
                            "source_year": source_year,
                            "continuing_relevance_justification": "Relevant.",
                        }
                    }
                )
                result = self.validate(evidence=evidence)

                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertEqual(
                    [issue.reason_code for issue in result.issues],
                    [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
                )

    def test_industry_data_with_future_year_rejected(self):
        evidence = self.build_industry(
            metadata={
                "policy": {
                    "kind": "long_term_industry",
                    "source_year": 2027,
                    "continuing_relevance_justification": "Relevant.",
                }
            }
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("INVALID_POLICY_METADATA")],
        )

    def test_industry_data_without_justification_rejected(self):
        evidence = self.build_industry(
            metadata={"policy": {"kind": "long_term_industry", "source_year": 2026}}
        )
        result = self.validate(evidence=evidence)

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_FRESHNESS_METADATA")],
        )


class ValidateEvidenceSetTests(PolicyTestBase):
    def test_duplicate_evidence_id_rejected(self):
        first = self.build_evidence()
        second = self.build_evidence(claim="A different claim.")

        result = self.policy.validate_evidence_set([first, second])

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].reason_code, self.policy.ReasonCode("DUPLICATE_EVIDENCE_ID"))
        self.assertEqual(result.issues[0].evidence_id, self.evidence.EvidenceId("E001"))

    def test_multiple_duplicates_reported_once_in_lexical_order(self):
        e001 = self.build_evidence()
        e002 = self.build_evidence(id=self.evidence.EvidenceId("E002"))
        e010 = self.build_evidence(id=self.evidence.EvidenceId("E010"))

        result = self.policy.validate_evidence_set([e002, e010, e001, e010, e002, e001])

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [(issue.reason_code, issue.evidence_id) for issue in result.issues],
            [
                (self.policy.ReasonCode("DUPLICATE_EVIDENCE_ID"), self.evidence.EvidenceId("E001")),
                (self.policy.ReasonCode("DUPLICATE_EVIDENCE_ID"), self.evidence.EvidenceId("E002")),
                (self.policy.ReasonCode("DUPLICATE_EVIDENCE_ID"), self.evidence.EvidenceId("E010")),
            ],
        )

    def test_collection_without_duplicates_accepted(self):
        first = self.build_evidence()
        second = self.build_evidence(id=self.evidence.EvidenceId("E002"))

        result = self.policy.validate_evidence_set([first, second])

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)
        self.assertEqual(result.issues, ())

    def test_collection_with_non_evidence_element_fails_closed(self):
        result = self.policy.validate_evidence_set([self.build_evidence(), "not evidence"])

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )


class ValidateClaimSupportTests(PolicyTestBase):
    def build_index(self, *evidences):
        return {evidence.id: evidence for evidence in evidences}

    def validate(self, evidence_ids=None, index=None, context=None, policy=None):
        return self.policy.validate_claim_support(
            evidence_ids if evidence_ids is not None else (self.evidence.EvidenceId("E001"),),
            index if index is not None else self.build_index(self.build_evidence()),
            context or self.build_context(),
            policy or self.build_policy(),
        )

    def test_material_claim_without_citation_rejected(self):
        result = self.validate(evidence_ids=())

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_CITATION")],
        )

    def test_material_claim_with_none_citations_rejected(self):
        result = self.policy.validate_claim_support(
            None,
            self.build_index(self.build_evidence()),
            self.build_context(),
            self.build_policy(),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("MISSING_CITATION")],
        )

    def test_multiple_unresolved_ids_reported_in_lexical_order(self):
        result = self.validate(
            evidence_ids=(
                self.evidence.EvidenceId("E010"),
                self.evidence.EvidenceId("E002"),
                self.evidence.EvidenceId("E999"),
            ),
            index=self.build_index(self.build_evidence()),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [(issue.reason_code, issue.evidence_id) for issue in result.issues],
            [
                (self.policy.ReasonCode("UNKNOWN_EVIDENCE_ID"), self.evidence.EvidenceId("E002")),
                (self.policy.ReasonCode("UNKNOWN_EVIDENCE_ID"), self.evidence.EvidenceId("E010")),
                (self.policy.ReasonCode("UNKNOWN_EVIDENCE_ID"), self.evidence.EvidenceId("E999")),
            ],
        )

    def test_claim_citing_unknown_evidence_id_rejected(self):
        result = self.validate(evidence_ids=(self.evidence.EvidenceId("E999"),))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [(issue.reason_code, issue.evidence_id) for issue in result.issues],
            [(self.policy.ReasonCode("UNKNOWN_EVIDENCE_ID"), self.evidence.EvidenceId("E999"))],
        )

    def test_resolved_stale_evidence_cannot_support_current_claim(self):
        stale = self.build_evidence(
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}
        )
        result = self.validate(index=self.build_index(stale))

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [(issue.reason_code, issue.evidence_id) for issue in result.issues],
            [(self.policy.ReasonCode("STALE_EVIDENCE"), self.evidence.EvidenceId("E001"))],
        )

    def test_claim_with_eligible_citation_accepted(self):
        result = self.validate()

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)
        self.assertEqual(result.issues, ())

    def test_repeated_ids_count_as_one_support_item(self):
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E001"), self.evidence.EvidenceId("E001"))
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))

    def test_context_scope_claim_accepts_old_evidence(self):
        old_price = self.build_evidence(
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}}
        )
        result = self.validate(
            index=self.build_index(old_price),
            context=self.build_context(temporal_scope=self.policy.TemporalScope("CONTEXT")),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_context_only_ineligible_citation_rejects_current_claim(self):
        old_industry = self.build_evidence(
            id=self.evidence.EvidenceId("E002"),
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/9",
                title="Industry structure report",
            ),
            tier=self.evidence.Tier("Tier 4"),
            metadata={
                "policy": {
                    "kind": "long_term_industry",
                    "source_year": 2023,
                    "continuing_relevance_justification": "Category structure remains unchanged.",
                }
            },
        )
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E002"),),
            index=self.build_index(old_industry),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [(issue.reason_code, issue.evidence_id) for issue in result.issues],
            [(self.policy.ReasonCode("STALE_EVIDENCE"), self.evidence.EvidenceId("E002"))],
        )

    def test_critical_claim_with_tier4_sole_support_rejected(self):
        tier4_first = self.build_evidence(
            id=self.evidence.EvidenceId("E004"),
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/4",
                title="Market note",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        tier4_second = self.build_evidence(
            id=self.evidence.EvidenceId("E005"),
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/5",
                title="Follow-up note",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E004"), self.evidence.EvidenceId("E005")),
            index=self.build_index(tier4_first, tier4_second),
            context=self.build_context(critical=True),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER4_SOLE_CRITICAL_SUPPORT")],
        )

    def test_repeated_tier4_id_does_not_satisfy_critical_restriction(self):
        tier4 = self.build_evidence(
            id=self.evidence.EvidenceId("E004"),
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/4",
                title="Market note",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E004"), self.evidence.EvidenceId("E004")),
            index=self.build_index(tier4),
            context=self.build_context(critical=True),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("TIER4_SOLE_CRITICAL_SUPPORT")],
        )

    def test_tier4_supplements_stronger_critical_support(self):
        tier4 = self.build_evidence(
            id=self.evidence.EvidenceId("E004"),
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://journal.test/article/4",
                title="Market note",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E001"), self.evidence.EvidenceId("E004")),
            index=self.build_index(self.build_evidence(), tier4),
            context=self.build_context(critical=True),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_non_material_claim_without_citation_accepted(self):
        result = self.validate(evidence_ids=(), context=self.build_context(material=False))

        self.assertEqual(result.outcome, self.policy.Outcome("ACCEPT_CURRENT"))
        self.assertTrue(result.fact_eligible)

    def test_supplied_citations_must_resolve_for_non_material_claims(self):
        result = self.validate(
            evidence_ids=(self.evidence.EvidenceId("E999"),),
            context=self.build_context(material=False),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("UNKNOWN_EVIDENCE_ID")],
        )


class ValidationBoundaryFailClosedTests(PolicyTestBase):
    def test_validate_evidence_with_non_evidence_fails_closed(self):
        result = self.policy.validate_evidence("not evidence", self.build_context(), self.build_policy())

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_naive_as_of_fails_closed_without_clock(self):
        naive_as_of = datetime(2026, 8, 15, 12, 0, 0)
        context = self.build_context(as_of=naive_as_of)

        result = self.policy.validate_evidence(self.build_evidence(), context, self.build_policy())

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_validate_evidence_with_invalid_context_fails_closed(self):
        result = self.policy.validate_evidence(self.build_evidence(), object(), self.build_policy())

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_validate_evidence_set_with_non_collection_fails_closed(self):
        result = self.policy.validate_evidence_set("not a collection")

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_validate_claim_support_with_indeterminate_index_fails_closed(self):
        broken_index = {self.evidence.EvidenceId("E001"): "not evidence"}
        result = self.policy.validate_claim_support(
            (self.evidence.EvidenceId("E001"),),
            broken_index,
            self.build_context(),
            self.build_policy(),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_validate_claim_support_with_mismatched_index_id_fails_closed(self):
        evidence = self.build_evidence(id=self.evidence.EvidenceId("E002"))
        broken_index = {self.evidence.EvidenceId("E001"): evidence}

        result = self.policy.validate_claim_support(
            (self.evidence.EvidenceId("E001"),),
            broken_index,
            self.build_context(),
            self.build_policy(),
        )

        self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
        self.assertFalse(result.fact_eligible)
        self.assertEqual(
            [issue.reason_code for issue in result.issues],
            [self.policy.ReasonCode("VALIDATION_ERROR")],
        )

    def test_validation_error_never_grants_factual_eligibility(self):
        cases = (
            lambda: self.policy.validate_evidence("not evidence", self.build_context(), self.build_policy()),
            lambda: self.policy.validate_evidence_set("not a collection"),
            lambda: self.policy.validate_claim_support(
                (self.evidence.EvidenceId("E001"),),
                {self.evidence.EvidenceId("E001"): "not evidence"},
                self.build_context(),
                self.build_policy(),
            ),
        )
        for case in cases:
            with self.subTest(case=case):
                result = case()
                self.assertEqual(result.outcome, self.policy.Outcome("REJECT"))
                self.assertFalse(result.fact_eligible)


if __name__ == "__main__":
    unittest.main()
