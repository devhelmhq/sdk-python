"""Smoke tests for the Devhelm client class."""

from __future__ import annotations

import pytest

from devhelm import Devhelm
from devhelm.resources.alert_channels import AlertChannels
from devhelm.resources.api_keys import ApiKeys
from devhelm.resources.dependencies import Dependencies
from devhelm.resources.deploy_lock import DeployLock
from devhelm.resources.environments import Environments
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
