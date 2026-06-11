"""Tests for HTTP utilities and Pydantic validation layer."""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel, Field

from devhelm._errors import DevhelmError, DevhelmRateLimitError
from devhelm._http import DevhelmConfig, api_get, build_client, path_param
from devhelm._validation import parse_list, parse_model, parse_single

# ---------- path_param ----------


class TestPathParam:
    def test_encodes_string(self) -> None:
        assert path_param("hello world") == "hello%20world"

    def test_encodes_int(self) -> None:
        assert path_param(42) == "42"

    def test_encodes_slash(self) -> None:
        assert path_param("a/b") == "a%2Fb"

    def test_encodes_special_chars(self) -> None:
        assert path_param("key?val#frag") == "key%3Fval%23frag"


# ---------- build_client ----------


class TestBuildClient:
    def test_defaults_org_and_workspace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DEVHELM_ORG_ID", raising=False)
        monkeypatch.delenv("DEVHELM_WORKSPACE_ID", raising=False)
        config = DevhelmConfig(token="test-token")
        client = build_client(config)
        assert client.headers["x-phelm-org-id"] == "1"
        assert client.headers["x-phelm-workspace-id"] == "1"
        client.close()

    def test_reads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEVHELM_ORG_ID", "42")
        monkeypatch.setenv("DEVHELM_WORKSPACE_ID", "7")
        config = DevhelmConfig(token="test-token")
        client = build_client(config)
        assert client.headers["x-phelm-org-id"] == "42"
        assert client.headers["x-phelm-workspace-id"] == "7"
        client.close()

    def test_config_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEVHELM_ORG_ID", "env-org")
        monkeypatch.setenv("DEVHELM_WORKSPACE_ID", "env-ws")
        config = DevhelmConfig(token="t", org_id="cfg-org", workspace_id="cfg-ws")
        client = build_client(config)
        assert client.headers["x-phelm-org-id"] == "cfg-org"
        assert client.headers["x-phelm-workspace-id"] == "cfg-ws"
        client.close()

    def test_strips_trailing_slash(self) -> None:
        config = DevhelmConfig(token="t", base_url="https://api.example.com///")
        client = build_client(config)
        assert str(client.base_url) == "https://api.example.com"
        client.close()


# ---------- Surface telemetry headers ----------


