"""Runs of browser and multi-step API monitors, and their evidence.

A Run is the generated ``RunDto``. ``runs.wait(id)`` follows the run's event
stream (then polls) until ``phase == "finished"`` and returns it whatever the
outcome. List filters are the generated ``RunListParams`` fields, passed as a
model, a dict or keyword arguments.
"""

from __future__ import annotations

import builtins

from devhelm._async._compat import Event
from devhelm._async.pagination import (
    fetch_all_cursor_pages,
    fetch_cursor_page,
    fetch_table,
)
from devhelm._async.resources.signed_download import read_signed_url
from devhelm._async.transport import (
    Client,
    api_delete,
    api_get,
    api_get_raw,
    api_post,
    as_transport,
)
from devhelm._async.wait import DEFAULT_WAIT_TIMEOUT_MS, get_run, wait_for_run
from devhelm._generated import (
    ArtifactDownloadDto,
    EvidencePurgeRequest,
    NetworkRowDto,
    RunArtifactDto,
    RunCaseDto,
    RunCaseListParams,
    RunConsoleDto,
    RunConsoleParams,
    RunDiffDto,
    RunDto,
    RunListParams,
    RunNetworkDto,
    RunNetworkParams,
    RunTraceSummaryDto,
)
from devhelm._pages import CursorPage
from devhelm._transport import ResourceId, path_param, query_from_model
from devhelm._validation import (
    RequestBody,
    RequestValue,
    build_request,
    merge_body,
    parse_model,
    parse_single,
)

_BASE = "/api/v1/runs"
DEFAULT_RUN_LIST_LIMIT = 50


def _run_path(run_id: ResourceId) -> str:
    return f"{_BASE}/{path_param(run_id)}"


def _run_list_params(
    params: RequestBody[RunListParams] | None, filters: dict[str, RequestValue]
) -> RunListParams:
    """``limit`` is required by the model; the API's own default is 50."""
    if not isinstance(params, RunListParams):
        merged = merge_body(params, filters)
        merged.setdefault("limit", DEFAULT_RUN_LIST_LIMIT)
        return build_request(RunListParams, merged, {}, "runs.list")
    return build_request(RunListParams, params, filters, "runs.list")


class RunArtifacts:
    """Screenshots, traces, videos, HARs and logs captured by a run."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self, run_id: ResourceId) -> builtins.list[RunArtifactDto]:
        """List a run's evidence files (``GET /runs/{id}/artifacts``)."""
        page = await fetch_table(
            self._client, f"{_run_path(run_id)}/artifacts", RunArtifactDto
        )
        return page.data

    async def link(self, artifact_id: ResourceId) -> ArtifactDownloadDto:
        """A short-lived signed URL for one artifact's bytes."""
        path = f"/api/v1/artifacts/{path_param(artifact_id)}/download"
        return parse_single(
            ArtifactDownloadDto, await api_get(self._client, path), f"GET {path}"
        )

    async def download(self, artifact_id: ResourceId) -> bytes:
        """The artifact's bytes (signed link, then a token-free GET)."""
        link = await self.link(artifact_id)
        return await read_signed_url(link.url)


