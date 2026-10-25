"""Real-API matrix for code checks (doc 42 §5.5.3).

Runs against the mono test stack (``make test-up``: API on :8081) when
``DEVHELM_E2E_API_URL`` is set, for example::

    DEVHELM_E2E_API_URL=http://localhost:8081 DEVHELM_API_TOKEN=devhelm-dev-token \\
    DEVHELM_ORG_ID=2 DEVHELM_WORKSPACE_ID=2 uv run pytest tests/test_synthetics_live.py

The test stack has no execution fleet. The matrix asserts on the contract
(status codes, Run shape, phase, ``startDeadlineAt``, error envelopes), not on
``passed``. Where the stack holds run admission, the run-producing calls must
answer the typed, retryable ``PlatformError`` (``RUNTIME_UNAVAILABLE``)
instead of a run; both answers are checked. Every resource it creates is
named ``sdk-python-e2e-<random>`` and deleted at the end.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import Callable, Iterator
from typing import TypeVar
from uuid import UUID

import pytest

from devhelm import (
    AsyncDevhelm,
    ConflictError,
    Devhelm,
    DevhelmMonitorTestQueuedError,
    FilesCode,
    MonitorDto,
    NotFoundError,
    PlatformError,
    RunDto,
    ValidationError,
    bundle_digest,
)

API_URL = os.environ.get("DEVHELM_E2E_API_URL")

pytestmark = pytest.mark.skipif(
    not API_URL, reason="DEVHELM_E2E_API_URL is not set (no test stack)"
)

BROWSER_SPEC = """import { test, expect } from '@playwright/test'

test('home loads', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/Example/)
})
"""

API_SPEC = """import { test, expect } from '@playwright/test'

