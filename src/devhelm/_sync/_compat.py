"""Blocking primitives. ``devhelm._async._compat`` is the async twin.

Generated sync code imports time and concurrency helpers from here. This
file is hand-written, not generated.
"""

from __future__ import annotations

import threading
import time

Event = threading.Event


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def monotonic() -> float:
    return time.monotonic()


def is_set(event: Event | None) -> bool:
    return event is not None and event.is_set()
