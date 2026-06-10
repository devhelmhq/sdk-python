"""DevHelm API client."""

from __future__ import annotations

from devhelm._http import DEFAULT_SURFACE, DevhelmConfig, build_client
from devhelm.resources.alert_channels import AlertChannels
from devhelm.resources.api_keys import ApiKeys
from devhelm.resources.dependencies import Dependencies
from devhelm.resources.deploy_lock import DeployLock
from devhelm.resources.environments import Environments
from devhelm.resources.forensics import Forensics
from devhelm.resources.incidents import Incidents
from devhelm.resources.maintenance_windows import MaintenanceWindows
from devhelm.resources.monitors import Monitors
from devhelm.resources.notification_policies import NotificationPolicies
from devhelm.resources.resource_groups import ResourceGroups
from devhelm.resources.secrets import Secrets
from devhelm.resources.services import Services
from devhelm.resources.status import Status
from devhelm.resources.status_pages import StatusPages
from devhelm.resources.tags import Tags
from devhelm.resources.webhooks import Webhooks


class Devhelm:
    """DevHelm API client.

    Example::

        from devhelm import Devhelm

        client = Devhelm(token="your-api-token")

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
    forensics: Forensics
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
    maintenance_windows: MaintenanceWindows
    services: Services
    status: Status
    status_pages: StatusPages

    def __init__(
        self,
        token: str = "",
        *,
        base_url: str = "https://api.devhelm.io",
        org_id: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 30.0,
        surface: str | None = None,
        surface_version: str | None = None,
        surface_metadata: dict[str, str] | None = None,
    ) -> None:
        # ``surface`` / ``surface_version`` / ``surface_metadata`` are passthroughs
        # for wrappers (e.g. the MCP server) that want their traffic attributed
        # to a different devtool surface than the default ``sdk-py``. End users
        # of the SDK should leave these unset. See
        # https://devhelm.io/telemetry for the wire contract and opt-out.
        config = DevhelmConfig(
            token=token,
            base_url=base_url,
            org_id=org_id,
            workspace_id=workspace_id,
            timeout=timeout,
            surface=surface if surface is not None else DEFAULT_SURFACE,
            surface_version=surface_version,
            surface_metadata=surface_metadata if surface_metadata is not None else {},
        )
        client = build_client(config)

        self.monitors = Monitors(client)
        self.incidents = Incidents(client)
        self.forensics = Forensics(client)
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
        self.maintenance_windows = MaintenanceWindows(client)
        self.services = Services(client)
        self.status = Status(client)
        self.status_pages = StatusPages(client)
