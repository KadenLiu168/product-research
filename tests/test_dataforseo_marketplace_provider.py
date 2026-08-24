"""ECO-43 requirement-to-test trace.

The test groups intentionally trace the Change tasks without introducing a
second acquisition or marketplace domain contract:

* ScopeTests: 1.3, 2.6, 5.4, and the one-way dependency boundary.
* RequestAndBindingTests: 2.1 through 2.6.
* SharedStackAndTransportTests: 3.1 through 3.4, 5.5, and 5.6.
* ProtocolAndMappingTests: 3.5 through 4.8.
* OutcomeAndOrchestrationTests: 5.1 through 5.4.

The fixture is deterministic and secret-free. No test constructs a live
transport, and credential-like environment values never enable one.
"""

import ast
import copy
import dataclasses
import importlib
import inspect
import json
import os
import pathlib
import unittest

from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "dataforseo"
SECRET_LOGIN = "marketplace-login-sentinel"
SECRET_PASSWORD = "marketplace-password-sentinel"


@dataclass(frozen=True)
class UnsupportedRequest:
    value: str


class ScopeTests(unittest.TestCase):
    def test_marketplace_surface_is_top_level_and_core_has_no_dataforseo_behavior(self):
        surface = ROOT / "dataforseo_marketplace_provider.py"
        self.assertEqual(surface.parent, ROOT)
        self.assertEqual(surface.name, "dataforseo_marketplace_provider.py")
        self.assertTrue(surface.exists(), "the concrete MARKETPLACE surface must be outside product_research")

        provider_neutral = (ROOT / "product_research_providers.py").read_text()
        self.assertNotIn("dataforseo", provider_neutral.lower())
        for path in (ROOT / "product_research").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any("dataforseo" in alias.name.lower() for alias in node.names), path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("dataforseo", (node.module or "").lower(), path.name)


