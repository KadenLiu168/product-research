"""ECO-45 requirement-to-test trace.

The tests keep DataForSEO acquisition provider-owned: committed ECO-42/ECO-43
fixtures are mapped with fake transports into existing RawFinding values, then
the external normalizer is exercised directly or through run_research.  The
trace is intentionally contract-oriented:

* ConstructionTests: explicit operation assignments and immutable setup.
* EvidenceContractTests: one Evidence, identity, status, and round-trip shape.
* ClaimAndProvenanceTests: neutral claims, exact basis, metadata, and thawing.
* PolicyAndRecognitionTests: task-owned kind, temporal fail-closed behavior,
  recognition-owned provenance, and non-revalidation of provider metrics.
* OrchestrationAndArchitectureTests: ID gaps, existing failure vocabulary,
  dependency direction, downstream ownership, and offline safety.
"""

import ast
import copy
import dataclasses
import importlib
import inspect
import json
import os
import pathlib
import socket
import unittest
from collections.abc import Mapping
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "dataforseo"
FIXED_TIME = "2026-08-24T00:00:00Z"
_UNSET = object()
OPERATIONS = (
    "google_ads_search_volume_live",
    "google_trends_explore_live",
    "amazon_bulk_search_volume_live",
    "amazon_products_live",
)
SEARCH_OPERATIONS = OPERATIONS[:3]
DATED_KINDS = ("market", "competition", "marketplace_price", "supplier_quotation", "voc")
NON_DERIVABLE_KINDS = (
    "regulation",
    "certification",
    "tariff",
    "ip_authoritative_record",
    "long_term_industry",
)


class DuplicateAssignmentMapping(Mapping):
    def __init__(self, items):
        self._items = tuple(items)

    def __getitem__(self, key):
        for item_key, value in self._items:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self):
        return (key for key, _ in self._items)

    def __len__(self):
        return len(self._items)

    def items(self):
        return self._items


class ForgedTier:
    pass


