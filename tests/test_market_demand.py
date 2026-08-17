"""Focused contract tests for the ECO-15 Market Demand boundary."""

import ast
import importlib
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from dataclasses import FrozenInstanceError
from unittest import mock


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)


class MarketDemandTestBase(unittest.TestCase):
    def setUp(self):
        try:
            self.market = importlib.import_module("product_research.market_demand")
        except ModuleNotFoundError:
            self.market = None
        self.assessment = importlib.import_module("product_research.evidence_assessment")
        self.policy = importlib.import_module("product_research.evidence_policy")
        self.evidence = importlib.import_module("product_research.evidence")

    def require_market(self):
        if self.market is None:
            self.fail("product_research.market_demand has not been implemented")
        return self.market

    def date_days_before(self, days):
        return (AS_OF.date() - timedelta(days=days)).isoformat()

    def build_evidence(self, evidence_id="E001", **overrides):
        values = {
            "id": self.evidence.EvidenceId(evidence_id),
            "claim": f"Demand proposition for {evidence_id}.",
            "evidence": f"Observed demand basis for {evidence_id}.",
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

    def build_policy(self):
        return self.policy.EvidencePolicy(
            source_registry={
                ("Example Marketplace", "marketplace_listing"): self.policy.SourceClass(
                    "FIRST_PARTY_MARKETPLACE_SUPPLIER"
                ),
                ("Consumer Review Hub", "customer_reviews"): self.policy.SourceClass(
                    "CONSUMER_REVIEW_DISCUSSION"
                ),
                ("Industry Journal", "secondary_articles"): self.policy.SourceClass(
                    "SECONDARY_INDUSTRY"
                ),
            },
            max_current_verification_age=365,
        )

    def binding(self, evidence_id, category="SEARCH", temporal="STABILITY_SUPPORT"):
        market = self.require_market()
        return market.MarketDemandBinding(
            self.evidence.EvidenceId(evidence_id),
            market.DemandSignalCategory(category),
            market.TemporalInterpretation(temporal),
        )

    def relation(self, evidence_id, stance="SUPPORTS"):
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

    def run_analysis(
        self,
        evidence_ids,
        categories=None,
        temporals=None,
        relations=None,
        independence=None,
        missing_information=(),
        evidence_index=None,
        validation_context=None,
        policy=None,
        bindings=None,
    ):
        market = self.require_market()
        if evidence_index is None:
            evidence_index = {
                self.evidence.EvidenceId(value): self.build_evidence(value)
                for value in evidence_ids
            }
        if categories is None:
            categories = {value: "SEARCH" for value in evidence_ids}
        if temporals is None:
            temporals = {value: "STABILITY_SUPPORT" for value in evidence_ids}
        if bindings is None:
            bindings = [
                self.binding(value, categories[value], temporals[value])
                for value in evidence_ids
            ]
        if relations is None:
            relations = [self.relation(value) for value in evidence_ids]
        if independence is None:
            independence = [self.independence(value, f"group-{value}") for value in evidence_ids]
        if validation_context is None:
            validation_context = self.build_context()
        if policy is None:
            policy = self.build_policy()
        return market.analyze_market_demand(
            [self.evidence.EvidenceId(value) for value in evidence_ids],
            evidence_index,
            bindings,
            relations,
            independence,
            missing_information,
            validation_context,
            policy,
        )

    def ids(self, value, field):
        return tuple(item.value for item in getattr(value, field))

    def factor_values(self, result):
        return tuple(item.value for item in result.factors)

    def assert_fail_closed(self, result):
        market = self.require_market()
        self.assertEqual(result.conclusion, market.DemandConclusion("UNKNOWN"))
        self.assertEqual(result.temporal_state, market.TemporalDemandState("UNKNOWN"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(result.supported_categories, ())
        self.assertEqual(result.supporting_ids, ())
        self.assertEqual(self.factor_values(result), ("MARKET_DEMAND_INPUT_ERROR",))


class MarketDemandVocabularyTests(MarketDemandTestBase):
    def test_closed_vocabularies_are_exact_and_immutable(self):
        market = self.require_market()
        expected = {
            "DemandSignalCategory": ("SEARCH", "COMMERCE", "SOCIAL"),
            "TemporalInterpretation": (
                "STABILITY_SUPPORT",
                "SHORT_TERM_HYPE_SUPPORT",
                "UNKNOWN",
            ),
            "DemandConclusion": ("POSITIVE", "UNKNOWN"),
            "TemporalDemandState": ("STABLE", "SHORT_TERM_HYPE", "UNKNOWN"),
        }
        for class_name, values in expected.items():
            value_type = getattr(market, class_name)
            self.assertEqual(value_type._allowed, values)
            for value in values:
                value = value_type(value)
                with self.assertRaises(AttributeError):
                    value._value = "OTHER"
                with self.assertRaises(AttributeError):
                    del value._value

    def test_closed_vocabularies_reject_aliases_case_errors_and_non_strings(self):
        market = self.require_market()
        for class_name in (
            "DemandSignalCategory",
            "TemporalInterpretation",
            "DemandConclusion",
            "TemporalDemandState",
        ):
            value_type = getattr(market, class_name)
            for invalid in ("search", "Search", "UNKNOWN_VALUE", 1, None):
                with self.assertRaises((TypeError, ValueError)):
                    value_type(invalid)


class MarketDemandValueTests(MarketDemandTestBase):
    def test_binding_is_frozen_and_requires_exact_existing_value_types(self):
        market = self.require_market()
        binding = self.binding("E001")
        with self.assertRaises(FrozenInstanceError):
            binding.category = market.DemandSignalCategory("COMMERCE")
        with self.assertRaises(TypeError):
            market.MarketDemandBinding("E001", market.DemandSignalCategory("SEARCH"), market.TemporalInterpretation("UNKNOWN"))
        with self.assertRaises(TypeError):
            market.MarketDemandBinding(
                self.evidence.EvidenceId("E001"), "SEARCH", market.TemporalInterpretation("UNKNOWN")
            )
        with self.assertRaises(TypeError):
            market.MarketDemandBinding(
                self.evidence.EvidenceId("E001"),
                market.DemandSignalCategory("SEARCH"),
                "UNKNOWN",
            )

    def test_result_shape_is_frozen_typed_and_has_no_numeric_decision_fields(self):
        market = self.require_market()
        result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
        )
        self.assertIs(type(result), market.MarketDemandResult)
        for field in (
            "conclusion",
            "temporal_state",
            "confidence",
            "supported_categories",
            "missing_categories",
            "supporting_ids",
            "adverse_ids",
            "excluded_ids",
            "assessment",
            "factors",
        ):
            self.assertTrue(hasattr(result, field))
        self.assertFalse(any(name in result.__dataclass_fields__ for name in ("score", "threshold", "weight", "recommendation")))
        with self.assertRaises(FrozenInstanceError):
            result.conclusion = market.DemandConclusion("UNKNOWN")
        with self.assertRaises(TypeError):
            market.MarketDemandResult(
                market.DemandConclusion("UNKNOWN"),
                market.TemporalDemandState("UNKNOWN"),
                self.evidence.Confidence("Low"),
                [],
                (),
                (),
                (),
                (),
                result.assessment,
                (),
            )


class MarketDemandInputFailureTests(MarketDemandTestBase):
    def assert_fail_closed(self, result):
        market = self.require_market()
        self.assertEqual(result.conclusion, market.DemandConclusion("UNKNOWN"))
        self.assertEqual(result.temporal_state, market.TemporalDemandState("UNKNOWN"))
        self.assertEqual(result.confidence, self.evidence.Confidence("Low"))
        self.assertEqual(self.ids(result, "supported_categories"), ())
        self.assertEqual(self.ids(result, "supporting_ids"), ())
        self.assertEqual(self.factor_values(result), ("MARKET_DEMAND_INPUT_ERROR",))

    def test_duplicate_conflicting_incomplete_and_unresolved_bindings_fail_closed(self):
        market = self.require_market()
        evidence_index = {
            self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
            self.evidence.EvidenceId("E002"): self.build_evidence("E002"),
        }
        duplicate = [self.binding("E001"), self.binding("E001", "COMMERCE")]
        self.assert_fail_closed(
            self.run_analysis(["E001"], bindings=duplicate, evidence_index=evidence_index)
        )
        self.assert_fail_closed(
            self.run_analysis(["E001", "E002"], bindings=[self.binding("E001")], evidence_index=evidence_index)
        )
        self.assert_fail_closed(
            self.run_analysis(["E001"], bindings=[self.binding("E001"), self.binding("E002")], evidence_index=evidence_index)
        )
        self.assert_fail_closed(
            self.run_analysis(["E001"], bindings=[self.binding("E002")], evidence_index=evidence_index)
        )

    def test_malformed_index_assessment_inputs_and_containers_fail_closed(self):
        market = self.require_market()
        valid_index = {self.evidence.EvidenceId("E001"): self.build_evidence("E001")}
        mismatched = {self.evidence.EvidenceId("E001"): self.build_evidence("E002")}
        self.assert_fail_closed(
            self.run_analysis(["E001"], evidence_index=mismatched)
        )
        self.assert_fail_closed(
            self.run_analysis(["E001"], relations=[], evidence_index=valid_index)
        )
        self.assert_fail_closed(
            self.run_analysis(["E001"], independence=[], evidence_index=valid_index)
        )
        self.assert_fail_closed(
            market.analyze_market_demand(
                None, valid_index, (), (), (), (), self.build_context(), self.build_policy()
            )
        )
        self.assert_fail_closed(
            market.analyze_market_demand(
                [self.evidence.EvidenceId("E001")], valid_index, "bad", (), (), (), self.build_context(), self.build_policy()
            )
        )

    def test_missing_evidence_does_not_fabricate_coverage_and_assessment_errors_stay_visible(self):
        result = self.run_analysis(
            ["E001", "E002"],
            evidence_index={self.evidence.EvidenceId("E001"): self.build_evidence("E001")},
        )
        self.assert_fail_closed(result)
        self.assertEqual(result.assessment.factors[0].value, "ASSESSMENT_INPUT_ERROR")

    def test_programmer_control_exceptions_propagate(self):
        market = self.require_market()
        with mock.patch.object(market, "assess_evidence", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_analysis(["E001"])


class MarketDemandCategoryTests(MarketDemandTestBase):
    def test_each_independent_two_of_three_category_pair_is_positive(self):
        for categories in (
            {"E001": "SEARCH", "E002": "COMMERCE"},
            {"E001": "SEARCH", "E002": "SOCIAL"},
            {"E001": "COMMERCE", "E002": "SOCIAL"},
        ):
            result = self.run_analysis(["E001", "E002"], categories=categories)
            self.assertEqual(result.conclusion.value, "POSITIVE")
            self.assertEqual(tuple(item.value for item in result.supported_categories), tuple(sorted(categories.values(), key=("SEARCH", "COMMERCE", "SOCIAL").index)))
            self.assertEqual(result.confidence.value, "High")

    def test_all_categories_are_unique_and_in_fixed_order(self):
        result = self.run_analysis(
            ["E003", "E001", "E002"],
            categories={"E001": "SEARCH", "E002": "SOCIAL", "E003": "COMMERCE"},
        )
        self.assertEqual(result.conclusion.value, "POSITIVE")
        self.assertEqual(tuple(item.value for item in result.supported_categories), ("SEARCH", "COMMERCE", "SOCIAL"))
        self.assertEqual(self.ids(result, "supporting_ids"), ("E001", "E002", "E003"))

    def test_one_category_duplicates_and_same_group_never_create_diversity(self):
        one = self.run_analysis(
            ["E001", "E002", "E003"],
            categories={"E001": "SEARCH", "E002": "SEARCH", "E003": "SEARCH"},
        )
        self.assertEqual(one.conclusion.value, "UNKNOWN")
        self.assertEqual(one.confidence.value, "Low")
        self.assertEqual(self.factor_values(one), ("INSUFFICIENT_CATEGORY_COVERAGE",))

        same_group = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            independence=[self.independence("E001", "same"), self.independence("E002", "same")],
        )
        self.assertEqual(same_group.conclusion.value, "UNKNOWN")
        self.assertEqual(same_group.confidence.value, "Low")
        self.assertEqual(self.factor_values(same_group), ("INSUFFICIENT_INDEPENDENT_CATEGORIES",))

        unknown_group = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            independence=[self.independence("E001", None), self.independence("E002", None)],
        )
        self.assertEqual(unknown_group.conclusion.value, "UNKNOWN")
        self.assertEqual(unknown_group.confidence.value, "Low")
        self.assertEqual(self.factor_values(unknown_group), ("INSUFFICIENT_INDEPENDENT_CATEGORIES",))

        duplicate_ids = self.run_analysis(["E001", "E001"])
        self.assert_fail_closed(duplicate_ids)

    def test_policy_excluded_support_cannot_satisfy_category_coverage(self):
        stale = self.build_evidence(
            "E002",
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
        )
        result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
                self.evidence.EvidenceId("E002"): stale,
            },
        )
        self.assertEqual(result.conclusion.value, "UNKNOWN")
        self.assertEqual(result.confidence.value, "Low")
        self.assertEqual(tuple(item.value for item in result.supported_categories), ("SEARCH",))
        self.assertEqual(tuple(item.value for item in result.missing_categories), ("COMMERCE", "SOCIAL"))
        self.assertEqual(self.ids(result, "excluded_ids"), ("E002",))
        self.assertEqual(result.assessment.policy_results[1].issues[0].reason_code.value, "STALE_EVIDENCE")

        unsupported = self.build_evidence(
            "E002",
            source=self.evidence.Source(
                provider="Unregistered Source",
                source_type="unknown_feed",
                reference="https://unknown.test/E002",
                title="Unknown source",
            ),
        )
        unsupported_result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
                self.evidence.EvidenceId("E002"): unsupported,
            },
        )
        self.assertEqual(unsupported_result.conclusion.value, "UNKNOWN")
        self.assertEqual(unsupported_result.assessment.policy_results[1].issues[0].reason_code.value, "UNSUPPORTED_SOURCE")

        context_only = self.build_evidence(
            "E002",
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
        )
        context_only_result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
                self.evidence.EvidenceId("E002"): context_only,
            },
            validation_context=self.build_context(
                temporal_scope=self.policy.TemporalScope("CURRENT")
            ),
        )
        self.assertEqual(context_only_result.conclusion.value, "UNKNOWN")
        self.assertEqual(context_only_result.assessment.policy_results[1].issues[0].reason_code.value, "STALE_EVIDENCE")

    def test_unsupported_status_context_only_and_claim_support_rejection_remain_assessment_owned(self):
        evidence = self.build_evidence(
            "E002", status=self.evidence.Status("Estimated")
        )
        result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
                self.evidence.EvidenceId("E002"): evidence,
            },
        )
        self.assertEqual(result.conclusion.value, "UNKNOWN")
        self.assertEqual(self.ids(result, "excluded_ids"), ("E002",))
        self.assertEqual(result.assessment.policy_results[1].issues[0].reason_code.value, "STATUS_NOT_FACT_ELIGIBLE")

        tier4 = self.build_evidence(
            "E002",
            source=self.evidence.Source(
                provider="Industry Journal",
                source_type="secondary_articles",
                reference="https://industry.test/articles/E002",
                title="Secondary article",
            ),
            tier=self.evidence.Tier("Tier 4"),
        )
        critical = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence(
                    "E001",
                    source=self.evidence.Source(
                        provider="Industry Journal",
                        source_type="secondary_articles",
                        reference="https://industry.test/articles/E001",
                        title="Secondary article",
                    ),
                    tier=self.evidence.Tier("Tier 4"),
                ),
                self.evidence.EvidenceId("E002"): tier4,
            },
            validation_context=self.build_context(critical=True),
        )
        self.assertEqual(critical.conclusion.value, "UNKNOWN")
        self.assertEqual(critical.assessment.claim_support_result.issues[0].reason_code.value, "TIER4_SOLE_CRITICAL_SUPPORT")

    def test_adverse_ids_and_conflict_are_preserved_without_positive_conclusion(self):
        result = self.run_analysis(
            ["E001", "E002", "E003"],
            categories={"E001": "SEARCH", "E002": "COMMERCE", "E003": "SOCIAL"},
            relations=[self.relation("E001"), self.relation("E002"), self.relation("E003", "CONTRADICTS")],
            independence=[self.independence("E001", "a"), self.independence("E002", "b"), self.independence("E003", "c")],
        )
        self.assertEqual(result.assessment.outcome.value, "CONFLICTED")
        self.assertEqual(result.conclusion.value, "UNKNOWN")
        self.assertEqual(self.ids(result, "adverse_ids"), ("E003",))
        self.assertEqual(result.assessment.conflict_state.value, "PRESENT")
        self.assertEqual(result.confidence.value, "Low")

    def test_policy_excluded_adverse_id_is_traceable_without_creating_conflict(self):
        stale = self.build_evidence(
            "E003",
            metadata={"policy": {"kind": "marketplace_price", "source_date": self.date_days_before(400)}},
        )
        result = self.run_analysis(
            ["E001", "E002", "E003"],
            categories={"E001": "SEARCH", "E002": "COMMERCE", "E003": "SOCIAL"},
            relations=[self.relation("E001"), self.relation("E002"), self.relation("E003", "CONTRADICTS")],
            independence=[self.independence("E001", "a"), self.independence("E002", "b"), self.independence("E003", "c")],
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
                self.evidence.EvidenceId("E002"): self.build_evidence("E002"),
                self.evidence.EvidenceId("E003"): stale,
            },
        )
        self.assertEqual(result.conclusion.value, "POSITIVE")
        self.assertEqual(result.assessment.conflict_state.value, "NONE")
        self.assertEqual(self.ids(result, "adverse_ids"), ("E003",))
        self.assertEqual(self.ids(result, "excluded_ids"), ("E003",))

    def test_missing_neutral_unknown_and_low_confidence_remain_assessment_owned(self):
        result = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            relations=[self.relation("E001"), self.relation("E002", "UNKNOWN")],
            independence=[self.independence("E001", "a"), self.independence("E002", "b")],
            missing_information=(self.missing("supplier_price", "MATERIAL"),),
        )
        self.assertEqual(result.conclusion.value, "UNKNOWN")
        self.assertEqual(result.confidence.value, "Low")
        self.assertEqual(result.assessment.confidence.value, "Low")
        self.assertEqual(result.assessment.unknown_ids[0].value, "E002")
        self.assertEqual(result.assessment.missing_information[0].key, "supplier_price")

        low_tier = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            evidence_index={
                self.evidence.EvidenceId("E001"): self.build_evidence(
                    "E001",
                    source=self.evidence.Source(
                        provider="Industry Journal",
                        source_type="secondary_articles",
                        reference="https://industry.test/articles/E001",
                        title="Secondary article",
                    ),
                    tier=self.evidence.Tier("Tier 4"),
                ),
                self.evidence.EvidenceId("E002"): self.build_evidence(
                    "E002",
                    source=self.evidence.Source(
                        provider="Industry Journal",
                        source_type="secondary_articles",
                        reference="https://industry.test/articles/E002",
                        title="Secondary article",
                    ),
                    tier=self.evidence.Tier("Tier 4"),
                ),
            },
        )
        self.assertEqual(low_tier.conclusion.value, "POSITIVE")
        self.assertEqual(low_tier.confidence.value, "Low")
        self.assertEqual(low_tier.assessment.factors[0].value, "ONLY_LOW_TIER_SUPPORT")


