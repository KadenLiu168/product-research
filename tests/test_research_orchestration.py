import ast
import dataclasses
import importlib
import inspect
import unittest
from types import MappingProxyType


def _orchestration_module():
    try:
        return importlib.import_module("product_research.research_orchestration")
    except ModuleNotFoundError as exc:
        raise AssertionError("research orchestration module has not been implemented") from exc


def _evidence_module():
    return importlib.import_module("product_research.evidence")


def _policy_module():
    return importlib.import_module("product_research.evidence_policy")


class ResearchOrchestrationTestBase(unittest.TestCase):
    def setUp(self):
        self.module = _orchestration_module()
        self.evidence = _evidence_module()
        self.policy = _policy_module()

    def objective(self, objective_id="objective-01"):
        return self.module.ResearchObjective(
            objective_id=objective_id,
            objective="Determine whether the candidate has a viable market.",
        )

    def task(self, task_id="task-01", required=True, evidence_kind="marketplace_price"):
        return self.module.ResearchTask(
            task_id=task_id,
            research_question=f"What is known for {task_id}?",
            source_family=self.module.SourceFamily("MARKETPLACE"),
            query_intent="listed_current_price",
            evidence_kind=self.policy.EvidenceKind(evidence_kind),
            required=required,
        )

    def plan(self, objective_id="objective-01", tasks=()):
        return self.module.ResearchPlan(objective_id=objective_id, tasks=tuple(tasks))

    def source(self, finding_id="finding-01"):
        return self.evidence.Source(
            provider="Example Marketplace",
            source_type="marketplace_listing",
            reference=f"https://example.test/products/{finding_id}",
            title=f"Listing {finding_id}",
        )

    def raw_finding(self, finding_id="finding-01", content=None):
        return self.module.RawFinding(
            finding_id=finding_id,
            content=content or f"The source reported a value for {finding_id}.",
            source=self.source(finding_id),
            observed_at="2026-08-14T08:30:00Z",
            metadata={"adapter": {"rank": 1, "labels": ["raw"]}},
        )

    def acquisition(self, task, status="SUCCESS", findings=()):
        return self.module.AcquisitionResult(
            task_id=task.task_id,
            status=self.module.TaskStatus(status),
            findings=tuple(findings),
        )

    def evidence_record(self, evidence_id, raw=None):
        raw = raw or self.raw_finding()
        return self.evidence.Evidence(
            id=evidence_id,
            claim=f"Claim for {raw.finding_id}.",
            evidence=raw.content,
            source=raw.source,
            observed_at=raw.observed_at,
            tier=self.evidence.Tier("Tier 2"),
            status=self.evidence.Status("Observed"),
            confidence=self.evidence.Confidence("Medium"),
            metadata={"policy": {"kind": "marketplace_price", "source_date": "2026-08-14"}},
        )

    def run_success(self, tasks, findings_by_task=None, normalize=None):
        findings_by_task = findings_by_task or {}
        calls = []

        def planner(objective):
            calls.append(("planner", objective.objective_id))
            return self.plan(objective.objective_id, tasks)

        def acquire(task):
            calls.append(("acquire", task.task_id))
            return self.acquisition(task, findings=findings_by_task.get(task.task_id, ()))

        normalize = normalize or (
            lambda task, raw, evidence_id: self.evidence_record(evidence_id, raw)
        )
        return self.module.run_research(self.objective(), planner, acquire, normalize), calls

    def corrupt_plan(self, objective_id, tasks):
        value = object.__new__(self.module.ResearchPlan)
        object.__setattr__(value, "objective_id", objective_id)
        object.__setattr__(value, "tasks", tuple(tasks))
        return value

    def corrupt_acquisition(self, task_id, status, findings):
        value = object.__new__(self.module.AcquisitionResult)
        object.__setattr__(value, "task_id", task_id)
        object.__setattr__(value, "status", self.module.TaskStatus(status))
        object.__setattr__(value, "findings", tuple(findings))
        return value