class NormalizerTestBase(unittest.TestCase):
    def setUp(self):
        self.normalizer_module = importlib.import_module("dataforseo_evidence_normalizer")
        self.evidence = importlib.import_module("product_research.evidence")
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.policy = importlib.import_module("product_research.evidence_policy")
        self.search = importlib.import_module("dataforseo_search_provider")
        self.marketplace = importlib.import_module("dataforseo_marketplace_provider")
        self.client = importlib.import_module("dataforseo_client")

    def assignments(self):
        return {
            operation: (self.evidence.Tier("Tier 2"), self.evidence.Confidence("Medium"))
            for operation in OPERATIONS
        }

    def normalizer(self, assignments=None):
        return self.normalizer_module.create_dataforseo_evidence_normalizer(
            assignments if assignments is not None else self.assignments()
        )

    def task(self, operation, *, evidence_kind="marketplace_price", task_id=None, question="declared question", intent="declared intent"):
        family = "MARKETPLACE" if operation == "amazon_products_live" else "SEARCH"
        return self.orchestration.ResearchTask(
            task_id=task_id or f"task-{operation}",
            research_question=question,
            source_family=self.orchestration.SourceFamily(family),
            query_intent=intent,
            evidence_kind=self.policy.EvidenceKind(evidence_kind),
            required=True,
        )

    def fixture(self, name):
        return json.loads((FIXTURES / name).read_text())

    @staticmethod
    def thaw(value):
        if isinstance(value, Mapping):
            return {key: NormalizerTestBase.thaw(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [NormalizerTestBase.thaw(item) for item in value]
        return value

    def search_finding(self, operation, task_id=None):
        task = self.task(operation, task_id=task_id)
        request_values = {
            "google_ads_search_volume_live": self.search.GoogleAdsSearchVolumeRequest(
                keywords=("blue shoes", "running shoes"), location_code=2840, language_code="en"
            ),
            "google_trends_explore_live": self.search.GoogleTrendsExploreRequest(
                keywords=("blue shoes", "running shoes"),
                location_name="United States",
                language_code="en",
                date_from="2026-01-01",
                date_to="2026-08-01",
                item_types=("google_trends_graph", "google_trends_map"),
            ),
            "amazon_bulk_search_volume_live": self.search.AmazonBulkSearchVolumeRequest(
                keywords=("blue shoes", "running shoes"), location_code=2840, language_code="en"
            ),
        }
        fixture_names = {
            "google_ads_search_volume_live": "google_ads_success.json",
            "google_trends_explore_live": "google_trends_success.json",
            "amazon_bulk_search_volume_live": "amazon_success.json",
        }
        request = request_values[operation]
        response = self.client.DataForSEOHTTPResponse(
            status_code=200,
            body=json.dumps(self.fixture(fixture_names[operation])),
        )
        binding = self.search.ProviderBinding(
            task_id=task.task_id,
            source_family=self.orchestration.SourceFamily("SEARCH"),
            request=request,
        )
        acquisition = self.search.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login="fixture-login",
            password="fixture-password",
            transport=lambda wire, headers: response,
            clock=lambda: FIXED_TIME,
        )
        result = acquisition(task)
        return task, result.findings[0]

    def marketplace_finding(self, task_id=None, *, rank_absolute=_UNSET):
        task = self.task("amazon_products_live", task_id=task_id)
        request = self.marketplace.AmazonProductsRequest(
            keyword="wireless headphones",
            location_code=2840,
            language_code="en",
            depth=100,
            tag="eco43",
            request_context="candidate-42",
        )
        payload = self.fixture("amazon_products_success.json")
        if rank_absolute is not _UNSET:
            payload["tasks"][0]["result"][0]["items"][0]["rank_absolute"] = rank_absolute
        task_data = payload["tasks"][0]["data"]
        task_data.update({
            "keyword": request.keyword,
            "location_code": request.location_code,
            "language_code": request.language_code,
            "depth": request.depth,
            "tag": request.tag,
        })
        response = self.client.DataForSEOHTTPResponse(status_code=200, body=json.dumps(payload))
        binding = self.marketplace.ProviderBinding(
            task_id=task.task_id,
            source_family=self.orchestration.SourceFamily("MARKETPLACE"),
            request=request,
        )
        acquisition = self.marketplace.create_dataforseo_marketplace_acquisition(
            resolve_binding=lambda current: binding,
            login="fixture-login",
            password="fixture-password",
            transport=lambda wire, headers: response,
        )
        result = acquisition(task)
        return task, result.findings[0]

    def finding_for(self, operation, task_id=None):
        if operation == "amazon_products_live":
            return self.marketplace_finding(task_id)
        return self.search_finding(operation, task_id)

    def raw_with(self, finding, *, source=None, content=None, metadata=None, finding_id=None):
        return self.orchestration.RawFinding(
            finding_id=finding_id or finding.finding_id,
            content=content if content is not None else finding.content,
            source=source or finding.source,
            observed_at=finding.observed_at,
            metadata=metadata if metadata is not None else self.thaw(finding.metadata),
        )

    def content_and_metadata_with_observation(self, finding, observation):
        content_data = json.loads(finding.content)
        content_data["observation"] = copy.deepcopy(observation)
        metadata = self.thaw(finding.metadata)
        metadata["observation"] = copy.deepcopy(observation)
        return json.dumps(content_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")), metadata


class ConstructionTests(NormalizerTestBase):
    def test_requires_exactly_one_existing_assignment_for_each_supported_operation(self):
        valid = self.assignments()
        cases = [
            {key: value for key, value in valid.items() if key != OPERATIONS[0]},
            {**valid, "unsupported": valid[OPERATIONS[0]]},
            DuplicateAssignmentMapping((*valid.items(), (OPERATIONS[0], valid[OPERATIONS[0]]))),
            {**valid, OPERATIONS[0]: (self.evidence.Tier("Tier 2"),)},
            {**valid, OPERATIONS[0]: ("Tier 2", self.evidence.Confidence("Medium"))},
            {**valid, OPERATIONS[0]: (self.evidence.Tier("Tier 2"), ForgedTier())},
        ]
        for assignments in cases:
            with self.subTest(assignments=assignments), self.assertRaises((TypeError, ValueError)):
                self.normalizer(assignments)

    def test_assignment_snapshot_is_defensive_and_uses_exact_tier_and_base_confidence(self):
        assignments = self.assignments()
        normalizer = self.normalizer(assignments)
        assignments[OPERATIONS[0]] = (self.evidence.Tier("Tier 1"), self.evidence.Confidence("Low"))
        task, finding = self.finding_for(OPERATIONS[0])
        record = normalizer(task, finding, self.evidence.EvidenceId("E001"))
        self.assertEqual(record.tier, self.evidence.Tier("Tier 2"))
        self.assertEqual(record.confidence, self.evidence.Confidence("Medium"))

    def test_construction_and_normalization_have_no_allocator_or_uuid_surface(self):
        source = inspect.getsource(self.normalizer_module).lower()
        self.assertNotIn("uuid", source)
        self.assertNotIn("random", source)
        self.assertNotIn("evidenceid(", source)
        self.assertNotIn("e001", source)


class EvidenceContractTests(NormalizerTestBase):
    def test_each_supported_operation_returns_one_existing_evidence_with_supplied_identity(self):
        normalizer = self.normalizer()
        for number, operation in enumerate(OPERATIONS, 1):
            with self.subTest(operation=operation):
                task, finding = self.finding_for(operation)
                evidence_id = self.evidence.EvidenceId(f"E{number:03d}")
                record = normalizer(task, finding, evidence_id)
                self.assertIs(type(record), self.evidence.Evidence)
                self.assertEqual(record.id, evidence_id)
                self.assertEqual(record.status, self.evidence.Status("Observed"))
                self.assertEqual(record.source, finding.source)
                self.assertEqual(record.observed_at, finding.observed_at)
                self.assertEqual(record.evidence, finding.content)
                self.assertEqual(self.evidence.Evidence.from_json(record.to_json()), record)

    def test_unsupported_operation_creates_no_evidence(self):
        task, finding = self.finding_for(OPERATIONS[0])
        metadata = self.thaw(finding.metadata)
        metadata["operation"] = "unsupported_operation"
        with self.assertRaises((TypeError, ValueError)):
            self.normalizer()(task, self.raw_with(finding, metadata=metadata), self.evidence.EvidenceId("E001"))

    def test_metadata_has_exact_policy_research_and_acquisition_namespaces(self):
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                task, finding = self.finding_for(operation)
                record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))
                self.assertEqual(set(record.metadata), {"policy", "research", "acquisition"})
                self.assertEqual(record.metadata["research"], {
                    "task_id": task.task_id,
                    "finding_id": finding.finding_id,
                })
                self.assertEqual(record.metadata["acquisition"], self.thaw(finding.metadata))


