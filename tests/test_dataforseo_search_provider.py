"""ECO-42 requirement-to-test trace.

The test classes intentionally map the Change scenarios without adding a new
acquisition contract:

* ArchitectureTests: 2.2, 5.3, 5.4, 5.5 and the modified adapter capability.
* ConfigurationAndTransportTests: 2.3, 2.4, 2.7, 3.3, 3.4, 5.4.
* RequestValidationTests: 2.5, 2.6, 3.5, 3.6.
* ProtocolOutcomeTests: 3.1 through 3.6 and validate-before-map atomicity.
* MappingTests: 4.1 through 4.6 and cross-operation replay/time/provenance.
* OrchestrationTests: 5.1 through 5.3 and ECO-13 failure ownership.

The committed fixtures are provider-like, deterministic, and secret-free.
No live test surface is defined; ordinary discovery therefore cannot charge an
account. The Apply allowlist is the two root DataForSEO modules, this focused
test module, its JSON fixtures, and the narrow SKILL.md capability wording.
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
FIXED_TIME = "2026-08-24T00:00:00Z"
SECRET_LOGIN = "login-sentinel-never-public"
SECRET_PASSWORD = "password-sentinel-never-public"


@dataclass(frozen=True)
class UnsupportedRequest:
    value: str


class DataForSEOTestBase(unittest.TestCase):
    def setUp(self):
        try:
            self.provider = importlib.import_module("dataforseo_search_provider")
        except ModuleNotFoundError:
            self.fail("DataForSEO SEARCH provider has not been implemented")
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.adapters = importlib.import_module("product_research.research_adapters")
        self.evidence = importlib.import_module("product_research.evidence")
        self.policy = importlib.import_module("product_research.evidence_policy")

    def task(self, task_id="search-01", family="SEARCH", question="declared question", intent="declared intent"):
        return self.orchestration.ResearchTask(
            task_id=task_id,
            research_question=question,
            source_family=self.orchestration.SourceFamily(family),
            query_intent=intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=True,
        )

    def request(self, kind="ads", **overrides):
        values = {
            "ads": dict(keywords=("blue shoes", "running shoes"), location_code=2840, language_code="en"),
            "trends": dict(
                keywords=("blue shoes", "running shoes"),
                location_name="United States",
                language_code="en",
                date_from="2026-01-01",
                date_to="2026-08-01",
                item_types=("google_trends_graph", "google_trends_map"),
            ),
            "amazon": dict(keywords=("blue shoes", "running shoes"), location_code=2840, language_code="en"),
        }[kind]
        values.update(overrides)
        cls = {
            "ads": self.provider.GoogleAdsSearchVolumeRequest,
            "trends": self.provider.GoogleTrendsExploreRequest,
            "amazon": self.provider.AmazonBulkSearchVolumeRequest,
        }[kind]
        return cls(**values)

    def fixture(self, name):
        return json.loads((FIXTURES / name).read_text())

    def response(self, payload, status=200):
        return self.provider.DataForSEOHTTPResponse(status_code=status, body=json.dumps(payload))

    def configured(self, task, request, response=None, *, transport=None, clock=lambda: FIXED_TIME):
        calls = []
        binding = self.provider.ProviderBinding(
            task_id=task.task_id,
            source_family=self.orchestration.SourceFamily("SEARCH"),
            request=request,
        )
        if response is None:
            response = self.response(self.fixture("google_ads_success.json"))
        if transport is None:
            def transport(wire_request, headers):
                calls.append((wire_request, headers))
                return response
        acquisition = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=transport,
            clock=clock,
        )
        return acquisition, calls

    def acquisition(self, task, request, fixture_name):
        return self.configured(task, request, self.response(self.fixture(fixture_name)))


class ArchitectureTests(DataForSEOTestBase):
    def test_concrete_layer_is_outside_core_and_provider_neutral_module_is_unchanged(self):
        source = pathlib.Path(importlib.util.find_spec("product_research_providers").origin).read_text()
        self.assertNotIn("dataforseo", source.lower())
        package_root = ROOT / "product_research"
        for path in package_root.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any("dataforseo" in alias.name.lower() for alias in node.names), path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("dataforseo", (node.module or "").lower(), path.name)

    def test_provider_callable_installs_directly_in_search_slot(self):
        task = self.task()
        acquisition, _ = self.acquisition(task, self.request("ads"), "google_ads_success.json")
        result = self.adapters.ResearchSourceAdapters(search=acquisition)(task)
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))

    def test_public_surface_has_no_second_result_taxonomy_or_later_capability(self):
        source = inspect.getsource(self.provider).lower()
        for token in ("class evidence", "evidenceid", "marketplace", "amazonproduct", "retry", "backoff", "async", "cache", "registry", "poll"):
            self.assertNotIn(token, source)
        self.assertFalse(hasattr(self.provider, "ProviderRegistry"))
        self.assertFalse(hasattr(self.provider, "AmazonProductRequest"))

    def test_exact_request_type_selects_only_its_endpoint_and_one_task_payload(self):
        expected = {
            "ads": "/v3/keywords_data/google_ads/search_volume/live",
            "trends": "/v3/keywords_data/google_trends/explore/live",
            "amazon": "/v3/dataforseo_labs/amazon/bulk_search_volume/live",
        }
        for kind, endpoint in expected.items():
            with self.subTest(kind=kind):
                task = self.task(task_id="dispatch-" + kind)
                request = self.request(kind)
                fixture = {"ads": "google_ads_success.json", "trends": "google_trends_success.json", "amazon": "amazon_success.json"}[kind]
                acquisition, calls = self.acquisition(task, request, fixture)
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
                self.assertEqual(len(calls), 1)
                wire, headers = calls[0]
                self.assertEqual(wire.endpoint, endpoint)
                self.assertEqual(len(wire.payload), 1)
                self.assertEqual(tuple(wire.payload[0]["keywords"]), request.keywords)
                self.assertNotIn("Authorization", repr(wire))

    def test_family_mismatch_and_unsupported_exact_request_fail_before_transport(self):
        task = self.task()
        request = self.request("ads")
        binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("SEARCH"), UnsupportedRequest("later"))
        calls = []
        acquisition = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda *args: calls.append(args),
        )
        result = acquisition(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
        self.assertEqual(calls, [])

        mismatched_task = self.task(family="MARKETPLACE")
        mismatch_binding = self.provider.ProviderBinding(mismatched_task.task_id, self.orchestration.SourceFamily("SEARCH"), request)
        mismatch = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: mismatch_binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda *args: calls.append(args),
        )
        result = mismatch(mismatched_task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
        self.assertEqual(calls, [])


class ConfigurationAndTransportTests(DataForSEOTestBase):
    def test_missing_empty_and_wrong_type_credentials_fail_before_transport(self):
        for login, password in ((None, "password"), ("login", None), ("", "password"), ("login", ""), (1, "password"), ("login", object())):
            with self.subTest(login=repr(login), password=repr(password)):
                calls = []
                with self.assertRaises(self.provider.ProviderConfigurationError) as raised:
                    self.provider.create_dataforseo_search_acquisition(
                        resolve_binding=lambda task: None,
                        login=login,
                        password=password,
                        transport=lambda *args: calls.append(args),
                    )
                self.assertNotIn("password", str(raised.exception).lower())
                self.assertEqual(calls, [])

    def test_environment_configuration_is_optional_and_redacted(self):
        config = self.provider.DataForSEOConfiguration.from_environment({"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD})
        self.assertNotIn(SECRET_LOGIN, repr(config))
        self.assertNotIn(SECRET_PASSWORD, str(config))
        with self.assertRaises(self.provider.ProviderConfigurationError):
            self.provider.DataForSEOConfiguration.from_environment({"DATAFORSEO_LOGIN": SECRET_LOGIN})

    def test_remote_http_and_provider_auth_failures_are_failed_after_one_send(self):
        task = self.task()
        request = self.request("ads")
        for status, payload in ((401, {}), (402, {}), (503, {}), (200, dict(self.fixture("google_ads_success.json"), status_code=40100))):
            with self.subTest(status=status):
                calls = []
                def transport(wire, headers):
                    calls.append((wire, headers))
                    return self.response(payload, status=status)
                acquisition, _ = self.configured(task, request, transport=transport)
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
                self.assertEqual(result.findings, ())
                self.assertEqual(len(calls), 1)

    def test_basic_auth_is_added_only_inside_actual_send_boundary(self):
        task = self.task()
        request = self.request("ads")
        acquisition, calls = self.acquisition(task, request, "google_ads_success.json")
        self.assertNotIn("Authorization", repr(request))
        self.assertNotIn(SECRET_LOGIN, repr(request))
        self.assertNotIn(SECRET_PASSWORD, repr(request))
        result = acquisition(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(len(calls), 1)
        wire, headers = calls[0]
        self.assertNotIn(SECRET_LOGIN, repr(wire))
        self.assertNotIn(SECRET_PASSWORD, repr(wire))
        self.assertTrue(headers["Authorization"].startswith("Basic "))
        self.assertNotIn("Authorization", repr(wire))

    def test_construction_is_io_free_synchronous_and_at_most_once(self):
        task = self.task()
        calls = []
        request = self.request("ads")
        binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("SEARCH"), request)
        acquisition = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda wire, headers: calls.append((wire, headers)) or self.response(self.fixture("google_ads_success.json")),
            clock=lambda: FIXED_TIME,
        )
        self.assertEqual(calls, [])
        self.assertFalse(inspect.iscoroutinefunction(acquisition))
        first = acquisition(task)
        self.assertEqual(first.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(len(calls), 1)

    def test_transport_exception_identity_crosses_without_retry(self):
        task = self.task()
        request = self.request("ads")
        error = TimeoutError("read timeout")
        calls = []
        def transport(wire, headers):
            calls.append(wire)
            raise error
        acquisition, _ = self.configured(task, request, transport=transport)
        with self.assertRaises(TimeoutError) as raised:
            acquisition(task)
        self.assertIs(raised.exception, error)
        self.assertEqual(len(calls), 1)

    def test_public_values_results_errors_and_fixtures_do_not_contain_credentials(self):
        task = self.task()
        acquisition, calls = self.acquisition(task, self.request("ads"), "google_ads_success.json")
        public = " ".join((repr(acquisition), str(acquisition), repr(self.request("ads")), repr(self.provider.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD))))
        result = acquisition(task)
        public += " " + repr(result) + " " + repr(result.findings)
        for value in (SECRET_LOGIN, SECRET_PASSWORD):
            self.assertNotIn(value, public)
        for path in FIXTURES.glob("*.json"):
            self.assertNotIn(SECRET_LOGIN, path.read_text())
            self.assertNotIn(SECRET_PASSWORD, path.read_text())


class RequestValidationTests(DataForSEOTestBase):
    def test_requests_are_frozen_exactly_three_and_store_immutable_ordered_keywords(self):
        requests = (self.request("ads"), self.request("trends"), self.request("amazon"))
        self.assertEqual(len({type(item) for item in requests}), 3)
        for request in requests:
            self.assertTrue(dataclasses.is_dataclass(request))
            self.assertTrue(type(request).__dataclass_params__.frozen)
            self.assertIsInstance(request.keywords, tuple)
            with self.assertRaises(dataclasses.FrozenInstanceError):
                request.keywords = ()

    def test_keyword_bounds_and_malformed_values_fail_without_transport(self):
        cases = (
            ("ads", (), 1001),
            ("trends", (), 6),
            ("amazon", (), 1001),
        )
        for kind, empty, too_many in cases:
            cls = {"ads": self.provider.GoogleAdsSearchVolumeRequest, "trends": self.provider.GoogleTrendsExploreRequest, "amazon": self.provider.AmazonBulkSearchVolumeRequest}[kind]
            base = {"ads": {"location_code": 2840, "language_code": "en"}, "trends": {}, "amazon": {"location_code": 2840, "language_code": "en"}}[kind]
            with self.subTest(kind=kind, case="empty"):
                with self.assertRaises((TypeError, ValueError)):
                    cls(keywords=empty, **base)
            with self.subTest(kind=kind, case="too_many"):
                with self.assertRaises((TypeError, ValueError)):
                    cls(keywords=tuple("k%04d" % i for i in range(too_many)), **base)
            with self.subTest(kind=kind, case="malformed"):
                with self.assertRaises((TypeError, ValueError)):
                    cls(keywords=("",), **base)
                with self.assertRaises((TypeError, ValueError)):
                    cls(keywords=(1,), **base)

    def test_location_and_language_name_code_shapes_and_amazon_requirements(self):
        for cls, base in (
            (self.provider.GoogleAdsSearchVolumeRequest, {"keywords": ("term",)}),
            (self.provider.GoogleTrendsExploreRequest, {"keywords": ("term",)}),
        ):
            with self.subTest(cls=cls.__name__):
                cls(**base, location_name="United States")
                cls(**base, location_code=2840)
                with self.assertRaises((TypeError, ValueError)):
                    cls(**base, location_name="United States", location_code=2840, language_name="English", language_code="en")
                with self.assertRaises((TypeError, ValueError)):
                    cls(**base, location_code=True)
        with self.assertRaises((TypeError, ValueError)):
            self.provider.AmazonBulkSearchVolumeRequest(keywords=("term",), language_code="en")
        with self.assertRaises((TypeError, ValueError)):
            self.provider.AmazonBulkSearchVolumeRequest(keywords=("term",), location_code=2840)
        with self.assertRaises((TypeError, ValueError)):
            self.provider.AmazonBulkSearchVolumeRequest(keywords=("term",), location_name="United States", location_code=2840, language_code="en")

    def test_closed_options_and_trends_date_ranges_are_validated(self):
        self.request("ads", sort_by="search_volume", search_partners=True, include_adult_keywords=True)
        self.request("trends", type="youtube", category_code=3, item_types=("google_trends_graph",), time_range=None)
        with self.assertRaises((TypeError, ValueError)):
            self.request("ads", sort_by="not-supported")
        with self.assertRaises((TypeError, ValueError)):
            self.request("trends", type="not-supported")
        with self.assertRaises((TypeError, ValueError)):
            self.request("trends", item_types=("not-supported",))
        with self.assertRaises((TypeError, ValueError)):
            self.request("trends", date_from="2026-02-01", date_to="2026-01-01")
        with self.assertRaises((TypeError, ValueError)):
            self.request("trends", date_from="bad-date")
        with self.assertRaises((TypeError, ValueError)):
            self.request("trends", date_from="2026-01-01", time_range="past_12_months")

    def test_trends_related_topic_and_query_discovery_are_out_of_scope(self):
        for item_type in ("google_trends_topics_list", "google_trends_queries_list"):
            with self.subTest(item_type=item_type):
                with self.assertRaises((TypeError, ValueError)):
                    self.request("trends", keywords=("blue shoes",), item_types=(item_type,))

    def test_invalid_forged_request_fails_before_transport_and_text_never_routes(self):
        task_a = self.task(question="Google Ads question", intent="ads intent")
        task_b = self.task(question="completely different", intent="trend intent")
        request = self.request("ads")
        provider_a, calls_a = self.configured(task_a, request, self.response(self.fixture("google_ads_success.json")))
        binding = self.provider.ProviderBinding(task_a.task_id, self.orchestration.SourceFamily("SEARCH"), request)
        provider_b = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda wire, headers: self.response(self.fixture("google_ads_success.json")),
            clock=lambda: FIXED_TIME,
        )
        self.assertEqual(provider_a(task_a).findings, provider_b(task_b).findings)
        corrupted = object.__new__(type(request))
        for field in dataclasses.fields(request):
            object.__setattr__(corrupted, field.name, getattr(request, field.name))
        object.__setattr__(corrupted, "keywords", ())
        bad_binding = self.provider.ProviderBinding(task_a.task_id, self.orchestration.SourceFamily("SEARCH"), corrupted)
        calls = []
        bad = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: bad_binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda *args: calls.append(args),
        )
        with self.assertRaises((TypeError, ValueError)):
            bad(task_a)
        self.assertEqual(calls, [])


class ProtocolOutcomeTests(DataForSEOTestBase):
    def provider_for(self, kind, payload, *, status=200, task_id=None):
        task = self.task(task_id or ("task-" + kind))
        request = self.request(kind)
        binding = self.provider.ProviderBinding(task.task_id, self.orchestration.SourceFamily("SEARCH"), request)
        calls = []
        acquisition = self.provider.create_dataforseo_search_acquisition(
            resolve_binding=lambda current: binding,
            login=SECRET_LOGIN,
            password=SECRET_PASSWORD,
            transport=lambda wire, headers: calls.append((wire, headers)) or self.response(payload, status),
            clock=lambda: FIXED_TIME,
        )
        return task, acquisition, calls

    def test_success_and_semantically_applicable_40102_are_success_empty_at_top_and_task(self):
        for kind, fixture in (("ads", "google_ads_success.json"), ("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            base = self.fixture(fixture)
            for position in ("top", "task"):
                payload = copy.deepcopy(base)
                if position == "top":
                    payload["status_code"] = 40102
                    payload["tasks"] = []
                    payload["tasks_count"] = 0
                else:
                    payload["tasks"][0]["status_code"] = 40102
                    payload["tasks"][0].pop("result", None)
                    payload["tasks"][0]["result_count"] = 0
                task, acquisition, calls = self.provider_for(kind, payload)
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"), (kind, position))
                self.assertEqual(result.findings, ())
                self.assertEqual(len(calls), 1)

    def test_successful_empty_operation_containers_are_success_empty(self):
        for kind, fixture in (("ads", "google_ads_success.json"), ("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            payload = self.fixture(fixture)
            payload["tasks"][0]["result"] = []
            payload["tasks"][0]["result_count"] = 0
            task, acquisition, _ = self.provider_for(kind, payload)
            result = acquisition(task)
            self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"), kind)
            self.assertEqual(result.findings, ())

    def test_provider_http_and_structurally_valid_non_success_statuses_fail_closed(self):
        status_codes = (401, 402, 404, 429, 500, 503, 504)
        for kind, fixture in (("ads", "google_ads_success.json"), ("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            for http_status in status_codes:
                task, acquisition, calls = self.provider_for(kind, {}, status=http_status)
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"), (kind, http_status))
                self.assertEqual(result.findings, ())
                self.assertEqual(len(calls), 1)
            for code in (40100, 40200, 40202, 40203, 40103, 50400, 59999):
                payload = self.fixture(fixture)
                payload["status_code"] = code
                payload["tasks"] = []
                payload["tasks_count"] = 0
                task, acquisition, calls = self.provider_for(kind, payload)
                result = acquisition(task)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"), (kind, code))
                self.assertEqual(result.findings, ())
                self.assertEqual(len(calls), 1)

    def test_invalid_json_envelopes_and_operation_shapes_raise_protocol_error_atomically(self):
        malformed = [
            "not-json",
            {},
            {"status_code": 20000, "status_message": "Ok", "version": "v", "time": "0", "cost": 0, "tasks_count": 1, "tasks_error": 0, "tasks": []},
        ]
        for payload in malformed:
            task, acquisition, _ = self.provider_for("ads", payload)
            with self.assertRaises(self.provider.DataForSEOProtocolError):
                acquisition(task)

    def test_malformed_provider_failure_and_impossible_no_result_task_raise_protocol_error(self):
        malformed_failure = self.fixture("google_ads_success.json")
        malformed_failure["status_code"] = 40100
        malformed_failure["tasks"][0] = {"status_code": "not-an-integer"}
        task, acquisition, _ = self.provider_for("ads", malformed_failure)
        with self.assertRaises(self.provider.DataForSEOProtocolError):
            acquisition(task)

        impossible_no_result = self.fixture("google_ads_success.json")
        impossible_no_result["tasks"][0]["status_code"] = 40102
        impossible_no_result["tasks"][0]["result_count"] = 1
        impossible_no_result["tasks"][0].pop("result")
        task, acquisition, _ = self.provider_for("ads", impossible_no_result)
        with self.assertRaises(self.provider.DataForSEOProtocolError):
            acquisition(task)
        for kind, fixture, key in (("ads", "google_ads_success.json", "result"), ("trends", "google_trends_success.json", "items"), ("amazon", "amazon_success.json", "items")):
            payload = self.fixture(fixture)
            if key == "result":
                payload["tasks"][0]["result"][0]["monthly_searches"] = "not-a-list"
            else:
                payload["tasks"][0]["result"][0][key] = "not-a-list"
            task, acquisition, _ = self.provider_for(kind, payload)
            with self.assertRaises(self.provider.DataForSEOProtocolError):
                acquisition(task)

    def test_later_malformed_item_cannot_leak_earlier_finding(self):
        payload = self.fixture("google_ads_success.json")
        payload["tasks"][0]["result"][1]["keyword"] = 123
        task, acquisition, _ = self.provider_for("ads", payload)
        with self.assertRaises(self.provider.DataForSEOProtocolError):
            acquisition(task)


class MappingTests(DataForSEOTestBase):
    def test_google_ads_maps_ordered_lossless_metrics_and_nulls(self):
        task = self.task()
        acquisition, _ = self.acquisition(task, self.request("ads"), "google_ads_success.json")
        result = acquisition(task)
        self.assertEqual([finding.metadata["ordinal"] for finding in result.findings], [0, 1])
        first, second = result.findings
        self.assertEqual(first.metadata["observation"]["keyword"], "blue shoes")
        self.assertEqual(first.metadata["observation"]["monthly_searches"][1]["month"], 2)
        self.assertIsNone(second.metadata["observation"]["search_volume"])
        self.assertNotIn("score", first.content.lower())
        self.assertEqual(first.observed_at, FIXED_TIME)

    def test_google_trends_maps_items_and_time_series_without_interpretation(self):
        task = self.task()
        acquisition, _ = self.acquisition(task, self.request("trends"), "google_trends_success.json")
        result = acquisition(task)
        self.assertEqual(len(result.findings), 2)
        first = result.findings[0]
        self.assertEqual(first.source.reference, "https://trends.google.com/trends/explore?geo=US&q=blue%20shoes")
        self.assertEqual(first.observed_at, "2026-08-20T18:40:17Z")
        self.assertEqual(first.metadata["observation"]["data"][1]["missing_data"], True)
        self.assertEqual(first.metadata["observation"]["data"][0]["values"], (54, 38))
        for forbidden in ("growth", "momentum", "seasonality", "hype", "demand_score"):
            self.assertNotIn(forbidden, first.content.lower())

    def test_google_trends_map_preserves_provider_geographic_shape(self):
        payload = self.fixture("google_trends_success.json")
        payload["tasks"][0]["result"][0]["items_count"] = 1
        payload["tasks"][0]["result"][0]["items"] = [
            {
                "position": 1,
                "type": "google_trends_map",
                "title": "Interest by subregion",
                "keywords": ["blue shoes", "running shoes"],
                "data": [
                    {"geo_id": "US-CA", "geo_name": "California", "values": [70, 30], "max_value_index": 0},
                    {"geo_id": "US-NV", "geo_name": "Nevada", "values": [None, 44], "max_value_index": 1},
                ],
            }
        ]
        task = self.task(task_id="trends-map")
        request = self.request("trends", item_types=("google_trends_map",))
        acquisition, _ = self.configured(task, request, self.response(payload))
        finding = acquisition(task).findings[0]
        self.assertEqual(finding.metadata["observation"]["data"][0]["geo_id"], "US-CA")
        self.assertEqual(finding.metadata["observation"]["data"][1]["values"], (None, 44))

    def test_amazon_maps_search_only_and_preserves_missing_metric(self):
        task = self.task()
        acquisition, _ = self.acquisition(task, self.request("amazon"), "amazon_success.json")
        result = acquisition(task)
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.findings[0].metadata["observation"]["keyword"], "blue shoes")
        self.assertNotIn("marketplace", repr(result).lower())
        self.assertNotIn("search_volume", result.findings[1].metadata["observation"])

    def test_nested_result_and_item_ordinals_are_preserved_in_provenance(self):
        for kind, fixture in (("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            task = self.task(task_id="nested-" + kind)
            acquisition, _ = self.acquisition(task, self.request(kind), fixture)
            result = acquisition(task)
            with self.subTest(kind=kind):
                self.assertEqual(
                    [finding.metadata["result_context"]["result_ordinal"] for finding in result.findings],
                    [0, 0],
                )
                self.assertEqual(
                    [finding.metadata["result_context"]["item_ordinal"] for finding in result.findings],
                    [0, 1],
                )

    def test_replay_identities_provenance_and_times_are_deterministic(self):
        for kind, fixture in (("ads", "google_ads_success.json"), ("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            task_a = self.task(task_id="same-task")
            task_b = self.task(task_id="same-task")
            acquisition_a, _ = self.acquisition(task_a, self.request(kind), fixture)
            acquisition_b, _ = self.acquisition(task_b, self.request(kind), fixture)
            first, second = acquisition_a(task_a), acquisition_b(task_b)
            self.assertEqual(first, second, kind)
            self.assertTrue(all("DataForSEO" == finding.source.provider for finding in first.findings))
            self.assertTrue(all("credential" not in repr(finding).lower() for finding in first.findings))
            self.assertTrue(all(finding.finding_id.startswith("same-task:") for finding in first.findings))

    def test_trends_rejects_malformed_provider_time_and_ads_amazon_use_one_injected_time(self):
        payload = self.fixture("google_trends_success.json")
        payload["tasks"][0]["result"][0]["datetime"] = "not-a-time"
        task, acquisition, _ = self.provider_for_payload("trends", payload)
        with self.assertRaises(self.provider.DataForSEOProtocolError):
            acquisition(task)
        calls = []
        def clock():
            calls.append(True)
            return FIXED_TIME
        task = self.task()
        acquisition, _ = self.configured(
            task,
            self.request("ads"),
            self.response(self.fixture("google_ads_success.json")),
            clock=clock,
        )
        result = acquisition(task)
        self.assertEqual(result.findings[0].observed_at, FIXED_TIME)

    def provider_for_payload(self, kind, payload):
        task = self.task(task_id="payload-task")
        request = self.request(kind)
        acquisition, calls = self.configured(task, request, self.response(payload))
        return task, acquisition, calls

    def test_factual_outputs_do_not_create_evidence_taxonomy_or_missing_zero(self):
        for kind, fixture in (("ads", "google_ads_success.json"), ("trends", "google_trends_success.json"), ("amazon", "amazon_success.json")):
            task = self.task()
            acquisition, _ = self.acquisition(task, self.request(kind), fixture)
            result = acquisition(task)
            self.assertFalse(any(hasattr(finding, "evidence_id") for finding in result.findings))
            for finding in result.findings:
                text = repr(finding) + finding.content + repr(finding.metadata)
                self.assertNotIn("Unknown Evidence", text)
                self.assertNotIn("Tier", text)
                self.assertNotIn("Confidence", text)
                self.assertNotIn("demand score", text.lower())


class OrchestrationTests(DataForSEOTestBase):
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

    def test_valid_findings_pass_unchanged_and_only_eco13_normalizes(self):
        task = self.task()
        acquisition, _ = self.acquisition(task, self.request("ads"), "google_ads_success.json")
        observed = []
        result = self.orchestration.run_research(
            self.orchestration.ResearchObjective("objective-01", "objective"),
            lambda objective: self.orchestration.ResearchPlan("objective-01", (task,)),
            self.adapters.ResearchSourceAdapters(search=acquisition),
            lambda current, finding, evidence_id: observed.append(finding) or self.evidence_record(evidence_id, finding),
        )
        self.assertEqual(result.status, self.orchestration.RunStatus("COMPLETE"))
        self.assertEqual([finding.finding_id for finding in observed], [finding.finding_id for finding in acquisition(task).findings])
        self.assertEqual([item.id.value for item in result.evidence], ["E001", "E002"])

    def test_provider_failure_exception_empty_success_and_later_valid_task_keep_eco13_ownership(self):
        failed = self.task("failed")
        raised = self.task("raised")
        empty = self.task("empty")
        valid = self.task("valid")
        def make(task, kind, fixture):
            acquisition, _ = self.acquisition(task, self.request(kind), fixture)
            return acquisition
        failed_provider = make(failed, "ads", "google_ads_success.json")
        raised_provider = make(raised, "ads", "google_ads_success.json")
        empty_provider = make(empty, "ads", "google_ads_success.json")
        valid_provider = make(valid, "ads", "google_ads_success.json")
        def acquire(task):
            if task == failed:
                return self.orchestration.AcquisitionResult(task.task_id, self.orchestration.TaskStatus("FAILED"), ())
            if task == raised:
                raise TimeoutError("transport")
            if task == empty:
                return self.orchestration.AcquisitionResult(task.task_id, self.orchestration.TaskStatus("SUCCESS"), ())
            return valid_provider(task)
        result = self.orchestration.run_research(
            self.orchestration.ResearchObjective("objective-01", "objective"),
            lambda objective: self.orchestration.ResearchPlan("objective-01", (failed, raised, empty, valid)),
            acquire,
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding),
        )
        self.assertEqual([str(f.reason) for f in result.failures], ["ACQUISITION_FAILED", "ACQUISITION_EXCEPTION"])
        self.assertEqual([item.id.value for item in result.evidence], ["E001", "E002"])
        self.assertEqual(result.task_results[2].status, self.orchestration.TaskStatus("SUCCESS"))

    def test_default_suite_surface_never_constructs_live_transport_from_credentials_alone(self):
        self.assertFalse(hasattr(self.provider, "run_live_test"))
        self.assertIsNone(os.environ.get("DATAFORSEO_LIVE_TEST"))


if __name__ == "__main__":
    unittest.main()