class ValueContractTests(ResearchOrchestrationTestBase):
    def test_public_values_are_immutable_and_collections_are_tuples(self):
        objective = self.objective()
        task = self.task()
        plan = self.plan(tasks=[task])
        finding = self.raw_finding()
        acquisition = self.acquisition(task, findings=[finding])

        for value in (objective, task, plan, finding, acquisition):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises((AttributeError, TypeError)):
                    setattr(value, dataclasses.fields(value)[0].name, None)
        self.assertIsInstance(plan.tasks, tuple)
        self.assertIsInstance(acquisition.findings, tuple)

    def test_rejects_empty_strings_without_trimming_or_repairing(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.ResearchObjective(objective_id="", objective="text")
        self.assertEqual(
            self.module.ResearchObjective(objective_id=" objective", objective="text").objective_id,
            " objective",
        )
        with self.assertRaises((TypeError, ValueError)):
            self.module.ResearchTask(
                task_id="task-01",
                research_question="",
                source_family=self.module.SourceFamily("SEARCH"),
                query_intent="intent",
                evidence_kind=self.policy.EvidenceKind("market"),
                required=True,
            )

    def test_task_reuses_existing_evidence_kind_and_requires_exact_boolean(self):
        task = self.task()
        self.assertIs(type(task.evidence_kind), self.policy.EvidenceKind)
        for required in (1, 0, "true", None):
            with self.subTest(required=required), self.assertRaises((TypeError, ValueError)):
                self.task(required=required)
        with self.assertRaises((TypeError, ValueError)):
            self.module.ResearchTask(
                task_id="task-01",
                research_question="question",
                source_family=self.module.SourceFamily("SEARCH"),
                query_intent="intent",
                evidence_kind="market",
                required=True,
            )

    def test_plan_requires_matching_objective_and_unique_task_ids(self):
        mismatched = self.plan(objective_id="other", tasks=[self.task()])
        result = self.module.run_research(
            self.objective(), lambda _: mismatched, lambda _: None, lambda *_: None
        )
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_PLAN"])
        with self.assertRaises((TypeError, ValueError)):
            self.plan(tasks=[self.task("task-01"), self.task("task-01")])
        malformed = self.corrupt_plan(
            "objective-01", [self.task("task-01"), object.__new__(self.module.ResearchTask)]
        )
        malformed_result = self.module.run_research(
            self.objective(), lambda _: malformed, lambda _: None, lambda *_: None
        )
        self.assertEqual(
            [str(failure.reason) for failure in malformed_result.failures], ["INVALID_PLAN"]
        )

    def test_raw_finding_validates_identity_source_time_and_defensive_metadata(self):
        metadata = {"nested": {"value": ["original"]}}
        finding = self.module.RawFinding(
            finding_id="finding-01",
            content="raw content",
            source=self.source(),
            observed_at="2026-08-14T08:30:00Z",
            metadata=metadata,
        )
        metadata["nested"]["value"].append("mutated")
        self.assertEqual(finding.metadata["nested"]["value"], ("original",))
        self.assertFalse(any(field.name in {"id", "evidence_id"} for field in dataclasses.fields(finding)))
        for invalid_time in ("2026-08-14", "2026-08-14T08:30:00+08:00", "2026-08-14T08:30:00.000Z"):
            with self.subTest(invalid_time=invalid_time), self.assertRaises((TypeError, ValueError)):
                self.module.RawFinding(
                    finding_id="finding-01",
                    content="raw content",
                    source=self.source(),
                    observed_at=invalid_time,
                    metadata={},
                )
        for invalid in ("", None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.module.RawFinding(
                    finding_id=invalid,
                    content="raw content",
                    source=self.source(),
                    observed_at="2026-08-14T08:30:00Z",
                    metadata={},
                )
        self.assertEqual(
            self.module.RawFinding(
                finding_id="finding-01 ",
                content="raw content",
                source=self.source(),
                observed_at="2026-08-14T08:30:00Z",
                metadata={},
            ).finding_id,
            "finding-01 ",
        )

    def test_raw_finding_rejects_non_json_metadata_and_missing_core_values(self):
        for metadata in ({"value": object()}, {"": "value"}, [], {"value": float("nan")}):
            with self.subTest(metadata=repr(metadata)), self.assertRaises((TypeError, ValueError)):
                self.module.RawFinding(
                    finding_id="finding-01",
                    content="raw content",
                    source=self.source(),
                    observed_at="2026-08-14T08:30:00Z",
                    metadata=metadata,
                )
        with self.assertRaises((TypeError, ValueError)):
            self.module.RawFinding(
                finding_id="finding-01",
                content="raw content",
                source=object(),
                observed_at="2026-08-14T08:30:00Z",
                metadata={},
            )

    def test_acquisition_result_has_closed_status_and_consistent_findings(self):
        task = self.task()
        finding = self.raw_finding()
        result = self.acquisition(task, findings=[finding])
        self.assertEqual(result.findings, (finding,))
        for status in ("SUCCESS", "UNAVAILABLE", "FAILED"):
            with self.subTest(status=status):
                self.acquisition(task, status=status)
        with self.assertRaises((TypeError, ValueError)):
            self.acquisition(task, status="PARTIAL")
        for status in ("UNAVAILABLE", "FAILED"):
            with self.subTest(status=status), self.assertRaises((TypeError, ValueError)):
                self.acquisition(task, status=status, findings=[finding])

    def test_task_result_rejects_impossible_status_failure_combinations(self):
        task = self.task()
        invalid_results = (
            {
                "status": "UNAVAILABLE",
                "failures": (
                    self.module.ResearchFailure(
                        self.module.FailureReason("ACQUISITION_FAILED"), task_id=task.task_id
                    ),
                ),
            },
            {
                "status": "FAILED",
                "failures": (
                    self.module.ResearchFailure(
                        self.module.FailureReason("ACQUISITION_UNAVAILABLE"), task_id=task.task_id
                    ),
                ),
            },
            {
                "status": "PARTIAL",
                "finding_ids": ("finding-01", "finding-02", "finding-03"),
                "evidence_ids": (self.evidence.EvidenceId("E001"),),
                "failures": (
                    self.module.ResearchFailure(
                        self.module.FailureReason("NORMALIZATION_EXCEPTION"),
                        task_id=task.task_id,
                        finding_id="finding-02",
                    ),
                ),
            },
            {
                "status": "FAILED",
                "finding_ids": ("finding-01", "finding-02"),
                "failures": (
                    self.module.ResearchFailure(
                        self.module.FailureReason("INVALID_EVIDENCE"),
                        task_id=task.task_id,
                        finding_id="finding-02",
                    ),
                    self.module.ResearchFailure(
                        self.module.FailureReason("NORMALIZATION_EXCEPTION"),
                        task_id=task.task_id,
                        finding_id="finding-01",
                    ),
                ),
            },
        )

        for fields in invalid_results:
            with self.subTest(status=fields["status"]), self.assertRaises((TypeError, ValueError)):
                self.module.TaskResult(
                    task=task,
                    status=self.module.TaskStatus(fields["status"]),
                    finding_ids=fields.get("finding_ids", ()),
                    evidence_ids=fields.get("evidence_ids", ()),
                    failures=fields["failures"],
                )

    def test_run_without_plan_requires_one_applicable_run_failure(self):
        objective = self.objective()
        invalid_failures = (
            (),
            (self.module.ResearchFailure(self.module.FailureReason("NORMALIZATION_EXCEPTION")),),
            (
                self.module.ResearchFailure(
                    self.module.FailureReason("INVALID_PLAN"), task_id="task-01"
                ),
            ),
        )

        for failures in invalid_failures:
            with self.subTest(failures=failures), self.assertRaises((TypeError, ValueError)):
                self.module.ResearchRunResult(
                    objective=objective,
                    plan=None,
                    task_results=(),
                    evidence=(),
                    failures=failures,
                    required_task_ids=(),
                    covered_required_task_ids=(),
                    missing_required_task_ids=(),
                    failed_task_ids=(),
                    status=self.module.RunStatus("FAILED"),
                )

    def test_run_result_rejects_evidence_ids_outside_declared_finding_positions(self):
        objective = self.objective()
        task = self.task()
        plan = self.plan(tasks=[task])
        evidence_id = self.evidence.EvidenceId("E999")
        task_result = self.module.TaskResult(
            task=task,
            status=self.module.TaskStatus("SUCCESS"),
            finding_ids=("finding-01",),
            evidence_ids=(evidence_id,),
        )

        with self.assertRaises((TypeError, ValueError)):
            self.module.ResearchRunResult(
                objective=objective,
                plan=plan,
                task_results=(task_result,),
                evidence=(self.evidence_record(evidence_id),),
                failures=(),
                required_task_ids=(task.task_id,),
                covered_required_task_ids=(task.task_id,),
                missing_required_task_ids=(),
                failed_task_ids=(),
                status=self.module.RunStatus("COMPLETE"),
            )


class PlannerAndAcquisitionTests(ResearchOrchestrationTestBase):
    def test_planner_is_called_once_and_acquisition_follows_declared_order(self):
        tasks = [self.task("task-02"), self.task("task-01"), self.task("task-03")]
        findings = {task.task_id: [self.raw_finding(f"{task.task_id}-finding")] for task in tasks}
        result, calls = self.run_success(tasks, findings)

        self.assertEqual([call for call in calls if call[0] == "planner"], [("planner", "objective-01")])
        self.assertEqual(
            [call[1] for call in calls if call[0] == "acquire"],
            ["task-02", "task-01", "task-03"],
        )
        self.assertEqual([str(record.id) for record in result.evidence], ["E001", "E002", "E003"])

    def test_malformed_planner_output_fails_before_acquisition(self):
        task = self.task()
        malformed = self.corrupt_plan("other-objective", [task])
        acquired = []
        result = self.module.run_research(
            self.objective(), lambda _: malformed, lambda task: acquired.append(task), lambda *_: None
        )

        self.assertEqual(result.status, self.module.RunStatus("FAILED"))
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_PLAN"])
        self.assertIsNone(result.plan)
        self.assertEqual(acquired, [])
        self.assertEqual(result.evidence, ())

    def test_duplicate_or_malformed_planner_tasks_fail_closed(self):
        task = self.task()
        planner_results = (
            ("duplicate", self.corrupt_plan("objective-01", [task, task])),
            ("malformed", self.corrupt_plan("objective-01", [object.__new__(self.module.ResearchTask)])),
        )
        for label, planner_result in planner_results:
            with self.subTest(label=label):
                acquired = []
                result = self.module.run_research(
                    self.objective(), lambda _: planner_result, lambda task: acquired.append(task), lambda *_: None
                )
                self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_PLAN"])
                self.assertEqual(acquired, [])

    def test_planner_exception_is_structured_and_does_not_fabricate_evidence(self):
        def planner(_):
            raise RuntimeError("planner details must not become a domain record")

        result = self.module.run_research(self.objective(), planner, lambda _: None, lambda *_: None)

        self.assertEqual(result.status, self.module.RunStatus("FAILED"))
        self.assertEqual([str(failure.reason) for failure in result.failures], ["PLANNER_EXCEPTION"])
        self.assertIsNone(result.plan)
        self.assertEqual(result.evidence, ())

    def test_matching_successful_result_preserves_finding_order(self):
        task = self.task()
        findings = [self.raw_finding("finding-z"), self.raw_finding("finding-a")]
        seen = []

        def normalize(current_task, finding, evidence_id):
            seen.append((current_task.task_id, finding.finding_id, str(evidence_id)))
            return self.evidence_record(evidence_id, finding)

        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=[task]), lambda _: self.acquisition(task, findings=findings), normalize
        )

        self.assertEqual(seen, [("task-01", "finding-z", "E001"), ("task-01", "finding-a", "E002")])
        self.assertEqual([str(record.id) for record in result.evidence], ["E001", "E002"])

    def test_mismatched_or_malformed_acquisition_result_fails_only_current_task(self):
        first = self.task("task-01")
        second = self.task("task-02")
        calls = []

        def acquire(task):
            calls.append(task.task_id)
            if task.task_id == "task-01":
                return self.corrupt_acquisition("task-02", "SUCCESS", [self.raw_finding()])
            return self.acquisition(task, findings=[self.raw_finding("second-finding")])

        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=[first, second]), acquire,
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding),
        )

        self.assertEqual(calls, ["task-01", "task-02"])
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_ACQUISITION_RESULT"])
        self.assertEqual([str(record.id) for record in result.evidence], ["E001"])
        self.assertEqual(result.task_results[0].status, self.module.TaskStatus("FAILED"))

    def test_duplicate_finding_identity_fails_before_normalization(self):
        task = self.task()
        duplicate = self.corrupt_acquisition(
            task.task_id, "SUCCESS", [self.raw_finding("same"), self.raw_finding("same")]
        )
        normalized = []
        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=[task]), lambda _: duplicate,
            lambda *args: normalized.append(args),
        )

        self.assertEqual(normalized, [])
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_ACQUISITION_RESULT"])

    def test_corrupted_raw_finding_metadata_fails_before_normalization(self):
        task = self.task()
        finding = object.__new__(self.module.RawFinding)
        object.__setattr__(finding, "finding_id", "finding-01")
        object.__setattr__(finding, "content", "raw content")
        object.__setattr__(finding, "source", self.source())
        object.__setattr__(finding, "observed_at", "2026-08-14T08:30:00Z")
        object.__setattr__(finding, "metadata", MappingProxyType({"bad": object()}))
        acquisition = self.corrupt_acquisition(task.task_id, "SUCCESS", [finding])
        normalized = []
        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=[task]), lambda _: acquisition,
            lambda *args: normalized.append(args),
        )

        self.assertEqual(normalized, [])
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_ACQUISITION_RESULT"])

    def test_unavailable_failed_and_exception_tasks_continue_in_order(self):
        tasks = [self.task("unavailable"), self.task("exception"), self.task("failed"), self.task("success")]
        calls = []

        def acquire(task):
            calls.append(task.task_id)
            if task.task_id == "unavailable":
                return self.acquisition(task, status="UNAVAILABLE")
            if task.task_id == "failed":
                return self.acquisition(task, status="FAILED")
            if task.task_id == "exception":
                raise RuntimeError("adapter error")
            return self.acquisition(task, findings=[self.raw_finding("success-finding")])

        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=tasks), acquire,
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding),
        )

        self.assertEqual(calls, [task.task_id for task in tasks])
        self.assertEqual(
            [str(failure.reason) for failure in result.failures],
            ["ACQUISITION_UNAVAILABLE", "ACQUISITION_EXCEPTION", "ACQUISITION_FAILED"],
        )
        self.assertEqual(result.failed_task_ids, ("unavailable", "exception", "failed"))
        self.assertEqual([str(record.id) for record in result.evidence], ["E001"])

    def test_programmer_control_exceptions_are_not_swallowed(self):
        task = self.task()

        def acquire(_):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self.module.run_research(
                self.objective(), lambda _: self.plan(tasks=[task]), acquire, lambda *_: None
            )