class MarketplaceTestBase(unittest.TestCase):
    def setUp(self):
        try:
            self.provider = importlib.import_module("dataforseo_marketplace_provider")
        except ModuleNotFoundError:
            self.fail("DataForSEO MARKETPLACE provider has not been implemented")
        self.search = importlib.import_module("dataforseo_search_provider")
        self.client = importlib.import_module("dataforseo_client")
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.adapters = importlib.import_module("product_research.research_adapters")
        self.evidence = importlib.import_module("product_research.evidence")
        self.policy = importlib.import_module("product_research.evidence_policy")

    def task(self, task_id="marketplace-01", question="caller question", intent="caller intent"):
        return self.orchestration.ResearchTask(
            task_id=task_id,
            research_question=question,
            source_family=self.orchestration.SourceFamily("MARKETPLACE"),
            query_intent=intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=True,
        )

    def request(self, **overrides):
        values = {
            "keyword": "wireless headphones",
            "location_code": 2840,
            "language_code": "en",
            "depth": 100,
            "tag": "eco43",
            "request_context": "candidate-42",
        }
        values.update(overrides)
        return self.provider.AmazonProductsRequest(**values)

    def fixture(self, name="amazon_products_success.json"):
        return json.loads((FIXTURES / name).read_text())

    def response(self, payload, status=200):
        return self.client.DataForSEOHTTPResponse(status_code=status, body=json.dumps(payload))

    def configured(self, task=None, request=None, payload=None, *, status=200, transport=None):
        task = task or self.task()
        request = request or self.request()
        calls = []
        binding = self.provider.ProviderBinding(
            task_id=task.task_id,
            source_family=self.orchestration.SourceFamily("MARKETPLACE"),
            request=request,
        )
        if payload is None:
            payload = self.fixture()
            task_data = payload["tasks"][0]["data"]
            task_data["keyword"] = request.keyword
            for field_name in ("location_name", "location_code", "language_name", "language_code", "depth"):
                value = getattr(request, field_name)
                if value is None:
                    task_data.pop(field_name, None)
                else:
                    task_data[field_name] = value
            if request.tag is None:
                task_data.pop("tag", None)
            else:
                task_data["tag"] = request.tag
        result = self.response(payload, status=status)
        if transport is None:
            def transport(wire, headers):
                calls.append((wire, headers))
                return result
        acquisition = self.provider.create_dataforseo_marketplace_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=transport,
        )
        return task, acquisition, calls

    def direct_result(self, acquisition, task):
        result = acquisition(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        return result

    def evidence_record(self, evidence_id, finding):
        return self.evidence.Evidence(
            id=evidence_id,
            claim="Declared factual observation",
            evidence=finding.content,
            source=finding.source,
            observed_at=finding.observed_at,
            tier=self.evidence.Tier("Tier 2"),
            status=self.evidence.Status("Observed"),
            confidence=self.evidence.Confidence("Medium"),
            metadata={"policy": {"kind": "marketplace_price"}},
        )


class RequestAndBindingTests(MarketplaceTestBase):
    def test_request_is_frozen_exactly_and_preserves_caller_values(self):
        request = self.request()
        self.assertTrue(dataclasses.is_dataclass(request))
        self.assertTrue(type(request).__dataclass_params__.frozen)
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(request)),
            ("keyword", "location_name", "location_code", "language_name", "language_code", "depth", "tag", "request_context"),
        )
        self.assertEqual(request.keyword, "wireless headphones")
        self.assertEqual(request.location_code, 2840)
        self.assertEqual(request.language_code, "en")
        self.assertEqual(request.depth, 100)
        self.assertEqual(request.tag, "eco43")
        self.assertEqual(request.request_context, "candidate-42")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.depth = 101

    def test_invalid_request_values_are_rejected_before_any_transport(self):
        cases = (
            {"keyword": 1},
            {"keyword": ""},
            {"keyword": " "},
            {"keyword": "k" * 701},
            {"location_code": True},
            {"location_name": "United States", "location_code": 2840},
            {"location_name": None, "location_code": None},
            {"language_code": "", "language_name": None},
            {"language_name": "English", "language_code": "en"},
            {"tag": ""},
            {"tag": "t" * 256},
            {"depth": True},
            {"depth": 0},
            {"depth": 701},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    self.request(**overrides)

        task = self.task()
        valid = self.request()
        forged = object.__new__(self.provider.AmazonProductsRequest)
        for field in dataclasses.fields(valid):
            object.__setattr__(forged, field.name, getattr(valid, field.name))
        object.__setattr__(forged, "depth", 701)
        _, acquisition, calls = self.configured(task=task, request=forged)
        with self.assertRaises((TypeError, ValueError)):
            acquisition(task)
        self.assertEqual(calls, [])

    def test_depth_boundaries_are_transmitted_without_inference_or_clamping(self):
        for depth in (1, 100, 101, 700):
            with self.subTest(depth=depth):
                task = self.task(question="depth must be inferred from this prose", intent="depth=1")
                _, acquisition, calls = self.configured(task=task, request=self.request(depth=depth))
                self.direct_result(acquisition, task)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0].payload[0]["depth"], depth)

    def test_exact_type_dispatch_rejects_forged_and_search_requests(self):
        task = self.task()
        request = self.request()

        class ForgedRequest(self.provider.AmazonProductsRequest):
            pass

        forged = object.__new__(ForgedRequest)
        for field in dataclasses.fields(request):
            object.__setattr__(forged, field.name, getattr(request, field.name))
        for unsupported in (forged, self.search.AmazonBulkSearchVolumeRequest(keywords=("term",), location_code=2840, language_code="en"), UnsupportedRequest("search") ):
            with self.subTest(request_type=type(unsupported).__name__):
                binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("MARKETPLACE"), unsupported)
                calls = []
                acquisition = self.provider.create_dataforseo_marketplace_acquisition(
                    resolve_binding=lambda current, binding=binding: binding,
                    login=SECRET_LOGIN,
                    password=SECRET_PASSWORD,
                    transport=lambda *args: calls.append(args),
                )
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
                self.assertEqual(result.findings, ())
                self.assertEqual(calls, [])

    def test_task_text_does_not_change_explicit_request_or_billable_payload(self):
        request = self.request(depth=100)
        task_a = self.task(question="find the cheapest products", intent="price")
        task_b = self.task(question="find demand and competitors", intent="market size")
        binding = self.provider.ProviderBinding(task_a.task_id, self.orchestration.SourceFamily("MARKETPLACE"), request)
        calls = []

        def transport(wire, headers):
            calls.append(wire)
            return self.response(self.fixture())

        acquisition = self.provider.create_dataforseo_marketplace_acquisition(
            resolve_binding=lambda task: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=transport,
        )
        first = acquisition(task_a)
        second = acquisition(task_b)
        self.assertEqual(first, second)
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(calls[0].endpoint, self.provider.AMAZON_PRODUCTS_ENDPOINT)

    def test_marketplace_slot_and_core_public_contracts_remain_unchanged(self):
        task = self.task()
        _, acquisition, _ = self.configured(task=task)
        self.assertIs(self.adapters.ResearchSourceAdapters(marketplace=acquisition)(task).__class__, self.orchestration.AcquisitionResult)
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.orchestration.ResearchTask)),
            ("task_id", "research_question", "source_family", "query_intent", "evidence_kind", "required"),
        )
        self.assertEqual(self.provider.ProviderAcquisition.__module__, "product_research_providers")
        self.assertNotEqual(self.provider.AMAZON_PRODUCTS_ENDPOINT, self.search.AMAZON_ENDPOINT)


