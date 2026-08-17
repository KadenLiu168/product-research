from dataclasses import dataclass
from typing import Callable, Optional

from .research_orchestration import (
    AcquisitionResult,
    ResearchTask,
    SourceFamily,
    TaskStatus,
    _validate_task,
)


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

        if task.source_family.value == "SEARCH":
            adapter = self.search
        elif task.source_family.value == "MARKETPLACE":
            adapter = self.marketplace
        elif task.source_family.value == "CONSUMER_SOCIAL":
            adapter = self.consumer_social
        elif task.source_family.value == "SUPPLIER":
            adapter = self.supplier
        elif task.source_family.value == "REGULATORY_IP":
            adapter = self.regulatory_ip
        else:
            raise ValueError("unsupported source family")

        if adapter is None:
            return AcquisitionResult(
                task_id=task.task_id,
                status=TaskStatus("UNAVAILABLE"),
                findings=(),
            )
        return adapter(task)
