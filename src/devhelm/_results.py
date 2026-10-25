"""Surface-only result types. Each one composes generated types."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from devhelm._generated import RunDto, TriggerRunsResponse


@dataclass(frozen=True)
class TriggeredRuns:
    """``monitors.trigger(..., wait=True)``: the trigger and its finished runs."""

    trigger: TriggerRunsResponse
    runs: list[RunDto]

    @property
    def trigger_id(self) -> UUID:
        return self.trigger.trigger_id

    @property
    def billed_runs(self) -> int:
        return self.trigger.billed_runs