class ClaimAndProvenanceTests(NormalizerTestBase):
    def test_operation_specific_claims_use_only_stable_observation_identity_fields(self):
        expected = {
            "google_ads_search_volume_live": ("blue shoes", "keyword metrics"),
            "google_trends_explore_live": ("Interest over time", "google_trends_graph"),
            "amazon_bulk_search_volume_live": ("blue shoes", "Amazon keyword search volume"),
            "amazon_products_live": ("B000001", "Wireless Headphones"),
        }
        forbidden = (
            "strong demand", "weak demand", "positive trend", "declining trend", "high competition",
            "low competition", "opportunity", "score", "gate", "go decision", "no-go", "judgment",
        )
        for operation, required_fragments in expected.items():
            with self.subTest(operation=operation):
                task, finding = self.finding_for(operation)
                claim = self.normalizer()(task, finding, self.evidence.EvidenceId("E001")).claim
                for fragment in required_fragments:
                    self.assertIn(fragment.lower(), claim.lower())
                for term in forbidden:
                    self.assertNotIn(term, claim.lower())

    def test_research_question_and_query_intent_cannot_change_claim_basis_or_classification(self):
        normalizer = self.normalizer()
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                task, finding = self.finding_for(operation)
                baseline = normalizer(task, finding, self.evidence.EvidenceId("E001"))
                changed_task = dataclasses.replace(
                    task,
                    research_question="Does this prove strong demand and a GO decision?",
                    query_intent="calculate score and competition opportunity",
                )
                changed = normalizer(changed_task, finding, self.evidence.EvidenceId("E001"))
                self.assertEqual(changed.claim, baseline.claim)
                self.assertEqual(changed.evidence, baseline.evidence)
                self.assertEqual(changed.tier, baseline.tier)
                self.assertEqual(changed.confidence, baseline.confidence)
                self.assertEqual(changed.metadata["policy"], baseline.metadata["policy"])

    def test_exact_raw_content_and_null_metric_are_preserved_without_coercion(self):
        task, finding = self.search_finding("google_ads_search_volume_live", task_id="null-task")
        metadata = self.thaw(finding.metadata)
        observation = metadata["observation"]
        observation["search_volume"] = None
        content, metadata = self.content_and_metadata_with_observation(finding, observation)
        null_finding = self.raw_with(finding, content=content, metadata=metadata)
        record = self.normalizer()(task, null_finding, self.evidence.EvidenceId("E001"))
        self.assertEqual(record.evidence, content)
        self.assertIsNone(json.loads(record.evidence)["observation"]["search_volume"])
        self.assertIsNone(record.metadata["acquisition"]["observation"]["search_volume"])
        self.assertEqual(record.status, self.evidence.Status("Observed"))
        self.assertNotIn("Unknown", record.claim)
        self.assertNotIn("zero", record.claim.lower())

    def test_provider_nullable_amazon_rank_round_trips_through_normalizer(self):
        task, finding = self.marketplace_finding(rank_absolute=None)
        self.assertIsNone(finding.metadata["provider_rank"])
        self.assertIsNone(finding.metadata["observation"]["rank_absolute"])

        record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))

        self.assertEqual(record.evidence, finding.content)
        self.assertIsNone(json.loads(record.evidence)["observation"]["rank_absolute"])
        self.assertIsNone(record.metadata["acquisition"]["provider_rank"])
        self.assertIsNone(record.metadata["acquisition"]["observation"]["rank_absolute"])
        self.assertEqual(record.status, self.evidence.Status("Observed"))

    def test_provider_integer_amazon_rank_normalizes_unchanged(self):
        for rank_absolute in (0, 1):
            with self.subTest(rank_absolute=rank_absolute):
                task, finding = self.marketplace_finding(rank_absolute=rank_absolute)
                record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))

                self.assertEqual(record.metadata["acquisition"]["provider_rank"], rank_absolute)
                self.assertEqual(
                    record.metadata["acquisition"]["observation"]["rank_absolute"],
                    rank_absolute,
                )

    def test_marketplace_rank_provenance_requires_both_equal_keys(self):
        task, finding = self.marketplace_finding(rank_absolute=1)
        cases = {}

        contradictory = self.thaw(finding.metadata)
        contradictory["provider_rank"] = 2
        cases["contradictory"] = self.raw_with(finding, metadata=contradictory)

        missing_provider = self.thaw(finding.metadata)
        missing_provider.pop("provider_rank")
        cases["missing provider_rank"] = self.raw_with(finding, metadata=missing_provider)

        observation = self.thaw(finding.metadata["observation"])
        observation.pop("rank_absolute")
        content, missing_observation = self.content_and_metadata_with_observation(finding, observation)
        cases["missing observation.rank_absolute"] = self.raw_with(
            finding,
            content=content,
            metadata=missing_observation,
        )

        for label, bad_finding in cases.items():
            with self.subTest(label=label), self.assertRaises((TypeError, ValueError)):
                self.normalizer()(task, bad_finding, self.evidence.EvidenceId("E001"))

    def test_marketplace_rank_provenance_rejects_cross_type_numeric_equality(self):
        task, finding = self.marketplace_finding(rank_absolute=1)
        for provider_rank, observation_rank in ((1, 1.0), (1, True), (0, False)):
            with self.subTest(provider_rank=provider_rank, observation_rank=observation_rank):
                observation = self.thaw(finding.metadata["observation"])
                observation["rank_absolute"] = observation_rank
                content, metadata = self.content_and_metadata_with_observation(finding, observation)
                metadata["provider_rank"] = provider_rank

                with self.assertRaises((TypeError, ValueError)):
                    self.normalizer()(
                        task,
                        self.raw_with(finding, content=content, metadata=metadata),
                        self.evidence.EvidenceId("E001"),
                    )

    def test_marketplace_normalizer_does_not_revalidate_provider_rank_type(self):
        task, finding = self.marketplace_finding(rank_absolute=1)
        for opaque_rank in (1.5, "provider-owned-opaque-rank", True, [1], {"rank": 1}):
            with self.subTest(opaque_rank=opaque_rank):
                observation = self.thaw(finding.metadata["observation"])
                observation["rank_absolute"] = opaque_rank
                content, metadata = self.content_and_metadata_with_observation(finding, observation)
                metadata["provider_rank"] = opaque_rank

                record = self.normalizer()(
                    task,
                    self.raw_with(finding, content=content, metadata=metadata),
                    self.evidence.EvidenceId("E001"),
                )

                self.assertEqual(record.evidence, content)
                self.assertEqual(record.metadata["acquisition"]["provider_rank"], opaque_rank)
                self.assertEqual(
                    record.metadata["acquisition"]["observation"]["rank_absolute"],
                    opaque_rank,
                )

    def test_provider_rejects_invalid_rank_type_before_normalizer_boundary(self):
        for invalid_rank in (1.5, "not-an-integer", True, [1], {"rank": 1}):
            with self.subTest(invalid_rank=invalid_rank), self.assertRaises(
                self.marketplace.DataForSEOProtocolError
            ):
                self.marketplace_finding(rank_absolute=invalid_rank)

    def test_frozen_metadata_is_thawed_mechanically_without_mutable_alias(self):
        task, finding = self.marketplace_finding()
        original = self.thaw(finding.metadata)
        record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))
        acquisition = record.metadata["acquisition"]
        self.assertEqual(acquisition, original)
        acquisition["request"]["request_context"] = "changed-only-in-evidence"
        acquisition["observation"]["title"] = "changed-only-in-evidence"
        self.assertEqual(self.thaw(finding.metadata), original)
        self.assertNotEqual(acquisition, self.thaw(finding.metadata))

    def test_all_provider_provenance_is_retained_json_equivalently(self):
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                task, finding = self.finding_for(operation)
                record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))
                self.assertEqual(record.source, finding.source)
                self.assertEqual(record.observed_at, finding.observed_at)
                self.assertEqual(record.metadata["acquisition"], self.thaw(finding.metadata))
                self.assertEqual(record.metadata["acquisition"]["provider"], "DataForSEO")
                self.assertEqual(record.metadata["acquisition"]["operation"], operation)
                self.assertIn("endpoint", record.metadata["acquisition"])
                self.assertIn("task_id", record.metadata["acquisition"])
                self.assertIn("request", record.metadata["acquisition"])