class NormalizationAndResultTests(ResearchOrchestrationTestBase):
    def test_normalization_accepts_only_round_trippable_existing_evidence_with_allocated_id(self):
        task = self.task()
        finding = self.raw_finding()
        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=[task]), lambda _: self.acquisition(task, findings=[finding]),
            lambda current_task, raw, evidence_id: self.evidence_record(evidence_id, raw),
        )

        self.assertEqual(type(result.evidence[0]), self.evidence.Evidence)
        self.assertEqual(result.evidence[0], self.evidence.Evidence.from_json(result.evidence[0].to_json()))
        self.assertEqual(result.evidence[0].id, self.evidence.EvidenceId("E001"))

    def test_normalization_exception_wrong_type_corruption_and_mismatched_id_are_isolated(self):
        tasks = [self.task("exception"), self.task("wrong"), self.task("corrupt"), self.task("mismatch"), self.task("good")]
        findings = {task.task_id: [self.raw_finding(task.task_id)] for task in tasks}

        def normalize(task, finding, evidence_id):
            if task.task_id == "exception":
                raise RuntimeError("normalizer error")
            if task.task_id == "wrong":
                return object()
            if task.task_id == "corrupt":
                value = self.evidence_record(evidence_id, finding)
                object.__setattr__(value, "status", "Observed")
                return value
            if task.task_id == "mismatch":
                return self.evidence_record(self.evidence.EvidenceId("E999"), finding)
            return self.evidence_record(evidence_id, finding)

        result, _ = self.run_success(tasks, findings, normalize)

        self.assertEqual(
            [str(failure.reason) for failure in result.failures],
            ["NORMALIZATION_EXCEPTION", "INVALID_EVIDENCE", "INVALID_EVIDENCE", "INVALID_EVIDENCE"],
        )
        self.assertEqual(
            [(failure.task_id, failure.finding_id) for failure in result.failures],
            [("exception", "exception"), ("wrong", "wrong"), ("corrupt", "corrupt"), ("mismatch", "mismatch")],
        )
        self.assertEqual([str(record.id) for record in result.evidence], ["E005"])

    def test_ids_are_position_based_not_lexical_and_failed_positions_leave_gaps(self):
        tasks = [self.task("task-01"), self.task("task-02")]
        findings = {
            "task-01": [self.raw_finding("finding-z"), self.raw_finding("finding-a")],
            "task-02": [self.raw_finding("finding-m")],
        }
        seen = []

        def normalize(task, finding, evidence_id):
            seen.append((finding.finding_id, str(evidence_id)))
            if evidence_id.value == "E002":
                raise RuntimeError("one finding fails")
            return self.evidence_record(evidence_id, finding)

        result, _ = self.run_success(tasks, findings, normalize)

        self.assertEqual(seen, [("finding-z", "E001"), ("finding-a", "E002"), ("finding-m", "E003")])
        self.assertEqual([str(record.id) for record in result.evidence], ["E001", "E003"])

    def test_task_statuses_cover_success_partial_unavailable_and_failed(self):
        tasks = [self.task("success"), self.task("partial"), self.task("unavailable"), self.task("failed")]

        def acquire(task):
            if task.task_id == "unavailable":
                return self.acquisition(task, status="UNAVAILABLE")
            if task.task_id == "failed":
                return self.acquisition(task, status="FAILED")
            if task.task_id == "partial":
                return self.acquisition(task, findings=[self.raw_finding("ok"), self.raw_finding("bad")])
            return self.acquisition(task, findings=[self.raw_finding("success-finding")])

        def normalize(task, finding, evidence_id):
            if task.task_id == "partial" and finding.finding_id == "bad":
                raise RuntimeError("bad finding")
            return self.evidence_record(evidence_id, finding)

        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=tasks), acquire, normalize
        )

        self.assertEqual(
            [str(task_result.status) for task_result in result.task_results],
            ["SUCCESS", "PARTIAL", "UNAVAILABLE", "FAILED"],
        )
        self.assertEqual(
            [(failure.task_id, failure.finding_id) for failure in result.failures],
            [("partial", "bad"), ("unavailable", None), ("failed", None)],
        )

    def test_zero_findings_and_all_failed_runs_do_not_fabricate_evidence(self):
        tasks = [self.task("zero"), self.task("failed")]

        def acquire(task):
            if task.task_id == "zero":
                return self.acquisition(task, findings=[])
            return self.acquisition(task, status="FAILED")

        result = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=tasks), acquire, lambda *_: None
        )

        self.assertEqual(result.status, self.module.RunStatus("FAILED"))
        self.assertEqual(result.evidence, ())
        self.assertEqual(result.task_results[0].status, self.module.TaskStatus("SUCCESS"))
        self.assertEqual(result.required_task_ids, ("zero", "failed"))

    def test_coverage_and_run_status_use_required_tasks_only_and_fixed_precedence(self):
        complete_tasks = [self.task("required", required=True), self.task("optional", required=False)]
        complete_result, _ = self.run_success(
            complete_tasks,
            {"required": [self.raw_finding("required-finding")], "optional": [self.raw_finding("optional-finding")]},
        )
        self.assertEqual(complete_result.status, self.module.RunStatus("COMPLETE"))
        self.assertEqual(complete_result.required_task_ids, ("required",))
        self.assertEqual(complete_result.covered_required_task_ids, ("required",))
        self.assertEqual(complete_result.missing_required_task_ids, ())

        optional_failure = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=complete_tasks),
            lambda task: self.acquisition(
                task,
                status="FAILED" if task.task_id == "optional" else "SUCCESS",
                findings=[] if task.task_id == "optional" else [self.raw_finding("required-finding")],
            ),
            lambda task, finding, evidence_id: self.evidence_record(evidence_id, finding),
        )
        self.assertEqual(optional_failure.status, self.module.RunStatus("COMPLETE"))
        self.assertEqual(optional_failure.missing_required_task_ids, ())
        self.assertEqual(optional_failure.failed_task_ids, ("optional",))

        partial = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=complete_tasks),
            lambda task: self.acquisition(
                task, findings=[self.raw_finding("required-finding")] if task.task_id == "required" else []
            ),
            lambda task, finding, evidence_id: (
                (_ for _ in ()).throw(RuntimeError("required normalization fails"))
                if task.task_id == "required"
                else self.evidence_record(evidence_id, finding)
            ),
        )
        self.assertEqual(partial.status, self.module.RunStatus("FAILED"))
        self.assertEqual(partial.missing_required_task_ids, ("required",))

        useful_partial = self.module.run_research(
            self.objective(), lambda _: self.plan(tasks=complete_tasks),
            lambda task: self.acquisition(
                task, findings=[self.raw_finding("required-finding"), self.raw_finding("required-finding-2")]
                if task.task_id == "required" else [],
            ),
            lambda task, finding, evidence_id: (
                (_ for _ in ()).throw(RuntimeError("one required normalization fails"))
                if finding.finding_id == "required-finding-2"
                else self.evidence_record(evidence_id, finding)
            ),
        )
        self.assertEqual(useful_partial.status, self.module.RunStatus("PARTIAL"))
        self.assertEqual(useful_partial.missing_required_task_ids, ("required",))
        self.assertEqual(useful_partial.failed_task_ids, ("required",))

    def test_replay_of_equivalent_inputs_is_structurally_equal_and_immutable(self):
        tasks = [self.task("task-02"), self.task("task-01")]
        findings = {
            "task-02": [self.raw_finding("finding-02")],
            "task-01": [self.raw_finding("finding-01")],
        }
        first, _ = self.run_success(tasks, findings)
        second, _ = self.run_success(tasks, findings)

        self.assertEqual(first, second)
        with self.assertRaises((AttributeError, TypeError)):
            first.task_results = ()


