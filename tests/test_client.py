"""Smoke tests for the Devhelm client class."""

from __future__ import annotations

import httpx
import pytest

from devhelm import Devhelm
from devhelm._http import DevhelmConfig
from devhelm.resources.alert_channels import AlertChannels
from devhelm.resources.api_keys import ApiKeys
from devhelm.resources.dependencies import Dependencies
from devhelm.resources.deploy_lock import DeployLock
from devhelm.resources.environments import Environments
from devhelm.resources.forensics import Forensics
from devhelm.resources.incidents import Incidents
from devhelm.resources.monitors import Monitors
from devhelm.resources.notification_policies import NotificationPolicies
from devhelm.resources.resource_groups import ResourceGroups
from devhelm.resources.secrets import Secrets
from devhelm.resources.status import Status
from devhelm.resources.status_pages import StatusPages
from devhelm.resources.tags import Tags
from devhelm.resources.webhooks import Webhooks


@pytest.fixture
def client() -> Devhelm:
    return Devhelm(token="test-token", base_url="http://localhost:8080")


class TestClientResources:
    def test_monitors(self, client: Devhelm) -> None:
        assert isinstance(client.monitors, Monitors)
        assert callable(client.monitors.list)
        assert callable(client.monitors.get)
        assert callable(client.monitors.create)

    def test_incidents(self, client: Devhelm) -> None:
        assert isinstance(client.incidents, Incidents)

    def test_forensics(self, client: Devhelm) -> None:
        assert isinstance(client.forensics, Forensics)
        assert callable(client.forensics.incident_timeline)
        assert callable(client.forensics.check_trace)
        assert callable(client.forensics.policy_snapshot)
        assert callable(client.forensics.monitor_rule_evaluations)
        assert callable(client.forensics.monitor_transitions)

    def test_alert_channels(self, client: Devhelm) -> None:
        assert isinstance(client.alert_channels, AlertChannels)

    def test_notification_policies(self, client: Devhelm) -> None:
        assert isinstance(client.notification_policies, NotificationPolicies)

    def test_environments(self, client: Devhelm) -> None:
        assert isinstance(client.environments, Environments)

    def test_secrets(self, client: Devhelm) -> None:
        assert isinstance(client.secrets, Secrets)

    def test_tags(self, client: Devhelm) -> None:
        assert isinstance(client.tags, Tags)

    def test_resource_groups(self, client: Devhelm) -> None:
        assert isinstance(client.resource_groups, ResourceGroups)

    def test_webhooks(self, client: Devhelm) -> None:
        assert isinstance(client.webhooks, Webhooks)

    def test_api_keys(self, client: Devhelm) -> None:
        assert isinstance(client.api_keys, ApiKeys)

    def test_dependencies(self, client: Devhelm) -> None:
        assert isinstance(client.dependencies, Dependencies)

    def test_deploy_lock(self, client: Devhelm) -> None:
        assert isinstance(client.deploy_lock, DeployLock)

    def test_status(self, client: Devhelm) -> None:
        assert isinstance(client.status, Status)

    def test_status_pages(self, client: Devhelm) -> None:
        assert isinstance(client.status_pages, StatusPages)


class TestStatusPagesResource:
    """Verify StatusPages exposes all sub-resources and methods."""

    def test_top_level_crud(self, client: Devhelm) -> None:
        sp = client.status_pages
        assert callable(sp.list)
        assert callable(sp.get)
        assert callable(sp.create)
        assert callable(sp.update)
        assert callable(sp.delete)

    def test_components_sub_resource(self, client: Devhelm) -> None:
        c = client.status_pages.components
        assert callable(c.list)
        assert callable(c.create)
        assert callable(c.update)
        assert callable(c.delete)
        assert callable(c.reorder)

    def test_groups_sub_resource(self, client: Devhelm) -> None:
        g = client.status_pages.groups
        assert callable(g.list)
        assert callable(g.create)
        assert callable(g.update)
        assert callable(g.delete)

    def test_incidents_sub_resource(self, client: Devhelm) -> None:
        i = client.status_pages.incidents
        assert callable(i.list)
        assert callable(i.get)
        assert callable(i.create)
        assert callable(i.update)
        assert callable(i.post_update)
        assert callable(i.publish)
        assert callable(i.dismiss)
        assert callable(i.delete)

    def test_subscribers_sub_resource(self, client: Devhelm) -> None:
        s = client.status_pages.subscribers
        assert callable(s.list)
        assert callable(s.add)
        assert callable(s.remove)

    def test_domains_sub_resource(self, client: Devhelm) -> None:
        d = client.status_pages.domains
        assert callable(d.list)
        assert callable(d.add)
        assert callable(d.verify)
        assert callable(d.remove)


