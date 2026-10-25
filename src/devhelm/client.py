# Generated from src/devhelm/_async/client.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""DevHelm API client."""

from __future__ import annotations

from types import TracebackType

from devhelm._http import DEFAULT_SURFACE, DevhelmConfig, build_client
from devhelm._sync.transport import Transport
from devhelm._transport import RetryPolicy
from devhelm.resources.account import Account
from devhelm.resources.alert_channels import AlertChannels
from devhelm.resources.api_keys import ApiKeys
from devhelm.resources.audit import Audit
from devhelm.resources.bundles import Bundles
from devhelm.resources.dependencies import Dependencies
from devhelm.resources.deploy_lock import DeployLock
from devhelm.resources.email import Email
from devhelm.resources.environments import Environments
from devhelm.resources.forensics import Forensics
from devhelm.resources.inboxes import Inboxes
from devhelm.resources.incidents import Incidents
from devhelm.resources.maintenance_windows import MaintenanceWindows
from devhelm.resources.monitors import Monitors
from devhelm.resources.notification_policies import NotificationPolicies
from devhelm.resources.resource_groups import ResourceGroups
from devhelm.resources.runs import Runs
from devhelm.resources.runtimes import Runtimes
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

        devhelm = Devhelm()  # token from DEVHELM_API_TOKEN

        m = devhelm.monitors.create(name="Checkout", type="BROWSER",
                                    environment="production",
                                    code="./checkout.spec.ts",
                                    frequency_seconds=600, regions=["us-east"])
        draft = devhelm.monitors.revisions.create(m.id, code="./checkout.spec.ts")
        run = devhelm.monitors.revisions.test(m.id, draft.revision.id, wait=True)

    The blocking and the asyncio client share this surface method for method.

    The token comes from ``token=``, else ``DEVHELM_API_TOKEN``, else the CLI's
    current context. ``base_url`` defaults to ``DEVHELM_API_URL`` or
    ``https://api.devhelm.io``. Rate limits (429), 503s and retryable
    conflicts are retried up to ``max_attempts`` times, honouring
    ``Retry-After``; every POST carries an ``Idempotency-Key`` so a retry
    never runs twice.
    """

    monitors: Monitors
    runs: Runs
    bundles: Bundles
    runtimes: Runtimes
    account: Account
    audit: Audit
    incidents: Incidents
    forensics: Forensics
    alert_channels: AlertChannels
    notification_policies: NotificationPolicies
    environments: Environments
    secrets: Secrets
    tags: Tags
    resource_groups: ResourceGroups
    webhooks: Webhooks
    inboxes: Inboxes
    email: Email
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
        base_url: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 30.0,
        max_attempts: int = 5,
        surface: str | None = None,
        surface_version: str | None = None,
        surface_metadata: dict[str, str] | None = None,
    ) -> None:
        # ``surface`` / ``surface_version`` / ``surface_metadata`` are for
        # wrappers (the MCP server) that report their own surface instead of
        # ``sdk-python``. End users leave them unset.
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
        self._http = build_client(config)
        client = Transport(self._http, retry=RetryPolicy(max_attempts=max_attempts))
        self._transport = client

        self.monitors = Monitors(client)
        self.runs = Runs(client)
        self.bundles = Bundles(client)
        self.runtimes = Runtimes(client)
        self.account = Account(client)
        self.audit = Audit(client)
        self.incidents = Incidents(client)
        self.forensics = Forensics(client)
        self.alert_channels = AlertChannels(client)
        self.notification_policies = NotificationPolicies(client)
        self.environments = Environments(client)
        self.secrets = Secrets(client)
        self.tags = Tags(client)
        self.resource_groups = ResourceGroups(client)
        self.webhooks = Webhooks(client)
        self.inboxes = Inboxes(client)
        self.email = Email(client)
        self.api_keys = ApiKeys(client)
        self.dependencies = Dependencies(client)
        self.deploy_lock = DeployLock(client)
        self.maintenance_windows = MaintenanceWindows(client)
        self.services = Services(client)
        self.status = Status(client)
        self.status_pages = StatusPages(client)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> Devhelm:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
