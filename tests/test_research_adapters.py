import ast
import dataclasses
import importlib
import inspect
import unittest


def _adapter_module():
    try:
        return importlib.import_module("product_research.research_adapters")
    except ModuleNotFoundError as exc:
        raise AssertionError("research adapter composition has not been implemented") from exc


class ResearchAdapterTestBase(unittest.TestCase):
    def setUp(self):
        self.adapters = _adapter_module()
        self.orchestration = importlib.import_module("product_research.research_orchestration")
        self.evidence = importlib.import_module("product_research.evidence")
        self.policy = importlib.import_module("product_research.evidence_policy")

    def objective(self):
        return self.orchestration.ResearchObjective(
            objective_id="objective-01",
            objective="Determine whether the candidate has a viable market.",
        )

    def task(self, family="SEARCH", task_id="task-01", query_intent="caller intent"):
        return self.orchestration.ResearchTask(
            task_id=task_id,
            research_question=f"What is known for {task_id}?",
            source_family=self.orchestration.SourceFamily(family),
            query_intent=query_intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=True,
        )

    def plan(self, tasks):
        return self.orchestration.ResearchPlan("objective-01", tuple(tasks))

    def source(self, finding_id):
        return self.evidence.Source(
            provider="Example Marketplace",
            source_type="marketplace_listing",
            reference=f"https://example.test/products/{finding_id}",
            title=f"Listing {finding_id}",
        )

    def finding(self, finding_id):
        return self.orchestration.RawFinding(
            finding_id=finding_id,
            content=f"Raw observation {finding_id}.",
            source=self.source(finding_id),
            observed_at="2026-08-14T08:30:00Z",
            metadata={"adapter": {"rank": finding_id}},
        )

    def acquisition(self, task, status="SUCCESS", findings=()):
        return self.orchestration.AcquisitionResult(
            task_id=task.task_id,
            status=self.orchestration.TaskStatus(status),
            findings=tuple(findings),
        )

    def corrupt_task(self, family):
        task = object.__new__(self.orchestration.ResearchTask)
        for name, value in (
            ("task_id", "corrupted-task"),
            ("research_question", "question"),
            ("source_family", family),
            ("query_intent", "intent"),
            ("evidence_kind", self.policy.EvidenceKind("marketplace_price")),
            ("required", True),
        ):
            object.__setattr__(task, name, value)
        return task

    def corrupt_acquisition(self, task_id):
        result = object.__new__(self.orchestration.AcquisitionResult)
        object.__setattr__(result, "task_id", task_id)
        object.__setattr__(result, "status", self.orchestration.TaskStatus("SUCCESS"))
        object.__setattr__(result, "findings", (self.finding("malformed"),))
        return result

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


class SourceAdapterValueTests(ResearchAdapterTestBase):
    def test_composition_is_frozen_and_has_exactly_five_optional_slots(self):
        fields = dataclasses.fields(self.adapters.ResearchSourceAdapters)
        self.assertTrue(dataclasses.is_dataclass(self.adapters.ResearchSourceAdapters))
        self.assertTrue(self.adapters.ResearchSourceAdapters.__dataclass_params__.frozen)
        self.assertEqual(
            tuple(field.name for field in fields),
            ("search", "marketplace", "consumer_social", "supplier", "regulatory_ip"),
        )
        composition = self.adapters.ResearchSourceAdapters()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            composition.search = lambda _: None
        self.assertFalse(hasattr(self.adapters.ResearchSourceAdapters, "registry"))
        self.assertFalse(hasattr(self.adapters.ResearchSourceAdapters, "factory"))

    def test_slots_accept_only_callables_or_explicit_absence(self):
        self.adapters.ResearchSourceAdapters(
            search=lambda _: None,
            marketplace=None,
            consumer_social=lambda _: None,
            supplier=None,
            regulatory_ip=lambda _: None,
        )
        for field_name in ("search", "marketplace", "consumer_social", "supplier", "regulatory_ip"):
            with self.subTest(field_name=field_name):
                with self.assertRaises((TypeError, ValueError)):
                    self.adapters.ResearchSourceAdapters(**{field_name: object()})


