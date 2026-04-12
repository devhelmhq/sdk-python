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
