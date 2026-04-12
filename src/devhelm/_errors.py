from __future__ import annotations

import json
from typing import Literal

DevhelmErrorCode = Literal["AUTH", "NOT_FOUND", "CONFLICT", "VALIDATION", "API"]


class DevhelmError(Exception):
    """Base error for all DevHelm API errors."""

    code: DevhelmErrorCode
    status: int
    message: str
    detail: str | None

    def __init__(
        self,
        code: DevhelmErrorCode,
        message: str,
        status: int,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message
        self.detail = detail


class AuthError(DevhelmError):
    """Raised on 401/403 authentication or authorization failures."""

    def __init__(self, message: str, status: int) -> None:
        super().__init__("AUTH", message, status)


def error_from_response(status: int, body: str) -> DevhelmError:
    """Map an HTTP error response to a typed DevhelmError."""
    message = f"HTTP {status}"
    detail: str | None = None

    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            message = str(parsed.get("message") or parsed.get("error") or message)
            raw_detail = parsed.get("detail")
            if raw_detail is not None:
                detail = str(raw_detail)
    except (json.JSONDecodeError, ValueError):
        if body:
            message = body

    if status in (401, 403):
        return AuthError(message, status)
    if status == 404:
        return DevhelmError("NOT_FOUND", message, status, detail)
    if status == 409:
        return DevhelmError("CONFLICT", message, status, detail)
    if status in (400, 422):
        return DevhelmError("VALIDATION", message, status, detail)
    return DevhelmError("API", message, status, detail)