class SourceAdapterRoutingTests(ResearchAdapterTestBase):
    def test_each_family_calls_only_its_matching_slot_once_with_original_task(self):
        calls = []
        outputs = {}

        def make_adapter(family):
            def adapter(task):
                calls.append((family, task))
                return outputs[family]

            return adapter

        tasks = [
            self.task("REGULATORY_IP", "regulatory", "unusual intent"),
            self.task("SEARCH", "search", "unusual intent"),
            self.task("SUPPLIER", "supplier", "unusual intent"),
            self.task("CONSUMER_SOCIAL", "social", "unusual intent"),
            self.task("MARKETPLACE", "marketplace", "unusual intent"),
        ]
        slots = {}
        for family, slot in (
            ("SEARCH", "search"),
            ("MARKETPLACE", "marketplace"),
            ("CONSUMER_SOCIAL", "consumer_social"),
            ("SUPPLIER", "supplier"),
            ("REGULATORY_IP", "regulatory_ip"),
        ):
            outputs[family] = self.acquisition(self.task(family, f"output-{slot}"))
            slots[slot] = make_adapter(family)

        composition = self.adapters.ResearchSourceAdapters(**slots)
        returned = [composition(task) for task in tasks]
        self.assertEqual([family for family, _ in calls], [
            "REGULATORY_IP", "SEARCH", "SUPPLIER", "CONSUMER_SOCIAL", "MARKETPLACE"
        ])
        self.assertEqual([task for _, task in calls], tasks)
        self.assertEqual(len(calls), 5)
        self.assertEqual(returned, [outputs[task.source_family.value] for task in tasks])

    def test_missing_slot_returns_exact_unavailable_result_without_findings(self):
        task = self.task("SUPPLIER")
        result = self.adapters.ResearchSourceAdapters()(task)
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(result.status, self.orchestration.TaskStatus("UNAVAILABLE"))
        self.assertEqual(result.findings, ())

    def test_corrupted_family_is_rejected_before_any_slot_runs(self):
        calls = []
        composition = self.adapters.ResearchSourceAdapters(
            search=lambda task: calls.append(task),
            marketplace=lambda task: calls.append(task),
            consumer_social=lambda task: calls.append(task),
            supplier=lambda task: calls.append(task),
            regulatory_ip=lambda task: calls.append(task),
        )
        with self.assertRaises((TypeError, ValueError)):
            composition(self.corrupt_task("NOT_SUPPORTED"))
        self.assertEqual(calls, [])

    def test_task_validation_precedes_family_dispatch_rejection(self):
        calls = []
        original_validate_task = self.adapters._validate_task

        def validate_task(task):
            calls.append(task)

        self.adapters._validate_task = validate_task
        try:
            composition = self.adapters.ResearchSourceAdapters()
            with self.assertRaisesRegex(TypeError, "task must be a ResearchTask"):
                composition(object())
            self.assertEqual(calls, [])

            task = self.corrupt_task("NOT_SUPPORTED")
            with self.assertRaisesRegex(TypeError, "source_family must be a SourceFamily"):
                composition(task)
        finally:
            self.adapters._validate_task = original_validate_task

        self.assertEqual(calls, [task])

    def test_configured_output_is_returned_by_identity_without_validation_or_repair(self):
        task = self.task("SEARCH")
        malformed = object()
        composition = self.adapters.ResearchSourceAdapters(search=lambda original: malformed)
        self.assertIs(composition(task), malformed)

        findings = (self.finding("z"), self.finding("a"))
        result = self.acquisition(task, findings=findings)
        composition = self.adapters.ResearchSourceAdapters(search=lambda original: result)
        returned = composition(task)
        self.assertIs(returned, result)
        self.assertEqual(returned.findings, findings)

        zero = self.acquisition(task, findings=())
        composition = self.adapters.ResearchSourceAdapters(search=lambda original: zero)
        self.assertIs(composition(task), zero)