class PolicyAndRecognitionTests(NormalizerTestBase):
    def test_policy_kind_is_exactly_task_declared_and_source_date_is_observation_date(self):
        normalizer = self.normalizer()
        for operation in OPERATIONS:
            for kind in DATED_KINDS:
                with self.subTest(operation=operation, kind=kind):
                    task, finding = self.finding_for(operation)
                    task = dataclasses.replace(task, evidence_kind=self.policy.EvidenceKind(kind))
                    policy = normalizer(task, finding, self.evidence.EvidenceId("E001")).metadata["policy"]
                    self.assertEqual(policy, {"kind": kind, "source_date": finding.observed_at[:10]})

    def test_policy_kind_is_not_inferred_from_operation_payload_url_or_free_form_text(self):
        task, finding = self.finding_for("amazon_products_live")
        task = dataclasses.replace(
            task,
            evidence_kind=self.policy.EvidenceKind("voc"),
            research_question="competition score opportunity GO",
            query_intent="strong demand and positive trend",
        )
        record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))
        self.assertEqual(record.metadata["policy"]["kind"], "voc")

    def test_policy_kinds_without_derivable_facts_fail_closed(self):
        for kind in NON_DERIVABLE_KINDS:
            with self.subTest(kind=kind):
                task, finding = self.finding_for("google_ads_search_volume_live")
                task = dataclasses.replace(task, evidence_kind=self.policy.EvidenceKind(kind))
                with self.assertRaises((TypeError, ValueError)):
                    self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))

    def test_recognition_rejects_contradictory_or_missing_owned_provenance(self):
        task, finding = self.marketplace_finding()
        for label in ("provider", "source-operation", "task-family", "finding-owner"):
            with self.subTest(label=label):
                if label == "provider":
                    bad_source = self.evidence.Source("Other", finding.source.source_type, finding.source.reference, finding.source.title)
                    bad_finding = self.raw_with(finding, source=bad_source)
                    bad_task = task
                elif label == "source-operation":
                    bad_task = task
                    bad_finding = self.raw_with(finding, source=dataclasses.replace(finding.source, source_type="other_operation"))
                elif label == "task-family":
                    bad_task = dataclasses.replace(task, source_family=self.orchestration.SourceFamily("SEARCH"))
                    bad_finding = finding
                else:
                    bad_task = task
                    bad_finding = self.raw_with(finding, finding_id="other-task:amazon_products_live:0:0")
                with self.assertRaises((TypeError, ValueError)):
                    self.normalizer()(bad_task, bad_finding, self.evidence.EvidenceId("E001"))

        for key in ("provider", "operation", "endpoint", "task_id", "request", "result_ordinal", "item_ordinal", "observation"):
            bad_metadata = self.thaw(finding.metadata)
            bad_metadata.pop(key, None)
            with self.subTest(missing=key), self.assertRaises((TypeError, ValueError)):
                self.normalizer()(task, self.raw_with(finding, metadata=bad_metadata), self.evidence.EvidenceId("E001"))

        malformed_values = {
            "provider": 3,
            "endpoint": "wrong-endpoint",
            "task_id": 3,
            "request": [],
            "result_ordinal": "0",
            "observation": [],
        }
        for key, value in malformed_values.items():
            bad_metadata = self.thaw(finding.metadata)
            bad_metadata[key] = value
            with self.subTest(malformed=key), self.assertRaises((TypeError, ValueError)):
                self.normalizer()(task, self.raw_with(finding, metadata=bad_metadata), self.evidence.EvidenceId("E001"))

    def test_content_and_metadata_observations_must_agree(self):
        task, finding = self.search_finding("google_ads_search_volume_live")
        data = json.loads(finding.content)
        data["observation"]["keyword"] = "forged keyword"
        with self.assertRaises((TypeError, ValueError)):
            self.normalizer()(task, self.raw_with(finding, content=json.dumps(data, sort_keys=True, separators=(",", ":"))), self.evidence.EvidenceId("E001"))
        duplicate_content = finding.content[:-1] + ',"operation":"google_ads_search_volume_live"}'
        with self.assertRaises((TypeError, ValueError)):
            self.normalizer()(task, self.raw_with(finding, content=duplicate_content), self.evidence.EvidenceId("E001"))

    def test_finding_identity_must_match_operation_and_ordering_provenance(self):
        search_task, search_finding = self.search_finding("google_ads_search_volume_live")
        marketplace_task, marketplace_finding = self.marketplace_finding()
        cases = (
            (search_task, self.raw_with(search_finding, finding_id=f"{search_task.task_id}:amazon_products_live:0")),
            (search_task, self.raw_with(search_finding, finding_id=f"{search_task.task_id}:google_ads_search_volume_live:9")),
            (
                marketplace_task,
                self.raw_with(
                    marketplace_finding,
                    finding_id=f"{marketplace_task.task_id}:amazon_products_live:0:9",
                ),
            ),
        )
        for task, finding in cases:
            with self.subTest(finding_id=finding.finding_id), self.assertRaises((TypeError, ValueError)):
                self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))

    def test_metric_details_are_not_revalidated_by_a_second_provider_schema(self):
        task, finding = self.search_finding("google_ads_search_volume_live")
        metadata = self.thaw(finding.metadata)
        metadata["observation"]["search_volume"] = {"provider-owned": "opaque"}
        content, metadata = self.content_and_metadata_with_observation(finding, metadata["observation"])
        record = self.normalizer()(task, self.raw_with(finding, content=content, metadata=metadata), self.evidence.EvidenceId("E001"))
        self.assertIsInstance(record, self.evidence.Evidence)


