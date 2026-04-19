"""Tests for HTTP utilities and Pydantic validation layer."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from devhelm._errors import DevhelmError
from devhelm._http import DevhelmConfig, build_client, path_param, unwrap_single
from devhelm._validation import parse_list, parse_model, parse_single

# ---------- unwrap_single (raw JSON envelope) ----------


class TestUnwrapSingle:
    def test_unwraps_data_key(self) -> None:
        assert unwrap_single({"data": {"id": 1}}) == {"id": 1}

    def test_returns_bare_value(self) -> None:
        assert unwrap_single({"id": 1}) == {"id": 1}

    def test_unwraps_null_data(self) -> None:
        assert unwrap_single({"data": None}) is None

    def test_unwraps_nested_data(self) -> None:
        result = unwrap_single({"data": {"data": "inner"}})
        assert result == {"data": "inner"}

    def test_non_dict_passthrough(self) -> None:
        assert unwrap_single([1, 2, 3]) == [1, 2, 3]


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

    def test_dict_passthrough(self) -> None:
        from devhelm._http import _serialize_body

        d = {"key": "value"}
        assert _serialize_body(d) is d

    def test_none_passthrough(self) -> None:
        from devhelm._http import _serialize_body

        assert _serialize_body(None) is None