test('health answers', async ({ request }) => {
  const res = await request.get('/health')
  expect(res.ok()).toBeTruthy()
})
"""

PHASES = {"created", "queued", "starting", "running", "finalizing", "finished"}
T = TypeVar("T")


def _code(entry: str, src: str) -> FilesCode:
    return FilesCode(entrypoint=entry, files={entry: src})


@pytest.fixture(scope="module")
def devhelm() -> Iterator[Devhelm]:
    # Two attempts keep a held-admission 503 fast while still exercising retry.
    client = Devhelm(base_url=API_URL, max_attempts=2)
    yield client
    client.close()


@pytest.fixture(scope="module")
def environment(devhelm: Devhelm) -> Iterator[str]:
    slug = f"sdk-python-e2e-{secrets.token_hex(4)}"
    devhelm.environments.create(
        {"name": slug, "slug": slug, "variables": {"BASE_URL": "https://example.com"}}
    )
    yield slug
    devhelm.environments.delete(slug)


def _assert_run(run: RunDto) -> None:
    assert isinstance(run.id, UUID)
    assert run.phase in PHASES
    assert run.counts_toward_health is False
    if run.phase != "finished":
        assert run.outcome is None
    if run.phase in {"created", "queued"}:
        assert run.start_deadline_at is not None


def _run_or_held(call: Callable[[], T]) -> T | None:
    """A run-producing call returns its result, or the typed held-admission
    refusal (``PlatformError`` ``RUNTIME_UNAVAILABLE``, retryable)."""
    try:
        return call()
    except PlatformError as err:
        assert err.status == 503
        assert err.code == "RUNTIME_UNAVAILABLE"
        assert err.retryable is True
        assert err.request_id
        return None


def _create(
    devhelm: Devhelm, environment: str, kind: str, entry: str, src: str
) -> MonitorDto:
    return devhelm.monitors.create(
        name=f"sdk-python-e2e-{kind.lower()}-{secrets.token_hex(4)}",
        type=kind,
        environment=environment,
        code=_code(entry, src),
        frequency_seconds=600,
        regions=["us-east"],
    )


CASES = [
    ("BROWSER", "home.spec.ts", BROWSER_SPEC),
    ("MULTI_STEP_API", "health.spec.ts", API_SPEC),
]


@pytest.mark.parametrize(("kind", "entry", "src"), CASES)
def test_code_check_lifecycle(  # noqa: C901 (one journey, read top to bottom)
    devhelm: Devhelm, environment: str, kind: str, entry: str, src: str
) -> None:
    created = _create(devhelm, environment, kind, entry, src)
    try:
        # create: revision 1 is live at once (read back with GET)
        m = devhelm.monitors.get(created.id)
        assert m.type == kind
        assert m.live_revision_id is not None
        assert m.live_revision_digest is not None
        assert m.live_revision_digest.startswith("sha256:")
        assert [x.id for x in devhelm.monitors.list(name=m.name)] == [m.id]

        # test the live code: a validation run (or held admission)
        run = _run_or_held(lambda: devhelm.monitors.test(m.id))
        if run is not None:
            _assert_run(run)
            assert run.source == "remote_validation"
            assert devhelm.runs.get(run.id).id == run.id

        # change: draft -> test -> publish
        code_v2 = _code(entry, src + "\n// v2\n")
        draft = devhelm.monitors.revisions.create(m.id, code=code_v2).revision
        assert draft.state == "draft"
        assert draft.digest.startswith("sha256:")
        again = devhelm.monitors.revisions.create(m.id, code=code_v2).revision
        assert again.id == draft.id  # same digest reuses the draft
        tested = _run_or_held(lambda: devhelm.monitors.revisions.test(m.id, draft.id))
        if tested is not None:
            _assert_run(tested)
            assert tested.revision_id == draft.id
        head = devhelm.monitors.publish(
            m.id, revision_id=draft.id, expected_live_revision_id=m.live_revision_id
        )
        assert head.revision.id == draft.id

        # a stale expected_live_revision_id is a typed conflict
        with pytest.raises(ConflictError) as stale:
            devhelm.monitors.publish(
                m.id, revision_id=draft.id, expected_live_revision_id=m.live_revision_id
            )
        assert stale.value.code == "LIVE_REVISION_CHANGED"

        # trigger and run now: one run per region, never signals
        started = _run_or_held(
            lambda: devhelm.monitors.trigger(m.id, regions=["us-east"])
        )
        if started is not None:
            assert started.billed_runs == len(started.runs) == 1
            assert started.runs[0].region == "us-east"
        one = _run_or_held(lambda: devhelm.monitors.run_now(m.id))
        if one is not None:
            _assert_run(one)

        # rollback to revision 1, then read revisions
        preview = devhelm.monitors.rollback_preview(m.id)
        assert preview.target.id == m.live_revision_id
        rolled = devhelm.monitors.rollback(m.id, reason="sdk-python e2e rollback")
        assert rolled.revision.id == m.live_revision_id
        ids = {r.id for r in devhelm.monitors.revisions.list(m.id, state="all").data}
        assert {m.live_revision_id, draft.id} <= ids
        assert devhelm.monitors.revisions.get(m.id, draft.id).id == draft.id
        files = devhelm.monitors.revisions.files(m.id, draft.id)
        assert entry in files.files
        diff = devhelm.monitors.revisions.diff(m.id, draft.id)
        assert {diff.left.id, diff.right.id} == {draft.id, m.live_revision_id}

        # the probe verb refuses a code monitor with the queued run or held admission
        try:
            devhelm.monitors.probe(m.id)
        except DevhelmMonitorTestQueuedError as queued:
            _assert_run(queued.run)
        except PlatformError as held:
            assert held.code == "RUNTIME_UNAVAILABLE"

        devhelm.monitors.history.list(m.id)
        devhelm.monitors.drift(m.id)
    finally:
        devhelm.monitors.delete(created.id)

    # delete -> trash -> restore -> delete
    assert any(t.id == created.id for t in devhelm.monitors.trash.list())
    assert devhelm.monitors.restore(created.id).id == created.id
    devhelm.monitors.delete(created.id)


@pytest.mark.xfail(
    strict=True,
    reason="API: POST /monitors returns liveRevisionId=null for code monitors; "
    "GET has it (reported to Wave 0)",
)
@pytest.mark.parametrize(("kind", "entry", "src"), CASES)
def test_create_response_carries_live_revision(
    devhelm: Devhelm, environment: str, kind: str, entry: str, src: str
) -> None:
    m = _create(devhelm, environment, kind, entry, src)
    try:
        assert m.live_revision_id is not None
        assert m.live_revision_digest is not None
    finally:
        devhelm.monitors.delete(m.id)


def test_bundle_digest_matches_server(devhelm: Devhelm) -> None:
    files = {"a.spec.ts": BROWSER_SPEC.replace("\n", "\r\n"), "data.json": "{}"}
    bundle = devhelm.bundles.create(FilesCode(entrypoint="a.spec.ts", files=files))
    local = bundle_digest({k: v.encode() for k, v in files.items()})
    assert bundle.upload_digest == local


def test_uptime_test_is_use_probe(devhelm: Devhelm) -> None:
    m = devhelm.monitors.create(
        name=f"sdk-python-e2e-http-{secrets.token_hex(4)}",
        type="HTTP",
        config={"url": "https://example.com", "method": "GET"},
        frequency_seconds=600,
        regions=["us-east"],
    )
    try:
        try:
            devhelm.monitors.test(m.id)
        except ValidationError as err:
            assert err.code == "USE_PROBE"
            assert err.status == 0
        except PlatformError as err:
            # The stack's probe service is an external dependency (mono's
            # surface tests skip on the same answer).
            pytest.skip(f"probe service unavailable: {err.message}")
        else:
            pytest.fail("monitors.test() on an HTTP monitor must raise USE_PROBE")
    finally:
        devhelm.monitors.delete(m.id)


def test_errors_are_typed(devhelm: Devhelm) -> None:
    with pytest.raises(NotFoundError) as missing:
        devhelm.monitors.get("00000000-0000-0000-0000-000000000001")
    assert missing.value.category == "not_found"
    assert missing.value.status == 404
    assert missing.value.request_id


def test_async_client_reads(environment: str) -> None:
    async def go() -> None:
        async with AsyncDevhelm(base_url=API_URL) as client:
            assert await client.runtimes.list()
            env = await client.environments.get(environment)
            assert env.slug == environment
            page = await client.runs.list(limit=5)
            assert len(page.data) <= 5

    asyncio.run(go())