class Runs:
    """List, read, wait on and manage runs (``/api/v1/runs``)."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)
        self.artifacts = RunArtifacts(self._client)

    async def list(
        self, params: RequestBody[RunListParams] | None = None, **filters: RequestValue
    ) -> CursorPage[RunDto]:
        """One page of runs, newest first (default: the last 24 hours).

        Filters are ``RunListParams`` fields, for example
        ``runs.list(monitor_id=m.id, outcome="failed", limit=25)``. Pass the
        page's ``next_cursor`` as ``cursor`` for the next page.
        """
        query = query_from_model(_run_list_params(params, filters))
        return await fetch_cursor_page(self._client, _BASE, RunDto, extra_params=query)

    async def list_all(
        self, params: RequestBody[RunListParams] | None = None, **filters: RequestValue
    ) -> builtins.list[RunDto]:
        """Every run matching the filters, following ``next_cursor``."""
        model = _run_list_params(params, filters)
        return await fetch_all_cursor_pages(
            self._client,
            _BASE,
            RunDto,
            limit=model.limit or DEFAULT_RUN_LIST_LIMIT,
            extra_params=query_from_model(model),
        )

    async def get(self, run_id: ResourceId) -> RunDto:
        """Get one run."""
        return await get_run(self._client, str(run_id))

    async def wait(
        self,
        run_id: ResourceId,
        *,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
        signal: Event | None = None,
    ) -> RunDto:
        """Wait until the run finishes and return it, whatever the outcome.

        Raises :class:`~devhelm.WaitTimeoutError` only, when the run is still
        going after ``timeout_ms`` (or ``signal`` is set). The run is never
        cancelled.
        """
        return await wait_for_run(
            self._client, str(run_id), timeout_ms=timeout_ms, signal=signal
        )

    async def cancel(self, run_id: ResourceId) -> RunDto:
        """Request cancellation. The phase changes once the runner stops."""
        path = f"{_run_path(run_id)}/cancel"
        return parse_single(RunDto, await api_post(self._client, path), f"POST {path}")

    async def steps(
        self,
        run_id: ResourceId,
        params: RequestBody[RunCaseListParams] | None = None,
        **filters: RequestValue,
    ) -> builtins.list[RunCaseDto]:
        """The run's test cases, each with its steps (``GET /runs/{id}/cases``)."""
        query = query_from_model(
            build_request(RunCaseListParams, params, filters, "runs.steps")
        )
        page = await fetch_table(
            self._client, f"{_run_path(run_id)}/cases", RunCaseDto, params=query
        )
        return page.data

    async def console(
        self,
        run_id: ResourceId,
        params: RequestBody[RunConsoleParams] | None = None,
        **filters: RequestValue,
    ) -> RunConsoleDto:
        """Browser console lines for the run."""
        query = query_from_model(
            build_request(RunConsoleParams, params, filters, "runs.console")
        )
        path = f"{_run_path(run_id)}/console"
        return parse_single(
            RunConsoleDto, await api_get(self._client, path, query), f"GET {path}"
        )

    async def network(
        self,
        run_id: ResourceId,
        params: RequestBody[RunNetworkParams] | None = None,
        **filters: RequestValue,
    ) -> RunNetworkDto:
        """Network requests the run made (one page; ``cursor`` for more)."""
        query = query_from_model(
            build_request(RunNetworkParams, params, filters, "runs.network")
        )
        path = f"{_run_path(run_id)}/network"
        return parse_model(
            RunNetworkDto, await api_get(self._client, path, query), f"GET {path}"
        )

    async def network_row(
        self, run_id: ResourceId, row_id: ResourceId
    ) -> NetworkRowDto:
        """One network request with its headers and timings."""
        path = f"{_run_path(run_id)}/network/{path_param(row_id)}"
        return parse_single(
            NetworkRowDto, await api_get(self._client, path), f"GET {path}"
        )

    async def trace_summary(self, run_id: ResourceId) -> RunTraceSummaryDto:
        """A text-sized summary of the run's Playwright trace."""
        path = f"{_run_path(run_id)}/trace-summary"
        return parse_single(
            RunTraceSummaryDto, await api_get(self._client, path), f"GET {path}"
        )

    async def diff(
        self, run_id: ResourceId, *, baseline_run_id: ResourceId | None = None
    ) -> RunDiffDto:
        """Compare the run with a baseline (default: the last passing run)."""
        path = f"{_run_path(run_id)}/diff"
        params = {"baselineRunId": str(baseline_run_id)} if baseline_run_id else None
        return parse_single(
            RunDiffDto, await api_get(self._client, path, params), f"GET {path}"
        )

    async def export(self, run_id: ResourceId) -> bytes:
        """The run and its evidence as a zip archive."""
        response = await api_get_raw(
            self._client, f"{_run_path(run_id)}/export", accept="application/zip"
        )
        return response.content

    async def pin(self, run_id: ResourceId) -> RunDto:
        """Keep the run and its evidence past retention."""
        path = f"{_run_path(run_id)}/pin"
        return parse_single(RunDto, await api_post(self._client, path), f"POST {path}")

    async def unpin(self, run_id: ResourceId) -> RunDto:
        """Let normal retention apply again."""
        path = f"{_run_path(run_id)}/pin"
        return parse_single(
            RunDto, await api_delete(self._client, path), f"DELETE {path}"
        )

    async def purge(self, run_id: ResourceId, *, reason: str) -> RunDto:
        """Delete the run's stored evidence now. ``reason`` is audited."""
        path = f"{_run_path(run_id)}/purge"
        body = EvidencePurgeRequest(reason=reason)
        return parse_single(
            RunDto, await api_post(self._client, path, body), f"POST {path}"
        )
