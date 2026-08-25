"""ECO-44 requirement-to-test trace.

The tests keep the runtime outside ``product_research`` and exercise only the
existing DataForSEO provider, acquisition, adapter, and orchestration seams.

Trace:
* BindingTests: runtime configuration and exact immutable task-ID lookup.
* CompositionTests: SEARCH/MARKETPLACE family slots, request validation, and
  partial-installation availability semantics.
* SetupSafetyTests: strict flags, shared configuration, environment parsing,
  secret redaction, and network-free construction.
* PassThroughTests: provider result/exception ownership and orchestration
  classification without a runtime wrapper or normalization.
* ArchitectureTests: external dependency direction, offline test surfaces,
  and the narrow documentation boundary.
"""

import ast
import importlib
import json
import pathlib
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "dataforseo"
SECRET_LOGIN = "eco44-login-sentinel-never-public"
SECRET_PASSWORD = "eco44-password-sentinel-never-public"
FIXED_TIME = "2026-08-24T00:00:00Z"


class UnsupportedRequest:
    pass


class RuntimeTestBase(unittest.TestCase):
    def setUp(self):
        self.runtime = importlib.import_module("dataforseo_acquisition_runtime")
        self.search = importlib.import_module("dataforseo_search_provider")
        self.marketplace = importlib.import_module("dataforseo_marketplace_provider")
        self.client = importlib.import_module("dataforseo_client")
        self.providers = importlib.import_module("product_research_providers")
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.policy = importlib.import_module("product_research.evidence_policy")

    def task(self, task_id, family="SEARCH", question="declared question", intent="declared intent"):
        return self.orchestration.ResearchTask(
            task_id=task_id,
            research_question=question,
            source_family=self.orchestration.SourceFamily(family),
            query_intent=intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=True,
        )

    def request(self, kind="ads"):
        if kind == "ads":
            return self.search.GoogleAdsSearchVolumeRequest(
                keywords=("blue shoes",), location_code=2840, language_code="en"
            )
        if kind == "trends":
            return self.search.GoogleTrendsExploreRequest(
                keywords=("blue shoes",),
                location_name="United States",
                language_code="en",
                date_from="2026-01-01",
                date_to="2026-08-01",
                item_types=("google_trends_graph", "google_trends_map"),
            )
        if kind == "amazon":
            return self.search.AmazonBulkSearchVolumeRequest(
                keywords=("blue shoes",), location_code=2840, language_code="en"
            )
        if kind == "products":
            return self.marketplace.AmazonProductsRequest(
                keyword="wireless headphones",
                location_code=2840,
                language_code="en",
                depth=10,
            )
        raise AssertionError(kind)

    def binding(self, task_id, family="SEARCH", kind="ads"):
        request = kind if not isinstance(kind, str) else self.request(kind)
        return self.providers.ProviderBinding(
            task_id=task_id,
            source_family=self.orchestration.SourceFamily(family),
            request=request,
        )

    def configuration(self):
        return self.client.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD)

    def fixture_response(self, module, name, status=200):
        payload = json.loads((FIXTURES / name).read_text())
        return module.DataForSEOHTTPResponse(status_code=status, body=json.dumps(payload))

    def search_transport(self, calls):
        responses = {
            self.search.GOOGLE_ADS_ENDPOINT: self.fixture_response(self.search, "google_ads_success.json"),
            self.search.GOOGLE_TRENDS_ENDPOINT: self.fixture_response(self.search, "google_trends_success.json"),
            self.search.AMAZON_ENDPOINT: self.fixture_response(self.search, "amazon_success.json"),
        }

        def transport(wire, headers):
            calls.append((wire, headers))
            return responses[wire.endpoint]

        return transport

    def marketplace_transport(self, calls):
        def transport(wire, headers):
            calls.append((wire, headers))
            payload = json.loads((FIXTURES / "amazon_products_success.json").read_text())
            payload["tasks"][0]["data"].update(wire.payload[0])
            return self.marketplace.DataForSEOHTTPResponse(200, json.dumps(payload))

        return transport

    def runtime_with_fake_transports(self, bindings, **kwargs):
        search_calls = []
        marketplace_calls = []
        adapters = self.runtime.create_dataforseo_acquisition_runtime(
            bindings=bindings,
            configuration=self.configuration(),
            search_transport=self.search_transport(search_calls),
            marketplace_transport=self.marketplace_transport(marketplace_calls),
            search_clock=lambda: FIXED_TIME,
            **kwargs,
        )
        return adapters, search_calls, marketplace_calls


