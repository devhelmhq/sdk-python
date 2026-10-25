"""Monitors: uptime probes and code checks (browser, multi-step API).

Code checks follow one lifecycle (doc 42 §1): create (revision 1 is live) →
change code as a draft → test it → publish. ``update(id, code=...)`` is the
one-call path: it publishes the new code live, untested.

``code`` accepts a path, ``{"entrypoint", "include"}``, or
``{"entrypoint", "files"}`` held in memory; the SDK uploads it to
``POST /bundles`` first (see ``devhelm._bundle``). ``environment`` accepts an
environment slug or id.

Request bodies are the generated ``*Request`` models. Every method that takes
one accepts the model, a dict, or the model's fields as keyword arguments.
"""

from __future__ import annotations

import builtins
import os
from collections.abc import Sequence
from typing import Literal, overload
from uuid import UUID

from devhelm._async._compat import monotonic
from devhelm._async.pagination import (
    fetch_all_cursor_pages,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
    fetch_table,
)
from devhelm._async.resources.bundles import code_spec
from devhelm._async.resources.environments import resolve_environment_id
from devhelm._async.transport import (
    AsyncTransport,
    Client,
    api_delete,
    api_get,
    api_post,
    api_post_with_status,
    api_put,
    as_transport,
)
from devhelm._async.wait import DEFAULT_WAIT_TIMEOUT_MS, wait_for_run
from devhelm._authoring import (
    CodeMonitorType,
    UptimeMonitorType,
    check_config,
    deprecated,
    is_code_type,
)
from devhelm._bundle import CodeInput
from devhelm._errors import (
    DevhelmMonitorTestQueuedError,
    DevhelmValidationError,
    client_error,
)
from devhelm._generated import (
    CheckResultDto,
    CodeSource,
    CodeTestTargetRequest,
    CreateDraftRevisionRequest,
    CreateDraftRevisionResponse,
    CreateMonitorRequest,
    DefinitionHeadDto,
    EvidencePurgeRequest,
    MonitorCodeSpec,
    MonitorDriftDto,
    MonitorDto,
    MonitorHistoryEntryDto,
    MonitorOverlayRequest,
    MonitorSecretRequestsDto,
    MonitorSessionDto,
    MonitorTestRequest,
    MonitorTestResultDto,
    MonitorVersionDto,
    PublishRevisionRequest,
    QuarantineMonitorRequest,
    RemapSecretRequest,
    RestoreMonitorRequest,
    RevisionDiffDto,
    RevisionDto,
    RevisionFilesDto,
    RollbackPreviewDto,
    RollbackRevisionRequest,
    RunDto,
    RunSessionContext,
    TakeoverMonitorRequest,
    TransferMonitorRequest,
    TriggerRunRequest,
    TriggerRunsResponse,
    UpdateMonitorRequest,
    UpsertMonitorSessionRequest,
)
from devhelm._pages import CursorPage, Page
from devhelm._results import TriggeredRuns
from devhelm._transport import QueryValue, ResourceId, path_param
from devhelm._validation import (
    RequestBody,
    RequestValue,
    build_request,
    merge_body,
    parse_single,
    validate_request,
)

_BASE = "/api/v1/monitors"

Root = str | os.PathLike[str] | None
Session = RunSessionContext | dict[str, RequestValue] | None


def _monitor_path(monitor_id: ResourceId | int) -> str:
    return f"{_BASE}/{path_param(monitor_id)}"


def _session(session: Session) -> RunSessionContext | None:
    if session is None or isinstance(session, RunSessionContext):
        return session
    return validate_request(RunSessionContext, session, "session")


def _list_filters(
    *,
    enabled: bool | None,
    type: str | None,
    types: Sequence[str] | None,
    managed_by: str | None,
    tags: str | None,
    tag: str | None,
    search: str | None,
    name: str | None,
    environment_id: str | None,
    display_health: str | None,
) -> dict[str, QueryValue]:
    """The ``GET /api/v1/monitors`` query, camelCase on the wire."""
    return {
        "enabled": enabled,
        "type": type,
        "types": ",".join(types) if types else None,
        "managedBy": managed_by,
        "tags": tags,
        "tag": tag,
        "search": search,
        "name": name,
        "environmentId": environment_id,
        "displayHealth": display_health,
    }


