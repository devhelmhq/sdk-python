"""Authoring helpers: the monitor ``type`` → ``config`` pairing and deprecations.

The spec's ``config`` is an untagged ``oneOf``, so pydantic alone would accept
an HTTP config on a BROWSER monitor (every ``ScriptMonitorConfig`` field is
optional). :func:`check_config` pins each type to its config model and
refuses unknown keys before any call.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing_extensions import TypeGuard

from devhelm._errors import DevhelmValidationError, client_error
from devhelm._generated import (
    DnsMonitorConfig,
    HeartbeatMonitorConfig,
    HttpMonitorConfig,
    IcmpMonitorConfig,
    McpServerMonitorConfig,
    MonitorTestResultDto,
    RunDto,
    ScriptMonitorConfig,
    TcpMonitorConfig,
)
from devhelm._validation import RequestValue

CodeMonitorType = Literal["BROWSER", "MULTI_STEP_API"]
UptimeMonitorType = Literal["HTTP", "DNS", "MCP_SERVER", "TCP", "ICMP", "HEARTBEAT"]

CODE_TYPES: frozenset[str] = frozenset({"BROWSER", "MULTI_STEP_API"})

MonitorConfig = (
    HttpMonitorConfig
    | DnsMonitorConfig
    | TcpMonitorConfig
    | IcmpMonitorConfig
    | McpServerMonitorConfig
    | HeartbeatMonitorConfig
    | ScriptMonitorConfig
)

CONFIG_MODELS: dict[str, type[BaseModel]] = {
    "HTTP": HttpMonitorConfig,
    "DNS": DnsMonitorConfig,
    "TCP": TcpMonitorConfig,
    "ICMP": IcmpMonitorConfig,
    "MCP_SERVER": McpServerMonitorConfig,
    "HEARTBEAT": HeartbeatMonitorConfig,
    "BROWSER": ScriptMonitorConfig,
    "MULTI_STEP_API": ScriptMonitorConfig,
}


def is_code_type(monitor_type: str | None) -> bool:
    return monitor_type in CODE_TYPES


def check_config(monitor_type: str, config: RequestValue) -> RequestValue:
    """Validate ``config`` as the model for ``monitor_type``.

    Returns the validated model (``None`` when ``config`` is ``None``; the
    value unchanged for a type this SDK does not know yet), or raises ``ValidationError`` (``MONITOR_CONFIG_TYPE_MISMATCH`` /
    ``FIELD_UNKNOWN``) or ``DevhelmValidationError`` for a bad value.
    """
    if config is None:
        return None
    model = CONFIG_MODELS.get(monitor_type)
    if model is None:
        # A type newer than this SDK: pass it through for the server to check.
        return config
    if isinstance(config, BaseModel):
        if not isinstance(config, model):
            raise client_error(
                "validation",
                "MONITOR_CONFIG_TYPE_MISMATCH",
                f"A {monitor_type} monitor takes {model.__name__}, "
                f"not {type(config).__name__}",
                field="config",
            )
        return config
    if not isinstance(config, Mapping):
        raise client_error(
            "validation",
            "MONITOR_CONFIG_TYPE_MISMATCH",
            f"config for a {monitor_type} monitor must be {model.__name__} or a dict",
            field="config",
        )
    known = set(model.model_fields)
    known |= {f.alias for f in model.model_fields.values() if f.alias}
    unknown = sorted(k for k in config if k not in known)
    if unknown:
        raise client_error(
            "validation",
            "FIELD_UNKNOWN",
            f"{model.__name__} has no field {unknown[0]!r} "
            f"(a {monitor_type} monitor's config)",
            field=f"config.{unknown[0]}",
        )
    try:
        return model.model_validate(config)
    except PydanticValidationError as e:
        raise DevhelmValidationError(
            f"Invalid config for a {monitor_type} monitor: {e}",
            errors=e.errors(),
            cause=e,
        ) from e


_warned: set[str] = set()

REMOVAL_DATE = "2027-01-31"
_REMOVAL_AT = datetime(2027, 1, 31, tzinfo=timezone.utc)


def removal_date_passed() -> bool:
    """True from 2027-01-31 (UTC), when the deprecated aliases stop working."""
    return datetime.now(timezone.utc) >= _REMOVAL_AT


# What ``monitors.test()`` returns: a run for code monitors; the probe result
# for uptime monitors (deprecated, until 2027-01-31).
MonitorTestOutcome = RunDto | MonitorTestResultDto


def is_run(result: MonitorTestOutcome) -> TypeGuard[RunDto]:
    """Whether a ``monitors.test()`` result is a run (code monitor) rather
    than a probe result."""
    return isinstance(result, RunDto)


def deprecated(name: str, replacement: str, since: str = "1.13") -> None:
    """Warn once per process that ``name`` is deprecated."""
    if name in _warned:
        return
    _warned.add(name)
    warnings.warn(
        f"{name} is deprecated since {since} and is removed on {REMOVAL_DATE}; "
        f"use {replacement}.",
        DeprecationWarning,
        stacklevel=3,
    )
