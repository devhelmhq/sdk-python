"""DevHelm API client."""

from __future__ import annotations

from devhelm._http import DevhelmConfig, build_client
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


class Devhelm:
    """DevHelm API client.

    Example::

        from devhelm import Devhelm

        client = Devhelm(token="your-api-token", org_id="1", workspace_id="1")

        monitors = client.monitors.list()
        monitor = client.monitors.create({
            "name": "My API",
            "type": "HTTP",
            "config": {"url": "https://api.example.com/health", "method": "GET"},
            "frequencySeconds": 60,
        })
    """

    monitors: Monitors
    incidents: Incidents
    alert_channels: AlertChannels
    notification_policies: NotificationPolicies
    environments: Environments
    secrets: Secrets
    tags: Tags
    resource_groups: ResourceGroups
    webhooks: Webhooks
    api_keys: ApiKeys
    dependencies: Dependencies
    deploy_lock: DeployLock
    status: Status

    def __init__(
        self,
        token: str = "",
        *,
        base_url: str = "https://api.devhelm.io",
        org_id: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        config = DevhelmConfig(
            token=token,
            base_url=base_url,
            org_id=org_id,
            workspace_id=workspace_id,
            timeout=timeout,
        )
        client = build_client(config)

        self.monitors = Monitors(client)
        self.incidents = Incidents(client)
        self.alert_channels = AlertChannels(client)
        self.notification_policies = NotificationPolicies(client)
        self.environments = Environments(client)
        self.secrets = Secrets(client)
        self.tags = Tags(client)
        self.resource_groups = ResourceGroups(client)
        self.webhooks = Webhooks(client)
        self.api_keys = ApiKeys(client)
        self.dependencies = Dependencies(client)
        self.deploy_lock = DeployLock(client)
        self.status = Status(client)