class SourceAdapterOrchestrationTests(ResearchAdapterTestBase):
    def run_with(self, tasks, adapter, normalize=None):
        normalize = normalize or (
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding)
        )
        return self.orchestration.run_research(
            self.objective(), lambda _: self.plan(tasks), self.adapters.ResearchSourceAdapters(search=adapter), normalize
        )

    def test_failure_exception_and_invalid_outputs_retain_eco13_classification_and_continue(self):
        tasks = [self.task("SEARCH", f"task-{index}") for index in range(1, 6)]

        def adapter(task):
            if task.task_id == "task-1":
                return self.acquisition(task, status="FAILED")
            if task.task_id == "task-2":
                raise RuntimeError("ordinary adapter error")
            if task.task_id == "task-3":
                return object()
            if task.task_id == "task-4":
                return self.corrupt_acquisition("other-task")
            return self.acquisition(task, findings=(self.finding("survives"),))

        result = self.run_with(tasks, adapter)
        self.assertEqual(
            [str(failure.reason) for failure in result.failures],
            ["ACQUISITION_FAILED", "ACQUISITION_EXCEPTION", "INVALID_ACQUISITION_RESULT", "INVALID_ACQUISITION_RESULT"],
        )
        self.assertEqual([task.task_id for task in result.plan.tasks], [f"task-{index}" for index in range(1, 6)])
        self.assertEqual([str(record.id) for record in result.evidence], ["E001"])

    def test_programmer_control_exceptions_propagate_through_composition_and_run(self):
        task = self.task("SEARCH")
        for error in (KeyboardInterrupt, SystemExit):
            with self.subTest(error=error), self.assertRaises(error):
                self.run_with([task], lambda _: (_ for _ in ()).throw(error()))

    def test_successful_findings_normalize_in_adapter_order_and_zero_findings_fabricate_nothing(self):
        task = self.task("SEARCH")
        findings = (self.finding("z"), self.finding("a"))
        seen = []

        def normalize(current_task, finding, evidence_id):
            seen.append((current_task, finding.finding_id, str(evidence_id)))
            return self.evidence_record(evidence_id, finding)

        result = self.run_with([task], lambda _: self.acquisition(task, findings=findings), normalize)
        self.assertEqual([(item[1], item[2]) for item in seen], [("z", "E001"), ("a", "E002")])
        self.assertEqual(result.evidence, (self.evidence_record(self.evidence.EvidenceId("E001"), findings[0]),
                                           self.evidence_record(self.evidence.EvidenceId("E002"), findings[1])))

        zero = self.run_with([task], lambda _: self.acquisition(task, findings=()))
        self.assertEqual(zero.evidence, ())
        self.assertEqual(zero.task_results[0].status, self.orchestration.TaskStatus("SUCCESS"))

    def test_missing_capability_is_execution_state_without_normalization_or_evidence(self):
        task = self.task("SUPPLIER")
        normalized = []
        result = self.orchestration.run_research(
            self.objective(), lambda _: self.plan([task]), self.adapters.ResearchSourceAdapters(),
            lambda *args: normalized.append(args),
        )
        self.assertEqual([str(failure.reason) for failure in result.failures], ["ACQUISITION_UNAVAILABLE"])
        self.assertEqual(normalized, [])
        self.assertEqual(result.evidence, ())


class SourceAdapterOwnershipTests(ResearchAdapterTestBase):
    def test_module_has_only_standard_library_and_orchestration_boundary_ownership(self):
        original_source = inspect.getsource(self.adapters)
        source = original_source.lower()
        forbidden = (
            "evidence", "provider", "network", "browser", "scrap", "credential", "retry", "caching",
            "rate limit", "async", "concurrency", "persistence", "clock", "random", "llm", "policy",
            "assessment", "economics", "analysis", "scoring", "risk", "red team", "report", "recommend",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)
        tree = ast.parse(original_source)
        forbidden_names = {"Evidence", "EvidenceId", "Tier", "Status", "Confidence"}
        self.assertFalse(
            any(isinstance(node, ast.Name) and node.id in forbidden_names for node in ast.walk(tree))
        )
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(imported_modules.issubset({None, "dataclasses", "typing", "research_orchestration"}))


if __name__ == "__main__":
    unittest.main()
