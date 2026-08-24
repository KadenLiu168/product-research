"""ECO-41 requirement-to-test map.

Provider boundary/ownership: architecture tests.
Explicit bindings: immutable values, exact task/family checks, typed routing,
deterministic replay, and no free-form intent routing.
Setup/secrets: fail-closed configuration and redacted public representations.
Transport: injected synchronous one-attempt behavior and exception identity.
Bridge: existing acquisition values, ordering, failure, and empty-success
semantics without introducing a second observation contract.
Integration: direct family-slot use and ECO-13 classification/normalization.
"""

import ast
import dataclasses
import importlib
import inspect
import pathlib
import unittest
from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordRequest:
    term: str


@dataclass(frozen=True)
class CatalogRequest:
    catalog_key: str


@dataclass(frozen=True)
class UnsupportedRequest:
    value: str


class ProviderInfrastructureTestBase(unittest.TestCase):
    def setUp(self):
        try:
            self.providers = importlib.import_module("product_research_providers")
        except ModuleNotFoundError:
            self.fail("provider infrastructure module has not been implemented")
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.adapters = importlib.import_module("product_research.research_adapters")
        self.evidence = importlib.import_module("product_research.evidence")
        self.policy = importlib.import_module("product_research.evidence_policy")

    def objective(self):
        return self.orchestration.ResearchObjective(
            objective_id="objective-01",
            objective="Determine whether the candidate has a viable market.",
        )

    def task(
        self,
        task_id="task-01",
        family="SEARCH",
        question=None,
        query_intent="caller-defined intent",
        required=True,
    ):
        return self.orchestration.ResearchTask(
            task_id=task_id,
            research_question=question or f"What is known for {task_id}?",
            source_family=self.orchestration.SourceFamily(family),
            query_intent=query_intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=required,
        )

    def source(self, finding_id):
        return self.evidence.Source(
            provider="Example provider",
            source_type="marketplace_listing",
            reference=f"https://example.test/items/{finding_id}",
            title=f"Item {finding_id}",
        )

    def finding(self, finding_id, content=None, metadata=None):
        return self.orchestration.RawFinding(
            finding_id=finding_id,
            content=content or f"Observation {finding_id}.",
            source=self.source(finding_id),
            observed_at="2026-08-14T08:30:00Z",
            metadata=metadata or {"rank": finding_id},
        )

    def acquisition(self, task, status="SUCCESS", findings=()):
        return self.orchestration.AcquisitionResult(
            task_id=task.task_id,
            status=self.orchestration.TaskStatus(status),
            findings=tuple(findings),
        )

    def binding(self, task, request, family=None, task_id=None):
        return self.providers.ProviderBinding(
            task_id=task_id or task.task_id,
            source_family=self.orchestration.SourceFamily(family or task.source_family.value),
            request=request,
        )

    def bridge(
        self,
        resolve_binding,
        execute=None,
        transport=None,
        family="SEARCH",
        supported_request_types=(KeywordRequest, CatalogRequest),
        **kwargs,
    ):
        transport = transport or (lambda request: {"request": request})
        execute = execute or (
            lambda task, request, injected_transport: self.acquisition(
                task, findings=()
            )
        )
        return self.providers.ProviderAcquisition(
            source_family=self.orchestration.SourceFamily(family),
            resolve_binding=resolve_binding,
            execute=execute,
            transport=transport,
            supported_request_types=supported_request_types,
            **kwargs,
        )

    def plan(self, tasks):
        return self.orchestration.ResearchPlan("objective-01", tuple(tasks))

    def evidence_record(self, evidence_id, finding):
        return self.evidence.Evidence(
            id=evidence_id,
            claim=f"Claim for {finding.finding_id}.",
            evidence=finding.content,
            source=finding.source,
            observed_at=finding.observed_at,
            tier=self.evidence.Tier("Tier 2"),
            status=self.evidence.Status("Observed"),
            confidence=self.evidence.Confidence("Medium"),
            metadata={"policy": {"kind": "marketplace_price"}},
        )