class MarketDemandTemporalAndReplayTests(MarketDemandTestBase):
    def test_unanimous_stability_and_hype_are_explicit(self):
        stable = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            temporals={"E001": "STABILITY_SUPPORT", "E002": "STABILITY_SUPPORT"},
        )
        self.assertEqual(stable.temporal_state.value, "STABLE")

        hype = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            temporals={"E001": "SHORT_TERM_HYPE_SUPPORT", "E002": "SHORT_TERM_HYPE_SUPPORT"},
        )
        self.assertEqual(hype.temporal_state.value, "SHORT_TERM_HYPE")

    def test_unknown_or_mixed_temporal_support_never_gets_inferred(self):
        unknown = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            temporals={"E001": "STABILITY_SUPPORT", "E002": "UNKNOWN"},
        )
        self.assertEqual(unknown.conclusion.value, "POSITIVE")
        self.assertEqual(unknown.temporal_state.value, "UNKNOWN")
        self.assertEqual(unknown.confidence.value, "Medium")
        self.assertEqual(self.factor_values(unknown), ("UNKNOWN_TEMPORAL_SUPPORT",))

        mixed = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            temporals={"E001": "STABILITY_SUPPORT", "E002": "SHORT_TERM_HYPE_SUPPORT"},
        )
        self.assertEqual(mixed.temporal_state.value, "UNKNOWN")
        self.assertEqual(mixed.confidence.value, "Medium")
        self.assertEqual(self.factor_values(mixed), ("MIXED_TEMPORAL_SUPPORT",))

        insufficient = self.run_analysis(
            ["E001"], temporals={"E001": "STABILITY_SUPPORT"}
        )
        self.assertEqual(insufficient.temporal_state.value, "UNKNOWN")
        self.assertEqual(insufficient.confidence.value, "Low")
        self.assertEqual(self.factor_values(insufficient), ("INSUFFICIENT_CATEGORY_COVERAGE",))

    def test_confidence_never_exceeds_assessment_and_caps_are_conservative(self):
        for evidence_confidence, expected in (("High", "High"), ("Medium", "Medium"), ("Low", "Low")):
            result = self.run_analysis(
                ["E001", "E002"],
                categories={"E001": "SEARCH", "E002": "COMMERCE"},
                evidence_index={
                    self.evidence.EvidenceId("E001"): self.build_evidence("E001", confidence=self.evidence.Confidence(evidence_confidence)),
                    self.evidence.EvidenceId("E002"): self.build_evidence("E002", confidence=self.evidence.Confidence(evidence_confidence)),
                },
            )
            self.assertEqual(result.assessment.confidence.value, expected)
            self.assertEqual(result.confidence.value, expected)

        capped = self.run_analysis(
            ["E001", "E002"],
            categories={"E001": "SEARCH", "E002": "COMMERCE"},
            temporals={"E001": "STABILITY_SUPPORT", "E002": "UNKNOWN"},
        )
        self.assertEqual(capped.assessment.confidence.value, "High")
        self.assertEqual(capped.confidence.value, "Medium")
        self.assertEqual(capped.assessment.usable_ids, capped.supporting_ids)

    def test_equivalent_input_orders_replay_identically_with_nested_assessment_unchanged(self):
        index_a = {
            self.evidence.EvidenceId("E003"): self.build_evidence("E003"),
            self.evidence.EvidenceId("E001"): self.build_evidence("E001"),
            self.evidence.EvidenceId("E002"): self.build_evidence("E002"),
        }
        index_b = {
            self.evidence.EvidenceId("E001"): index_a[self.evidence.EvidenceId("E001")],
            self.evidence.EvidenceId("E002"): index_a[self.evidence.EvidenceId("E002")],
            self.evidence.EvidenceId("E003"): index_a[self.evidence.EvidenceId("E003")],
        }
        kwargs = {
            "categories": {"E001": "SEARCH", "E002": "COMMERCE", "E003": "SOCIAL"},
            "temporals": {"E001": "STABILITY_SUPPORT", "E002": "STABILITY_SUPPORT", "E003": "STABILITY_SUPPORT"},
            "relations": [self.relation("E001"), self.relation("E002"), self.relation("E003")],
            "independence": [self.independence("E001", "a"), self.independence("E002", "b"), self.independence("E003", "c")],
            "missing_information": (self.missing("weight", "MATERIAL"), self.missing("notes", "NON_MATERIAL")),
        }
        first = self.run_analysis(["E003", "E001", "E002"], evidence_index=index_a, **kwargs)
        second = self.run_analysis(
            ["E001", "E002", "E003"],
            evidence_index=index_b,
            relations=list(reversed(kwargs["relations"])),
            independence=list(reversed(kwargs["independence"])),
            missing_information=tuple(reversed(kwargs["missing_information"])),
            categories=kwargs["categories"],
            temporals=kwargs["temporals"],
        )
        self.assertEqual(first, second)
        self.assertEqual(self.ids(first, "supporting_ids"), ("E001", "E002", "E003"))
        self.assertEqual(tuple(item.value for item in first.supported_categories), ("SEARCH", "COMMERCE", "SOCIAL"))
        self.assertEqual(first.assessment.missing_information[0].key, "notes")

    def test_analysis_does_not_mutate_evidence_or_caller_inputs_and_assessment_runs_once(self):
        market = self.require_market()
        evidence = self.build_evidence("E001")
        index = {evidence.id: evidence}
        bindings = [self.binding("E001")]
        relations = [self.relation("E001")]
        independence = [self.independence("E001", "a")]
        missing = [self.missing("notes", "NON_MATERIAL")]
        snapshots = (
            evidence.to_json(),
            tuple(index.items()),
            tuple(bindings),
            tuple(relations),
            tuple(independence),
            tuple(missing),
            self.build_context(),
            self.build_policy(),
        )
        original = market.assess_evidence
        with mock.patch.object(market, "assess_evidence", wraps=original) as assessed:
            result = self.run_analysis(
                ["E001"],
                evidence_index=index,
                bindings=bindings,
                relations=relations,
                independence=independence,
                missing_information=missing,
            )
        self.assertEqual(assessed.call_count, 1)
        self.assertEqual(result.conclusion.value, "UNKNOWN")
        self.assertEqual(evidence.to_json(), snapshots[0])
        self.assertEqual(tuple(index.items()), snapshots[1])
        self.assertEqual(tuple(bindings), snapshots[2])
        self.assertEqual(tuple(relations), snapshots[3])
        self.assertEqual(tuple(independence), snapshots[4])
        self.assertEqual(tuple(missing), snapshots[5])


class MarketDemandOwnershipTests(MarketDemandTestBase):
    def test_module_is_standard_library_only_and_owns_no_acquisition_or_scoring_behavior(self):
        market = self.require_market()
        source = inspect.getsource(market)
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        self.assertTrue(all(name in {"dataclasses", "typing", "evidence", "evidence_assessment", "evidence_policy"} for name in imported))
        forbidden = (
            "requests", "urllib", "http", "browser", "scrape", "retry", "cache", "asyncio",
            "persistence", "random", "environment", "LLM", "score", "threshold", "weight", "recommendation",
            "provider", "acquisition", "normalize", "EvidenceId allocation",
        )
        lowered = source.lower()
        for term in forbidden:
            self.assertNotIn(term.lower(), lowered)
        self.assertEqual(sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "analyze_market_demand" for node in tree.body), 1)


if __name__ == "__main__":
    unittest.main()