async def _env_id(client: AsyncTransport, environment: str | UUID | None) -> str | None:
    if environment is None:
        return None
    return str(await resolve_environment_id(client, environment))


async def _maybe_wait(
    client: AsyncTransport, run: RunDto, wait: bool, timeout_ms: int
) -> RunDto:
    if not wait:
        return run
    return await wait_for_run(client, str(run.id), timeout_ms=timeout_ms)


def _str_or_none(value: RequestValue) -> str | None:
    return value if isinstance(value, str) else None


def _runtime_of(config: RequestValue) -> str | None:
    """``config.runtimeId`` (model or dict), used to check imports on upload."""
    runtime = getattr(config, "runtime_id", None)
    if isinstance(runtime, str):
        return runtime
    if isinstance(config, dict):
        value = config.get("runtimeId") or config.get("runtime_id")
        return value if isinstance(value, str) else None
    return None


class MonitorRevisions:
    """Code revisions of one monitor: drafts, tests, files and diffs."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def list(
        self,
        monitor_id: ResourceId,
        *,
        state: str | Sequence[str] | None = None,
        page: int = 0,
        size: int = 25,
    ) -> Page[RevisionDto]:
        """Revisions newest first. ``state`` filters (default ``live,previous``):
        ``draft``, ``tested_passed``, ``tested_failed``, ``live``,
        ``previous``, ``discarded`` or ``all``."""
        states = state if isinstance(state, str) or state is None else ",".join(state)
        return await fetch_page(
            self._client,
            f"{_monitor_path(monitor_id)}/revisions",
            RevisionDto,
            page,
            size,
            extra_params={"state": states},
        )

    async def get(self, monitor_id: ResourceId, revision_id: ResourceId) -> RevisionDto:
        """One revision (``GET /revisions/{id}``)."""
        path = f"/api/v1/revisions/{path_param(revision_id)}"
        return parse_single(
            RevisionDto, await api_get(self._client, path), f"GET {path}"
        )

    async def create(
        self,
        monitor_id: ResourceId,
        *,
        code: CodeInput | MonitorCodeSpec,
        root: Root = None,
        source: CodeSource | None = None,
    ) -> CreateDraftRevisionResponse:
        """Upload ``code`` and save it as a draft. Nothing goes live.

        A draft with the same digest is reused. ``evicted`` names the draft
        discarded to stay under the cap of 10.
        """
        spec = await code_spec(self._client, code, root=root, source=source)
        path = f"{_monitor_path(monitor_id)}/revisions"
        body = CreateDraftRevisionRequest(code=spec)
        return parse_single(
            CreateDraftRevisionResponse,
            await api_post(self._client, path, body),
            f"POST {path}",
        )

    async def test(
        self,
        monitor_id: ResourceId,
        revision_id: ResourceId,
        *,
        region: str | None = None,
        session: Session = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto:
        """Queue a validation run of this revision in the monitor's environment.

        Billed, saved, never signals. With ``wait=True`` returns the finished
        run (see ``runs.wait``).
        """
        path = f"{_monitor_path(monitor_id)}/revisions/{path_param(revision_id)}/test"
        body = CodeTestTargetRequest(region=region, session=_session(session))
        run = parse_single(
            RunDto, await api_post(self._client, path, body), f"POST {path}"
        )
        return await _maybe_wait(self._client, run, wait, timeout_ms)

    async def diff(
        self,
        monitor_id: ResourceId,
        revision_id: ResourceId,
        other: ResourceId | None = None,
    ) -> RevisionDiffDto:
        """Diff two revisions. ``other`` defaults to the monitor's live
        revision (one extra ``GET /monitors/{id}``)."""
        if other is None:
            monitor = parse_single(
                MonitorDto,
                await api_get(self._client, _monitor_path(monitor_id)),
                f"GET {_monitor_path(monitor_id)}",
            )
            if monitor.live_revision_id is None:
                raise client_error(
                    "validation",
                    "REVISION_NEVER_LIVE",
                    "The monitor has no live revision to diff against; pass other=",
                    field="other",
                )
            other = monitor.live_revision_id
        path = f"/api/v1/revisions/{path_param(revision_id)}/diff/{path_param(other)}"
        return parse_single(
            RevisionDiffDto, await api_get(self._client, path), f"GET {path}"
        )

    async def files(
        self, monitor_id: ResourceId, revision_id: ResourceId
    ) -> RevisionFilesDto:
        """The revision's source files as text, by path."""
        path = f"/api/v1/revisions/{path_param(revision_id)}/files"
        return parse_single(
            RevisionFilesDto, await api_get(self._client, path), f"GET {path}"
        )

    async def discard(self, monitor_id: ResourceId, revision_id: ResourceId) -> None:
        """Discard a draft. A live or once-live revision is refused (409)."""
        await api_delete(
            self._client,
            f"{_monitor_path(monitor_id)}/revisions/{path_param(revision_id)}",
        )

    async def keep(
        self, monitor_id: ResourceId, revision_id: ResourceId
    ) -> RevisionDto:
        """Extend a draft's 14-day expiry."""
        path = f"{_monitor_path(monitor_id)}/revisions/{path_param(revision_id)}/keep"
        return parse_single(
            RevisionDto, await api_post(self._client, path), f"POST {path}"
        )

    async def purge(
        self, monitor_id: ResourceId, revision_id: ResourceId, *, reason: str
    ) -> RevisionDto:
        """Delete the revision's stored bytes now. ``reason`` is audited."""
        path = f"/api/v1/revisions/{path_param(revision_id)}/purge"
        body = EvidencePurgeRequest(reason=reason)
        return parse_single(
            RevisionDto, await api_post(self._client, path, body), f"POST {path}"
        )