class BindingTests(RuntimeTestBase):
    def test_exact_bindings_resolve_to_original_values_in_any_call_order(self):
        task_a = self.task("search-a")
        task_b = self.task("search-b", question="different question", intent="different intent")
        binding_a = self.binding(task_a.task_id)
        binding_b = self.binding(task_b.task_id, kind="trends")
        captured = {}

        def factory(**kwargs):
            captured.update(kwargs)
            return lambda task: self.orchestration.AcquisitionResult(
                task.task_id, self.orchestration.TaskStatus("SUCCESS"), ()
            )

        with patch.object(self.runtime, "create_dataforseo_search_acquisition", side_effect=factory):
            self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[binding_a, binding_b], configuration=self.configuration(), enable_marketplace=False
            )

        resolver = captured["resolve_binding"]
        self.assertIs(resolver(task_b), binding_b)
        self.assertIs(resolver(task_a), binding_a)
        self.assertIs(resolver(task_a), binding_a)

    def test_duplicate_exact_task_id_fails_before_any_transport(self):
        calls = []
        with self.assertRaises((TypeError, ValueError)):
            self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[self.binding("same"), self.binding("same", kind="trends")],
                configuration=self.configuration(),
                search_transport=lambda *args: calls.append(args),
            )
        self.assertEqual(calls, [])

    def test_malformed_collections_members_and_forged_bindings_fail_closed(self):
        malformed = object.__new__(self.providers.ProviderBinding)
        object.__setattr__(malformed, "task_id", "")
        object.__setattr__(malformed, "source_family", "SEARCH")
        object.__setattr__(malformed, "request", self.request())
        cases = (None, object(), "not-bindings", [object()], [malformed])
        for bindings in cases:
            with self.subTest(bindings=bindings):
                with self.assertRaises((TypeError, ValueError)):
                    self.runtime.create_dataforseo_acquisition_runtime(
                        bindings=bindings,
                        configuration=self.configuration(),
                        search_transport=lambda *args: self.fail("transport called"),
                    )

    def test_binding_index_is_immutable_after_caller_collection_mutation(self):
        task = self.task("stable")
        original = self.binding(task.task_id)
        replacement = self.binding(task.task_id, kind="trends")
        bindings = [original]
        captured = {}

        def factory(**kwargs):
            captured.update(kwargs)
            return lambda current: self.orchestration.AcquisitionResult(
                current.task_id, self.orchestration.TaskStatus("SUCCESS"), ()
            )

        with patch.object(self.runtime, "create_dataforseo_search_acquisition", side_effect=factory):
            adapters = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=bindings, configuration=self.configuration(), enable_marketplace=False
            )
        bindings[:] = [replacement]
        bindings.append(self.binding("new"))
        self.assertIs(captured["resolve_binding"](task), original)
        self.assertEqual(adapters(task).status, self.orchestration.TaskStatus("SUCCESS"))

    def test_question_and_intent_changes_cannot_select_request_or_operation(self):
        binding = self.binding("stable", kind="ads")
        task_one = self.task("stable", question="question one", intent="intent one")
        task_two = self.task("stable", question="question two", intent="intent two")
        calls = []
        adapters, calls, _ = self.runtime_with_fake_transports([binding], enable_marketplace=False)
        first = adapters(task_one)
        second = adapters(task_two)
        self.assertEqual(first.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(second.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(calls[0][0].endpoint, calls[1][0].endpoint)
        self.assertEqual(calls[0][0].payload, calls[1][0].payload)
        self.assertEqual(first.findings[0].metadata["operation"], second.findings[0].metadata["operation"])


class CompositionTests(RuntimeTestBase):
    def test_all_supported_request_types_use_existing_family_slots(self):
        bindings = [
            self.binding("ads", kind="ads"),
            self.binding("trends", kind="trends"),
            self.binding("amazon", kind="amazon"),
            self.binding("products", family="MARKETPLACE", kind="products"),
        ]
        adapters, search_calls, marketplace_calls = self.runtime_with_fake_transports(bindings)
        for task_id in ("ads", "trends", "amazon"):
            result = adapters(self.task(task_id))
            self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        result = adapters(self.task("products", family="MARKETPLACE"))
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(len(search_calls), 3)
        self.assertEqual(len(marketplace_calls), 1)
        self.assertIsNotNone(adapters.search)
        self.assertIsNotNone(adapters.marketplace)

    def test_missing_binding_family_mismatch_and_unsupported_request_are_failed(self):
        adapters, search_calls, _ = self.runtime_with_fake_transports(
            [self.binding("present")], enable_marketplace=True
        )
        missing = adapters(self.task("missing"))
        mismatch = adapters(self.task("present", family="MARKETPLACE"))
        unsupported_binding = self.binding("unsupported", kind=UnsupportedRequest())
        unsupported, _, _ = self.runtime_with_fake_transports(
            [unsupported_binding], enable_marketplace=False
        )
        unsupported_result = unsupported(self.task("unsupported"))
        for result in (missing, mismatch, unsupported_result):
            self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
            self.assertEqual(result.findings, ())
        self.assertEqual(search_calls, [])

    def test_partial_installation_preserves_absent_unavailable_slot(self):
        search_only, search_calls, marketplace_calls = self.runtime_with_fake_transports(
            [self.binding("search")], enable_marketplace=False
        )
        result = search_only(self.task("marketplace", family="MARKETPLACE"))
        self.assertEqual(result.status, self.orchestration.TaskStatus("UNAVAILABLE"))
        self.assertEqual(result.findings, ())
        self.assertIsNone(search_only.marketplace)
        self.assertEqual(search_calls, [])
        self.assertEqual(marketplace_calls, [])

    def test_disabled_or_unsupported_binding_is_rejected_at_setup(self):
        cases = (
            [self.binding("marketplace", family="MARKETPLACE", kind="products")],
            [self.binding("supplier", family="SUPPLIER", kind=object())],
        )
        for bindings in cases:
            with self.subTest(bindings=bindings):
                with self.assertRaises((TypeError, ValueError)):
                    self.runtime.create_dataforseo_acquisition_runtime(
                        bindings=bindings,
                        configuration=self.configuration(),
                        enable_search=True,
                        enable_marketplace=False,
                        search_transport=lambda *args: self.fail("transport called"),
                    )


class SetupSafetyTests(RuntimeTestBase):
    def test_family_flags_are_strict_and_at_least_one_family_is_required(self):
        dual, _, _ = self.runtime_with_fake_transports([])
        self.assertIsNotNone(dual.search)
        self.assertIsNotNone(dual.marketplace)
        search_only, _, _ = self.runtime_with_fake_transports([], enable_marketplace=False)
        marketplace_only, _, _ = self.runtime_with_fake_transports([], enable_search=False)
        self.assertIsNotNone(search_only.search)
        self.assertIsNone(search_only.marketplace)
        self.assertIsNone(marketplace_only.search)
        self.assertIsNotNone(marketplace_only.marketplace)
        for kwargs in (
            {"enable_search": 1},
            {"enable_marketplace": "false"},
            {"enable_search": False, "enable_marketplace": False},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    self.runtime.create_dataforseo_acquisition_runtime(
                        bindings=[], configuration=self.configuration(), **kwargs
                    )

    def test_one_exact_configuration_is_passed_unchanged_to_both_factories(self):
        config = self.configuration()
        captured = {}

        def factory(name):
            def create(**kwargs):
                captured[name] = kwargs
                return lambda task: self.orchestration.AcquisitionResult(
                    task.task_id, self.orchestration.TaskStatus("SUCCESS"), ()
                )

            return create

        with patch.object(
            self.runtime,
            "create_dataforseo_search_acquisition",
            side_effect=factory("search"),
        ) as search_factory, patch.object(
            self.runtime,
            "create_dataforseo_marketplace_acquisition",
            side_effect=factory("marketplace"),
        ) as marketplace_factory:
            self.runtime.create_dataforseo_acquisition_runtime(bindings=[], configuration=config)
        search_factory.assert_called_once()
        marketplace_factory.assert_called_once()
        self.assertIs(captured["search"]["configuration"], config)
        self.assertIs(captured["marketplace"]["configuration"], config)
        self.assertIs(captured["search"]["resolve_binding"], captured["marketplace"]["resolve_binding"])

    def test_invalid_explicit_configuration_fails_before_provider_construction(self):
        with patch.object(self.runtime, "create_dataforseo_search_acquisition") as search_factory:
            with self.assertRaises((TypeError, ValueError)):
                self.runtime.create_dataforseo_acquisition_runtime(bindings=[], configuration=object())
        search_factory.assert_not_called()

    def test_environment_factory_resolves_once_then_reuses_configured_path(self):
        config = self.configuration()
        expected = object()
        with patch.object(self.runtime.DataForSEOConfiguration, "from_environment", return_value=config) as from_env, patch.object(
            self.runtime, "create_dataforseo_acquisition_runtime", return_value=expected
        ) as configured:
            actual = self.runtime.create_dataforseo_acquisition_runtime_from_environment(
                bindings=[], environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD}
            )
        self.assertIs(actual, expected)
        from_env.assert_called_once()
        self.assertIs(configured.call_args.kwargs["configuration"], config)

    def test_missing_or_invalid_environment_configuration_fails_before_transport(self):
        calls = []
        cases = (
            {"DATAFORSEO_LOGIN": SECRET_LOGIN},
            {"DATAFORSEO_LOGIN": "", "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
            {"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": None},
        )
        for environ in cases:
            with self.subTest(environ=environ):
                with self.assertRaises(self.providers.ProviderConfigurationError) as raised:
                    self.runtime.create_dataforseo_acquisition_runtime_from_environment(
                        bindings=[],
                        environ=environ,
                        search_transport=lambda *args: calls.append(args),
                    )
                self.assertNotIn(SECRET_LOGIN, str(raised.exception))
                self.assertNotIn(SECRET_PASSWORD, str(raised.exception))
        self.assertEqual(calls, [])

    def test_setup_is_network_free_and_public_surfaces_are_secret_free(self):
        with patch.object(self.client, "_urllib_send", side_effect=AssertionError("live transport")) as sender:
            adapters = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[],
                configuration=self.configuration(),
            )
        self.assertFalse(sender.called)
        public = " ".join((repr(adapters), str(adapters), repr(self.configuration())))
        self.assertNotIn(SECRET_LOGIN, public)
        self.assertNotIn(SECRET_PASSWORD, public)

    def test_environment_backed_setup_results_and_findings_are_secret_free(self):
        search_calls = []
        marketplace_calls = []
        adapters = self.runtime.create_dataforseo_acquisition_runtime_from_environment(
            bindings=[
                self.binding("ads"),
                self.binding("products", family="MARKETPLACE", kind="products"),
            ],
            environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
            search_transport=self.search_transport(search_calls),
            marketplace_transport=self.marketplace_transport(marketplace_calls),
            search_clock=lambda: FIXED_TIME,
        )
        results = (
            adapters(self.task("ads")),
            adapters(self.task("products", family="MARKETPLACE")),
        )
        public = [repr(adapters), str(adapters), repr(self.binding("ads"))]
        for result in results:
            self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
            self.assertTrue(result.findings)
            public.extend((repr(result), str(result), repr(result.findings)))
            for finding in result.findings:
                public.extend((finding.content, repr(finding), repr(finding.metadata), repr(finding.source)))
        surface = " ".join(public)
        self.assertNotIn(SECRET_LOGIN, surface)
        self.assertNotIn(SECRET_PASSWORD, surface)
        self.assertEqual(len(search_calls), 1)
        self.assertEqual(len(marketplace_calls), 1)


class PassThroughTests(RuntimeTestBase):
    def test_existing_provider_success_order_and_zero_findings_pass_through(self):
        bindings = [self.binding("success", kind="ads")]
        adapters, calls, _ = self.runtime_with_fake_transports(bindings, enable_marketplace=False)
        result = adapters(self.task("success"))
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertGreaterEqual(len(result.findings), 1)
        for finding in result.findings:
            self.assertIs(type(finding), self.orchestration.RawFinding)
            self.assertFalse(hasattr(finding, "evidence_id"))
        self.assertEqual(
            [finding.metadata["ordinal"] for finding in result.findings],
            list(range(len(result.findings))),
        )
        self.assertEqual(len(calls), 1)

        no_result = json.loads((FIXTURES / "google_ads_success.json").read_text())
        no_result["status_code"] = 40102
        no_result["tasks_count"] = 0
        no_result["tasks_error"] = 0
        no_result["tasks"] = []
        empty_response = self.search.DataForSEOHTTPResponse(200, json.dumps(no_result))
        with patch.object(
            self.runtime,
            "create_dataforseo_search_acquisition",
            wraps=self.search.create_dataforseo_search_acquisition,
        ):
            empty = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[self.binding("empty")],
                configuration=self.configuration(),
                enable_marketplace=False,
                search_transport=lambda wire, headers: empty_response,
            )
        empty_result = empty(self.task("empty"))
        self.assertEqual(empty_result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(empty_result.findings, ())

    def test_provider_failure_and_transport_exception_remain_owned_by_provider(self):
        failure_payload = json.loads((FIXTURES / "google_ads_success.json").read_text())
        failure_payload["tasks"][0]["status_code"] = 40501
        failure_payload["tasks"][0]["result_count"] = 0
        failure_payload["tasks"][0].pop("result")
        failure_response = self.search.DataForSEOHTTPResponse(200, json.dumps(failure_payload))
        failed = self.runtime.create_dataforseo_acquisition_runtime(
            bindings=[self.binding("failed")],
            configuration=self.configuration(),
            enable_marketplace=False,
            search_transport=lambda wire, headers: failure_response,
        )
        result = failed(self.task("failed"))
        self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
        sentinel = TimeoutError("transport sentinel")
        raised = self.runtime.create_dataforseo_acquisition_runtime(
            bindings=[self.binding("raises")],
            configuration=self.configuration(),
            enable_marketplace=False,
            search_transport=lambda wire, headers: (_ for _ in ()).throw(sentinel),
        )
        with self.assertRaises(TimeoutError) as error:
            raised(self.task("raises"))
        self.assertIs(error.exception, sentinel)

    def test_runtime_returns_existing_provider_callable_without_wrapper_or_result_repair(self):
        expected = self.orchestration.AcquisitionResult(
            "sentinel", self.orchestration.TaskStatus("SUCCESS"), ()
        )
        provider = lambda task: expected
        with patch.object(self.runtime, "create_dataforseo_search_acquisition", return_value=provider):
            adapters = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[], configuration=self.configuration(), enable_marketplace=False
            )
        task = self.task("sentinel")
        self.assertIs(adapters.search, provider)
        self.assertIs(adapters(task), expected)

    def test_orchestration_classifies_exception_and_malformed_result_at_its_boundary(self):
        task = self.task("exception")
        sentinel = RuntimeError("provider exception sentinel")
        with patch.object(
            self.runtime,
            "create_dataforseo_search_acquisition",
            return_value=lambda current: (_ for _ in ()).throw(sentinel),
        ):
            adapters = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[], configuration=self.configuration(), enable_marketplace=False
            )
        objective = self.orchestration.ResearchObjective("objective", "objective")
        plan = self.orchestration.ResearchPlan("objective", (task,))
        result = self.orchestration.run_research(
            objective,
            planner=lambda _: plan,
            acquire=adapters,
            normalize=lambda *_: self.fail("normalization must not run"),
        )
        self.assertEqual([failure.reason.value for failure in result.failures], ["ACQUISITION_EXCEPTION"])

        malformed_task = self.task("malformed")
        malformed = self.orchestration.AcquisitionResult("other", self.orchestration.TaskStatus("SUCCESS"), ())
        with patch.object(
            self.runtime,
            "create_dataforseo_search_acquisition",
            return_value=lambda current: malformed,
        ):
            malformed_adapters = self.runtime.create_dataforseo_acquisition_runtime(
                bindings=[], configuration=self.configuration(), enable_marketplace=False
            )
        malformed_plan = self.orchestration.ResearchPlan("objective", (malformed_task,))
        malformed_result = self.orchestration.run_research(
            objective,
            planner=lambda _: malformed_plan,
            acquire=malformed_adapters,
            normalize=lambda *_: self.fail("normalization must not run"),
        )
        self.assertEqual(
            [failure.reason.value for failure in malformed_result.failures],
            ["INVALID_ACQUISITION_RESULT"],
        )


