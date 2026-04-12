"""Tests for HTTP utilities."""

from __future__ import annotations

import pytest

from devhelm._errors import DevhelmError
from devhelm._http import DevhelmConfig, build_client, path_param, unwrap_single


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


class TestPathParam:
    def test_encodes_string(self) -> None:
        assert path_param("hello world") == "hello%20world"

    def test_encodes_int(self) -> None:
        assert path_param(42) == "42"

    def test_encodes_slash(self) -> None:
        assert path_param("a/b") == "a%2Fb"

    def test_encodes_special_chars(self) -> None:
        assert path_param("key?val#frag") == "key%3Fval%23frag"


class TestBuildClient:
    def test_requires_org_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DEVHELM_ORG_ID", raising=False)
        monkeypatch.delenv("DEVHELM_WORKSPACE_ID", raising=False)
        config = DevhelmConfig(token="test-token")
        with pytest.raises(DevhelmError, match="org_id is required"):
            build_client(config)

    def test_requires_workspace_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DEVHELM_WORKSPACE_ID", raising=False)
        config = DevhelmConfig(token="test-token", org_id="1")
        with pytest.raises(DevhelmError, match="workspace_id is required"):
            build_client(config)

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

    def test_strips_trailing_slash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEVHELM_ORG_ID", "1")
        monkeypatch.setenv("DEVHELM_WORKSPACE_ID", "1")
        config = DevhelmConfig(token="t", base_url="https://api.example.com///")
        client = build_client(config)
        assert str(client.base_url) == "https://api.example.com"
        client.close()
