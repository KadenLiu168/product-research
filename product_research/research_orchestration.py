from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, Tuple

from .evidence import (
    Evidence,
    EvidenceId,
    Source,
    _ConstrainedValue,
    _require_non_empty_string,
    _validate_metadata,
    _validate_observed_at,
)
from .evidence_policy import EvidenceKind


class TaskStatus(_ConstrainedValue):
    _allowed = ("SUCCESS", "PARTIAL", "UNAVAILABLE", "FAILED")


class FailureReason(_ConstrainedValue):
    _allowed = (
        "PLANNER_EXCEPTION",
        "INVALID_PLAN",
        "ACQUISITION_UNAVAILABLE",
        "ACQUISITION_FAILED",
        "ACQUISITION_EXCEPTION",
        "INVALID_ACQUISITION_RESULT",
        "NORMALIZATION_EXCEPTION",
        "INVALID_EVIDENCE",
    )


class RunStatus(_ConstrainedValue):
    _allowed = ("COMPLETE", "PARTIAL", "FAILED")


def _require_exact_string(value, field_name):
    _require_non_empty_string(value, field_name)


def _freeze_json(value, path):
    checked = _validate_metadata(value, path)
    if type(checked) is dict:
        return MappingProxyType({key: _freeze_json(item, f"{path}.{key}") for key, item in checked.items()})
    if type(checked) is list:
        return tuple(_freeze_json(item, f"{path}[]") for item in checked)
    return checked


def _validate_frozen_json(value, path):
    if type(value) is MappingProxyType:
        for key, item in value.items():
            _require_exact_string(key, f"{path} key")
            _validate_frozen_json(item, f"{path}.{key}")
        return
    if type(value) is tuple:
        for item in value:
            _validate_frozen_json(item, f"{path}[]")
        return
    _validate_metadata(value, path)


def _validate_objective(value):
    if type(value) is not ResearchObjective:
        raise TypeError("objective must be a ResearchObjective")
    _require_exact_string(value.objective_id, "objective_id")
    _require_exact_string(value.objective, "objective")


def _validate_task(value):
    if type(value) is not ResearchTask:
        raise TypeError("task must be a ResearchTask")
    _require_exact_string(value.task_id, "task_id")
    _require_exact_string(value.research_question, "research_question")
    _require_exact_string(value.source_family, "source_family")
    _require_exact_string(value.query_intent, "query_intent")
    if type(value.evidence_kind) is not EvidenceKind:
        raise TypeError("evidence_kind must be an EvidenceKind")
    if type(value.required) is not bool:
        raise TypeError("required must be a boolean")


def _validate_finding(value):
    if type(value) is not RawFinding:
        raise TypeError("finding must be a RawFinding")
    _require_exact_string(value.finding_id, "finding_id")
    _require_exact_string(value.content, "content")
    if type(value.source) is not Source:
        raise TypeError("source must be a Source")
    _validate_observed_at(value.observed_at)
    if type(value.metadata) is not MappingProxyType:
        raise TypeError("metadata must be an immutable JSON object")
    _validate_frozen_json(value.metadata, "metadata")


def _validate_plan(value):
    if type(value) is not ResearchPlan:
        raise TypeError("planner must return a ResearchPlan")
    _require_exact_string(value.objective_id, "objective_id")
    if type(value.tasks) is not tuple:
        raise TypeError("tasks must be a tuple")
    task_ids = set()
    for task in value.tasks:
        _validate_task(task)
        if task.task_id in task_ids:
            raise ValueError("task identities must be unique")
        task_ids.add(task.task_id)