class TestClientOptionalTenantArgs:
    """`org_id` / `workspace_id` are optional — single-tenant tokens
    auto-resolve them server-side, so the README quickstart and the
    constructor must work with just a token (the most common case).
    """

    def test_constructible_without_org_or_workspace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Strip any env fallback so we prove the constructor itself accepts
        # missing tenant args, not that the test environment leaks them in.
        monkeypatch.delenv("DEVHELM_ORG_ID", raising=False)
        monkeypatch.delenv("DEVHELM_WORKSPACE_ID", raising=False)

        client = Devhelm(token="test-token", base_url="http://localhost:8080")

        assert client.monitors is not None
        assert client.incidents is not None

    def test_config_defaults_tenant_ids_to_none(self) -> None:
        # Documents the API contract: leaving them unset on the config
        # dataclass yields ``None``, which ``build_client`` then resolves
        # via env var or the server-side default.
        config = DevhelmConfig(token="test-token")
        assert config.org_id is None
        assert config.workspace_id is None


class TestMonitorsListFilters:
    """The documented ``GET /api/v1/monitors`` query params (``enabled``,
    ``type``, ``managedBy``, ``tags``, ``search``, ``environmentId``) must
    be reachable from ``client.monitors.list(...)`` so users don't have to
    drop down to ``httpx`` to do server-side filtering. Round-3 DevEx fix
    P1.Bug7.
    """

    @staticmethod
    def _stub_transport(captured: list[httpx.Request]) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200, json={"data": [], "hasNext": False, "hasPrev": False}
            )

        return httpx.MockTransport(handler)

    def _client_with_transport(self, transport: httpx.MockTransport) -> Monitors:
        http_client = httpx.Client(
            transport=transport, base_url="http://localhost:8080"
        )
        return Monitors(http_client)

    def test_list_threads_filters_to_query_string(self) -> None:
        captured: list[httpx.Request] = []
        monitors = self._client_with_transport(self._stub_transport(captured))

        monitors.list(
            enabled=True,
            type="HTTP",
            managed_by="API",
            tags="prod,critical",
            search="checkout",
            environment_id="11111111-2222-3333-4444-555555555555",
        )

        assert len(captured) == 1
        params = captured[0].url.params
        # snake_case kwargs must be projected onto the camelCase wire names
        # the API documents in the OpenAPI spec.
        assert params["enabled"] == "true"
        assert params["type"] == "HTTP"
        assert params["managedBy"] == "API"
        assert params["tags"] == "prod,critical"
        assert params["search"] == "checkout"
        assert params["environmentId"] == "11111111-2222-3333-4444-555555555555"

    def test_list_omits_unspecified_filters(self) -> None:
        captured: list[httpx.Request] = []
        monitors = self._client_with_transport(self._stub_transport(captured))

        monitors.list()

        assert len(captured) == 1
        params = captured[0].url.params
        # No filters → only the pagination keys reach the wire so the API's
        # default behaviour applies (no ``enabled=null`` etc.).
        assert "enabled" not in params
        assert "type" not in params
        assert "managedBy" not in params
        assert "tags" not in params
        assert "search" not in params
        assert "environmentId" not in params
        assert params["page"] == "0"

    def test_list_page_threads_filters(self) -> None:
        captured: list[httpx.Request] = []
        monitors = self._client_with_transport(self._stub_transport(captured))

        monitors.list_page(2, 50, enabled=False, search="api")

        assert len(captured) == 1
        params = captured[0].url.params
        assert params["enabled"] == "false"
        assert params["search"] == "api"
        assert params["page"] == "2"
        assert params["size"] == "50"


class TestSdkVersionExposed:
    """``devhelm.__version__`` must be reachable so users can log it,
    pin it in error reports, and so wrappers (e.g. the MCP server) can
    surface the underlying SDK version. Round-3 DevEx fix P1.Bug14.
    """

    def test_version_attribute_exists(self) -> None:
        import devhelm

        assert hasattr(devhelm, "__version__")
        assert isinstance(devhelm.__version__, str)
        assert devhelm.__version__  # non-empty

    def test_version_listed_in_all(self) -> None:
        import devhelm

        assert "__version__" in devhelm.__all__
