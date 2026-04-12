"""DevHelm SDK for Python — typed client for monitors, incidents, alerting, and more."""

from devhelm._errors import AuthError, DevhelmError
from devhelm._pagination import CursorPage, Page
from devhelm.client import Devhelm
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
from devhelm.types import (
    AcquireDeployLockRequest,
    AlertChannelDto,
    ApiKeyCreateResponse,
    ApiKeyDto,
    AssertionTestResultDto,
    CheckResultDto,
    CreateAlertChannelRequest,
    CreateApiKeyRequest,
    CreateEnvironmentRequest,
    CreateManualIncidentRequest,
    CreateMonitorRequest,
    CreateNotificationPolicyRequest,
    CreateResourceGroupRequest,
    CreateSecretRequest,
    CreateTagRequest,
    CreateWebhookEndpointRequest,
    DashboardOverviewDto,
    DeployLockDto,
    EnvironmentDto,
    IncidentDetailDto,
    IncidentDto,
    MonitorDto,
    MonitorVersionDto,
    NotificationPolicyDto,
    ResourceGroupDto,
    ResourceGroupMemberDto,
    SecretDto,
    ServiceSubscriptionDto,
    TagDto,
    UpdateAlertChannelRequest,
    UpdateEnvironmentRequest,
    UpdateMonitorRequest,
    UpdateNotificationPolicyRequest,
    UpdateResourceGroupRequest,
    UpdateSecretRequest,
    UpdateTagRequest,
    UpdateWebhookEndpointRequest,
    WebhookEndpointDto,
)

__all__ = [
    # Client
    "Devhelm",
    # Errors
    "DevhelmError",
    "AuthError",
    # Pagination
    "Page",
    "CursorPage",
    # Resource classes
    "Monitors",
    "Incidents",
    "AlertChannels",
    "NotificationPolicies",
    "Environments",
    "Secrets",
    "Tags",
    "ResourceGroups",
    "Webhooks",
    "ApiKeys",
    "Dependencies",
    "DeployLock",
    "Status",
    # Response DTOs
    "MonitorDto",
    "IncidentDto",
    "IncidentDetailDto",
    "AlertChannelDto",
    "NotificationPolicyDto",
    "EnvironmentDto",
    "SecretDto",
    "TagDto",
    "ResourceGroupDto",
    "ResourceGroupMemberDto",
    "WebhookEndpointDto",
    "ApiKeyDto",
    "ApiKeyCreateResponse",
    "ServiceSubscriptionDto",
    "MonitorVersionDto",
    "CheckResultDto",
    "DashboardOverviewDto",
    "DeployLockDto",
    "AssertionTestResultDto",
    # Request types
    "CreateMonitorRequest",
    "UpdateMonitorRequest",
    "CreateManualIncidentRequest",
    "CreateAlertChannelRequest",
    "UpdateAlertChannelRequest",
    "CreateNotificationPolicyRequest",
    "UpdateNotificationPolicyRequest",
    "CreateEnvironmentRequest",
    "UpdateEnvironmentRequest",
    "CreateSecretRequest",
    "UpdateSecretRequest",
    "CreateTagRequest",
    "UpdateTagRequest",
    "CreateResourceGroupRequest",
    "UpdateResourceGroupRequest",
    "CreateWebhookEndpointRequest",
    "UpdateWebhookEndpointRequest",
    "CreateApiKeyRequest",
    "AcquireDeployLockRequest",
]