class OrchestrationAndArchitectureTests(NormalizerTestBase):
    def test_real_orchestration_retains_order_gaps_and_existing_normalization_exception(self):
        task, first = self.search_finding("google_ads_search_volume_live", task_id="integration-task")
        _, second = self.search_finding("google_ads_search_volume_live", task_id="integration-task")
        _, third = self.search_finding("google_ads_search_volume_live", task_id="integration-task")
        second_metadata = self.thaw(second.metadata)
        second_metadata["ordinal"] = 1
        second = self.raw_with(
            second,
            source=dataclasses.replace(second.source, source_type="contradictory"),
            metadata=second_metadata,
            finding_id="integration-task:google_ads_search_volume_live:1",
        )
        third_metadata = self.thaw(third.metadata)
        third_metadata["ordinal"] = 2
        third = self.raw_with(
            third,
            metadata=third_metadata,
            finding_id="integration-task:google_ads_search_volume_live:2",
        )
        findings = (first, second, third)
        acquisition = self.orchestration.AcquisitionResult(task.task_id, self.orchestration.TaskStatus("SUCCESS"), findings)
        normalizer = self.normalizer()
        result = self.orchestration.run_research(
            self.orchestration.ResearchObjective("objective-01", "objective"),
            lambda objective: self.orchestration.ResearchPlan(objective.objective_id, (task,)),
            lambda current: acquisition,
            normalizer,
        )
        self.assertEqual([record.id.value for record in result.evidence], ["E001", "E003"])
        self.assertEqual([str(failure.reason) for failure in result.failures], ["NORMALIZATION_EXCEPTION"])
        self.assertEqual(result.failures[0].finding_id, "integration-task:google_ads_search_volume_live:1")

    def test_external_architecture_has_no_reverse_import_or_downstream_execution_surface(self):
        module_path = ROOT / "dataforseo_evidence_normalizer.py"
        self.assertTrue(module_path.exists())
        source = module_path.read_text()
        tree = ast.parse(source)
        for path in (ROOT / "product_research").glob("*.py"):
            core_tree = ast.parse(path.read_text())
            for node in ast.walk(core_tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any("dataforseo_evidence_normalizer" in alias.name for alias in node.names), path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "dataforseo_evidence_normalizer", path.name)
        forbidden = (
            "dataforseo_client", "dataforseo_search_provider", "dataforseo_marketplace_provider",
            "evidence_policy", "evidence_assessment", "market_demand", "unit_economics",
            "risk_gate", "scoring", "red_team", "reporting", "persistence", "end_to_end_workflow",
        )
        lowered = source.lower()
        for token in forbidden:
            self.assertNotIn(token, lowered)
        imported_modules = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        self.assertIn("product_research.evidence", imported_modules)
        self.assertIn("product_research.research_orchestration", imported_modules)
        for path in (
            ROOT / "dataforseo_search_provider.py",
            ROOT / "dataforseo_marketplace_provider.py",
            ROOT / "dataforseo_acquisition_runtime.py",
        ):
            provider_source = path.read_text()
            for token in ("Evidence(", "EvidenceId(", "Tier(", "Confidence("):
                self.assertNotIn(token, provider_source, path.name)

    def test_fixture_path_is_offline_even_with_credential_like_environment(self):
        task, finding = self.search_finding("google_ads_search_volume_live")
        with patch.dict(os.environ, {"DATAFORSEO_LOGIN": "sentinel", "DATAFORSEO_PASSWORD": "sentinel"}, clear=False), \
                patch.object(socket, "socket", side_effect=AssertionError("network access is forbidden")):
            record = self.normalizer()(task, finding, self.evidence.EvidenceId("E001"))
        self.assertEqual(record.id, self.evidence.EvidenceId("E001"))


if __name__ == "__main__":
    unittest.main()
