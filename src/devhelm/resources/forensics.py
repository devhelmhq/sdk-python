"""Forensic read-only endpoints: incident timelines, check traces, policy
snapshots, rule evaluations, and state transitions.

These endpoints expose the immutable event-sourced forensic model described
in ``cowork/design/046-detection-forensic-model.md``. Use them to audit how
the detection engine arrived at a given state change, replay an incident,
or inspect the exact policy that fired a rule.
"""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

import httpx
from pydantic import BaseModel

from devhelm._generated import (
    CheckTraceDto,
    IncidentStateTransitionDto,
    IncidentTimelineDto,
    PolicySnapshotDto,
    RuleEvaluationDto,
)
from devhelm._http import api_get, path_param
from devhelm._pagination import Page, _validate_page
from devhelm._validation import parse_list, parse_single

M = TypeVar("M", bound=BaseModel)

# Explicit primitive-only param dict avoids mypy's ``disallow_any_explicit``
# in strict mode while still accepting the shapes httpx serialises for us.
_ParamValue = str | int | bool | None
_ParamDict = dict[str, _ParamValue]


def _format_instant(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class Forensics:
    """Read-only forensic endpoints for detection audit trails."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def incident_timeline(self, id: int | str) -> IncidentTimelineDto:
        """Full reconstructed timeline for an incident: state transitions,
        triggering rule evaluations, and the active policy snapshot.
        """
        return parse_single(
            IncidentTimelineDto,
            api_get(
                self._client, f"/api/v1/forensics/incidents/{path_param(id)}/timeline"
            ),
            f"GET /api/v1/forensics/incidents/{id}/timeline",
        )

    def check_trace(self, check_id: str) -> CheckTraceDto:
        """Everything recorded for a single check execution: rule
        evaluations, state transitions, and the policy snapshot in effect.
        """
        return parse_single(
            CheckTraceDto,
            api_get(self._client, f"/api/v1/forensics/traces/{path_param(check_id)}"),
            f"GET /api/v1/forensics/traces/{check_id}",
        )

    def policy_snapshot(self, hash_hex: str) -> PolicySnapshotDto:
        """Fetch a policy snapshot by its content-addressed SHA-256 hash."""
        return parse_single(
            PolicySnapshotDto,
            api_get(
                self._client,
                f"/api/v1/forensics/policy-snapshots/{path_param(hash_hex)}",
            ),
            f"GET /api/v1/forensics/policy-snapshots/{hash_hex}",
        )

    def monitor_rule_evaluations(
        self,
        monitor_id: int | str,
        *,
        rule_type: str | None = None,
        region: str | None = None,
        only_matched: bool | None = None,
        from_: datetime | str | None = None,
        to: datetime | str | None = None,
        page: int = 0,
        size: int = 50,
    ) -> Page[RuleEvaluationDto]:
        """List rule evaluations produced for a monitor (paginated)."""
        params: _ParamDict = {"page": page, "size": size}
        if rule_type is not None:
            params["ruleType"] = rule_type
        if region is not None:
            params["region"] = region
        if only_matched is not None:
            params["onlyMatched"] = only_matched
        if from_ is not None:
            params["from"] = _format_instant(from_)
        if to is not None:
            params["to"] = _format_instant(to)

        path = f"/api/v1/forensics/monitors/{path_param(monitor_id)}/rule-evaluations"
        return self._fetch_table_page(path, RuleEvaluationDto, params)

    def monitor_transitions(
        self,
        monitor_id: int | str,
        *,
        from_: datetime | str | None = None,
        to: datetime | str | None = None,
        page: int = 0,
        size: int = 50,
    ) -> Page[IncidentStateTransitionDto]:
        """List state transitions recorded for a monitor (paginated)."""
        params: _ParamDict = {"page": page, "size": size}
        if from_ is not None:
            params["from"] = _format_instant(from_)
        if to is not None:
            params["to"] = _format_instant(to)

        path = f"/api/v1/forensics/monitors/{path_param(monitor_id)}/transitions"
        return self._fetch_table_page(path, IncidentStateTransitionDto, params)

    def _fetch_table_page(
        self, path: str, model_class: type[M], params: _ParamDict
    ) -> Page[M]:
        """Forensic monitor endpoints return the offset-paged envelope
        ``{data, hasNext, hasPrev, totalElements, totalPages}``; reuse the
        shared validator but forward filter params alongside page/size.
        """
        resp = api_get(self._client, path, params=params)
        envelope = _validate_page(resp)
        return Page(
            data=parse_list(model_class, envelope.data, f"GET {path}"),
            has_next=envelope.hasNext,
            has_prev=envelope.hasPrev,
            total_elements=envelope.totalElements,
            total_pages=envelope.totalPages,
        )