class TestSurfaceTelemetry:
    """The SDK reports its identity to the API on every authenticated request
    so the GTM rollup can attribute usage. See https://devhelm.io/telemetry."""

    def test_default_headers_announce_sdk_py(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEVHELM_TELEMETRY", raising=False)
        client = build_client(DevhelmConfig(token="t"))
        assert client.headers["x-devhelm-surface"] == "sdk-py"
        # version comes from importlib.metadata; its exact value is the
        # SDK release, but it must always be a non-empty string.
        assert client.headers["x-devhelm-surface-version"]
        assert client.headers["x-devhelm-sdk-name"] == "sdk-py"
        client.close()

    def test_wrapper_can_override_surface(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEVHELM_TELEMETRY", raising=False)
        client = build_client(
            DevhelmConfig(
                token="t",
                surface="mcp",
                surface_version="0.5.0",
                surface_metadata={"Mcp-Client": "cursor"},
            )
        )
        assert client.headers["x-devhelm-surface"] == "mcp"
        assert client.headers["x-devhelm-surface-version"] == "0.5.0"
        # SDK identity is preserved alongside the wrapper surface.
        assert client.headers["x-devhelm-sdk-name"] == "sdk-py"
        assert client.headers["x-devhelm-mcp-client"] == "cursor"
        client.close()

    def test_env_opt_out_drops_all_surface_headers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEVHELM_TELEMETRY", "0")
        client = build_client(
            DevhelmConfig(token="t", surface="mcp", surface_metadata={"X": "y"})
        )
        # Surface, version, sdk-name, and any extras must all be absent.
        assert "x-devhelm-surface" not in client.headers
        assert "x-devhelm-surface-version" not in client.headers
        assert "x-devhelm-sdk-name" not in client.headers
        assert "x-devhelm-x" not in client.headers
        # Auth + tenant headers must still be there — opt-out is for
        # telemetry only, not for legitimate routing headers.
        assert client.headers["x-phelm-org-id"] == "1"
        client.close()


# ---------- Rate-limit Retry-After surfacing ----------


class TestRetryAfterFromResponse:
    """A 429 with a ``Retry-After`` header must surface ``retry_after`` as an
    integer on the raised :class:`DevhelmRateLimitError` so callers can back
    off for exactly as long as the server asked.
    """

    def test_429_retry_after_header_surfaces_as_int(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                429,
                headers={"Retry-After": "30"},
                json={"message": "Slow down", "code": "RATE_LIMITED"},
            )

        client = httpx.Client(
            transport=httpx.MockTransport(handler), base_url="http://localhost:8080"
        )
        with pytest.raises(DevhelmRateLimitError) as exc_info:
            api_get(client, "/api/v1/monitors")
        client.close()

        err = exc_info.value
        assert err.status == 429
        assert err.retry_after == 30
        assert isinstance(err.retry_after, int)

    def test_429_without_header_has_none_retry_after(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"message": "Slow down"})

        client = httpx.Client(
            transport=httpx.MockTransport(handler), base_url="http://localhost:8080"
        )
        with pytest.raises(DevhelmRateLimitError) as exc_info:
            api_get(client, "/api/v1/monitors")
        client.close()

        assert exc_info.value.retry_after is None


# ---------- Pydantic validation helpers ----------


class _Item(BaseModel):
    id: int
    name: str


class _AliasedItem(BaseModel):
    my_field: str = Field(alias="myField")


class TestParseModel:
    def test_valid_data(self) -> None:
        result = parse_model(_Item, {"id": 1, "name": "test"})
        assert result.id == 1
        assert result.name == "test"

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Response validation failed"):
            parse_model(_Item, {"id": 1})

    def test_wrong_type_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Response validation failed"):
            parse_model(_Item, {"id": "not-a-number", "name": "test"})

    def test_context_in_error(self) -> None:
        with pytest.raises(DevhelmError, match="GET /api/v1/monitors"):
            parse_model(_Item, {}, "GET /api/v1/monitors")

    def test_extra_fields_are_allowed(self) -> None:
        result = parse_model(_Item, {"id": 1, "name": "test", "extra": True})
        assert result.id == 1

    def test_aliased_field(self) -> None:
        result = parse_model(_AliasedItem, {"myField": "hello"})
        assert result.my_field == "hello"

    def test_none_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Response validation failed"):
            parse_model(_Item, None)


class TestParseSingle:
    def test_unwraps_data_envelope(self) -> None:
        result = parse_single(_Item, {"data": {"id": 1, "name": "test"}})
        assert result.id == 1

    def test_bare_dict_without_envelope(self) -> None:
        result = parse_single(_Item, {"id": 1, "name": "test"})
        assert result.id == 1

    def test_invalid_data_inside_envelope_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Response validation failed"):
            parse_single(_Item, {"data": {"id": "bad"}})

    def test_null_data_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Response validation failed"):
            parse_single(_Item, {"data": None})


class TestParseList:
    def test_valid_list(self) -> None:
        result = parse_list(_Item, [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].name == "b"

    def test_empty_list(self) -> None:
        result = parse_list(_Item, [])
        assert result == []

    def test_invalid_item_raises(self) -> None:
        with pytest.raises(DevhelmError, match="List validation failed"):
            parse_list(_Item, [{"id": 1, "name": "ok"}, {"id": "bad"}])

    def test_non_list_raises(self) -> None:
        with pytest.raises(DevhelmError, match="Expected list"):
            parse_list(_Item, {"id": 1})

    def test_context_in_error(self) -> None:
        with pytest.raises(DevhelmError, match="GET /api/v1/monitors"):
            parse_list(_Item, "not-a-list", "GET /api/v1/monitors")


class TestSerializeBody:
    def test_pydantic_model_serialized(self) -> None:
        from devhelm._http import _serialize_body

        item = _AliasedItem(myField="test")
        result = _serialize_body(item)
        assert result == {"myField": "test"}

    def test_dict_rejected(self) -> None:
        import pytest

        from devhelm._errors import DevhelmError
        from devhelm._http import _serialize_body

        with pytest.raises(DevhelmError, match="Raw dicts are not accepted"):
            _serialize_body({"key": "value"})

    def test_none_passthrough(self) -> None:
        from devhelm._http import _serialize_body

        assert _serialize_body(None) is None