class ArchitectureAndBindingTests(ProviderInfrastructureTestBase):
    def test_provider_boundary_imports_existing_contracts_without_reverse_imports(self):
        source = inspect.getsource(self.providers)
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertIn("product_research.research_orchestration", imported_modules)
        self.assertNotIn("product_research.research_adapters", imported_modules)

        package_root = pathlib.Path(__file__).resolve().parents[1] / "product_research"
        for path in package_root.glob("*.py"):
            module_tree = ast.parse(path.read_text())
            for node in ast.walk(module_tree):
                if isinstance(node, ast.Import):
                    imported = {alias.name for alias in node.names}
                    self.assertNotIn("product_research_providers", imported, path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "product_research_providers", path.name)

    def test_provider_binding_is_frozen_and_rejects_malformed_family_values(self):
        task = self.task()
        binding = self.binding(task, KeywordRequest("bracelet"))
        self.assertTrue(dataclasses.is_dataclass(binding))
        self.assertTrue(type(binding).__dataclass_params__.frozen)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            binding.task_id = "other"

        with self.assertRaises((TypeError, ValueError)):
            self.providers.ProviderBinding(
                task_id=task.task_id,
                source_family="SEARCH",
                request=KeywordRequest("bracelet"),
            )
        corrupted_family = object.__new__(self.orchestration.SourceFamily)
        object.__setattr__(corrupted_family, "_value", "CORRUPTED")
        with self.assertRaises((TypeError, ValueError)):
            self.providers.ProviderBinding(
                task_id=task.task_id,
                source_family=corrupted_family,
                request=KeywordRequest("bracelet"),
            )

    def test_exact_declared_request_routes_deterministically_without_intent_parsing(self):
        request = KeywordRequest("declared-term")
        task_a = self.task(
            question="Question text A",
            query_intent="arbitrary intent A",
        )
        task_b = self.task(
            question="Question text B",
            query_intent="arbitrary intent B",
        )
        calls = []
        binding = self.binding(task_a, request)

        def execute(task, declared_request, transport):
            calls.append((task, declared_request))
            return self.acquisition(task)

        provider = self.bridge(lambda task: binding, execute=execute)
        first = provider(task_a)
        second = provider(task_b)

        self.assertEqual([request for _, request in calls], [request, request])
        self.assertEqual(first, second)
        self.assertEqual(first.status, self.orchestration.TaskStatus("SUCCESS"))

    def test_task_and_family_association_fails_before_provider_or_transport(self):
        calls = []
        transport_calls = []
        task = self.task()

        def execute(*args):
            calls.append(args)
            return self.acquisition(task)

        def transport(request):
            transport_calls.append(request)
            return object()

        mismatched_task = self.binding(task, KeywordRequest("term"), task_id="other-task")
        mismatched_family = self.binding(task, KeywordRequest("term"), family="MARKETPLACE")
        for label, binding in (("task", mismatched_task), ("family", mismatched_family)):
            with self.subTest(label=label):
                provider = self.bridge(lambda current: binding, execute=execute, transport=transport)
                result = provider(task)
                self.assertEqual(result.task_id, task.task_id)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
                self.assertEqual(result.findings, ())
        self.assertEqual(calls, [])
        self.assertEqual(transport_calls, [])

    def test_missing_ambiguous_unsupported_and_corrupted_bindings_fail_closed(self):
        task = self.task()
        calls = []
        transport_calls = []

        def execute(*args):
            calls.append(args)
            return self.acquisition(task)

        def transport(request):
            transport_calls.append(request)
            return object()

        valid = self.binding(task, KeywordRequest("term"))
        ambiguous = (valid, self.binding(task, CatalogRequest("catalog")))
        unsupported = self.binding(task, UnsupportedRequest("unsupported"))
        corrupted = object.__new__(self.providers.ProviderBinding)
        object.__setattr__(corrupted, "task_id", task.task_id)
        object.__setattr__(corrupted, "source_family", "SEARCH")
        object.__setattr__(corrupted, "request", KeywordRequest("term"))

        cases = (
            ("missing", lambda _: None, (KeywordRequest,)),
            ("ambiguous", lambda _: ambiguous, (KeywordRequest, CatalogRequest)),
            ("unsupported", lambda _: unsupported, (KeywordRequest,)),
            ("corrupted", lambda _: corrupted, (KeywordRequest,)),
        )
        for label, resolver, supported in cases:
            with self.subTest(label=label):
                provider = self.bridge(
                    resolver,
                    execute=execute,
                    transport=transport,
                    supported_request_types=supported,
                )
                result = provider(task)
                self.assertEqual(result.task_id, task.task_id)
                self.assertEqual(result.status, self.orchestration.TaskStatus("FAILED"))
                self.assertEqual(result.findings, ())
        self.assertEqual(calls, [])
        self.assertEqual(transport_calls, [])


