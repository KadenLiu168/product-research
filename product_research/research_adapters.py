from dataclasses import dataclass
from typing import Callable, Optional

from .research_orchestration import (
    AcquisitionResult,
    ResearchTask,
    SourceFamily,
    TaskStatus,
    _validate_task,
)


_ADAPTER_FIELDS = {
    "SEARCH": "search",
    "MARKETPLACE": "marketplace",
    "CONSUMER_SOCIAL": "consumer_social",
    "SUPPLIER": "supplier",
    "REGULATORY_IP": "regulatory_ip",
}


@dataclass(frozen=True)
class ResearchSourceAdapters:
    search: Optional[Callable] = None
    marketplace: Optional[Callable] = None
    consumer_social: Optional[Callable] = None
    supplier: Optional[Callable] = None
    regulatory_ip: Optional[Callable] = None

    def __post_init__(self):
        for adapter in (
            self.search,
            self.marketplace,
            self.consumer_social,
            self.supplier,
            self.regulatory_ip,
        ):
            if adapter is not None and not callable(adapter):
                raise TypeError("adapter slots must be callable or None")

    def __call__(self, task):
        if type(task) is not ResearchTask:
            raise TypeError("task must be a ResearchTask")
        _validate_task(task)
        if type(task.source_family) is not SourceFamily:
            raise TypeError("source_family must be a SourceFamily")

        field_name = _ADAPTER_FIELDS.get(task.source_family.value)
        if field_name is None:
            raise ValueError("unsupported source family")
        adapter = getattr(self, field_name)

        if adapter is None:
            return AcquisitionResult(
                task_id=task.task_id,
                status=TaskStatus("UNAVAILABLE"),
                findings=(),
            )
        return adapter(task)
