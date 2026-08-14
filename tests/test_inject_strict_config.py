"""Classifier used by ``scripts/inject_strict_config.py``.

Request / Params stay strict. Every other generated model is a response
shape and must ignore unknown fields (Postel's Law).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from inject_strict_config import _is_response_shape  # noqa: E402


@pytest.mark.parametrize(
    ("name", "tolerant"),
    [
        ("CreateStatusPageRequest", False),
        ("UpdateMonitorRequest", False),
        ("ListMonitorsParams", False),
        ("StatusPageDto", True),
        ("StatusPageComponentDto", True),
        ("StatusPageBranding", True),
        ("Http", True),
        ("Dns", True),
        ("LinearChannelConfig", True),
        ("CursorPageMonitorDto", True),
        ("WebhookTestResult", True),
    ],
)
def test_is_response_shape(name: str, tolerant: bool) -> None:
    assert _is_response_shape(name) is tolerant