def _validate_acquisition(value):
    if type(value) is not AcquisitionResult:
        raise TypeError("acquire must return an AcquisitionResult")
    _require_exact_string(value.task_id, "task_id")
    if type(value.status) is not TaskStatus:
        raise TypeError("acquisition status must be a TaskStatus")
    if value.status.value not in ("SUCCESS", "UNAVAILABLE", "FAILED"):
        raise ValueError("unsupported acquisition status")
    if type(value.findings) is not tuple:
        raise TypeError("findings must be a tuple")
    finding_ids = set()
    for finding in value.findings:
        _validate_finding(finding)
        if finding.finding_id in finding_ids:
            raise ValueError("finding identities must be unique within a task")
        finding_ids.add(finding.finding_id)
    if value.status.value != "SUCCESS" and value.findings:
        raise ValueError("non-success acquisition results cannot contain findings")


def _validate_failure(value):
    if type(value) is not ResearchFailure:
        raise TypeError("failures must be ResearchFailure values")
    if type(value.reason) is not FailureReason:
        raise TypeError("reason must be a FailureReason")
    if value.task_id is not None:
        _require_exact_string(value.task_id, "task_id")
    if value.finding_id is not None:
        if value.task_id is None:
            raise ValueError("finding_id requires task_id")
        _require_exact_string(value.finding_id, "finding_id")


@dataclass(frozen=True)
class ResearchObjective:
    objective_id: str
    objective: str

    def __post_init__(self):
        _require_exact_string(self.objective_id, "objective_id")
        _require_exact_string(self.objective, "objective")


@dataclass(frozen=True)
class ResearchTask:
    task_id: str
    research_question: str
    source_family: str
    query_intent: str
    evidence_kind: EvidenceKind
    required: bool

    def __post_init__(self):
        _validate_task(self)


@dataclass(frozen=True)
class ResearchPlan:
    objective_id: str
    tasks: Tuple[ResearchTask, ...]

    def __post_init__(self):
        object.__setattr__(self, "tasks", tuple(self.tasks))
        _validate_plan(self)


@dataclass(frozen=True)
class RawFinding:
    finding_id: str
    content: str
    source: Source
    observed_at: str
    metadata: dict

    def __post_init__(self):
        _require_exact_string(self.finding_id, "finding_id")
        _require_exact_string(self.content, "content")
        if type(self.source) is not Source:
            raise TypeError("source must be a Source")
        _validate_observed_at(self.observed_at)
        if type(self.metadata) is not dict:
            raise TypeError("metadata must be a JSON object")
        object.__setattr__(self, "metadata", _freeze_json(self.metadata, "metadata"))


@dataclass(frozen=True)
class AcquisitionResult:
    task_id: str
    status: TaskStatus
    findings: Tuple[RawFinding, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "findings", tuple(self.findings))
        _validate_acquisition(self)


@dataclass(frozen=True)
class ResearchFailure:
    reason: FailureReason
    task_id: Optional[str] = None
    finding_id: Optional[str] = None

    def __post_init__(self):
        _validate_failure(self)