class OwnershipAuditTests(ResearchOrchestrationTestBase):
    def test_module_owns_only_control_plane_and_reuses_existing_evidence_contract(self):
        original_source = inspect.getsource(self.module)
        source = original_source.lower()
        forbidden = (
            "requests", "httpx", "urllib", "scrap", "authentication", "retry", "caching", "rate limiting",
            "async", "sqlite", "persistence", "random", "clock", "llm", "validate_evidence",
            "evidence_assessment", "unit_economics", "scoring", "risk", "red team", "report",
            "decision label",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)
        tree = ast.parse(original_source)
        self.assertFalse(any(isinstance(node, ast.ClassDef) and node.name == "Evidence" for node in ast.walk(tree)))
        imported_names = {
            alias.name.split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertIn("Evidence", imported_names)
        self.assertIn("EvidenceKind", imported_names)


class SourceFamilyTests(ResearchOrchestrationTestBase):
    def source_family_task(self, source_family, query_intent="caller-defined intent"):
        return self.module.ResearchTask(
            task_id="task-01",
            research_question="Which source family can answer this?",
            source_family=source_family,
            query_intent=query_intent,
            evidence_kind=self.policy.EvidenceKind("marketplace_price"),
            required=True,
        )

    def test_source_family_accepts_only_the_exact_closed_vocabulary(self):
        expected = ("SEARCH", "MARKETPLACE", "CONSUMER_SOCIAL", "SUPPLIER", "REGULATORY_IP")
        actual = tuple(self.module.SourceFamily(value).value for value in expected)
        self.assertEqual(actual, expected)
        for value in ("search", "", "OTHER", None, 1):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.module.SourceFamily(value)
        family = self.module.SourceFamily("SEARCH")
        with self.assertRaises(AttributeError):
            family._value = "MARKETPLACE"

    def test_research_task_and_plan_require_exact_source_family_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.source_family_task("SEARCH")

        corrupted = object.__new__(self.module.ResearchTask)
        for name, value in (
            ("task_id", "task-01"),
            ("research_question", "question"),
            ("source_family", "SEARCH"),
            ("query_intent", "intent"),
            ("evidence_kind", self.policy.EvidenceKind("marketplace_price")),
            ("required", True),
        ):
            object.__setattr__(corrupted, name, value)
        malformed_plan = self.corrupt_plan("objective-01", [corrupted])
        acquired = []
        result = self.module.run_research(
            self.objective(), lambda _: malformed_plan, lambda task: acquired.append(task), lambda *_: None
        )
        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_PLAN"])
        self.assertEqual(acquired, [])

    def test_plan_rejects_corrupted_exact_source_family_before_acquisition(self):
        corrupted_family = object.__new__(self.module.SourceFamily)
        object.__setattr__(corrupted_family, "_value", "NOT_SUPPORTED")
        corrupted_task = object.__new__(self.module.ResearchTask)
        for name, value in (
            ("task_id", "task-01"),
            ("research_question", "question"),
            ("source_family", corrupted_family),
            ("query_intent", "intent"),
            ("evidence_kind", self.policy.EvidenceKind("marketplace_price")),
            ("required", True),
        ):
            object.__setattr__(corrupted_task, name, value)
        malformed_plan = self.corrupt_plan("objective-01", [corrupted_task])
        acquired = []

        result = self.module.run_research(
            self.objective(), lambda _: malformed_plan, lambda task: acquired.append(task), lambda *_: None
        )

        self.assertEqual([str(failure.reason) for failure in result.failures], ["INVALID_PLAN"])
        self.assertEqual(acquired, [])

    def test_valid_source_family_and_query_intent_are_preserved_without_taxonomy(self):
        for value in ("SEARCH", "MARKETPLACE", "CONSUMER_SOCIAL", "SUPPLIER", "REGULATORY_IP"):
            with self.subTest(value=value):
                family = self.module.SourceFamily(value)
                task = self.source_family_task(family, query_intent="  caller intent / v9  ")
                self.assertEqual(task.source_family, family)
                self.assertEqual(task.query_intent, "  caller intent / v9  ")


if __name__ == "__main__":
    unittest.main()