class SharedStackAndTransportTests(MarketplaceTestBase):
    def test_marketplace_reuses_all_existing_shared_values(self):
        for name in (
            "DataForSEOConfiguration",
            "DataForSEOWireRequest",
            "DataForSEOHTTPResponse",
            "DataForSEOProtocolError",
            "authenticated_sender",
            "parse_live_response",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(self.provider, name), getattr(self.client, name))
        self.assertIs(self.provider.ProviderBinding, importlib.import_module("product_research_providers").ProviderBinding)
        self.assertIs(self.provider.ProviderAcquisition, importlib.import_module("product_research_providers").ProviderAcquisition)
        source = inspect.getsource(self.provider)
        for forbidden in ("class DataForSEOConfiguration", "class DataForSEOWireRequest", "class DataForSEOHTTPResponse", "class ProviderAcquisition", "class ProviderBinding", "def parse_live_response"):
            self.assertNotIn(forbidden, source)

    def test_construction_is_io_free_and_authentication_is_send_time_only(self):
        task = self.task()
        request = self.request()
        binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("MARKETPLACE"), request)
        calls = []
        acquisition = self.provider.create_dataforseo_marketplace_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda wire, headers: calls.append((wire, headers)) or self.response(self.fixture()),
        )
        public = " ".join((repr(acquisition), repr(request), repr(binding), repr(self.provider.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD))))
        self.assertEqual(calls, [])
        self.assertNotIn(SECRET_LOGIN, public)
        self.assertNotIn(SECRET_PASSWORD, public)
        self.direct_result(acquisition, task)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][1]["Authorization"].startswith("Basic "))
        self.assertNotIn(SECRET_LOGIN, repr(calls[0][0]))
        self.assertNotIn(SECRET_PASSWORD, repr(calls[0][0]))
        self.assertNotIn("Authorization", repr(calls[0][0]))

    def test_exact_endpoint_payload_and_single_attempt(self):
        task, acquisition, calls = self.configured()
        self.direct_result(acquisition, task)
        self.assertEqual(len(calls), 1)
        wire, _ = calls[0]
        self.assertEqual(wire.endpoint, "/v3/merchant/amazon/products/live/advanced")
        self.assertEqual(len(wire.payload), 1)
        self.assertEqual(
            set(wire.payload[0]),
            {"keyword", "location_code", "language_code", "depth", "tag"},
        )
        self.assertEqual(wire.payload[0]["keyword"], "wireless headphones")
        self.assertNotIn("request_context", wire.payload[0])
        self.assertNotIn("location_coordinate", wire.payload[0])
        self.assertNotIn("search_param", wire.payload[0])

    def test_provider_failure_and_transport_exception_are_not_retried(self):
        task = self.task()
        calls = []
        failure_payload = self.fixture()
        failure_payload["tasks"][0]["status_code"] = 40501
        failure_payload["tasks"][0]["result_count"] = 0
        failure_payload["tasks"][0].pop("result")
        _, acquisition, calls = self.configured(task=task, payload=failure_payload)
        result = acquisition(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
        self.assertEqual(len(calls), 1)

        error = TimeoutError("transport sentinel")
        raised_calls = []
        _, raised, _ = self.configured(task=task, transport=lambda wire, headers: raised_calls.append(wire) or (_ for _ in ()).throw(error))
        with self.assertRaises(TimeoutError) as raised_error:
            raised(task)
        self.assertIs(raised_error.exception, error)
        self.assertEqual(len(raised_calls), 1)

    def test_secret_sentinels_never_enter_results_exceptions_fixtures_or_default_surface(self):
        task, acquisition, _ = self.configured()
        result = acquisition(task)
        public = " ".join((repr(result), repr(result.findings), repr(acquisition)))
        self.assertNotIn(SECRET_LOGIN, public)
        self.assertNotIn(SECRET_PASSWORD, public)
        for path in FIXTURES.glob("*.json"):
            self.assertNotIn(SECRET_LOGIN, path.read_text())
            self.assertNotIn(SECRET_PASSWORD, path.read_text())
        self.assertFalse(hasattr(self.provider, "run_live_test"))
        self.assertIsNone(os.environ.get("DATAFORSEO_LIVE_TEST"))


class ProtocolAndMappingTests(MarketplaceTestBase):
    def test_documented_provider_task_metadata_does_not_invalidate_request_echo(self):
        payload = self.fixture()
        payload["tasks"][0]["data"].update(
            {
                "api": "merchant",
                "function": "products",
                "se": "amazon",
                "se_type": "products",
                "device": "desktop",
                "os": "windows",
            }
        )
        task, acquisition, _ = self.configured(payload=payload)

        result = self.direct_result(acquisition, task)

        self.assertEqual(len(result.findings), 4)

    def test_success_fixture_preserves_direct_order_and_skips_known_containers(self):
        task, acquisition, _ = self.configured()
        result = self.direct_result(acquisition, task)
        self.assertEqual(
            [finding.metadata["observation"]["data_asin"] for finding in result.findings],
            ["B000001", "B000001", "B000002", "B000003"],
        )
        self.assertEqual(
            [finding.metadata["observation"]["type"] for finding in result.findings],
            ["amazon_serp", "amazon_paid", "amazon_serp", "amazon_paid"],
        )
        ordinals = [(finding.metadata["result_ordinal"], finding.metadata["item_ordinal"]) for finding in result.findings]
        self.assertEqual(ordinals, [(0, 0), (0, 2), (0, 4), (1, 0)])

    def test_lossless_mapping_and_provider_null_absence_are_preserved(self):
        task, acquisition, _ = self.configured()
        result = self.direct_result(acquisition, task)
        first = result.findings[0]
        observation = first.metadata["observation"]
        self.assertEqual(observation["rank_group"], 1)
        self.assertEqual(observation["rank_absolute"], 1)
        self.assertEqual(observation["domain"], "amazon.com")
        self.assertEqual(observation["title"], "Wireless Headphones")
        self.assertEqual(observation["url"], "https://www.amazon.com/dp/B000001")
        self.assertEqual(observation["image_url"], "https://images.example/B000001.jpg")
        self.assertEqual(observation["bought_past_month"], 1000)
        self.assertIsNone(observation["price_from"])
        self.assertEqual(observation["currency"], "USD")
        self.assertEqual(observation["rating"]["value"], 4.5)
        self.assertEqual(observation["rating"]["votes_count"], 120)
        self.assertEqual(observation["special_offers"], ("Deal",))
        self.assertEqual(observation["delivery"]["tag"], "FREE delivery")
        self.assertEqual(observation["labels"], ("choice",))
        self.assertNotIn("is_paid", repr(first))
        second_observation = result.findings[2].metadata["observation"]
        self.assertNotIn("rating", second_observation)
        self.assertNotIn("price_from", second_observation)
        self.assertNotIn("Unknown Evidence", repr(result))
        self.assertNotIn("demand", first.content.lower())

    def test_known_non_listing_containers_are_not_recursively_extracted_and_unknown_fails_closed(self):
        payload = self.fixture()
        payload["tasks"][0]["result"][0]["items"] = [
            {"type": "editorial_recommendations", "products": [{"type": "amazon_serp", "data_asin": "NESTED"}]},
            {"type": "top_rated_from_our_brands", "products": [{"type": "amazon_paid", "data_asin": "NESTED2"}]},
            {"type": "related_searches", "products": [{"type": "amazon_serp", "data_asin": "NESTED3"}]},
        ]
        payload["tasks"][0]["result"][0]["items_count"] = 3
        payload["tasks"][0]["result"][1]["items"] = []
        payload["tasks"][0]["result"][1]["items_count"] = 0
        task, acquisition, _ = self.configured(payload=payload)
        result = self.direct_result(acquisition, task)
        self.assertEqual(result.findings, ())

        unknown = copy.deepcopy(payload)
        unknown["tasks"][0]["result"][0]["items"] = [{"type": "future_unknown_container", "products": []}]
        task, acquisition, _ = self.configured(payload=unknown)
        with self.assertRaises(self.provider.DataForSEOProtocolError):
            acquisition(task)

    def test_replay_identity_provenance_source_and_time_are_deterministic(self):
        task_a, first, _ = self.configured(task=self.task(task_id="same-task"))
        task_b, second, _ = self.configured(task=self.task(task_id="same-task"))
        first_result = first(task_a)
        second_result = second(task_b)
        self.assertEqual(first_result, second_result)
        self.assertEqual(
            [finding.finding_id for finding in first_result.findings],
            ["same-task:amazon_products_live:0:0", "same-task:amazon_products_live:0:2", "same-task:amazon_products_live:0:4", "same-task:amazon_products_live:1:0"],
        )
        first_finding = first_result.findings[0]
        self.assertEqual(first_finding.source.provider, "DataForSEO")
        self.assertEqual(first_finding.source.source_type, "amazon_products_live")
        self.assertEqual(first_finding.source.reference, "https://www.amazon.com/s?k=wireless+headphones")
        self.assertEqual(first_finding.observed_at, "2026-08-24T08:20:30Z")
        self.assertEqual(first_finding.metadata["provider"], "DataForSEO")
        self.assertEqual(first_finding.metadata["operation"], "amazon_products_live")
        self.assertEqual(first_finding.metadata["endpoint"], self.provider.AMAZON_PRODUCTS_ENDPOINT)
        self.assertEqual(first_finding.metadata["task_id"], "33333333-3333-4333-8333-333333333333")
        self.assertEqual(first_finding.metadata["request"]["request_context"], "candidate-42")
        self.assertEqual(first_finding.metadata["request"]["location_code"], 2840)
        self.assertEqual(first_finding.metadata["request"]["language_code"], "en")
        self.assertEqual(first_finding.metadata["provider_rank"], 1)
        self.assertEqual(first_finding.metadata["amazon_domain"], "amazon.com")
        self.assertEqual(first_finding.metadata["result_reference"], first_finding.source.reference)
        source = inspect.getsource(self.provider)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("uuid", source.lower())

    def test_multiple_results_use_each_provider_time_and_stable_fallback_reference(self):
        payload = self.fixture()
        for result in payload["tasks"][0]["result"]:
            result.pop("check_url", None)
        payload["tasks"][0]["result"][1]["datetime"] = "2026-08-25T00:00:00.123456Z"
        task, acquisition, _ = self.configured(payload=payload)
        result = self.direct_result(acquisition, task)
        self.assertEqual(result.findings[0].observed_at, "2026-08-24T08:20:30Z")
        self.assertEqual(result.findings[-1].observed_at, "2026-08-25T00:00:00Z")
        self.assertTrue(result.findings[0].source.reference.startswith("dataforseo:/v3/merchant/amazon/products/live/advanced:"))
        self.assertEqual(result.findings[0].source.reference, result.findings[1].source.reference)

    def test_protocol_failures_are_atomic_across_envelope_task_result_time_url_and_items(self):
        mutations = []
        payload = self.fixture()
        malformed_json = self.provider.DataForSEOHTTPResponse(200, "not-json")
        mutations.append(("json", malformed_json))
        for label, mutate in (
            ("envelope", lambda value: value.pop("tasks")),
            ("task_count", lambda value: value.__setitem__("tasks_count", 2)),
            ("path", lambda value: value["tasks"][0].__setitem__("path", ["v3", "wrong"])),
            ("task_data_missing", lambda value: value["tasks"][0]["data"].pop("depth")),
            ("task_data_mismatch", lambda value: value["tasks"][0]["data"].__setitem__("depth", 101)),
            ("result", lambda value: value["tasks"][0]["result"].__setitem__(0, {"items": []})),
            ("later_result", lambda value: value["tasks"][0]["result"].__setitem__(1, {"keyword": "wireless headphones", "type": "organic", "datetime": "bad-time", "items_count": 0, "items": []})),
            ("datetime", lambda value: value["tasks"][0]["result"][0].__setitem__("datetime", "bad-time")),
            ("check_url", lambda value: value["tasks"][0]["result"][0].__setitem__("check_url", 1)),
            ("items", lambda value: value["tasks"][0]["result"][0].__setitem__("items", {})),
            ("later_item", lambda value: value["tasks"][0]["result"][0]["items"].__setitem__(4, {"type": "amazon_serp", "data_asin": "bad"})),
            ("unknown_item", lambda value: value["tasks"][0]["result"][0]["items"].__setitem__(0, {"type": "future_unknown"})),
        ):
            changed = copy.deepcopy(payload)
            mutate(changed)
            mutations.append((label, self.response(changed)))
        for label, response in mutations:
            with self.subTest(label=label):
                task = self.task(task_id="malformed-" + label)
                request = self.request()
                binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("MARKETPLACE"), request)
                calls = []
                acquisition = self.provider.create_dataforseo_marketplace_acquisition(
                    resolve_binding=lambda current, binding=binding: binding,
                    login=SECRET_LOGIN,
                    password=SECRET_PASSWORD,
                    transport=lambda wire, headers, response=response: calls.append(wire) or response,
                )
                with self.assertRaises(self.provider.DataForSEOProtocolError):
                    acquisition(task)
                self.assertEqual(len(calls), 1)

    def test_empty_and_provider_status_outcomes_reuse_existing_semantics(self):
        top_level_40102 = self.fixture()
        top_level_40102["status_code"] = 40102
        top_level_40102["tasks"] = []
        top_level_40102["tasks_count"] = 0
        task, acquisition, _ = self.configured(payload=top_level_40102)
        result = acquisition(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(result.findings, ())

        empty = self.fixture()
        empty["tasks"][0]["result"][0]["items"] = []
        empty["tasks"][0]["result"][0]["items_count"] = 0
        empty["tasks"][0]["result"][1]["items"] = []
        empty["tasks"][0]["result"][1]["items_count"] = 0
        task, acquisition, _ = self.configured(payload=empty)
        self.assertEqual(acquisition(task).findings, ())

        failure = self.fixture()
        failure["status_code"] = 40501
        failure["tasks"][0]["status_code"] = 40501
        failure["tasks"][0]["result_count"] = 0
        failure["tasks"][0].pop("result")
        task, acquisition, _ = self.configured(payload=failure)
        self.assertEqual(acquisition(task).status, self.orchestration.TaskStatus("FAILED"))

        task, acquisition, _ = self.configured(status=503)
        self.assertEqual(acquisition(task).status, self.orchestration.TaskStatus("FAILED"))


class OutcomeAndOrchestrationTests(MarketplaceTestBase):
    def test_findings_stop_at_raw_finding_and_normalize_only_through_orchestration(self):
        task, acquisition, _ = self.configured()
        normalized = []
        result = self.orchestration.run_research(
            self.orchestration.ResearchObjective("objective", "objective"),
            lambda objective: self.orchestration.ResearchPlan("objective", (task,)),
            self.adapters.ResearchSourceAdapters(marketplace=acquisition),
            lambda current, finding, evidence_id: normalized.append(finding) or self.evidence_record(evidence_id, finding),
        )
        self.assertEqual(result.status, self.orchestration.RunStatus("COMPLETE"))
        self.assertEqual([finding.finding_id for finding in normalized], [finding.finding_id for finding in acquisition(task).findings])
        self.assertEqual([item.id.value for item in result.evidence], ["E001", "E002", "E003", "E004"])
        source = inspect.getsource(self.provider)
        for forbidden in ("class Evidence", "EvidenceId", "Evidence(", "UnitEconomics", "RiskGate", "Scoring", "RedTeam", "Report"):
            self.assertNotIn(forbidden, source)

    def test_failed_exception_empty_and_independent_tasks_keep_existing_classification(self):
        failed_task = self.task("failed")
        exception_task = self.task("exception")
        empty_task = self.task("empty")
        valid_task = self.task("valid")
        valid_payload = self.fixture()
        empty_payload = copy.deepcopy(valid_payload)
        empty_payload["tasks"][0]["result"][0]["items"] = []
        empty_payload["tasks"][0]["result"][0]["items_count"] = 0
        empty_payload["tasks"][0]["result"][1]["items"] = []
        empty_payload["tasks"][0]["result"][1]["items_count"] = 0
        failure_payload = copy.deepcopy(valid_payload)
        failure_payload["status_code"] = 40501
        failure_payload["tasks"][0]["status_code"] = 40501
        failure_payload["tasks"][0]["result_count"] = 0
        failure_payload["tasks"][0].pop("result")
        providers = {}
        for current, payload in ((failed_task, failure_payload), (empty_task, empty_payload), (valid_task, valid_payload)):
            _, providers[current.task_id], _ = self.configured(task=current, payload=payload)

        def acquire(current):
            if current == exception_task:
                raise self.provider.DataForSEOProtocolError("malformed provider response")
            return providers[current.task_id](current)

        result = self.orchestration.run_research(
            self.orchestration.ResearchObjective("objective", "objective"),
            lambda objective: self.orchestration.ResearchPlan("objective", (failed_task, exception_task, empty_task, valid_task)),
            acquire,
            lambda current, finding, evidence_id: self.evidence_record(evidence_id, finding),
        )
        self.assertEqual([str(failure.reason) for failure in result.failures], ["ACQUISITION_FAILED", "ACQUISITION_EXCEPTION"])
        self.assertEqual(result.task_results[2].status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual([item.id.value for item in result.evidence], ["E001", "E002", "E003", "E004"])

    def test_default_execution_is_offline_even_with_credential_like_environment(self):
        previous = {key: os.environ.get(key) for key in ("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD", "DATAFORSEO_LIVE_TEST")}
        try:
            os.environ["DATAFORSEO_LOGIN"] = SECRET_LOGIN
            os.environ["DATAFORSEO_PASSWORD"] = SECRET_PASSWORD
            os.environ.pop("DATAFORSEO_LIVE_TEST", None)
            self.assertFalse(hasattr(self.provider, "run_live_test"))
            task, acquisition, calls = self.configured()
            self.assertEqual(calls, [])
            self.assertFalse(inspect.iscoroutinefunction(acquisition))
            self.assertEqual(acquisition(task).status, self.orchestration.TaskStatus("SUCCESS"))
            self.assertEqual(len(calls), 1)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
