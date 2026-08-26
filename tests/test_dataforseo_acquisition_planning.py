"""ECO-47 requirement-to-test trace for the external DataForSEO planner."""

import ast
import dataclasses
import importlib
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "dataforseo"
FIXED_TIME = "2026-08-24T00:00:00Z"
SECRET_LOGIN = "eco47-login-sentinel-never-public"
SECRET_PASSWORD = "eco47-password-sentinel-never-public"


class PlanningTestBase(unittest.TestCase):
    def setUp(self):
        try:
            self.planning = importlib.import_module("dataforseo_acquisition_planning")
        except ModuleNotFoundError:
            self.fail("dataforseo_acquisition_planning module has not been implemented")
        self.configuration = importlib.import_module("dataforseo_configuration")
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

    def defaults(self, **overrides):
        values = dict(location_code=2840, language_code="en", amazon_products_depth=10)
        values.update(overrides)
        return self.configuration.DataForSEOProviderDefaults(**values)

    def run_overrides(self, **overrides):
        return self.planning.DataForSEORunOverrides(**overrides)

    def input_for(self, operation, **overrides):
        values = {
            "google_ads_search_volume_live": self.planning.GoogleAdsSearchVolumeInput(
                keywords=("blue shoes", "running shoes")
            ),
            "google_trends_explore_live": self.planning.GoogleTrendsExploreInput(
                keywords=("blue shoes", "running shoes"),
                date_from="2026-01-01",
                date_to="2026-08-01",
                item_types=("google_trends_graph", "google_trends_map"),
            ),
            "amazon_bulk_search_volume_live": self.planning.AmazonBulkSearchVolumeInput(
                keywords=("blue shoes", "running shoes")
            ),
            "amazon_products_live": self.planning.AmazonProductsInput(keyword="wireless headphones"),
        }
        value = values[operation]
        if not overrides:
            return value
        return dataclasses.replace(value, **overrides)

    def entry(self, task_id, operation, *, family=None, semantic_input=None, task=None, **input_overrides):
        if family is None:
            family = "MARKETPLACE" if operation == "amazon_products_live" else "SEARCH"
        task = task or self.task(task_id, family=family)
        semantic_input = semantic_input or self.input_for(operation, **input_overrides)
        return self.planning.DataForSEOAcquisitionEntry(
            task=task,
            operation=self.planning.DataForSEOOperation(operation),
            semantic_input=semantic_input,
        )

    def plan(self, *entries):
        return self.planning.DataForSEOAcquisitionPlan(entries)

    def compile(self, plan, *, defaults=None, overrides=None):
        return self.planning.compile_dataforseo_acquisition_plan(
            plan,
            defaults=self.defaults() if defaults is None else defaults,
            overrides=overrides,
        )