@dataclass(frozen=True)
class TaskResult:
    task: ResearchTask
    status: TaskStatus
    finding_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[EvidenceId, ...] = ()
    failures: Tuple[ResearchFailure, ...] = ()

    def __post_init__(self):
        _validate_task(self.task)
        if type(self.status) is not TaskStatus:
            raise TypeError("status must be a TaskStatus")
        finding_ids = tuple(self.finding_ids)
        evidence_ids = tuple(self.evidence_ids)
        failures = tuple(self.failures)
        object.__setattr__(self, "finding_ids", finding_ids)
        object.__setattr__(self, "evidence_ids", evidence_ids)
        object.__setattr__(self, "failures", failures)
        if len(set(finding_ids)) != len(finding_ids):
            raise ValueError("finding identities must be unique")
        for finding_id in finding_ids:
            _require_exact_string(finding_id, "finding_id")
        for evidence_id in evidence_ids:
            if type(evidence_id) is not EvidenceId:
                raise TypeError("evidence_ids must contain EvidenceId values")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("Evidence IDs must be unique")
        for failure in failures:
            _validate_failure(failure)
            if failure.task_id != self.task.task_id:
                raise ValueError("failure task identity does not match task result")
            if failure.finding_id is not None and failure.finding_id not in finding_ids:
                raise ValueError("failure finding identity does not match task result")
        normalization_failure_ids = tuple(
            failure.finding_id
            for failure in failures
            if failure.reason.value in ("NORMALIZATION_EXCEPTION", "INVALID_EVIDENCE")
            and failure.finding_id is not None
        )
        normalization_failure_id_set = set(normalization_failure_ids)
        expected_normalization_failure_ids = tuple(
            finding_id for finding_id in finding_ids if finding_id in normalization_failure_id_set
        )
        if normalization_failure_ids != expected_normalization_failure_ids:
            raise ValueError("normalization failure order does not match finding order")
        if self.status.value == "SUCCESS":
            if failures or len(evidence_ids) != len(finding_ids):
                raise ValueError("successful task result has inconsistent outcomes")
        elif self.status.value == "PARTIAL":
            if (
                not evidence_ids
                or len(normalization_failure_ids) != len(failures)
                or len(set(normalization_failure_ids)) != len(normalization_failure_ids)
                or len(evidence_ids) + len(failures) != len(finding_ids)
            ):
                raise ValueError("partial task result has inconsistent outcomes")
        elif self.status.value == "UNAVAILABLE":
            if (
                finding_ids
                or evidence_ids
                or len(failures) != 1
                or failures[0].reason.value != "ACQUISITION_UNAVAILABLE"
                or failures[0].finding_id is not None
            ):
                raise ValueError("unavailable task result has inconsistent outcomes")
        elif self.status.value == "FAILED":
            if evidence_ids or not failures:
                raise ValueError("failed task result has inconsistent outcomes")
            if finding_ids:
                if (
                    len(normalization_failure_ids) != len(failures)
                    or len(set(normalization_failure_ids)) != len(normalization_failure_ids)
                    or len(failures) != len(finding_ids)
                ):
                    raise ValueError("failed task result has inconsistent outcomes")
            elif (
                len(failures) != 1
                or failures[0].reason.value
                not in ("ACQUISITION_FAILED", "ACQUISITION_EXCEPTION", "INVALID_ACQUISITION_RESULT")
                or failures[0].finding_id is not None
            ):
                raise ValueError("failed task result has inconsistent outcomes")
        else:
            raise ValueError("unsupported task result status")