class MonitorVersions:
    """Settings history of a monitor (``/monitors/{id}/versions``).

    Calling it like a method (``monitors.versions(id)``) is the pre-1.13
    spelling of :meth:`list`; it still works and warns once.
    """

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def __call__(
        self, monitor_id: ResourceId | int, page: int = 0, size: int = 20
    ) -> Page[MonitorVersionDto]:
        deprecated("monitors.versions(id)", "monitors.versions.list(id)")
        return await self.list(monitor_id, page=page, size=size)

    async def list(
        self, monitor_id: ResourceId | int, *, page: int = 0, size: int = 20
    ) -> Page[MonitorVersionDto]:
        """Settings snapshots, newest first."""
        return await fetch_page(
            self._client,
            f"{_monitor_path(monitor_id)}/versions",
            MonitorVersionDto,
            page,
            size,
        )

    async def get(self, monitor_id: ResourceId, version: int) -> MonitorVersionDto:
        """One settings snapshot by version number."""
        path = f"{_monitor_path(monitor_id)}/versions/{version}"
        return parse_single(
            MonitorVersionDto, await api_get(self._client, path), f"GET {path}"
        )


class MonitorHistory:
    """What happened to a monitor over time, both probe and code kinds."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def list(
        self,
        monitor_id: ResourceId,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> CursorPage[MonitorHistoryEntryDto]:
        """One page of history entries; pass ``next_cursor`` for the next."""
        return await fetch_cursor_page(
            self._client,
            f"{_monitor_path(monitor_id)}/history",
            MonitorHistoryEntryDto,
            cursor,
            limit,
        )

    async def list_all(
        self, monitor_id: ResourceId
    ) -> builtins.list[MonitorHistoryEntryDto]:
        """Every history entry, following ``next_cursor``."""
        return await fetch_all_cursor_pages(
            self._client, f"{_monitor_path(monitor_id)}/history", MonitorHistoryEntryDto
        )


class MonitorTrash:
    """Deleted monitors, restorable until they are purged."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def list(self) -> builtins.list[MonitorDto]:
        """Every monitor in Trash."""
        return await fetch_all_pages(self._client, f"{_BASE}/trash", MonitorDto)

    async def list_page(self, page: int, size: int) -> Page[MonitorDto]:
        """One page of Trash."""
        return await fetch_page(self._client, f"{_BASE}/trash", MonitorDto, page, size)


