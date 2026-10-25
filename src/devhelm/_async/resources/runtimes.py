"""Synthetics runtime profiles (Node, Playwright and the package catalog)."""

from __future__ import annotations

import builtins

from devhelm._async.pagination import fetch_table
from devhelm._async.transport import Client, api_get, as_transport
from devhelm._generated import RuntimeProfileDto
from devhelm._transport import path_param
from devhelm._validation import parse_single

_BASE = "/api/v1/synthetics/runtime-profiles"


class Runtimes:
    """Read the runtime catalog. A monitor pins one with ``config.runtimeId``."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> builtins.list[RuntimeProfileDto]:
        """Every runtime profile, including deprecated and retired ones."""
        return (await fetch_table(self._client, _BASE, RuntimeProfileDto)).data

    async def get(self, runtime_id: str) -> RuntimeProfileDto:
        """One runtime profile, such as ``2026.11``."""
        path = f"{_BASE}/{path_param(runtime_id)}"
        return parse_single(
            RuntimeProfileDto, await api_get(self._client, path), f"GET {path}"
        )