class ArchitectureTests(RuntimeTestBase):
    def test_runtime_is_external_and_core_does_not_import_it(self):
        runtime_path = ROOT / "dataforseo_acquisition_runtime.py"
        self.assertEqual(runtime_path.parent, ROOT)
        self.assertTrue(runtime_path.exists())
        for path in (ROOT / "product_research").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any("dataforseo_acquisition_runtime" in alias.name for alias in node.names), path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "dataforseo_acquisition_runtime", path.name)

    def test_default_runtime_docs_name_only_configured_supported_composition(self):
        skill = (ROOT / "SKILL.md").read_text()
        spec = (ROOT / "docs" / "product-research-skill-spec.md").read_text()
        combined = skill + "\n" + spec
        self.assertIn("ResearchSourceAdapters", combined)
        self.assertIn("SEARCH", combined)
        self.assertIn("MARKETPLACE", combined)
        self.assertIn("dataforseo_acquisition_runtime", combined)
        self.assertNotIn(SECRET_LOGIN, combined)
        self.assertNotIn(SECRET_PASSWORD, combined)

    def test_runtime_tests_use_fake_transports_and_secret_free_fixtures(self):
        source = pathlib.Path(__file__).read_text()
        self.assertIn("search_transport=", source)
        self.assertIn("marketplace_transport=", source)
        tree = ast.parse(source)
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
        self.assertFalse(any(module == "urllib" or module.startswith("urllib.") for module in imported_modules))


if __name__ == "__main__":
    unittest.main()
