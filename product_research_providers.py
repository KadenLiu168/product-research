from dataclasses import dataclass
from typing import Callable, Tuple

from product_research.research_orchestration import (
    AcquisitionResult,
    SourceFamily,
    TaskStatus,
    _validate_task,
)


class ProviderConfigurationError(ValueError):
    pass


@dataclass(frozen=True, repr=False)
class ProviderBinding:
    task_id: str
    source_family: SourceFamily
    request: object

    def __post_init__(self):
        if type(self.task_id) is not str or not self.task_id:
            raise TypeError("task_id must be a non-empty string")
        if type(self.source_family) is not SourceFamily:
            raise TypeError("source_family must be a SourceFamily")
        SourceFamily(self.source_family.value)
        if self.request is None:
            raise TypeError("request must be a provider-defined value")

    def __repr__(self):
        return (
            "ProviderBinding("
            f"task_id={self.task_id!r}, "
            f"source_family={self.source_family.value!r}, "
            f"request_type={type(self.request).__name__!r})"
        )


class ProviderAcquisition:
    def __init__(
        self,
        *,
        source_family: SourceFamily,
        resolve_binding: Callable,
        execute: Callable,
        transport: Callable,
        supported_request_types: Tuple[type, ...] = (),
        configuration=None,
        validate_configuration: Callable = None,
    ):
        if type(source_family) is not SourceFamily:
            raise TypeError("source_family must be a SourceFamily")
        normalized_family = SourceFamily(source_family.value)
        if not callable(resolve_binding):
            raise TypeError("resolve_binding must be callable")
        if not callable(execute):
            raise TypeError("execute must be callable")
        if not callable(transport):
            raise TypeError("transport must be callable")
        request_types = tuple(supported_request_types)
        if not all(isinstance(request_type, type) for request_type in request_types):
            raise TypeError("supported_request_types must contain types")
        if validate_configuration is not None:
            if not callable(validate_configuration):
                raise TypeError("validate_configuration must be callable")
            try:
                valid = validate_configuration(configuration)
            except Exception:
                raise ProviderConfigurationError("invalid provider configuration") from None
            if valid is False:
                raise ProviderConfigurationError("invalid provider configuration")

        self._source_family = normalized_family
        self._resolve_binding = resolve_binding
        self._execute = execute
        self._transport = transport
        self._supported_request_types = request_types

    def __repr__(self):
        return f"ProviderAcquisition(source_family={self._source_family.value!r})"

    def __call__(self, task):
        try:
            _validate_task(task)
            task_family = SourceFamily(task.source_family.value)
            if task_family != self._source_family:
                return self._failed(task)
            resolved = self._resolve_binding(task)
            binding = self._one_binding(resolved)
            if binding.task_id != task.task_id:
                return self._failed(task)
            binding_family = SourceFamily(binding.source_family.value)
            if binding_family != task_family or binding_family != self._source_family:
                return self._failed(task)
            if type(binding.request) not in self._supported_request_types:
                return self._failed(task)
        except Exception:
            return self._failed(task)

        transport_used = False

        def transport_once(request):
            nonlocal transport_used
            if transport_used:
                raise RuntimeError("transport may be invoked at most once per acquisition")
            transport_used = True
            return self._transport(request)

        return self._execute(task, binding.request, transport_once)

    @staticmethod
    def _one_binding(resolved):
        if resolved is None:
            raise ValueError("binding is missing")
        if type(resolved) is ProviderBinding:
            return resolved
        if type(resolved) is tuple and len(resolved) == 1 and type(resolved[0]) is ProviderBinding:
            return resolved[0]
        raise ValueError("binding is not unambiguous")

    @staticmethod
    def _failed(task):
        return AcquisitionResult(
            task_id=task.task_id,
            status=TaskStatus("FAILED"),
            findings=(),
        )