class MonitorSecretRequests:
    """Secret keys a monitor's code asks for, and how they are mapped."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def list(
        self, monitor_id: ResourceId, *, revision_id: ResourceId | None = None
    ) -> MonitorSecretRequestsDto:
        """Requested keys for the live revision (or ``revision_id``)."""
        path = f"{_monitor_path(monitor_id)}/secret-requests"
        params = {"revisionId": str(revision_id)} if revision_id else None
        return parse_single(
            MonitorSecretRequestsDto,
            await api_get(self._client, path, params),
            f"GET {path}",
        )

    async def remap(
        self,
        monitor_id: ResourceId,
        key: str,
        body: RequestBody[RemapSecretRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorSecretRequestsDto:
        """Point a requested key at another workspace secret."""
        req = build_request(RemapSecretRequest, body, fields, "secret_requests.remap")
        path = f"{_monitor_path(monitor_id)}/secret-requests/{path_param(key)}"
        return parse_single(
            MonitorSecretRequestsDto,
            await api_put(self._client, path, req),
            f"PUT {path}",
        )

    async def rescan(self, monitor_id: ResourceId) -> MonitorSecretRequestsDto:
        """Scan the live code again for the keys it asks for."""
        path = f"{_monitor_path(monitor_id)}/secret-requests/rescan"
        return parse_single(
            MonitorSecretRequestsDto, await api_post(self._client, path), f"POST {path}"
        )


class MonitorSessions:
    """Saved login sessions produced by a monitor's setup files."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def list(self, monitor_id: ResourceId) -> builtins.list[MonitorSessionDto]:
        """One entry per setup file."""
        page = await fetch_table(
            self._client, f"{_monitor_path(monitor_id)}/sessions", MonitorSessionDto
        )
        return page.data

    async def upsert(
        self,
        monitor_id: ResourceId,
        body: RequestBody[UpsertMonitorSessionRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorSessionDto:
        """Create or change a setup file's session policy."""
        req = build_request(
            UpsertMonitorSessionRequest, body, fields, "sessions.upsert"
        )
        path = f"{_monitor_path(monitor_id)}/sessions"
        return parse_single(
            MonitorSessionDto, await api_put(self._client, path, req), f"PUT {path}"
        )

    async def renew(
        self,
        monitor_id: ResourceId,
        *,
        setup_file: str | None = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto:
        """Run the setup file now to capture a fresh session."""
        path = f"{_monitor_path(monitor_id)}/sessions/renew"
        params = {"setupFile": setup_file} if setup_file else None
        run = parse_single(
            RunDto, await api_post(self._client, path, params=params), f"POST {path}"
        )
        return await _maybe_wait(self._client, run, wait, timeout_ms)

    async def revoke(
        self, monitor_id: ResourceId, *, setup_file: str | None = None
    ) -> MonitorSessionDto:
        """Drop the saved session so the next run logs in again."""
        path = f"{_monitor_path(monitor_id)}/sessions/revoke"
        params = {"setupFile": setup_file} if setup_file else None
        return parse_single(
            MonitorSessionDto,
            await api_post(self._client, path, params=params),
            f"POST {path}",
        )


class Monitors:
    """Uptime probes (HTTP, DNS, TCP, ICMP, MCP, Heartbeat) and code checks."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)
        self.revisions = MonitorRevisions(self._client)
        self.versions = MonitorVersions(self._client)
        self.history = MonitorHistory(self._client)
        self.trash = MonitorTrash(self._client)
        self.secret_requests = MonitorSecretRequests(self._client)
        self.sessions = MonitorSessions(self._client)

    # -- read ---------------------------------------------------------------

    async def list(
        self,
        *,
        name: str | None = None,
        environment: str | UUID | None = None,
        type: str | None = None,
        types: Sequence[str] | None = None,
        tag: str | None = None,
        tags: str | None = None,
        managed_by: str | None = None,
        search: str | None = None,
        display_health: str | None = None,
        enabled: bool | None = None,
        environment_id: str | None = None,
    ) -> builtins.list[MonitorDto]:
        """Every monitor matching the filters (auto-paginates).

        ``name`` is an exact, case-sensitive match. ``environment`` is a slug
        or id. ``tags`` is a comma-separated list.
        """
        filters = _list_filters(
            enabled=enabled,
            type=type,
            types=types,
            managed_by=managed_by,
            tags=tags,
            tag=tag,
            search=search,
            name=name,
            environment_id=await _env_id(self._client, environment) or environment_id,
            display_health=display_health,
        )
        items = await fetch_all_pages(
            self._client, _BASE, MonitorDto, extra_params=filters
        )
        # ``name`` is an exact-match query filter (doc 42 W0-6). A server
        # without it ignores the key, so the match is also applied here.
        return [m for m in items if name is None or m.name == name]

    async def list_all(
        self,
        *,
        name: str | None = None,
        environment: str | UUID | None = None,
        type: str | None = None,
        types: Sequence[str] | None = None,
        tag: str | None = None,
        managed_by: str | None = None,
        search: str | None = None,
        display_health: str | None = None,
    ) -> builtins.list[MonitorDto]:
        """Same as :meth:`list`: every monitor matching the filters."""
        return await self.list(
            name=name,
            environment=environment,
            type=type,
            types=types,
            tag=tag,
            managed_by=managed_by,
            search=search,
            display_health=display_health,
        )

    async def list_page(
        self,
        page: int,
        size: int,
        *,
        name: str | None = None,
        environment: str | UUID | None = None,
        type: str | None = None,
        types: Sequence[str] | None = None,
        tag: str | None = None,
        tags: str | None = None,
        managed_by: str | None = None,
        search: str | None = None,
        display_health: str | None = None,
        enabled: bool | None = None,
        environment_id: str | None = None,
    ) -> Page[MonitorDto]:
        """One page of monitors, with the same filters as :meth:`list`."""
        filters = _list_filters(
            enabled=enabled,
            type=type,
            types=types,
            managed_by=managed_by,
            tags=tags,
            tag=tag,
            search=search,
            name=name,
            environment_id=await _env_id(self._client, environment) or environment_id,
            display_health=display_health,
        )
        return await fetch_page(
            self._client, _BASE, MonitorDto, page, size, extra_params=filters
        )

    async def get(self, id: ResourceId | int) -> MonitorDto:
        """Get a single monitor by ID."""
        path = _monitor_path(id)
        return parse_single(
            MonitorDto, await api_get(self._client, path), f"GET {path}"
        )

    async def drift(self, id: ResourceId) -> MonitorDriftDto:
        """How the live monitor differs from what was last applied from code."""
        path = f"{_monitor_path(id)}/drift"
        return parse_single(
            MonitorDriftDto, await api_get(self._client, path), f"GET {path}"
        )

    # -- write --------------------------------------------------------------

    async def _authoring_body(
        self,
        body: RequestBody[CreateMonitorRequest]
        | RequestBody[UpdateMonitorRequest]
        | None,
        fields: dict[str, RequestValue],
        *,
        code: CodeInput | MonitorCodeSpec | None,
        environment: str | UUID | None,
        root: Root,
        monitor_type: str | None,
    ) -> dict[str, RequestValue]:
        data = merge_body(body, fields)
        if environment is not None:
            data["environmentId"] = str(
                await resolve_environment_id(self._client, environment)
            )
        kind = monitor_type or _str_or_none(data.get("type"))
        config = data.get("config")
        if kind is not None and config is not None:
            data["config"] = check_config(kind, config)
        if code is not None:
            data["code"] = await code_spec(
                self._client,
                code,
                root=root,
                runtime_id=_runtime_of(data.get("config")),
            )
        return data

    async def create(
        self,
        body: RequestBody[CreateMonitorRequest] | None = None,
        *,
        code: CodeInput | MonitorCodeSpec | None = None,
        environment: str | UUID | None = None,
        root: Root = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Create a monitor. A code monitor's revision 1 goes live at once.

        Example::

            devhelm.monitors.create(name="Checkout", type="BROWSER",
                                    environment="production",
                                    code="./checkout.spec.ts",
                                    frequency_seconds=600, regions=["us-east"])
        """
        data = await self._authoring_body(
            body,
            fields,
            code=code,
            environment=environment,
            root=root,
            monitor_type=None,
        )
        req = build_request(CreateMonitorRequest, data, {}, "monitors.create")
        return parse_single(
            MonitorDto, await api_post(self._client, _BASE, req), f"POST {_BASE}"
        )

    async def update(
        self,
        id: ResourceId | int,
        body: RequestBody[UpdateMonitorRequest] | None = None,
        *,
        code: CodeInput | MonitorCodeSpec | None = None,
        environment: str | UUID | None = None,
        root: Root = None,
        type: str | None = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Update a monitor. With ``code`` the new code is published live,
        untested (use ``revisions.create`` → ``revisions.test`` → ``publish``
        to test first). ``type`` (optional) checks ``config`` against the
        monitor's type before the call.
        """
        data = await self._authoring_body(
            body,
            fields,
            code=code,
            environment=environment,
            root=root,
            monitor_type=type,
        )
        req = build_request(UpdateMonitorRequest, data, {}, "monitors.update")
        path = _monitor_path(id)
        return parse_single(
            MonitorDto, await api_put(self._client, path, req), f"PUT {path}"
        )

    async def delete(self, id: ResourceId | int) -> None:
        """Move a monitor to Trash (``monitors.restore`` brings it back)."""
        await api_delete(self._client, _monitor_path(id))

    async def restore(
        self, id: ResourceId, *, environment: str | UUID | None = None
    ) -> MonitorDto:
        """Restore a monitor from Trash, optionally into another environment."""
        env = await _env_id(self._client, environment)
        body = RestoreMonitorRequest(environment_id=UUID(env) if env else None)
        path = f"{_monitor_path(id)}/restore"
        return parse_single(
            MonitorDto, await api_post(self._client, path, body), f"POST {path}"
        )

    async def _overlay(
        self,
        id: ResourceId | int,
        verb: str,
        body: RequestBody[MonitorOverlayRequest] | None,
        fields: dict[str, RequestValue],
    ) -> MonitorDto:
        req = build_request(MonitorOverlayRequest, body, fields, f"monitors.{verb}")
        path = f"{_monitor_path(id)}/{verb}"
        return parse_single(
            MonitorDto, await api_post(self._client, path, req), f"POST {path}"
        )

    async def _verb(self, id: ResourceId | int, verb: str) -> MonitorDto:
        path = f"{_monitor_path(id)}/{verb}"
        return parse_single(
            MonitorDto, await api_post(self._client, path), f"POST {path}"
        )

    async def pause(
        self,
        id: ResourceId | int,
        body: RequestBody[MonitorOverlayRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Pause scheduled runs (``reason``, ``expires_at`` optional)."""
        return await self._overlay(id, "pause", body, fields)

    async def resume(self, id: ResourceId | int) -> MonitorDto:
        """Resume a paused monitor."""
        return await self._verb(id, "resume")

    async def mute(
        self,
        id: ResourceId,
        body: RequestBody[MonitorOverlayRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Mute alert delivery (``reason``, ``expires_at`` optional)."""
        return await self._overlay(id, "mute", body, fields)

    async def unmute(self, id: ResourceId) -> MonitorDto:
        """Deliver alerts again."""
        return await self._verb(id, "unmute")

    async def quarantine(
        self,
        id: ResourceId,
        body: RequestBody[QuarantineMonitorRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Hold a flaky monitor out of alerting until ``expires_at``."""
        req = build_request(
            QuarantineMonitorRequest, body, fields, "monitors.quarantine"
        )
        path = f"{_monitor_path(id)}/quarantine"
        return parse_single(
            MonitorDto, await api_post(self._client, path, req), f"POST {path}"
        )

    async def release_quarantine(self, id: ResourceId) -> MonitorDto:
        """End a quarantine early."""
        return await self._verb(id, "release-quarantine")

    async def transfer(
        self,
        id: ResourceId,
        body: RequestBody[TransferMonitorRequest] | None = None,
        **fields: RequestValue,
    ) -> MonitorDto:
        """Move ownership to another tool (``to``, ``reason``; audited)."""
        req = build_request(TransferMonitorRequest, body, fields, "monitors.transfer")
        path = f"{_monitor_path(id)}/transfer"
        return parse_single(
            MonitorDto, await api_post(self._client, path, req), f"POST {path}"
        )

    async def takeover(self, id: ResourceId, *, field: str) -> MonitorDto:
        """Clear one dashboard overlay: ``managedBy``, ``enabled``, ``muted``
        or ``quarantine``."""
        path = f"{_monitor_path(id)}/takeover"
        body = TakeoverMonitorRequest(field=field)
        return parse_single(
            MonitorDto, await api_post(self._client, path, body), f"POST {path}"
        )

    # -- code lifecycle -----------------------------------------------------

    async def publish(
        self,
        id: ResourceId,
        body: RequestBody[PublishRevisionRequest] | None = None,
        **fields: RequestValue,
    ) -> DefinitionHeadDto:
        """Make a revision live in the monitor's environment.

        Publishing does not require a test unless ``require_tested=True``.
        ``expected_live_revision_id`` refuses the publish (409
        ``LIVE_REVISION_CHANGED``) if someone published in between.
        """
        req = build_request(PublishRevisionRequest, body, fields, "monitors.publish")
        path = f"{_monitor_path(id)}/publish"
        return parse_single(
            DefinitionHeadDto, await api_post(self._client, path, req), f"POST {path}"
        )

    async def rollback(
        self,
        id: ResourceId,
        body: RequestBody[RollbackRevisionRequest] | None = None,
        **fields: RequestValue,
    ) -> DefinitionHeadDto:
        """Restore a previous revision (default: the one live before).

        ``reason`` is required; ``emergency=True`` needs a confirmed incident.
        """
        req = build_request(RollbackRevisionRequest, body, fields, "monitors.rollback")
        path = f"{_monitor_path(id)}/rollback"
        return parse_single(
            DefinitionHeadDto, await api_post(self._client, path, req), f"POST {path}"
        )

    async def rollback_preview(
        self, id: ResourceId, *, revision_id: ResourceId | None = None
    ) -> RollbackPreviewDto:
        """What a rollback would restore and which monitors it moves."""
        path = f"{_monitor_path(id)}/rollback-preview"
        params = {"revisionId": str(revision_id)} if revision_id else None
        return parse_single(
            RollbackPreviewDto, await api_get(self._client, path, params), f"GET {path}"
        )

    # -- runs ---------------------------------------------------------------

    async def test(
        self,
        id: ResourceId,
        *,
        code: CodeInput | MonitorCodeSpec | None = None,
        region: str | None = None,
        session: Session = None,
        root: Root = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto:
        """Queue a validation run of a code monitor in its own environment.

        With ``code`` it tests that code (as an unpublished revision) instead
        of the live one. Billed, saved, never signals. ``wait=True`` returns
        the finished run.

        On an uptime monitor this raises ``ValidationError`` with code
        ``USE_PROBE``: call :meth:`probe` for those.
        """
        spec = None if code is None else await code_spec(self._client, code, root=root)
        body = CodeTestTargetRequest(
            region=region, code=spec, session=_session(session)
        )
        path = f"{_monitor_path(id)}/test"
        status, data = await api_post_with_status(self._client, path, body)
        if status != 202:
            raise client_error(
                "validation",
                "USE_PROBE",
                "This is an uptime monitor: monitors.test() runs code checks. "
                "Use monitors.probe(id) for a probe result.",
                next_command="monitors.probe(id)",
            )
        run = parse_single(RunDto, data, f"POST {path}")
        return await _maybe_wait(self._client, run, wait, timeout_ms)

    async def probe(self, id: ResourceId | int) -> MonitorTestResultDto:
        """Probe an uptime monitor once and return the result. Nothing is saved.

        A code monitor raises ``DevhelmMonitorTestQueuedError`` carrying the
        validation run the API queued; use :meth:`test` for those.
        """
        path = f"{_monitor_path(id)}/test"
        status, data = await api_post_with_status(self._client, path)
        if status == 202:
            raise DevhelmMonitorTestQueuedError(
                parse_single(RunDto, data, f"POST {path}")
            )
        return parse_single(MonitorTestResultDto, data, f"POST {path}")

    async def test_run(
        self, id: ResourceId, target: RequestBody[CodeTestTargetRequest] | None = None
    ) -> RunDto:
        """Deprecated spelling of :meth:`test` for code monitors."""
        deprecated("monitors.test_run()", "monitors.test()")
        path = f"{_monitor_path(id)}/test"
        body = (
            None
            if target is None
            else validate_request(CodeTestTargetRequest, target, "monitors.test_run")
        )
        status, data = await api_post_with_status(self._client, path, body)
        if status != 202:
            raise DevhelmValidationError(
                f"Response validation failed (POST {path}): expected a queued "
                f"validation run (202), got {status}. This is an uptime monitor; "
                "use monitors.probe() for it."
            )
        return parse_single(RunDto, data, f"POST {path}")

    @overload
    async def test_adhoc(
        self,
        *,
        type: CodeMonitorType,
        environment: str | UUID,
        code: CodeInput | MonitorCodeSpec,
        config: RequestValue = None,
        region: str | None = None,
        session: Session = None,
        root: Root = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto: ...

    @overload
    async def test_adhoc(
        self,
        *,
        type: UptimeMonitorType,
        config: RequestValue,
        environment: str | UUID | None = None,
        assertions: RequestValue = None,
    ) -> MonitorTestResultDto: ...

    async def test_adhoc(
        self,
        *,
        type: CodeMonitorType | UptimeMonitorType,
        environment: str | UUID | None = None,
        code: CodeInput | MonitorCodeSpec | None = None,
        config: RequestValue = None,
        assertions: RequestValue = None,
        region: str | None = None,
        session: Session = None,
        root: Root = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto | MonitorTestResultDto:
        """Test code or a probe config without a saved monitor.

        Code types (``BROWSER``, ``MULTI_STEP_API``) return a validation
        ``RunDto`` (billed, saved, no ``monitor_id``); uptime types return
        the probe result.
        """
        data: dict[str, RequestValue] = {"type": type}
        if environment is not None:
            data["environmentId"] = str(
                await resolve_environment_id(self._client, environment)
            )
        if is_code_type(type):
            if code is None:
                raise client_error(
                    "validation",
                    "FIELD_REQUIRED",
                    f"test_adhoc for a {type} check needs code=",
                    field="code",
                )
            checked = check_config(type, config if config is not None else {})
            data["config"] = checked
            data["code"] = await code_spec(
                self._client, code, root=root, runtime_id=_runtime_of(checked)
            )
            if session is not None:
                data["session"] = _session(session)
            if region is not None:
                data["region"] = region
        else:
            data["config"] = check_config(type, config)
            if assertions is not None:
                data["assertions"] = assertions
        req = validate_request(MonitorTestRequest, data, "monitors.test_adhoc")
        path = f"{_BASE}/test"
        status, raw = await api_post_with_status(self._client, path, req)
        if status == 202:
            run = parse_single(RunDto, raw, f"POST {path}")
            return await _maybe_wait(self._client, run, wait, timeout_ms)
        return parse_single(MonitorTestResultDto, raw, f"POST {path}")

    async def run_now(
        self,
        id: ResourceId,
        *,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> RunDto:
        """Run a code monitor once in its first region, now (works when
        paused). Never votes on health."""
        path = f"{_monitor_path(id)}/runs"
        run = parse_single(RunDto, await api_post(self._client, path), f"POST {path}")
        return await _maybe_wait(self._client, run, wait, timeout_ms)

    @overload
    async def trigger(
        self,
        id: ResourceId,
        *,
        regions: Sequence[str] | None = None,
        signal: bool | None = None,
        session: Session = None,
        wait: Literal[False] = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> TriggerRunsResponse: ...

    @overload
    async def trigger(
        self,
        id: ResourceId,
        *,
        regions: Sequence[str] | None = None,
        signal: bool | None = None,
        session: Session = None,
        wait: Literal[True],
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> TriggeredRuns: ...

    async def trigger(
        self,
        id: ResourceId,
        *,
        regions: Sequence[str] | None = None,
        signal: bool | None = None,
        session: Session = None,
        wait: bool = False,
        timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    ) -> TriggerRunsResponse | TriggeredRuns:
        """Run a code monitor now in several regions (default: all configured).

        Billed one run per region. The runs never alert unless
        ``signal=True``. With ``wait=True`` returns every finished run.
        """
        body = TriggerRunRequest(
            regions=list(regions) if regions is not None else None,
            signal=signal,
            session=_session(session),
        )
        path = f"{_monitor_path(id)}/triggers"
        started = parse_single(
            TriggerRunsResponse,
            await api_post(self._client, path, body),
            f"POST {path}",
        )
        if not wait:
            return started
        # One deadline for the whole trigger, not timeout_ms per region.
        deadline = monotonic() + timeout_ms / 1000
        runs = []
        for ref in started.runs:
            remaining_ms = max(0, int((deadline - monotonic()) * 1000))
            runs.append(
                await wait_for_run(self._client, str(ref.id), timeout_ms=remaining_ms)
            )
        return TriggeredRuns(trigger=started, runs=runs)

    async def results(
        self, id: ResourceId | int, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[CheckResultDto]:
        """Deprecated: probe check results. Use ``monitors.history.list(id)``."""
        deprecated("monitors.results(id)", "monitors.history.list(id)")
        return await fetch_cursor_page(
            self._client,
            f"{_monitor_path(id)}/results",
            CheckResultDto,
            cursor=cursor,
            limit=limit,
        )