@dataclass(frozen=True)
class ResearchRunResult:
    objective: ResearchObjective
    plan: Optional[ResearchPlan]
    task_results: Tuple[TaskResult, ...]
    evidence: Tuple[Evidence, ...]
    failures: Tuple[ResearchFailure, ...]
    required_task_ids: Tuple[str, ...]
    covered_required_task_ids: Tuple[str, ...]
    missing_required_task_ids: Tuple[str, ...]
    failed_task_ids: Tuple[str, ...]
    status: RunStatus

    def __post_init__(self):
        _validate_objective(self.objective)
        task_results = tuple(self.task_results)
        evidence = tuple(self.evidence)
        failures = tuple(self.failures)
        required_task_ids = tuple(self.required_task_ids)
        covered_required_task_ids = tuple(self.covered_required_task_ids)
        missing_required_task_ids = tuple(self.missing_required_task_ids)
        failed_task_ids = tuple(self.failed_task_ids)
        object.__setattr__(self, "task_results", task_results)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "failures", failures)
        object.__setattr__(self, "required_task_ids", required_task_ids)
        object.__setattr__(self, "covered_required_task_ids", covered_required_task_ids)
        object.__setattr__(self, "missing_required_task_ids", missing_required_task_ids)
        object.__setattr__(self, "failed_task_ids", failed_task_ids)
        for item in task_results:
            if type(item) is not TaskResult:
                raise TypeError("task_results must contain TaskResult values")
        for item in evidence:
            if type(item) is not Evidence:
                raise TypeError("evidence must contain Evidence values")
        for failure in failures:
            _validate_failure(failure)
        if type(self.status) is not RunStatus:
            raise TypeError("status must be a RunStatus")
        if self.plan is None:
            if task_results or evidence or any(
                collection
                for collection in (
                    self.required_task_ids,
                    self.covered_required_task_ids,
                    self.missing_required_task_ids,
                    self.failed_task_ids,
                )
            ):
                raise ValueError("a run without a plan cannot contain task outcomes")
            if self.status.value != "FAILED":
                raise ValueError("a run without a plan must be failed")
            if (
                len(failures) != 1
                or failures[0].reason.value not in ("PLANNER_EXCEPTION", "INVALID_PLAN")
                or failures[0].task_id is not None
                or failures[0].finding_id is not None
            ):
                raise ValueError("a run without a plan must contain one run-level failure")
            return
        _validate_plan(self.plan)
        if self.plan.objective_id != self.objective.objective_id:
            raise ValueError("plan objective identity does not match result objective")
        if len(task_results) != len(self.plan.tasks):
            raise ValueError("task result count does not match plan")
        for expected, actual in zip(self.plan.tasks, task_results):
            if actual.task != expected:
                raise ValueError("task result order does not match plan")
        expected_failures = tuple(failure for item in task_results for failure in item.failures)
        if failures != expected_failures:
            raise ValueError("failure order does not match task result order")
        next_evidence_number = 1
        for item in task_results:
            failed_finding_ids = {failure.finding_id for failure in item.failures if failure.finding_id is not None}
            expected_task_evidence_ids = []
            for finding_id in item.finding_ids:
                evidence_id = EvidenceId(f"E{next_evidence_number:03d}")
                next_evidence_number += 1
                if finding_id not in failed_finding_ids:
                    expected_task_evidence_ids.append(evidence_id)
            if item.evidence_ids != tuple(expected_task_evidence_ids):
                raise ValueError("Evidence IDs do not match declared finding positions")
        expected_evidence_ids = tuple(evidence_id for item in task_results for evidence_id in item.evidence_ids)
        actual_evidence_ids = tuple(item.id for item in evidence)
        if actual_evidence_ids != expected_evidence_ids:
            raise ValueError("Evidence order does not match task result order")
        required_ids = tuple(task.task_id for task in self.plan.tasks if task.required)
        covered_ids = tuple(
            item.task.task_id for item in task_results if item.task.required and item.status.value == "SUCCESS"
        )
        missing_ids = tuple(task_id for task_id in required_ids if task_id not in covered_ids)
        failed_ids = tuple(
            item.task.task_id
            for item in task_results
            if item.status.value in ("PARTIAL", "UNAVAILABLE", "FAILED")
        )
        for actual, expected in (
            (self.required_task_ids, required_ids),
            (self.covered_required_task_ids, covered_ids),
            (self.missing_required_task_ids, missing_ids),
            (self.failed_task_ids, failed_ids),
        ):
            if tuple(actual) != expected:
                raise ValueError("coverage values do not match task outcomes")
        expected_status = "FAILED" if not evidence else "PARTIAL" if missing_ids else "COMPLETE"
        if self.status.value != expected_status:
            raise ValueError("run status does not match outcomes")


def _failure(reason, task_id=None, finding_id=None):
    return ResearchFailure(FailureReason(reason), task_id=task_id, finding_id=finding_id)


def _failed_without_plan(objective, failure):
    return ResearchRunResult(
        objective=objective,
        plan=None,
        task_results=(),
        evidence=(),
        failures=(failure,),
        required_task_ids=(),
        covered_required_task_ids=(),
        missing_required_task_ids=(),
        failed_task_ids=(),
        status=RunStatus("FAILED"),
    )


def _validate_normalized_evidence(value, evidence_id):
    if type(value) is not Evidence:
        raise TypeError("normalizer must return an Evidence")
    if value.id != evidence_id:
        raise ValueError("normalized Evidence ID does not match allocated ID")
    reconstructed = Evidence.from_json(value.to_json())
    if reconstructed != value:
        raise ValueError("normalized Evidence failed structural round trip")