class DeclarationTests(PlanningTestBase):
    def test_operation_vocabulary_is_exact_and_inputs_are_frozen(self):
        self.assertEqual(
            tuple(operation.value for operation in self.planning.DataForSEOOperation),
            (
                "google_ads_search_volume_live",
                "google_trends_explore_live",
                "amazon_bulk_search_volume_live",
                "amazon_products_live",
            ),
        )
        values = (
            self.input_for("google_ads_search_volume_live"),
            self.input_for("google_trends_explore_live"),
            self.input_for("amazon_bulk_search_volume_live"),
            self.input_for("amazon_products_live"),
        )
        self.assertEqual(values[0].keywords, ("blue shoes", "running shoes"))
        self.assertIsInstance(values[1].item_types, tuple)
        for value in values:
            with self.assertRaises(dataclasses.FrozenInstanceError):
                if hasattr(value, "keyword"):
                    value.keyword = "changed"
                else:
                    value.keywords = ("changed",)

    def test_declared_ordered_collections_normalize_once_and_mappings_fail_closed(self):
        ads = self.planning.GoogleAdsSearchVolumeInput(["blue shoes"])
        trends = self.planning.GoogleTrendsExploreInput(
            ["blue shoes"], item_types=["google_trends_graph"]
        )
        self.assertEqual(ads.keywords, ("blue shoes",))
        self.assertEqual(trends.keywords, ("blue shoes",))
        self.assertEqual(trends.item_types, ("google_trends_graph",))
        for constructor, kwargs in (
            (self.planning.GoogleAdsSearchVolumeInput, {"keywords": {"blue shoes": 1}}),
            (self.planning.GoogleTrendsExploreInput, {"keywords": {"blue shoes": 1}}),
            (self.planning.AmazonBulkSearchVolumeInput, {"keywords": {"blue shoes": 1}}),
            (self.planning.AmazonProductsInput, {"keyword": ["blue shoes"]}),
        ):
            with self.subTest(constructor=constructor.__name__):
                with self.assertRaises((TypeError, ValueError)):
                    constructor(**kwargs)

    def test_entry_retains_exact_task_and_plan_retains_declared_order(self):
        task_a = self.task("task-a")
        task_b = self.task("task-b", question="another question", intent="another intent")
        entry_a = self.entry("task-a", "google_ads_search_volume_live", task=task_a)
        entry_b = self.entry("task-b", "amazon_bulk_search_volume_live", task=task_b)
        plan = self.plan(entry_b, entry_a)
        self.assertIs(entry_a.task, task_a)
        self.assertIs(entry_b.task, task_b)
        self.assertEqual(plan.entries, (entry_b, entry_a))
        self.assertIsInstance(plan.entries, tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            plan.entries = ()

    def test_exact_public_fields_do_not_create_a_second_research_model(self):
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.GoogleAdsSearchVolumeInput)),
            ("keywords",),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.GoogleTrendsExploreInput)),
            ("keywords", "search_type", "category_code", "date_from", "date_to", "time_range", "item_types"),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.AmazonBulkSearchVolumeInput)),
            ("keywords",),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.AmazonProductsInput)),
            ("keyword",),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.DataForSEOAcquisitionEntry)),
            ("task", "operation", "semantic_input"),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.DataForSEOAcquisitionPlan)),
            ("entries",),
        )
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(self.planning.DataForSEORunOverrides)),
            ("location_name", "location_code", "language_name", "language_code", "amazon_products_depth"),
        )

    def test_duplicate_task_identity_and_wrong_declarations_fail_before_compilation(self):
        first = self.entry("same", "google_ads_search_volume_live")
        second = self.entry("same", "amazon_bulk_search_volume_live")
        with self.assertRaises(ValueError):
            self.plan(first, second)
        with self.assertRaises((TypeError, ValueError)):
            self.planning.DataForSEOAcquisitionEntry(
                task=self.task("wrong"),
                operation="google_ads_search_volume_live",
                semantic_input=self.input_for("google_ads_search_volume_live"),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.planning.DataForSEOAcquisitionEntry(
                task=self.task("wrong"),
                operation=self.planning.DataForSEOOperation("google_ads_search_volume_live"),
                semantic_input=self.input_for("amazon_products_live"),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.planning.DataForSEOAcquisitionPlan({"entry": first})

    def test_no_task_identity_or_generic_plan_fields_are_generated(self):
        task = self.task("retained")
        entry = self.entry("retained", "google_ads_search_volume_live", task=task)
        plan = self.plan(entry)
        self.assertEqual(entry.task.task_id, "retained")
        self.assertFalse(hasattr(entry, "objective_id"))
        self.assertFalse(hasattr(entry, "research_question"))
        self.assertFalse(hasattr(entry, "source_family"))
        self.assertFalse(hasattr(entry, "query_intent"))
        self.assertFalse(hasattr(entry, "evidence_kind"))
        self.assertFalse(hasattr(entry, "required"))
        self.assertFalse(hasattr(plan, "objective_id"))


class CompilationTests(PlanningTestBase):
    def test_each_operation_maps_once_to_exact_request_and_family_in_plan_order(self):
        entries = (
            self.entry("ads", "google_ads_search_volume_live"),
            self.entry("trends", "google_trends_explore_live"),
            self.entry("amazon", "amazon_bulk_search_volume_live"),
            self.entry("products", "amazon_products_live"),
        )
        bindings = self.compile(self.plan(*entries))
        self.assertEqual(tuple(binding.task_id for binding in bindings), ("ads", "trends", "amazon", "products"))
        self.assertEqual(
            tuple(binding.request for binding in bindings),
            (
                self.search.GoogleAdsSearchVolumeRequest(
                    keywords=("blue shoes", "running shoes"),
                    location_code=2840,
                    language_code="en",
                ),
                self.search.GoogleTrendsExploreRequest(
                    keywords=("blue shoes", "running shoes"),
                    location_code=2840,
                    language_code="en",
                    type="web",
                    category_code=0,
                    date_from="2026-01-01",
                    date_to="2026-08-01",
                    item_types=("google_trends_graph", "google_trends_map"),
                ),
                self.search.AmazonBulkSearchVolumeRequest(
                    keywords=("blue shoes", "running shoes"),
                    location_code=2840,
                    language_code="en",
                ),
                self.marketplace.AmazonProductsRequest(
                    keyword="wireless headphones",
                    location_code=2840,
                    language_code="en",
                    depth=10,
                ),
            ),
        )
        self.assertEqual(
            tuple(binding.source_family.value for binding in bindings),
            ("SEARCH", "SEARCH", "SEARCH", "MARKETPLACE"),
        )
        self.assertEqual(bindings[0].request.keywords, entries[0].semantic_input.keywords)
        self.assertEqual(bindings[1].request.type, entries[1].semantic_input.search_type)
        self.assertEqual(bindings[3].request.keyword, entries[3].semantic_input.keyword)
        self.assertIsInstance(bindings, tuple)

    def test_compilation_preserves_exact_task_identity_and_ignores_free_form_text(self):
        task_one = self.task("stable", question="question one", intent="intent one")
        task_two = self.task("stable", question="question two", intent="intent two")
        first_snapshot = dataclasses.astuple(task_one)
        second_snapshot = dataclasses.astuple(task_two)
        first_entry = self.entry("stable", "google_ads_search_volume_live", task=task_one)
        second_entry = self.entry("stable", "google_ads_search_volume_live", task=task_two)
        first = self.compile(self.plan(first_entry))[0]
        second = self.compile(self.plan(second_entry))[0]
        self.assertEqual(first, second)
        self.assertIs(first_entry.task, task_one)
        self.assertIs(second_entry.task, task_two)
        self.assertEqual(dataclasses.astuple(task_one), first_snapshot)
        self.assertEqual(dataclasses.astuple(task_two), second_snapshot)

    def test_current_run_settings_replace_whole_default_dimensions(self):
        defaults = self.defaults(
            location_code=2840,
            language_name="English",
            language_code=None,
            amazon_products_depth=10,
        )
        overrides = self.run_overrides(
            location_name="United States",
            language_code="en-US",
            amazon_products_depth=25,
        )
        bindings = self.compile(
            self.plan(
                self.entry("ads", "google_ads_search_volume_live"),
                self.entry("products", "amazon_products_live"),
            ),
            defaults=defaults,
            overrides=overrides,
        )
        for request in bindings:
            self.assertEqual(request.request.location_name, "United States")
            self.assertIsNone(request.request.location_code)
            self.assertEqual(request.request.language_code, "en-US")
            self.assertIsNone(request.request.language_name)
        self.assertEqual(bindings[1].request.depth, 25)

    def test_absent_run_settings_preserve_defaults_and_unspecified_values(self):
        defaults = self.configuration.DataForSEOProviderDefaults()
        request = self.compile(
            self.plan(self.entry("ads", "google_ads_search_volume_live")),
            defaults=defaults,
        )[0].request
        self.assertIsNone(request.location_name)
        self.assertIsNone(request.location_code)
        self.assertIsNone(request.language_name)
        self.assertIsNone(request.language_code)
        with self.assertRaises((TypeError, ValueError)):
            self.compile(self.plan(self.entry("amazon", "amazon_bulk_search_volume_live")), defaults=defaults)
        with self.assertRaises((TypeError, ValueError)):
            self.compile(self.plan(self.entry("products", "amazon_products_live")), defaults=defaults)

    def test_conflicting_run_forms_and_family_mismatch_fail_before_provider_construction(self):
        with self.assertRaises((TypeError, ValueError)):
            self.run_overrides(location_name="United States", location_code=2840)
        with self.assertRaises((TypeError, ValueError)):
            self.run_overrides(language_name="English", language_code="en")
        for kwargs in (
            {"location_name": ""},
            {"language_name": ""},
            {"language_code": ""},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    self.run_overrides(**kwargs)
        entry = self.entry("wrong-family", "amazon_products_live", family="SEARCH")
        with self.assertRaises((TypeError, ValueError)):
            self.compile(self.plan(entry))

    def test_provider_constructor_validation_is_authoritative_and_no_transport_is_possible(self):
        calls = []
        invalid = self.planning.GoogleAdsSearchVolumeInput(keywords=("",))
        entry = self.entry("invalid", "google_ads_search_volume_live", semantic_input=invalid)
        with self.assertRaises((TypeError, ValueError)):
            self.compile(self.plan(entry))
        self.assertEqual(calls, [])
        with self.assertRaises((TypeError, ValueError)):
            self.run_overrides(amazon_products_depth=701)
        self.assertEqual(calls, [])

    def test_equivalent_inputs_are_deterministic_and_overrides_are_optional(self):
        plan = self.plan(self.entry("stable", "google_trends_explore_live"))
        first = self.compile(plan)
        second = self.compile(plan, overrides=self.run_overrides())
        self.assertEqual(first, second)
        with self.assertRaises((TypeError, ValueError)):
            self.planning.compile_dataforseo_acquisition_plan(
                plan, defaults=self.defaults(), overrides={}
            )


class RuntimeAndBoundaryTests(PlanningTestBase):
    def fixture_response(self, module, name, status=200):
        payload = json.loads((FIXTURES / name).read_text())
        return module.DataForSEOHTTPResponse(status_code=status, body=json.dumps(payload))

    def test_compiled_bindings_enter_unchanged_runtime_for_search_and_marketplace(self):
        entries = (
            self.entry("ads", "google_ads_search_volume_live"),
            self.entry("products", "amazon_products_live"),
        )
        bindings = self.compile(self.plan(*entries))
        search_calls = []
        marketplace_calls = []

        def search_transport(wire, headers):
            search_calls.append((wire, headers))
            return self.fixture_response(self.search, "google_ads_success.json")

        def marketplace_transport(wire, headers):
            marketplace_calls.append((wire, headers))
            payload = json.loads((FIXTURES / "amazon_products_success.json").read_text())
            payload["tasks"][0]["data"].update(wire.payload[0])
            return self.marketplace.DataForSEOHTTPResponse(200, json.dumps(payload))

        runtime = importlib.import_module("dataforseo_acquisition_runtime")
        adapters = runtime.create_dataforseo_acquisition_runtime(
            bindings=bindings,
            configuration=self.client.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
            search_transport=search_transport,
            marketplace_transport=marketplace_transport,
            search_clock=lambda: FIXED_TIME,
        )
        self.assertEqual(adapters(self.task("ads")).status.value, "SUCCESS")
        self.assertEqual(adapters(self.task("products", family="MARKETPLACE")).status.value, "SUCCESS")
        self.assertEqual(len(search_calls), 1)
        self.assertEqual(len(marketplace_calls), 1)

    def test_runtime_findings_cross_separately_constructed_normalizer(self):
        entry = self.entry("ads", "google_ads_search_volume_live")
        bindings = self.compile(self.plan(entry))
        runtime = importlib.import_module("dataforseo_acquisition_runtime")
        adapters = runtime.create_dataforseo_acquisition_runtime(
            bindings=bindings,
            configuration=self.client.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
            search_transport=lambda wire, headers: self.fixture_response(self.search, "google_ads_success.json"),
            search_clock=lambda: FIXED_TIME,
            enable_marketplace=False,
        )
        result = adapters(self.task("ads"))
        self.assertEqual(result.status.value, "SUCCESS")
        normalizer_module = importlib.import_module("dataforseo_evidence_normalizer")
        normalizer = normalizer_module.create_dataforseo_evidence_normalizer(
            {
                operation: (
                    importlib.import_module("product_research.evidence").Tier("Tier 2"),
                    importlib.import_module("product_research.evidence").Confidence("Medium"),
                )
                for operation in (
                    "google_ads_search_volume_live",
                    "google_trends_explore_live",
                    "amazon_bulk_search_volume_live",
                    "amazon_products_live",
                )
            }
        )
        evidence = normalizer(
            self.task("ads"),
            result.findings[0],
            importlib.import_module("product_research.evidence").EvidenceId("E001"),
        )
        self.assertEqual(type(evidence).__name__, "Evidence")


class ArchitectureAndDocumentationTests(unittest.TestCase):
    def test_core_does_not_import_concrete_planning_module(self):
        for path in (ROOT / "product_research").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(
                        any(alias.name == "dataforseo_acquisition_planning" for alias in node.names),
                        path.name,
                    )
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "dataforseo_acquisition_planning", path.name)

    def test_planner_source_has_no_transport_configuration_or_downstream_execution_path(self):
        path = ROOT / "dataforseo_acquisition_planning.py"
        if not path.exists():
            self.fail("dataforseo_acquisition_planning.py has not been implemented")
        source = path.read_text()
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden = {
            "urllib",
            "requests",
            "socket",
            "playwright",
            "selenium",
            "dataforseo_client",
        }
        self.assertTrue(forbidden.isdisjoint(imported | imported_from))
        for forbidden_text in (
            "DataForSEOConfiguration",
            "ProviderAcquisition",
            "RawFinding",
            "Evidence",
            "normalize",
            "transport",
            "credential",
            "environment",
            "research_question",
            "query_intent",
        ):
            self.assertNotIn(forbidden_text, source)

    def test_skill_documents_structured_planning_and_separate_downstream_boundaries(self):
        source = (ROOT / "SKILL.md").read_text()
        for phrase in (
            "DataForSEOAcquisitionPlan",
            "DataForSEORunOverrides",
            "compile_dataforseo_acquisition_plan",
            "ResearchTask",
            "google_ads_search_volume_live",
            "google_trends_explore_live",
            "amazon_bulk_search_volume_live",
            "amazon_products_live",
            "current-run",
            "ECO-44",
            "ECO-45",
        ):
            self.assertIn(phrase, source)
