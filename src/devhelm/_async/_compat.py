"""Async primitives. ``devhelm._sync._compat`` is the blocking twin.

Code under ``devhelm/_async`` imports time and concurrency helpers from here
so ``scripts/unasync.py`` can produce the sync client by swapping this module
for ``devhelm._sync._compat``. This file is hand-written, not generated.
"""

from __future__ import annotations

import asyncio
import time

Event = asyncio.Event


async def sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def monotonic() -> float:
    return time.monotonic()


def is_set(event: Event | None) -> bool:
    return event is not None and event.is_set()