def run_research(objective, planner, acquire, normalize):
    _validate_objective(objective)
    try:
        plan = planner(objective)
    except Exception:
        return _failed_without_plan(objective, _failure("PLANNER_EXCEPTION"))
    try:
        _validate_plan(plan)
        if plan.objective_id != objective.objective_id:
            raise ValueError("plan objective identity does not match objective")
    except Exception:
        return _failed_without_plan(objective, _failure("INVALID_PLAN"))

    task_results = []
    accepted_evidence = []
    failures = []
    next_evidence_number = 1

    for task in plan.tasks:
        try:
            acquisition = acquire(task)
        except Exception:
            failure = _failure("ACQUISITION_EXCEPTION", task.task_id)
            task_results.append(TaskResult(task, TaskStatus("FAILED"), failures=(failure,)))
            failures.append(failure)
            continue
        try:
            _validate_acquisition(acquisition)
            if acquisition.task_id != task.task_id:
                raise ValueError("acquisition task identity does not match task")
        except Exception:
            failure = _failure("INVALID_ACQUISITION_RESULT", task.task_id)
            task_results.append(TaskResult(task, TaskStatus("FAILED"), failures=(failure,)))
            failures.append(failure)
            continue

        if acquisition.status.value == "UNAVAILABLE":
            failure = _failure("ACQUISITION_UNAVAILABLE", task.task_id)
            task_result = TaskResult(task, TaskStatus("UNAVAILABLE"), failures=(failure,))
            task_results.append(task_result)
            failures.append(failure)
            continue
        if acquisition.status.value == "FAILED":
            failure = _failure("ACQUISITION_FAILED", task.task_id)
            task_result = TaskResult(task, TaskStatus("FAILED"), failures=(failure,))
            task_results.append(task_result)
            failures.append(failure)
            continue

        finding_ids = tuple(finding.finding_id for finding in acquisition.findings)
        evidence_ids = []
        task_failures = []
        for finding in acquisition.findings:
            evidence_id = EvidenceId(f"E{next_evidence_number:03d}")
            next_evidence_number += 1
            try:
                normalized = normalize(task, finding, evidence_id)
            except Exception:
                failure = _failure("NORMALIZATION_EXCEPTION", task.task_id, finding.finding_id)
                task_failures.append(failure)
                failures.append(failure)
                continue
            try:
                _validate_normalized_evidence(normalized, evidence_id)
            except Exception:
                failure = _failure("INVALID_EVIDENCE", task.task_id, finding.finding_id)
                task_failures.append(failure)
                failures.append(failure)
                continue
            accepted_evidence.append(normalized)
            evidence_ids.append(evidence_id)

        if not task_failures:
            task_status = TaskStatus("SUCCESS")
        elif evidence_ids:
            task_status = TaskStatus("PARTIAL")
        else:
            task_status = TaskStatus("FAILED")
        task_results.append(
            TaskResult(
                task=task,
                status=task_status,
                finding_ids=finding_ids,
                evidence_ids=tuple(evidence_ids),
                failures=tuple(task_failures),
            )
        )

    required_task_ids = tuple(task.task_id for task in plan.tasks if task.required)
    covered_required_task_ids = tuple(
        item.task.task_id for item in task_results if item.task.required and item.status.value == "SUCCESS"
    )
    missing_required_task_ids = tuple(
        task_id for task_id in required_task_ids if task_id not in covered_required_task_ids
    )
    failed_task_ids = tuple(
        item.task.task_id
        for item in task_results
        if item.status.value in ("PARTIAL", "UNAVAILABLE", "FAILED")
    )
    status = RunStatus("FAILED" if not accepted_evidence else "PARTIAL" if missing_required_task_ids else "COMPLETE")
    return ResearchRunResult(
        objective=objective,
        plan=plan,
        task_results=tuple(task_results),
        evidence=tuple(accepted_evidence),
        failures=tuple(failures),
        required_task_ids=required_task_ids,
        covered_required_task_ids=covered_required_task_ids,
        missing_required_task_ids=missing_required_task_ids,
        failed_task_ids=failed_task_ids,
        status=status,
    )
