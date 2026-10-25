"""``Devhelm`` and ``AsyncDevhelm`` expose one surface, method for method.

The sync client is generated from the async sources by
``scripts/unasync.py``; these tests pin that the generated files are fresh,
that every resource has the same public methods with the same signatures,
and that the async client works end to end on a mock transport.
"""

from __future__ import annotations

import asyncio
import inspect
import re
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from devhelm import AsyncDevhelm, CursorPage, Devhelm, MonitorDto
from devhelm._async.resources.monitors import Monitors as AsyncMonitors
from devhelm._async.resources.runs import Runs as AsyncRuns
from tests.test_synthetics_monitors import (
    BASE,
    ENV,
    MEMORY_CODE,
    MID,
    Router,
    add_bundles,
    body_of,
    cursor,
    monitor,
    run,
    single,
)

ROOT = Path(__file__).resolve().parent.parent

Surface = dict[str, dict[str, inspect.Signature]]


def _is_resource(value: object) -> bool:
    module = type(value).__module__
    return module.startswith("devhelm.resources") or module.startswith(
        "devhelm._async.resources"
    )


def _methods(cls: type) -> dict[str, inspect.Signature]:
    out: dict[str, inspect.Signature] = {}
    for name, member in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_") and name != "__call__":
            continue
        out[name] = inspect.signature(member)
    return out


def _surface(root: object, prefix: str = "") -> Surface:
    found: Surface = {}
    for name, value in sorted(vars(root).items()):
        if name.startswith("_") or not _is_resource(value):
            continue
        path = f"{prefix}{name}"
        found[path] = _methods(type(value))
        found.update(_surface(value, f"{path}."))
    return found


def _normalise(text: str) -> str:
    return re.sub(r"\bAsync(?=[A-Z])", "", text)


def _shape(sig: inspect.Signature) -> list[tuple[str, str, str, str]]:
    return [
        (p.name, str(p.kind), repr(p.default), _normalise(str(p.annotation)))
        for p in sig.parameters.values()
    ] + [("return", "", "", _normalise(str(sig.return_annotation)))]


@pytest.fixture
def surfaces() -> tuple[Surface, Surface]:
    sync = Devhelm(token="t", base_url="http://x")
    aio = AsyncDevhelm(token="t", base_url="http://x")
    return _surface(sync), _surface(aio)


def test_same_resources(surfaces: tuple[Surface, Surface]) -> None:
    sync, aio = surfaces
    assert sorted(sync) == sorted(aio)
    # Spot-check the synthetics tree is reachable on both.
    for path in (
        "monitors.revisions",
        "monitors.versions",
        "runs.artifacts",
        "secrets.values",
    ):
        assert path in sync


def test_same_methods_and_signatures(surfaces: tuple[Surface, Surface]) -> None:
    sync, aio = surfaces
    for path, methods in sync.items():
        assert sorted(methods) == sorted(aio[path]), path
        for name, sig in methods.items():
            assert _shape(sig) == _shape(aio[path][name]), f"{path}.{name}"


def test_async_methods_are_coroutines() -> None:
    aio = AsyncDevhelm(token="t", base_url="http://x")
    checked = 0
    for path, methods in _surface(aio).items():
        obj: object = aio
        for part in path.split("."):
            obj = getattr(obj, part)
        for name in methods:
            assert inspect.iscoroutinefunction(getattr(type(obj), name)), (
                f"{path}.{name}"
            )
            checked += 1
    assert checked > 200


def test_sync_methods_are_not_coroutines() -> None:
    sync = Devhelm(token="t", base_url="http://x")
    for path, methods in _surface(sync).items():
        obj: object = sync
        for part in path.split("."):
            obj = getattr(obj, part)
        for name in methods:
            assert not inspect.iscoroutinefunction(getattr(type(obj), name)), (
                f"{path}.{name}"
            )


def _async_client(router: Router) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(router), base_url=BASE)


def test_async_monitor_get_and_create_with_code() -> None:
    router = Router()
    router.add("GET", f"/api/v1/monitors/{MID}", single(monitor()))
    add_bundles(router)
    router.add("POST", "/api/v1/monitors", single(monitor()), status=201)

    async def scenario() -> tuple[MonitorDto, MonitorDto]:
        async with _async_client(router) as http:
            monitors = AsyncMonitors(http)
            got = await monitors.get(MID)
            made = await monitors.create(
                name="Checkout", type="BROWSER", environment=ENV, code=MEMORY_CODE
            )
            return got, made

    got, made = asyncio.run(scenario())
    assert got.name == made.name == "Checkout"
    created = body_of(router.last("POST", "/api/v1/monitors"))
    code = created["code"]
    assert isinstance(code, dict)
    assert code["entrypoint"] == "checkout.spec.ts"


def test_async_runs_list() -> None:
    router = Router()
    router.add("GET", "/api/v1/runs", cursor([run()]))

    async def scenario() -> CursorPage[object]:
        async with _async_client(router) as http:
            page = await AsyncRuns(http).list(outcome="failed")
            return CursorPage(data=list(page.data), has_more=page.has_more)

    page = asyncio.run(scenario())
    assert len(page.data) == 1
    assert router.calls[0].url.params["limit"] == "50"


def test_async_client_closes() -> None:
    async def scenario() -> bool:
        async with AsyncDevhelm(token="t", base_url="http://x") as client:
            http = client._http
        return http.is_closed

    assert asyncio.run(scenario()) is True


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not on PATH")
def test_generated_sync_files_are_fresh() -> None:
    result = subprocess.run(  # noqa: S603 (fixed argv)
        [sys.executable, str(ROOT / "scripts" / "unasync.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