class SetupTransportAndBridgeTests(ProviderInfrastructureTestBase):
    def test_invalid_explicit_configuration_fails_before_transport_and_absent_slot_stays_unavailable(self):
        secret = "fake-credential-sentinel"
        transport_calls = []

        def validate(configuration):
            raise ValueError(f"invalid credential {secret}")

        with self.assertRaises(self.providers.ProviderConfigurationError) as raised:
            self.bridge(
                lambda task: None,
                transport=lambda request: transport_calls.append(request),
                configuration=None,
                validate_configuration=validate,
            )
        self.assertNotIn(secret, str(raised.exception))
        self.assertEqual(transport_calls, [])

        unavailable = self.adapters.ResearchSourceAdapters()(self.task(family="SUPPLIER"))
        self.assertEqual(unavailable.status, self.orchestration.TaskStatus("UNAVAILABLE"))
        self.assertEqual(unavailable.findings, ())

    def test_secret_sentinel_is_absent_from_public_values_errors_and_acquisition_outputs(self):
        secret = "fake-credential-sentinel"
        configuration = {"credential": secret}
        finding = self.finding("safe", metadata={"rank": 1})
        task = self.task()
        binding = self.binding(task, KeywordRequest("safe-term"))

        def validate(value):
            if value != configuration:
                raise ValueError(f"bad configuration {secret}")

        provider = self.bridge(
            lambda current: binding,
            execute=lambda current, request, transport: self.acquisition(current, findings=(finding,)),
            configuration=configuration,
            validate_configuration=validate,
        )
        public_text = " ".join((repr(provider), str(provider), repr(binding), str(binding)))
        output = provider(task)
        public_text += " " + repr(output) + " " + repr(output.findings[0]) + " " + repr(output.findings[0].source)
        self.assertNotIn(secret, public_text)

        with self.assertRaises(self.providers.ProviderConfigurationError) as raised:
            self.bridge(
                lambda current: binding,
                configuration={"credential": "wrong"},
                validate_configuration=validate,
            )
        self.assertNotIn(secret, str(raised.exception))

    def test_construction_is_io_free_and_one_logical_attempt_is_synchronous_and_exact(self):
        task = self.task()
        binding = self.binding(task, CatalogRequest("catalog-01"))
        transport_calls = []
        provider_calls = []

        def transport(request):
            transport_calls.append(request)
            return {"observations": ()}

        def execute(current, request, injected_transport):
            provider_calls.append(request)
            injected_transport(request)
            return self.acquisition(current)

        provider = self.bridge(
            lambda current: binding,
            execute=execute,
            transport=transport,
            supported_request_types=(CatalogRequest,),
        )
        self.assertEqual(provider_calls, [])
        self.assertEqual(transport_calls, [])
        self.assertFalse(inspect.iscoroutinefunction(provider))

        result = provider(task)
        self.assertEqual(result.status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(provider_calls, [binding.request])
        self.assertEqual(transport_calls, [binding.request])

    def test_provider_execution_cannot_invoke_transport_more_than_once(self):
        task = self.task()
        binding = self.binding(task, KeywordRequest("term"))
        transport_calls = []

        def transport(request):
            transport_calls.append(request)
            return {"observations": ()}

        def execute(current, request, injected_transport):
            injected_transport(request)
            injected_transport(request)
            return self.acquisition(current)

        provider = self.bridge(lambda current: binding, execute=execute, transport=transport)

        with self.assertRaises(RuntimeError):
            provider(task)
        self.assertEqual(transport_calls, [binding.request])

    def test_transport_exception_crosses_unchanged_with_one_call(self):
        task = self.task()
        binding = self.binding(task, KeywordRequest("term"))
        error = RuntimeError("ordinary transport failure")
        transport_calls = []

        def transport(request):
            transport_calls.append(request)
            raise error

        def execute(current, request, injected_transport):
            return injected_transport(request)

        provider = self.bridge(lambda current: binding, execute=execute, transport=transport)
        with self.assertRaises(RuntimeError) as raised:
            provider(task)
        self.assertIs(raised.exception, error)
        self.assertEqual(transport_calls, [binding.request])

    def test_successful_bridge_preserves_existing_ordered_findings_and_stops_before_durable_values(self):
        task = self.task()
        findings = (self.finding("z"), self.finding("a"))
        binding = self.binding(task, KeywordRequest("term"))

        provider = self.bridge(
            lambda current: binding,
            execute=lambda current, request, transport: self.acquisition(current, findings=findings),
        )
        result = provider(task)

        self.assertIsInstance(result, self.orchestration.AcquisitionResult)
        self.assertEqual(result.findings, findings)
        self.assertEqual([finding.finding_id for finding in result.findings], ["z", "a"])
        self.assertTrue(all(type(finding) is self.orchestration.RawFinding for finding in result.findings))
        self.assertTrue(all(type(finding.source) is self.evidence.Source for finding in result.findings))
        source = inspect.getsource(self.providers)
        self.assertNotIn("class Evidence", source)
        self.assertNotIn("EvidenceId", source)

    def test_provider_failure_and_legitimate_empty_success_reuse_existing_results(self):
        task = self.task()
        binding = self.binding(task, KeywordRequest("term"))
        failed = self.acquisition(task, status="FAILED")
        empty = self.acquisition(task, status="SUCCESS", findings=())

        for expected in (failed, empty):
            with self.subTest(status=expected.status.value):
                provider = self.bridge(
                    lambda current: binding,
                    execute=lambda current, request, transport, expected=expected: expected,
                )
                result = provider(task)
                self.assertIs(result, expected)
                self.assertEqual(result.task_id, task.task_id)
                self.assertEqual(result.findings, ())


class IntegrationTests(ProviderInfrastructureTestBase):
    def run_with(self, tasks, composition, normalize=None):
        normalize = normalize or (
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding)
        )
        return self.orchestration.run_research(
            self.objective(),
            lambda objective: self.plan(tasks),
            composition,
            normalize,
        )

    def test_provider_callable_installs_directly_in_matching_family_slot(self):
        task = self.task()
        finding = self.finding("first")
        binding = self.binding(task, KeywordRequest("term"))
        provider = self.bridge(
            lambda current: binding,
            execute=lambda current, request, transport: self.acquisition(current, findings=(finding,)),
        )
        normalized = []
        result = self.run_with(
            [task],
            self.adapters.ResearchSourceAdapters(search=provider),
            lambda current, raw, evidence_id: normalized.append((current, raw))
            or self.evidence_record(evidence_id, raw),
        )

        self.assertEqual(result.status, self.orchestration.RunStatus("COMPLETE"))
        self.assertEqual([raw.finding_id for _, raw in normalized], ["first"])
        self.assertEqual([str(record.id) for record in result.evidence], ["E001"])

    def test_provider_failures_and_malformed_outputs_keep_eco13_classification_and_continue(self):
        failed_task = self.task("failed")
        exception_task = self.task("exception")
        malformed_task = self.task("malformed")
        mismatched_task = self.task("mismatched")
        valid_task = self.task("valid", family="MARKETPLACE")
        bindings = {
            task.task_id: self.binding(task, KeywordRequest(task.task_id))
            for task in (failed_task, exception_task, malformed_task, mismatched_task)
        }
        error = RuntimeError("ordinary transport failure")

        def resolve(task):
            return bindings[task.task_id]

        def execute(task, request, transport):
            if task.task_id == "failed":
                return self.acquisition(task, status="FAILED")
            if task.task_id == "exception":
                raise error
            if task.task_id == "malformed":
                return object()
            if task.task_id == "mismatched":
                return self.orchestration.AcquisitionResult(
                    task_id="other-task",
                    status=self.orchestration.TaskStatus("SUCCESS"),
                    findings=(),
                )
            raise AssertionError("unexpected task")

        provider = self.bridge(resolve, execute=execute)
        composition = self.adapters.ResearchSourceAdapters(
            search=provider,
            marketplace=lambda task: self.acquisition(task, findings=(self.finding("survives"),)),
        )
        result = self.run_with(
            [failed_task, exception_task, malformed_task, mismatched_task, valid_task],
            composition,
        )

        self.assertEqual(
            [str(failure.reason) for failure in result.failures],
            [
                "ACQUISITION_FAILED",
                "ACQUISITION_EXCEPTION",
                "INVALID_ACQUISITION_RESULT",
                "INVALID_ACQUISITION_RESULT",
            ],
        )
        self.assertEqual([record.id.value for record in result.evidence], ["E001"])
        self.assertEqual(result.evidence[0].evidence, "Observation survives.")

    def test_successful_findings_normalize_only_through_eco13_and_empty_success_has_no_normalizer_call(self):
        task = self.task()
        empty_task = self.task("empty")
        bindings = {
            task.task_id: self.binding(task, KeywordRequest("term")),
            empty_task.task_id: self.binding(empty_task, KeywordRequest("empty")),
        }
        findings = (self.finding("z"), self.finding("a"))
        normalize_calls = []

        def execute(current, request, transport):
            if current.task_id == "empty":
                return self.acquisition(current, findings=())
            return self.acquisition(current, findings=findings)

        provider = self.bridge(lambda current: bindings[current.task_id], execute=execute)
        result = self.run_with(
            [task, empty_task],
            self.adapters.ResearchSourceAdapters(search=provider),
            lambda current, raw, evidence_id: normalize_calls.append((current.task_id, raw.finding_id))
            or self.evidence_record(evidence_id, raw),
        )

        self.assertEqual(normalize_calls, [("task-01", "z"), ("task-01", "a")])
        self.assertEqual([record.id.value for record in result.evidence], ["E001", "E002"])
        self.assertEqual(result.task_results[1].status, self.orchestration.TaskStatus("SUCCESS"))
        self.assertEqual(result.task_results[1].finding_ids, ())


class ProviderNeutralityTests(ProviderInfrastructureTestBase):
    def test_provider_layer_contains_no_downstream_provider_behavior_or_extra_result_contract(self):
        source = inspect.getsource(self.providers)
        lowered = source.lower()
        forbidden = (
            "dataforseo",
            "google ads",
            "google trends",
            "amazon",
            "requests",
            "httpx",
            "urllib",
            "dotenv",
            "retry",
            "backoff",
            "async",
            "network",
            "registry",
            "plugin",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, lowered)
        tree = ast.parse(source)
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        self.assertNotIn("Evidence", class_names)
        self.assertNotIn("RawFinding", class_names)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertIn("AcquisitionResult", imported_names)
        self.assertIn("TaskStatus", imported_names)


if __name__ == "__main__":
    unittest.main()
