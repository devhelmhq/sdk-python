"""Tests for the public validation helpers in :mod:`devhelm._validation`.

Focuses on :func:`parse_strict_envelope`, which guarantees P1 (response
extras forbidden) for envelopes whose ``data`` field can legitimately be
``null`` (today: only ``GET /api/v1/deploy/lock``).
"""

from __future__ import annotations

import pytest

from devhelm._errors import DevhelmValidationError
from devhelm._generated import DeployLockDto
from devhelm._validation import parse_strict_envelope


class TestParseStrictEnvelope:
    def _valid_lock(self) -> dict[str, str | int]:
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "lockedBy": "ci-bot",
            "lockedAt": "2026-01-01T00:00:00Z",
            "expiresAt": "2026-01-01T00:30:00Z",
        }

    def test_unwraps_data_into_typed_model(self) -> None:
        lock = parse_strict_envelope(
            DeployLockDto, {"data": self._valid_lock()}, context="ctx"
        )
        assert lock is not None
        assert lock.locked_by == "ci-bot"

    def test_returns_none_when_data_is_null_and_optional(self) -> None:
        result = parse_strict_envelope(
            DeployLockDto, {"data": None}, optional=True, context="ctx"
        )
        assert result is None

    def test_raises_when_data_null_and_not_optional(self) -> None:
        with pytest.raises(DevhelmValidationError, match="missing required `data`"):
            parse_strict_envelope(DeployLockDto, {"data": None}, context="ctx")

    def test_rejects_unknown_top_level_keys(self) -> None:
        with pytest.raises(DevhelmValidationError, match="Unknown envelope fields"):
            parse_strict_envelope(
                DeployLockDto,
                {"data": self._valid_lock(), "metadata": {"hint": "drift"}},
                optional=True,
                context="ctx",
            )

    def test_unknown_keys_surface_as_structured_errors(self) -> None:
        with pytest.raises(DevhelmValidationError) as exc_info:
            parse_strict_envelope(
                DeployLockDto, {"data": None, "x": 1, "y": 2}, optional=True
            )
        # Sorted by key for determinism — `x` first, `y` second.
        assert exc_info.value.errors == [
            {
                "loc": ("x",),
                "msg": "Extra inputs are not permitted",
                "type": "extra_forbidden",
            },
            {
                "loc": ("y",),
                "msg": "Extra inputs are not permitted",
                "type": "extra_forbidden",
            },
        ]

    def test_rejects_non_dict_response(self) -> None:
        with pytest.raises(DevhelmValidationError, match="Expected envelope dict"):
            parse_strict_envelope(DeployLockDto, "not a dict", optional=True)

    def test_inner_validation_failure_propagates_pydantic_errors(self) -> None:
        with pytest.raises(DevhelmValidationError) as exc_info:
            parse_strict_envelope(
                DeployLockDto,
                {"data": {"id": "not-a-uuid"}},
                context="GET /api/v1/deploy/lock",
            )
        # Pydantic-level errors were captured (not the hand-rolled
        # extra_forbidden shape), so the failure points at the inner field.
        assert exc_info.value.errors  # non-empty
        assert any(e["type"] != "extra_forbidden" for e in exc_info.value.errors)
