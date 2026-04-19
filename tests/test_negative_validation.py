"""Comprehensive negative Pydantic validation tests for all SDK models.

Every test deliberately supplies invalid data and asserts that
``pydantic.ValidationError`` is raised.  The suite covers missing required
fields, wrong field types, invalid enum values, empty strings on constrained
fields, invalid format patterns, and null for non-nullable fields.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from devhelm._generated import (
    AcquireDeployLockRequest,
    AddCustomDomainRequest,
    AddIncidentUpdateRequest,
    AdminAddSubscriberRequest,
    AlertChannelDto,
    ApiKeyDto,
    CheckResultDto,
    ComponentPosition,
    ConfirmationPolicy,
    CreateAlertChannelRequest,
    CreateApiKeyRequest,
    CreateEnvironmentRequest,
    CreateManualIncidentRequest,
    CreateMonitorRequest,
    CreateNotificationPolicyRequest,
    CreateResourceGroupRequest,
    CreateSecretRequest,
    CreateStatusPageComponentGroupRequest,
    CreateStatusPageComponentRequest,
    CreateStatusPageIncidentRequest,
    CreateStatusPageIncidentUpdateRequest,
    CreateStatusPageRequest,
    CreateTagRequest,
    CreateWebhookEndpointRequest,
    DashboardOverviewDto,
    DeployLockDto,
    EnvironmentDto,
    EscalationStep,
    IncidentDetailDto,
    IncidentDto,
    IncidentPolicyDto,
    MatchRule,
    MonitorDto,
    MonitorVersionDto,
    NotificationPolicyDto,
    RecoveryPolicy,
    ReorderComponentsRequest,
    ResolveIncidentRequest,
    ResourceGroupDto,
    RetryStrategy,
    SecretDto,
    StatusPageBranding,
    StatusPageComponentDto,
    StatusPageComponentGroupDto,
    StatusPageCustomDomainDto,
    StatusPageDto,
    StatusPageIncidentComponentDto,
    StatusPageIncidentDto,
    StatusPageIncidentUpdateDto,
    StatusPageSubscriberDto,
    TagDto,
    TestChannelResult,
    TriggerRule,
    UpdateAlertChannelRequest,
    UpdateEnvironmentRequest,
    UpdateMonitorRequest,
    UpdateNotificationPolicyRequest,
    UpdateResourceGroupRequest,
    UpdateSecretRequest,
    UpdateStatusPageComponentGroupRequest,
    UpdateStatusPageComponentRequest,
    UpdateStatusPageIncidentRequest,
    UpdateStatusPageRequest,
    UpdateTagRequest,
    UpdateWebhookEndpointRequest,
    WebhookEndpointDto,
    WebhookTestResult,
)

UID = str(uuid4())
NOW = "2026-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Helpers – minimal valid fixture factories
# ---------------------------------------------------------------------------


def _monitor(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "name": "M",
        "type": "HTTP",
        "config": {"url": "https://a.com", "method": "GET"},
        "frequencySeconds": 60,
        "enabled": True,
        "regions": ["us-east"],
        "managedBy": "DASHBOARD",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _incident(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "source": "MANUAL",
        "status": "TRIGGERED",
        "severity": "DOWN",
        "affectedRegions": [],
        "reopenCount": 0,
        "statusPageVisible": False,
        "startedAt": NOW,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _alert_channel(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "name": "ch",
        "channelType": "slack",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _api_key(**kw: object) -> dict:
    base: dict = {
        "id": 1,
        "name": "k",
        "key": "dh_live_x",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _environment(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "orgId": 1,
        "name": "prod",
        "slug": "prod",
        "variables": {},
        "createdAt": NOW,
        "updatedAt": NOW,
        "monitorCount": 0,
        "isDefault": False,
    }
    base.update(kw)
    return base


def _secret(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "key": "MY_KEY",
        "dekVersion": 1,
        "valueHash": "abc123",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _tag(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "name": "prod",
        "color": "#000000",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _webhook(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "url": "https://hook.example.com",
        "subscribedEvents": ["monitor.created"],
        "enabled": True,
        "consecutiveFailures": 0,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _deploy_lock(**kw: object) -> dict:
    base: dict = {"id": UID, "lockedBy": "ci-job-42", "lockedAt": NOW, "expiresAt": NOW}
    base.update(kw)
    return base


def _resource_group(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "name": "rg",
        "slug": "rg",
        "suppressMemberAlerts": False,
        "health": {
            "status": "operational",
            "totalMembers": 0,
            "operationalCount": 0,
            "activeIncidents": 0,
        },
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _notification_policy(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "name": "np",
        "matchRules": [],
        "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
        "enabled": True,
        "priority": 0,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _status_page(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "organizationId": 1,
        "workspaceId": 1,
        "name": "SP",
        "slug": "sp",
        "branding": {},
        "visibility": "PUBLIC",
        "enabled": True,
        "incidentMode": "MANUAL",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _sp_component(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "statusPageId": UID,
        "name": "API",
        "type": "STATIC",
        "currentStatus": "OPERATIONAL",
        "showUptime": True,
        "displayOrder": 0,
        "pageOrder": 0,
        "excludeFromOverall": False,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _sp_group(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "statusPageId": UID,
        "name": "Infra",
        "displayOrder": 0,
        "pageOrder": 0,
        "collapsed": True,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _sp_incident(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "statusPageId": UID,
        "title": "Down",
        "status": "INVESTIGATING",
        "impact": "MINOR",
        "scheduled": False,
        "autoResolve": False,
        "startedAt": NOW,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _sp_incident_update(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "status": "INVESTIGATING",
        "body": "Looking into it",
        "notifySubscribers": True,
        "createdAt": NOW,
    }
    base.update(kw)
    return base


def _sp_subscriber(**kw: object) -> dict:
    base: dict = {"id": UID, "email": "a@b.com", "confirmed": True, "createdAt": NOW}
    base.update(kw)
    return base


def _sp_custom_domain(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "hostname": "status.example.com",
        "status": "ACTIVE",
        "verificationMethod": "CNAME",
        "verificationToken": "tok123",
        "verificationCnameTarget": "verify.example.com",
        "createdAt": NOW,
        "updatedAt": NOW,
        "primary": True,
    }
    base.update(kw)
    return base


def _sp_incident_component(**kw: object) -> dict:
    base: dict = {
        "statusPageComponentId": UID,
        "componentStatus": "OPERATIONAL",
        "componentName": "API",
    }
    base.update(kw)
    return base


def _check_result(**kw: object) -> dict:
    base: dict = {"id": UID, "timestamp": NOW, "region": "us-east", "passed": True}
    base.update(kw)
    return base


def _incident_policy(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "monitorId": UID,
        "triggerRules": [
            {"type": "consecutive_failures", "scope": "per_region", "severity": "down"}
        ],
        "confirmation": {
            "type": "ALL_REGIONS",
            "minRegionsFailing": 1,
            "maxWaitSeconds": 30,
        },
        "recovery": {
            "consecutiveSuccesses": 1,
            "minRegionsPassing": 1,
            "cooldownMinutes": 5,
        },
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(kw)
    return base


def _monitor_version(**kw: object) -> dict:
    base: dict = {
        "id": UID,
        "monitorId": UID,
        "version": 1,
        "snapshot": _monitor(),
        "changedVia": "DASHBOARD",
        "createdAt": NOW,
    }
    base.update(kw)
    return base


def _del(d: dict, key: str) -> dict:
    c = dict(d)
    del c[key]
    return c


# ===================================================================
# MonitorDto
# ===================================================================


class TestMonitorDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            MonitorDto.model_validate(_del(_monitor(), "id"))

    def test_wrong_id_type_int(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(id=12345))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            MonitorDto.model_validate(_del(_monitor(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(name=""))

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(name=[1, 2]))

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            MonitorDto.model_validate(_del(_monitor(), "type"))

    def test_invalid_type_enum(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(type="BANANA"))

    def test_wrong_frequency_type(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(frequencySeconds="not-int"))

    def test_missing_frequency(self) -> None:
        with pytest.raises(ValidationError, match="frequencySeconds"):
            MonitorDto.model_validate(_del(_monitor(), "frequencySeconds"))

    def test_missing_enabled(self) -> None:
        with pytest.raises(ValidationError, match="enabled"):
            MonitorDto.model_validate(_del(_monitor(), "enabled"))

    def test_wrong_enabled_type(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(enabled=[1, 2]))

    def test_missing_regions(self) -> None:
        with pytest.raises(ValidationError, match="regions"):
            MonitorDto.model_validate(_del(_monitor(), "regions"))

    def test_missing_managed_by(self) -> None:
        with pytest.raises(ValidationError, match="managedBy"):
            MonitorDto.model_validate(_del(_monitor(), "managedBy"))

    def test_invalid_managed_by(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(managedBy="MAGIC"))

    def test_missing_created_at(self) -> None:
        with pytest.raises(ValidationError, match="createdAt"):
            MonitorDto.model_validate(_del(_monitor(), "createdAt"))

    def test_missing_config(self) -> None:
        with pytest.raises(ValidationError, match="config"):
            MonitorDto.model_validate(_del(_monitor(), "config"))

    def test_wrong_config_type(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(config="not-a-dict"))

    def test_non_dict_input(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate("string-not-dict")

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate({})

    def test_null_id(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor(id=None))


# ===================================================================
# CreateMonitorRequest
# ===================================================================


class TestCreateMonitorRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateMonitorRequest.model_validate(
                {
                    "type": "HTTP",
                    "config": {"url": "https://x.com", "method": "GET"},
                    "managedBy": "DASHBOARD",
                }
            )

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            CreateMonitorRequest.model_validate(
                {
                    "name": "X",
                    "config": {"url": "https://x.com", "method": "GET"},
                    "managedBy": "DASHBOARD",
                }
            )

    def test_missing_config(self) -> None:
        with pytest.raises(ValidationError, match="config"):
            CreateMonitorRequest.model_validate(
                {"name": "X", "type": "HTTP", "managedBy": "DASHBOARD"}
            )

    def test_missing_managed_by(self) -> None:
        with pytest.raises(ValidationError, match="managedBy"):
            CreateMonitorRequest.model_validate(
                {
                    "name": "X",
                    "type": "HTTP",
                    "config": {"url": "https://x.com", "method": "GET"},
                }
            )

    def test_invalid_type_enum(self) -> None:
        with pytest.raises(ValidationError):
            CreateMonitorRequest.model_validate(
                {
                    "name": "X",
                    "type": "FTP",
                    "config": {"url": "https://x.com", "method": "GET"},
                    "managedBy": "DASHBOARD",
                }
            )

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateMonitorRequest.model_validate(
                {
                    "name": [1, 2],
                    "type": "HTTP",
                    "config": {"url": "https://x.com", "method": "GET"},
                    "managedBy": "DASHBOARD",
                }
            )

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateMonitorRequest.model_validate(
                {
                    "name": None,
                    "type": "HTTP",
                    "config": {"url": "https://x.com", "method": "GET"},
                    "managedBy": "DASHBOARD",
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateMonitorRequest.model_validate({})


# ===================================================================
# UpdateMonitorRequest
# ===================================================================


class TestUpdateMonitorRequestNegative:
    def test_wrong_type_for_frequency(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"frequencySeconds": "slow"})

    def test_wrong_type_for_enabled(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"enabled": [1, 2]})

    def test_invalid_managed_by(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"managedBy": "GITHUB"})

    def test_invalid_environment_id_format(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"environmentId": "not-a-uuid"})

    def test_wrong_type_for_regions(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"regions": "us-east"})

    def test_alert_channel_ids_wrong_element(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"alertChannelIds": ["not-uuid"]})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMonitorRequest.model_validate({"name": "x" * 256})


# ===================================================================
# IncidentDto
# ===================================================================


class TestIncidentDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            IncidentDto.model_validate(_del(_incident(), "id"))

    def test_wrong_id_type(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(id=42))

    def test_missing_source(self) -> None:
        with pytest.raises(ValidationError, match="source"):
            IncidentDto.model_validate(_del(_incident(), "source"))

    def test_invalid_source_enum(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(source="ALIEN"))

    def test_missing_status(self) -> None:
        with pytest.raises(ValidationError, match="status"):
            IncidentDto.model_validate(_del(_incident(), "status"))

    def test_invalid_status_enum(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(status="OPEN"))

    def test_missing_severity(self) -> None:
        with pytest.raises(ValidationError, match="severity"):
            IncidentDto.model_validate(_del(_incident(), "severity"))

    def test_invalid_severity_enum(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(severity="SEV1"))

    def test_wrong_reopen_count_type(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(reopenCount="many"))

    def test_missing_affected_regions(self) -> None:
        with pytest.raises(ValidationError, match="affectedRegions"):
            IncidentDto.model_validate(_del(_incident(), "affectedRegions"))

    def test_missing_status_page_visible(self) -> None:
        with pytest.raises(ValidationError, match="statusPageVisible"):
            IncidentDto.model_validate(_del(_incident(), "statusPageVisible"))

    def test_null_id(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate(_incident(id=None))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate({})


# ===================================================================
# CreateManualIncidentRequest
# ===================================================================


class TestCreateManualIncidentRequestNegative:
    def test_missing_title(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CreateManualIncidentRequest.model_validate({"severity": "DOWN"})

    def test_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": "", "severity": "DOWN"}
            )

    def test_missing_severity(self) -> None:
        with pytest.raises(ValidationError, match="severity"):
            CreateManualIncidentRequest.model_validate({"title": "X"})

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": "X", "severity": "SEV1"}
            )

    def test_wrong_title_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": [1], "severity": "DOWN"}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate({})

    def test_null_title(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": None, "severity": "DOWN"}
            )

    def test_invalid_monitor_id(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": "X", "severity": "DOWN", "monitorId": "bad-uuid"}
            )


# ===================================================================
# AlertChannelDto
# ===================================================================


class TestAlertChannelDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            AlertChannelDto.model_validate(_del(_alert_channel(), "id"))

    def test_wrong_id_type(self) -> None:
        with pytest.raises(ValidationError):
            AlertChannelDto.model_validate(_alert_channel(id=42))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            AlertChannelDto.model_validate(_del(_alert_channel(), "name"))

    def test_missing_channel_type(self) -> None:
        with pytest.raises(ValidationError, match="channelType"):
            AlertChannelDto.model_validate(_del(_alert_channel(), "channelType"))

    def test_invalid_channel_type(self) -> None:
        with pytest.raises(ValidationError):
            AlertChannelDto.model_validate(_alert_channel(channelType="telegram"))

    def test_missing_created_at(self) -> None:
        with pytest.raises(ValidationError, match="createdAt"):
            AlertChannelDto.model_validate(_del(_alert_channel(), "createdAt"))

    def test_null_id(self) -> None:
        with pytest.raises(ValidationError):
            AlertChannelDto.model_validate(_alert_channel(id=None))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            AlertChannelDto.model_validate({})


# ===================================================================
# CreateAlertChannelRequest
# ===================================================================


class TestCreateAlertChannelRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateAlertChannelRequest.model_validate(
                {"config": {"webhookUrl": "https://x.com"}}
            )

    def test_missing_config(self) -> None:
        with pytest.raises(ValidationError, match="config"):
            CreateAlertChannelRequest.model_validate({"name": "ch"})

    def test_wrong_config_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateAlertChannelRequest.model_validate(
                {"name": "ch", "config": "not-a-dict"}
            )

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateAlertChannelRequest.model_validate(
                {"name": None, "config": {"webhookUrl": "https://x.com"}}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateAlertChannelRequest.model_validate({})

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateAlertChannelRequest.model_validate(
                {"name": [1, 2], "config": {"webhookUrl": "https://x.com"}}
            )


# ===================================================================
# UpdateAlertChannelRequest  (only name + config are updatable)
# ===================================================================


class TestUpdateAlertChannelRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            UpdateAlertChannelRequest.model_validate(
                {"config": {"webhookUrl": "https://x.com"}}
            )

    def test_missing_config(self) -> None:
        with pytest.raises(ValidationError, match="config"):
            UpdateAlertChannelRequest.model_validate({"name": "ch"})

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateAlertChannelRequest.model_validate(
                {"name": [1, 2], "config": {"webhookUrl": "https://x.com"}}
            )

    def test_wrong_config_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateAlertChannelRequest.model_validate({"name": "ch", "config": "bad"})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            UpdateAlertChannelRequest.model_validate({})


# ===================================================================
# NotificationPolicyDto
# ===================================================================


class TestNotificationPolicyDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            NotificationPolicyDto.model_validate(_del(_notification_policy(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            NotificationPolicyDto.model_validate(_del(_notification_policy(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            NotificationPolicyDto.model_validate(_notification_policy(name=""))

    def test_missing_match_rules(self) -> None:
        with pytest.raises(ValidationError, match="matchRules"):
            NotificationPolicyDto.model_validate(
                _del(_notification_policy(), "matchRules")
            )

    def test_wrong_match_rules_type(self) -> None:
        with pytest.raises(ValidationError):
            NotificationPolicyDto.model_validate(
                _notification_policy(matchRules="not-a-list")
            )

    def test_missing_escalation(self) -> None:
        with pytest.raises(ValidationError, match="escalation"):
            NotificationPolicyDto.model_validate(
                _del(_notification_policy(), "escalation")
            )

    def test_missing_enabled(self) -> None:
        with pytest.raises(ValidationError, match="enabled"):
            NotificationPolicyDto.model_validate(
                _del(_notification_policy(), "enabled")
            )

    def test_missing_priority(self) -> None:
        with pytest.raises(ValidationError, match="priority"):
            NotificationPolicyDto.model_validate(
                _del(_notification_policy(), "priority")
            )

    def test_wrong_priority_type(self) -> None:
        with pytest.raises(ValidationError):
            NotificationPolicyDto.model_validate(_notification_policy(priority="high"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            NotificationPolicyDto.model_validate({})


# ===================================================================
# CreateNotificationPolicyRequest
# ===================================================================


class TestCreateNotificationPolicyRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "matchRules": [],
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "enabled": True,
                    "priority": 0,
                }
            )

    def test_missing_match_rules(self) -> None:
        with pytest.raises(ValidationError, match="matchRules"):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "name": "np",
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "enabled": True,
                    "priority": 0,
                }
            )

    def test_missing_escalation(self) -> None:
        with pytest.raises(ValidationError, match="escalation"):
            CreateNotificationPolicyRequest.model_validate(
                {"name": "np", "matchRules": [], "enabled": True, "priority": 0}
            )

    def test_missing_enabled(self) -> None:
        with pytest.raises(ValidationError, match="enabled"):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "name": "np",
                    "matchRules": [],
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "priority": 0,
                }
            )

    def test_missing_priority(self) -> None:
        with pytest.raises(ValidationError, match="priority"):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "name": "np",
                    "matchRules": [],
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "enabled": True,
                }
            )

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "name": None,
                    "matchRules": [],
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "enabled": True,
                    "priority": 0,
                }
            )

    def test_wrong_match_rules_element(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationPolicyRequest.model_validate(
                {
                    "name": "np",
                    "matchRules": ["bad"],
                    "escalation": {"steps": [{"delayMinutes": 0, "channelIds": [UID]}]},
                    "enabled": True,
                    "priority": 0,
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationPolicyRequest.model_validate({})


# ===================================================================
# UpdateNotificationPolicyRequest
# ===================================================================


class TestUpdateNotificationPolicyRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationPolicyRequest.model_validate({"name": "x" * 256})

    def test_wrong_match_rules_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationPolicyRequest.model_validate({"matchRules": "bad"})

    def test_wrong_enabled_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationPolicyRequest.model_validate({"enabled": [1, 2]})


# ===================================================================
# EnvironmentDto
# ===================================================================


class TestEnvironmentDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            EnvironmentDto.model_validate(_del(_environment(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            EnvironmentDto.model_validate(_del(_environment(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            EnvironmentDto.model_validate(_environment(name=""))

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            EnvironmentDto.model_validate(_del(_environment(), "slug"))

    def test_missing_variables(self) -> None:
        with pytest.raises(ValidationError, match="variables"):
            EnvironmentDto.model_validate(_del(_environment(), "variables"))

    def test_wrong_variables_type(self) -> None:
        with pytest.raises(ValidationError):
            EnvironmentDto.model_validate(_environment(variables="not-a-dict"))

    def test_missing_monitor_count(self) -> None:
        with pytest.raises(ValidationError, match="monitorCount"):
            EnvironmentDto.model_validate(_del(_environment(), "monitorCount"))

    def test_missing_is_default(self) -> None:
        with pytest.raises(ValidationError, match="isDefault"):
            EnvironmentDto.model_validate(_del(_environment(), "isDefault"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            EnvironmentDto.model_validate({})


# ===================================================================
# CreateEnvironmentRequest
# ===================================================================


class TestCreateEnvironmentRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateEnvironmentRequest.model_validate({"slug": "prod"})

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            CreateEnvironmentRequest.model_validate({"name": "Prod"})

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": [1], "slug": "prod"})

    def test_slug_invalid_pattern(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": "P", "slug": "BAD SLUG!"})

    def test_slug_starts_with_hyphen(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": "P", "slug": "-bad"})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": "x" * 101, "slug": "p"})

    def test_slug_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": "P", "slug": "x" * 101})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({})

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateEnvironmentRequest.model_validate({"name": None, "slug": "prod"})


# ===================================================================
# UpdateEnvironmentRequest
# ===================================================================


class TestUpdateEnvironmentRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateEnvironmentRequest.model_validate({"name": "x" * 101})

    def test_wrong_variables_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateEnvironmentRequest.model_validate({"variables": "not-dict"})


# ===================================================================
# SecretDto
# ===================================================================


class TestSecretDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            SecretDto.model_validate(_del(_secret(), "id"))

    def test_missing_key(self) -> None:
        with pytest.raises(ValidationError, match="key"):
            SecretDto.model_validate(_del(_secret(), "key"))

    def test_missing_dek_version(self) -> None:
        with pytest.raises(ValidationError, match="dekVersion"):
            SecretDto.model_validate(_del(_secret(), "dekVersion"))

    def test_wrong_dek_version_type(self) -> None:
        with pytest.raises(ValidationError):
            SecretDto.model_validate(_secret(dekVersion="one"))

    def test_missing_value_hash(self) -> None:
        with pytest.raises(ValidationError, match="valueHash"):
            SecretDto.model_validate(_del(_secret(), "valueHash"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            SecretDto.model_validate({})

    def test_null_id(self) -> None:
        with pytest.raises(ValidationError):
            SecretDto.model_validate(_secret(id=None))


# ===================================================================
# CreateSecretRequest
# ===================================================================


class TestCreateSecretRequestNegative:
    def test_missing_key(self) -> None:
        with pytest.raises(ValidationError, match="key"):
            CreateSecretRequest.model_validate({"value": "s3cret"})

    def test_missing_value(self) -> None:
        with pytest.raises(ValidationError, match="value"):
            CreateSecretRequest.model_validate({"key": "K"})

    def test_key_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({"key": "k" * 256, "value": "v"})

    def test_value_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({"key": "K", "value": "v" * 32769})

    def test_null_key(self) -> None:
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({"key": None, "value": "v"})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({})


# ===================================================================
# UpdateSecretRequest
# ===================================================================


class TestUpdateSecretRequestNegative:
    def test_missing_value(self) -> None:
        with pytest.raises(ValidationError, match="value"):
            UpdateSecretRequest.model_validate({})

    def test_value_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateSecretRequest.model_validate({"value": "v" * 32769})

    def test_null_value(self) -> None:
        with pytest.raises(ValidationError):
            UpdateSecretRequest.model_validate({"value": None})


# ===================================================================
# TagDto
# ===================================================================


class TestTagDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            TagDto.model_validate(_del(_tag(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            TagDto.model_validate(_del(_tag(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            TagDto.model_validate(_tag(name=""))

    def test_missing_color(self) -> None:
        with pytest.raises(ValidationError, match="color"):
            TagDto.model_validate(_del(_tag(), "color"))

    def test_empty_color(self) -> None:
        with pytest.raises(ValidationError):
            TagDto.model_validate(_tag(color=""))

    def test_missing_organization_id(self) -> None:
        with pytest.raises(ValidationError, match="organizationId"):
            TagDto.model_validate(_del(_tag(), "organizationId"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            TagDto.model_validate({})


# ===================================================================
# CreateTagRequest
# ===================================================================


class TestCreateTagRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateTagRequest.model_validate({})

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateTagRequest.model_validate({"name": None})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateTagRequest.model_validate({"name": "t" * 101})

    def test_invalid_color_format(self) -> None:
        with pytest.raises(ValidationError):
            CreateTagRequest.model_validate({"name": "t", "color": "red"})

    def test_invalid_color_no_hash(self) -> None:
        with pytest.raises(ValidationError):
            CreateTagRequest.model_validate({"name": "t", "color": "AABBCC"})

    def test_wrong_name_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateTagRequest.model_validate({"name": [1]})


# ===================================================================
# UpdateTagRequest
# ===================================================================


class TestUpdateTagRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTagRequest.model_validate({"name": "n" * 101})

    def test_invalid_color_format(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTagRequest.model_validate({"color": "not-hex"})

    def test_color_missing_hash(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTagRequest.model_validate({"color": "FF00FF"})


# ===================================================================
# ResourceGroupDto
# ===================================================================


class TestResourceGroupDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            ResourceGroupDto.model_validate(_del(_resource_group(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            ResourceGroupDto.model_validate(_del(_resource_group(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            ResourceGroupDto.model_validate(_resource_group(name=""))

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            ResourceGroupDto.model_validate(_del(_resource_group(), "slug"))

    def test_missing_health(self) -> None:
        with pytest.raises(ValidationError, match="health"):
            ResourceGroupDto.model_validate(_del(_resource_group(), "health"))

    def test_missing_suppress_member_alerts(self) -> None:
        with pytest.raises(ValidationError, match="suppressMemberAlerts"):
            ResourceGroupDto.model_validate(
                _del(_resource_group(), "suppressMemberAlerts")
            )

    def test_wrong_health_type(self) -> None:
        with pytest.raises(ValidationError):
            ResourceGroupDto.model_validate(_resource_group(health="not-dict"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            ResourceGroupDto.model_validate({})


# ===================================================================
# CreateResourceGroupRequest
# ===================================================================


class TestCreateResourceGroupRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateResourceGroupRequest.model_validate({})

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate({"name": None})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate({"name": "x" * 256})

    def test_default_frequency_below_minimum(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "defaultFrequency": 10}
            )

    def test_default_frequency_above_maximum(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "defaultFrequency": 100000}
            )

    def test_health_threshold_value_above_100(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "healthThresholdValue": 150}
            )

    def test_health_threshold_value_below_zero(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "healthThresholdValue": -5}
            )

    def test_confirmation_delay_above_max(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "confirmationDelaySeconds": 700}
            )

    def test_invalid_health_threshold_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "healthThresholdType": "ABSOLUTE"}
            )

    def test_invalid_alert_channel_uuid(self) -> None:
        with pytest.raises(ValidationError):
            CreateResourceGroupRequest.model_validate(
                {"name": "rg", "defaultAlertChannels": ["not-a-uuid"]}
            )


# ===================================================================
# UpdateResourceGroupRequest
# ===================================================================


class TestUpdateResourceGroupRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            UpdateResourceGroupRequest.model_validate({})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateResourceGroupRequest.model_validate({"name": "x" * 256})

    def test_default_frequency_below_min(self) -> None:
        with pytest.raises(ValidationError):
            UpdateResourceGroupRequest.model_validate(
                {"name": "rg", "defaultFrequency": 5}
            )


# ===================================================================
# WebhookEndpointDto
# ===================================================================


class TestWebhookEndpointDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            WebhookEndpointDto.model_validate(_del(_webhook(), "id"))

    def test_missing_url(self) -> None:
        with pytest.raises(ValidationError, match="url"):
            WebhookEndpointDto.model_validate(_del(_webhook(), "url"))

    def test_missing_subscribed_events(self) -> None:
        with pytest.raises(ValidationError, match="subscribedEvents"):
            WebhookEndpointDto.model_validate(_del(_webhook(), "subscribedEvents"))

    def test_missing_enabled(self) -> None:
        with pytest.raises(ValidationError, match="enabled"):
            WebhookEndpointDto.model_validate(_del(_webhook(), "enabled"))

    def test_missing_consecutive_failures(self) -> None:
        with pytest.raises(ValidationError, match="consecutiveFailures"):
            WebhookEndpointDto.model_validate(_del(_webhook(), "consecutiveFailures"))

    def test_wrong_consecutive_failures_type(self) -> None:
        with pytest.raises(ValidationError):
            WebhookEndpointDto.model_validate(_webhook(consecutiveFailures="many"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            WebhookEndpointDto.model_validate({})


# ===================================================================
# CreateWebhookEndpointRequest
# ===================================================================


class TestCreateWebhookEndpointRequestNegative:
    def test_missing_url(self) -> None:
        with pytest.raises(ValidationError, match="url"):
            CreateWebhookEndpointRequest.model_validate(
                {"subscribedEvents": ["monitor.created"]}
            )

    def test_missing_subscribed_events(self) -> None:
        with pytest.raises(ValidationError, match="subscribedEvents"):
            CreateWebhookEndpointRequest.model_validate(
                {"url": "https://hook.example.com"}
            )

    def test_empty_subscribed_events(self) -> None:
        with pytest.raises(ValidationError):
            CreateWebhookEndpointRequest.model_validate(
                {"url": "https://hook.example.com", "subscribedEvents": []}
            )

    def test_url_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateWebhookEndpointRequest.model_validate(
                {
                    "url": "https://" + "x" * 2050,
                    "subscribedEvents": ["monitor.created"],
                }
            )

    def test_null_url(self) -> None:
        with pytest.raises(ValidationError):
            CreateWebhookEndpointRequest.model_validate(
                {"url": None, "subscribedEvents": ["monitor.created"]}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateWebhookEndpointRequest.model_validate({})


# ===================================================================
# UpdateWebhookEndpointRequest
# ===================================================================


class TestUpdateWebhookEndpointRequestNegative:
    def test_url_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateWebhookEndpointRequest.model_validate({"url": "x" * 2049})

    def test_wrong_enabled_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateWebhookEndpointRequest.model_validate({"enabled": [1]})


# ===================================================================
# ApiKeyDto
# ===================================================================


class TestApiKeyDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            ApiKeyDto.model_validate(_del(_api_key(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            ApiKeyDto.model_validate(_del(_api_key(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            ApiKeyDto.model_validate(_api_key(name=""))

    def test_missing_key(self) -> None:
        with pytest.raises(ValidationError, match="key"):
            ApiKeyDto.model_validate(_del(_api_key(), "key"))

    def test_empty_key(self) -> None:
        with pytest.raises(ValidationError):
            ApiKeyDto.model_validate(_api_key(key=""))

    def test_wrong_id_type(self) -> None:
        with pytest.raises(ValidationError):
            ApiKeyDto.model_validate(_api_key(id="not-an-int"))

    def test_missing_created_at(self) -> None:
        with pytest.raises(ValidationError, match="createdAt"):
            ApiKeyDto.model_validate(_del(_api_key(), "createdAt"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            ApiKeyDto.model_validate({})


# ===================================================================
# CreateApiKeyRequest
# ===================================================================


class TestCreateApiKeyRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateApiKeyRequest.model_validate({})

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateApiKeyRequest.model_validate({"name": None})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateApiKeyRequest.model_validate({"name": "k" * 201})

    def test_invalid_expires_at(self) -> None:
        with pytest.raises(ValidationError):
            CreateApiKeyRequest.model_validate({"name": "k", "expiresAt": "not-a-date"})


# ===================================================================
# DeployLockDto
# ===================================================================


class TestDeployLockDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            DeployLockDto.model_validate(_del(_deploy_lock(), "id"))

    def test_missing_locked_by(self) -> None:
        with pytest.raises(ValidationError, match="lockedBy"):
            DeployLockDto.model_validate(_del(_deploy_lock(), "lockedBy"))

    def test_empty_locked_by(self) -> None:
        with pytest.raises(ValidationError):
            DeployLockDto.model_validate(_deploy_lock(lockedBy=""))

    def test_missing_locked_at(self) -> None:
        with pytest.raises(ValidationError, match="lockedAt"):
            DeployLockDto.model_validate(_del(_deploy_lock(), "lockedAt"))

    def test_missing_expires_at(self) -> None:
        with pytest.raises(ValidationError, match="expiresAt"):
            DeployLockDto.model_validate(_del(_deploy_lock(), "expiresAt"))

    def test_wrong_locked_at_type(self) -> None:
        with pytest.raises(ValidationError):
            DeployLockDto.model_validate(_deploy_lock(lockedAt="not-a-date"))

    def test_null_id(self) -> None:
        with pytest.raises(ValidationError):
            DeployLockDto.model_validate(_deploy_lock(id=None))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            DeployLockDto.model_validate({})


# ===================================================================
# AcquireDeployLockRequest
# ===================================================================


class TestAcquireDeployLockRequestNegative:
    def test_missing_locked_by(self) -> None:
        with pytest.raises(ValidationError, match="lockedBy"):
            AcquireDeployLockRequest.model_validate({})

    def test_empty_locked_by(self) -> None:
        with pytest.raises(ValidationError):
            AcquireDeployLockRequest.model_validate({"lockedBy": ""})

    def test_null_locked_by(self) -> None:
        with pytest.raises(ValidationError):
            AcquireDeployLockRequest.model_validate({"lockedBy": None})

    def test_wrong_ttl_type(self) -> None:
        with pytest.raises(ValidationError):
            AcquireDeployLockRequest.model_validate(
                {"lockedBy": "ci", "ttlMinutes": "thirty"}
            )


# ===================================================================
# StatusPageDto
# ===================================================================


class TestStatusPageDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageDto.model_validate(_del(_status_page(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            StatusPageDto.model_validate(_del(_status_page(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate(_status_page(name=""))

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            StatusPageDto.model_validate(_del(_status_page(), "slug"))

    def test_empty_slug(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate(_status_page(slug=""))

    def test_invalid_visibility(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate(_status_page(visibility="PRIVATE"))

    def test_invalid_incident_mode(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate(_status_page(incidentMode="AUTO_PILOT"))

    def test_missing_branding(self) -> None:
        with pytest.raises(ValidationError, match="branding"):
            StatusPageDto.model_validate(_del(_status_page(), "branding"))

    def test_missing_enabled(self) -> None:
        with pytest.raises(ValidationError, match="enabled"):
            StatusPageDto.model_validate(_del(_status_page(), "enabled"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate({})


# ===================================================================
# CreateStatusPageRequest
# ===================================================================


class TestCreateStatusPageRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateStatusPageRequest.model_validate({"slug": "sp"})

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            CreateStatusPageRequest.model_validate({"name": "SP"})

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "", "slug": "sp"})

    def test_slug_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "SP", "slug": "s" * 256})

    def test_slug_uppercase(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "SP", "slug": "UPPER"})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({})


# ===================================================================
# UpdateStatusPageRequest
# ===================================================================


class TestUpdateStatusPageRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageRequest.model_validate({"name": "x" * 256})

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageRequest.model_validate({"description": "x" * 501})

    def test_invalid_visibility(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageRequest.model_validate({"visibility": "INVITE_ONLY"})

    def test_invalid_incident_mode(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageRequest.model_validate({"incidentMode": "FULL_AUTO"})

    def test_wrong_enabled_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageRequest.model_validate({"enabled": [1]})


# ===================================================================
# StatusPageBranding
# ===================================================================


class TestStatusPageBrandingNegative:
    def test_invalid_brand_color(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"brandColor": "red"})

    def test_brand_color_no_hash(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"brandColor": "4F46E5"})

    def test_invalid_page_background(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"pageBackground": "blue"})

    def test_invalid_card_background(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"cardBackground": "xyz"})

    def test_invalid_text_color(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"textColor": "rgb(0,0,0)"})

    def test_invalid_border_color(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"borderColor": "hsl(0,0,0)"})

    def test_invalid_logo_url_protocol(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"logoUrl": "ftp://bad.com/logo.png"})

    def test_invalid_favicon_url_protocol(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"faviconUrl": "ftp://bad.com/fav.ico"})

    def test_logo_url_too_long(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"logoUrl": "https://" + "x" * 2050})

    def test_wrong_hide_powered_by_type(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageBranding.model_validate({"hidePoweredBy": [1]})


# ===================================================================
# StatusPageComponentDto
# ===================================================================


class TestStatusPageComponentDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageComponentDto.model_validate(_del(_sp_component(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            StatusPageComponentDto.model_validate(_del(_sp_component(), "name"))

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageComponentDto.model_validate(_sp_component(name=""))

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            StatusPageComponentDto.model_validate(_del(_sp_component(), "type"))

    def test_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageComponentDto.model_validate(_sp_component(type="CUSTOM"))

    def test_invalid_current_status(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageComponentDto.model_validate(_sp_component(currentStatus="BROKEN"))

    def test_missing_show_uptime(self) -> None:
        with pytest.raises(ValidationError, match="showUptime"):
            StatusPageComponentDto.model_validate(_del(_sp_component(), "showUptime"))

    def test_missing_display_order(self) -> None:
        with pytest.raises(ValidationError, match="displayOrder"):
            StatusPageComponentDto.model_validate(_del(_sp_component(), "displayOrder"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageComponentDto.model_validate({})


# ===================================================================
# CreateStatusPageComponentRequest
# ===================================================================


class TestCreateStatusPageComponentRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateStatusPageComponentRequest.model_validate({"type": "STATIC"})

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            CreateStatusPageComponentRequest.model_validate({"name": "API"})

    def test_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentRequest.model_validate(
                {"name": "API", "type": "CUSTOM"}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentRequest.model_validate({})


# ===================================================================
# UpdateStatusPageComponentRequest
# ===================================================================


class TestUpdateStatusPageComponentRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentRequest.model_validate({"name": "x" * 256})

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentRequest.model_validate({"description": "x" * 501})

    def test_wrong_show_uptime_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentRequest.model_validate({"showUptime": [1]})

    def test_wrong_display_order_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentRequest.model_validate({"displayOrder": "first"})

    def test_invalid_group_id(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentRequest.model_validate({"groupId": "bad-uuid"})


# ===================================================================
# StatusPageComponentGroupDto
# ===================================================================


class TestStatusPageComponentGroupDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageComponentGroupDto.model_validate(_del(_sp_group(), "id"))

    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            StatusPageComponentGroupDto.model_validate(_del(_sp_group(), "name"))

    def test_missing_status_page_id(self) -> None:
        with pytest.raises(ValidationError, match="statusPageId"):
            StatusPageComponentGroupDto.model_validate(
                _del(_sp_group(), "statusPageId")
            )

    def test_missing_display_order(self) -> None:
        with pytest.raises(ValidationError, match="displayOrder"):
            StatusPageComponentGroupDto.model_validate(
                _del(_sp_group(), "displayOrder")
            )

    def test_missing_collapsed(self) -> None:
        with pytest.raises(ValidationError, match="collapsed"):
            StatusPageComponentGroupDto.model_validate(_del(_sp_group(), "collapsed"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageComponentGroupDto.model_validate({})


# ===================================================================
# CreateStatusPageComponentGroupRequest
# ===================================================================


class TestCreateStatusPageComponentGroupRequestNegative:
    def test_missing_name(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateStatusPageComponentGroupRequest.model_validate({})

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentGroupRequest.model_validate({"name": "x" * 256})

    def test_null_name(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentGroupRequest.model_validate({"name": None})

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentGroupRequest.model_validate(
                {"name": "g", "description": "x" * 501}
            )


# ===================================================================
# UpdateStatusPageComponentGroupRequest
# ===================================================================


class TestUpdateStatusPageComponentGroupRequestNegative:
    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentGroupRequest.model_validate({"name": "x" * 256})

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentGroupRequest.model_validate(
                {"description": "x" * 501}
            )

    def test_wrong_collapsed_type(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageComponentGroupRequest.model_validate({"collapsed": [1]})


# ===================================================================
# StatusPageIncidentDto
# ===================================================================


class TestStatusPageIncidentDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageIncidentDto.model_validate(_del(_sp_incident(), "id"))

    def test_missing_title(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            StatusPageIncidentDto.model_validate(_del(_sp_incident(), "title"))

    def test_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentDto.model_validate(_sp_incident(title=""))

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentDto.model_validate(_sp_incident(status="PENDING"))

    def test_invalid_impact(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentDto.model_validate(_sp_incident(impact="CATASTROPHIC"))

    def test_missing_scheduled(self) -> None:
        with pytest.raises(ValidationError, match="scheduled"):
            StatusPageIncidentDto.model_validate(_del(_sp_incident(), "scheduled"))

    def test_missing_auto_resolve(self) -> None:
        with pytest.raises(ValidationError, match="autoResolve"):
            StatusPageIncidentDto.model_validate(_del(_sp_incident(), "autoResolve"))

    def test_missing_started_at(self) -> None:
        with pytest.raises(ValidationError, match="startedAt"):
            StatusPageIncidentDto.model_validate(_del(_sp_incident(), "startedAt"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentDto.model_validate({})


# ===================================================================
# CreateStatusPageIncidentRequest
# ===================================================================


class TestCreateStatusPageIncidentRequestNegative:
    def test_missing_title(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CreateStatusPageIncidentRequest.model_validate(
                {"impact": "MINOR", "body": "t"}
            )

    def test_missing_body(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "X", "impact": "MINOR"}
            )

    def test_invalid_impact(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "X", "impact": "CATASTROPHIC", "body": "t"}
            )

    def test_title_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "x" * 501, "impact": "MINOR", "body": "t"}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentRequest.model_validate({})


# ===================================================================
# UpdateStatusPageIncidentRequest
# ===================================================================


class TestUpdateStatusPageIncidentRequestNegative:
    def test_title_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageIncidentRequest.model_validate({"title": "x" * 501})

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageIncidentRequest.model_validate({"status": "PENDING"})

    def test_invalid_impact(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageIncidentRequest.model_validate({"impact": "APOCALYPSE"})

    def test_postmortem_url_bad_protocol(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageIncidentRequest.model_validate(
                {"postmortemUrl": "ftp://bad.com/post"}
            )

    def test_postmortem_url_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStatusPageIncidentRequest.model_validate(
                {"postmortemUrl": "https://" + "x" * 2050}
            )


# ===================================================================
# CreateStatusPageIncidentUpdateRequest
# ===================================================================


class TestCreateStatusPageIncidentUpdateRequestNegative:
    def test_missing_body(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            CreateStatusPageIncidentUpdateRequest.model_validate({"status": "RESOLVED"})

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentUpdateRequest.model_validate(
                {"body": "X", "status": "BANANA"}
            )

    def test_null_body(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentUpdateRequest.model_validate(
                {"body": None, "status": "RESOLVED"}
            )


# ===================================================================
# StatusPageIncidentUpdateDto
# ===================================================================


class TestStatusPageIncidentUpdateDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageIncidentUpdateDto.model_validate(
                _del(_sp_incident_update(), "id")
            )

    def test_missing_status(self) -> None:
        with pytest.raises(ValidationError, match="status"):
            StatusPageIncidentUpdateDto.model_validate(
                _del(_sp_incident_update(), "status")
            )

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentUpdateDto.model_validate(
                _sp_incident_update(status="OOPS")
            )

    def test_missing_body(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            StatusPageIncidentUpdateDto.model_validate(
                _del(_sp_incident_update(), "body")
            )

    def test_missing_notify_subscribers(self) -> None:
        with pytest.raises(ValidationError, match="notifySubscribers"):
            StatusPageIncidentUpdateDto.model_validate(
                _del(_sp_incident_update(), "notifySubscribers")
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentUpdateDto.model_validate({})


# ===================================================================
# StatusPageSubscriberDto
# ===================================================================


class TestStatusPageSubscriberDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageSubscriberDto.model_validate(_del(_sp_subscriber(), "id"))

    def test_missing_email(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            StatusPageSubscriberDto.model_validate(_del(_sp_subscriber(), "email"))

    def test_missing_confirmed(self) -> None:
        with pytest.raises(ValidationError, match="confirmed"):
            StatusPageSubscriberDto.model_validate(_del(_sp_subscriber(), "confirmed"))

    def test_missing_created_at(self) -> None:
        with pytest.raises(ValidationError, match="createdAt"):
            StatusPageSubscriberDto.model_validate(_del(_sp_subscriber(), "createdAt"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageSubscriberDto.model_validate({})


# ===================================================================
# StatusPageCustomDomainDto
# ===================================================================


class TestStatusPageCustomDomainDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            StatusPageCustomDomainDto.model_validate(_del(_sp_custom_domain(), "id"))

    def test_missing_hostname(self) -> None:
        with pytest.raises(ValidationError, match="hostname"):
            StatusPageCustomDomainDto.model_validate(
                _del(_sp_custom_domain(), "hostname")
            )

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageCustomDomainDto.model_validate(_sp_custom_domain(status="MAGIC"))

    def test_invalid_verification_method(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageCustomDomainDto.model_validate(
                _sp_custom_domain(verificationMethod="HTTP")
            )

    def test_missing_verification_token(self) -> None:
        with pytest.raises(ValidationError, match="verificationToken"):
            StatusPageCustomDomainDto.model_validate(
                _del(_sp_custom_domain(), "verificationToken")
            )

    def test_missing_primary(self) -> None:
        with pytest.raises(ValidationError, match="primary"):
            StatusPageCustomDomainDto.model_validate(
                _del(_sp_custom_domain(), "primary")
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageCustomDomainDto.model_validate({})


# ===================================================================
# StatusPageIncidentComponentDto
# ===================================================================


class TestStatusPageIncidentComponentDtoNegative:
    def test_missing_component_id(self) -> None:
        with pytest.raises(ValidationError, match="statusPageComponentId"):
            StatusPageIncidentComponentDto.model_validate(
                _del(_sp_incident_component(), "statusPageComponentId")
            )

    def test_missing_component_status(self) -> None:
        with pytest.raises(ValidationError, match="componentStatus"):
            StatusPageIncidentComponentDto.model_validate(
                _del(_sp_incident_component(), "componentStatus")
            )

    def test_invalid_component_status(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentComponentDto.model_validate(
                _sp_incident_component(componentStatus="BROKEN")
            )

    def test_missing_component_name(self) -> None:
        with pytest.raises(ValidationError, match="componentName"):
            StatusPageIncidentComponentDto.model_validate(
                _del(_sp_incident_component(), "componentName")
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentComponentDto.model_validate({})


# ===================================================================
# AddCustomDomainRequest
# ===================================================================


class TestAddCustomDomainRequestNegative:
    def test_missing_hostname(self) -> None:
        with pytest.raises(ValidationError, match="hostname"):
            AddCustomDomainRequest.model_validate({})

    def test_empty_hostname(self) -> None:
        with pytest.raises(ValidationError):
            AddCustomDomainRequest.model_validate({"hostname": ""})

    def test_invalid_hostname(self) -> None:
        with pytest.raises(ValidationError):
            AddCustomDomainRequest.model_validate({"hostname": "NOT A HOST!"})

    def test_hostname_too_long(self) -> None:
        with pytest.raises(ValidationError):
            AddCustomDomainRequest.model_validate({"hostname": "a" * 256})


# ===================================================================
# AdminAddSubscriberRequest
# ===================================================================


class TestAdminAddSubscriberRequestNegative:
    def test_missing_email(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            AdminAddSubscriberRequest.model_validate({})

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            AdminAddSubscriberRequest.model_validate({"email": "bad"})

    def test_empty_email(self) -> None:
        with pytest.raises(ValidationError):
            AdminAddSubscriberRequest.model_validate({"email": ""})

    def test_null_email(self) -> None:
        with pytest.raises(ValidationError):
            AdminAddSubscriberRequest.model_validate({"email": None})


# ===================================================================
# TriggerRule
# ===================================================================


class TestTriggerRuleNegative:
    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            TriggerRule.model_validate({"scope": "per_region", "severity": "down"})

    def test_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            TriggerRule.model_validate(
                {"type": "magic_failures", "scope": "per_region", "severity": "down"}
            )

    def test_missing_scope(self) -> None:
        with pytest.raises(ValidationError, match="scope"):
            TriggerRule.model_validate(
                {"type": "consecutive_failures", "severity": "down"}
            )

    def test_invalid_scope(self) -> None:
        with pytest.raises(ValidationError):
            TriggerRule.model_validate(
                {"type": "consecutive_failures", "scope": "global", "severity": "down"}
            )

    def test_missing_severity(self) -> None:
        with pytest.raises(ValidationError, match="severity"):
            TriggerRule.model_validate(
                {"type": "consecutive_failures", "scope": "per_region"}
            )

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            TriggerRule.model_validate(
                {
                    "type": "consecutive_failures",
                    "scope": "per_region",
                    "severity": "critical",
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            TriggerRule.model_validate({})

    def test_wrong_count_type(self) -> None:
        with pytest.raises(ValidationError):
            TriggerRule.model_validate(
                {
                    "type": "consecutive_failures",
                    "scope": "per_region",
                    "severity": "down",
                    "count": "three",
                }
            )


# ===================================================================
# ConfirmationPolicy
# ===================================================================


class TestConfirmationPolicyNegative:
    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            ConfirmationPolicy.model_validate(
                {"minRegionsFailing": 1, "maxWaitSeconds": 30}
            )

    def test_missing_min_regions_failing(self) -> None:
        with pytest.raises(ValidationError, match="minRegionsFailing"):
            ConfirmationPolicy.model_validate(
                {"type": "ALL_REGIONS", "maxWaitSeconds": 30}
            )

    def test_missing_max_wait_seconds(self) -> None:
        with pytest.raises(ValidationError, match="maxWaitSeconds"):
            ConfirmationPolicy.model_validate(
                {"type": "ALL_REGIONS", "minRegionsFailing": 1}
            )

    def test_wrong_min_regions_type(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmationPolicy.model_validate(
                {
                    "type": "ALL_REGIONS",
                    "minRegionsFailing": "all",
                    "maxWaitSeconds": 30,
                }
            )

    def test_wrong_max_wait_type(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmationPolicy.model_validate(
                {
                    "type": "ALL_REGIONS",
                    "minRegionsFailing": 1,
                    "maxWaitSeconds": "forever",
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmationPolicy.model_validate({})


# ===================================================================
# RecoveryPolicy
# ===================================================================


class TestRecoveryPolicyNegative:
    def test_missing_consecutive_successes(self) -> None:
        with pytest.raises(ValidationError, match="consecutiveSuccesses"):
            RecoveryPolicy.model_validate(
                {"minRegionsPassing": 1, "cooldownMinutes": 5}
            )

    def test_missing_min_regions_passing(self) -> None:
        with pytest.raises(ValidationError, match="minRegionsPassing"):
            RecoveryPolicy.model_validate(
                {"consecutiveSuccesses": 1, "cooldownMinutes": 5}
            )

    def test_missing_cooldown_minutes(self) -> None:
        with pytest.raises(ValidationError, match="cooldownMinutes"):
            RecoveryPolicy.model_validate(
                {"consecutiveSuccesses": 1, "minRegionsPassing": 1}
            )

    def test_wrong_consecutive_type(self) -> None:
        with pytest.raises(ValidationError):
            RecoveryPolicy.model_validate(
                {
                    "consecutiveSuccesses": "two",
                    "minRegionsPassing": 1,
                    "cooldownMinutes": 5,
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            RecoveryPolicy.model_validate({})


# ===================================================================
# EscalationStep
# ===================================================================


class TestEscalationStepNegative:
    def test_missing_delay_minutes(self) -> None:
        with pytest.raises(ValidationError, match="delayMinutes"):
            EscalationStep.model_validate({"channelIds": [UID]})

    def test_missing_channel_ids(self) -> None:
        with pytest.raises(ValidationError, match="channelIds"):
            EscalationStep.model_validate({"delayMinutes": 0})

    def test_empty_channel_ids(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate({"delayMinutes": 0, "channelIds": []})

    def test_invalid_channel_id_format(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate({"delayMinutes": 0, "channelIds": ["bad"]})

    def test_negative_delay_minutes(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate({"delayMinutes": -1, "channelIds": [UID]})

    def test_wrong_delay_type(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate({"delayMinutes": "soon", "channelIds": [UID]})

    def test_wrong_repeat_interval_type(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate(
                {
                    "delayMinutes": 0,
                    "channelIds": [UID],
                    "repeatIntervalSeconds": "fast",
                }
            )

    def test_repeat_interval_below_min(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate(
                {"delayMinutes": 0, "channelIds": [UID], "repeatIntervalSeconds": 0}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            EscalationStep.model_validate({})


# ===================================================================
# MatchRule
# ===================================================================


class TestMatchRuleNegative:
    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            MatchRule.model_validate({})

    def test_wrong_type_field_type(self) -> None:
        with pytest.raises(ValidationError):
            MatchRule.model_validate({"type": [1, 2]})

    def test_wrong_monitor_ids_element(self) -> None:
        with pytest.raises(ValidationError):
            MatchRule.model_validate(
                {"type": "monitor_id_in", "monitorIds": ["not-a-uuid"]}
            )

    def test_wrong_regions_type(self) -> None:
        with pytest.raises(ValidationError):
            MatchRule.model_validate({"type": "region_in", "regions": "us-east"})


# ===================================================================
# RetryStrategy
# ===================================================================


class TestRetryStrategyNegative:
    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            RetryStrategy.model_validate({"maxRetries": 3, "interval": 30})

    def test_missing_max_retries(self) -> None:
        with pytest.raises(ValidationError, match="maxRetries"):
            RetryStrategy.model_validate({"type": "fixed", "interval": 30})

    def test_missing_interval(self) -> None:
        with pytest.raises(ValidationError, match="interval"):
            RetryStrategy.model_validate({"type": "fixed", "maxRetries": 3})

    def test_wrong_max_retries_type(self) -> None:
        with pytest.raises(ValidationError):
            RetryStrategy.model_validate(
                {"type": "fixed", "maxRetries": "three", "interval": 30}
            )

    def test_wrong_interval_type(self) -> None:
        with pytest.raises(ValidationError):
            RetryStrategy.model_validate(
                {"type": "fixed", "maxRetries": 3, "interval": "slow"}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            RetryStrategy.model_validate({})


# ===================================================================
# IncidentPolicyDto
# ===================================================================


class TestIncidentPolicyDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            IncidentPolicyDto.model_validate(_del(_incident_policy(), "id"))

    def test_missing_monitor_id(self) -> None:
        with pytest.raises(ValidationError, match="monitorId"):
            IncidentPolicyDto.model_validate(_del(_incident_policy(), "monitorId"))

    def test_missing_trigger_rules(self) -> None:
        with pytest.raises(ValidationError, match="triggerRules"):
            IncidentPolicyDto.model_validate(_del(_incident_policy(), "triggerRules"))

    def test_missing_confirmation(self) -> None:
        with pytest.raises(ValidationError, match="confirmation"):
            IncidentPolicyDto.model_validate(_del(_incident_policy(), "confirmation"))

    def test_missing_recovery(self) -> None:
        with pytest.raises(ValidationError, match="recovery"):
            IncidentPolicyDto.model_validate(_del(_incident_policy(), "recovery"))

    def test_wrong_trigger_rules_type(self) -> None:
        with pytest.raises(ValidationError):
            IncidentPolicyDto.model_validate(_incident_policy(triggerRules="bad"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            IncidentPolicyDto.model_validate({})


# ===================================================================
# IncidentDetailDto
# ===================================================================


class TestIncidentDetailDtoNegative:
    def test_missing_incident(self) -> None:
        with pytest.raises(ValidationError, match="incident"):
            IncidentDetailDto.model_validate({"updates": [], "statusPageIncidents": []})

    def test_wrong_incident_type(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDetailDto.model_validate(
                {"incident": "not-a-dict", "updates": [], "statusPageIncidents": []}
            )

    def test_missing_updates(self) -> None:
        with pytest.raises(ValidationError, match="updates"):
            IncidentDetailDto.model_validate(
                {"incident": _incident(), "statusPageIncidents": []}
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDetailDto.model_validate({})


# ===================================================================
# CheckResultDto
# ===================================================================


class TestCheckResultDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            CheckResultDto.model_validate(_del(_check_result(), "id"))

    def test_missing_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="timestamp"):
            CheckResultDto.model_validate(_del(_check_result(), "timestamp"))

    def test_missing_region(self) -> None:
        with pytest.raises(ValidationError, match="region"):
            CheckResultDto.model_validate(_del(_check_result(), "region"))

    def test_missing_passed(self) -> None:
        with pytest.raises(ValidationError, match="passed"):
            CheckResultDto.model_validate(_del(_check_result(), "passed"))

    def test_wrong_passed_type(self) -> None:
        with pytest.raises(ValidationError):
            CheckResultDto.model_validate(_check_result(passed=[1]))

    def test_wrong_response_time_type(self) -> None:
        with pytest.raises(ValidationError):
            CheckResultDto.model_validate(_check_result(responseTimeMs="fast"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            CheckResultDto.model_validate({})


# ===================================================================
# MonitorVersionDto
# ===================================================================


class TestMonitorVersionDtoNegative:
    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            MonitorVersionDto.model_validate(_del(_monitor_version(), "id"))

    def test_missing_monitor_id(self) -> None:
        with pytest.raises(ValidationError, match="monitorId"):
            MonitorVersionDto.model_validate(_del(_monitor_version(), "monitorId"))

    def test_missing_version(self) -> None:
        with pytest.raises(ValidationError, match="version"):
            MonitorVersionDto.model_validate(_del(_monitor_version(), "version"))

    def test_wrong_version_type(self) -> None:
        with pytest.raises(ValidationError):
            MonitorVersionDto.model_validate(_monitor_version(version="v1"))

    def test_missing_snapshot(self) -> None:
        with pytest.raises(ValidationError, match="snapshot"):
            MonitorVersionDto.model_validate(_del(_monitor_version(), "snapshot"))

    def test_missing_changed_via(self) -> None:
        with pytest.raises(ValidationError, match="changedVia"):
            MonitorVersionDto.model_validate(_del(_monitor_version(), "changedVia"))

    def test_invalid_changed_via(self) -> None:
        with pytest.raises(ValidationError):
            MonitorVersionDto.model_validate(_monitor_version(changedVia="GITHUB"))

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            MonitorVersionDto.model_validate({})


# ===================================================================
# DashboardOverviewDto
# ===================================================================


class TestDashboardOverviewDtoNegative:
    def test_missing_monitors(self) -> None:
        with pytest.raises(ValidationError, match="monitors"):
            DashboardOverviewDto.model_validate(
                {"incidents": {"total": 0, "open": 0, "resolved": 0}}
            )

    def test_missing_incidents(self) -> None:
        with pytest.raises(ValidationError, match="incidents"):
            DashboardOverviewDto.model_validate(
                {
                    "monitors": {
                        "total": 0,
                        "healthy": 0,
                        "degraded": 0,
                        "down": 0,
                        "disabled": 0,
                        "paused": 0,
                    }
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            DashboardOverviewDto.model_validate({})


# ===================================================================
# TestChannelResult
# ===================================================================


class TestChannelResultNegative:
    def test_missing_success(self) -> None:
        with pytest.raises(ValidationError, match="success"):
            TestChannelResult.model_validate({"message": "ok"})

    def test_missing_message(self) -> None:
        with pytest.raises(ValidationError, match="message"):
            TestChannelResult.model_validate({"success": True})

    def test_wrong_success_type(self) -> None:
        with pytest.raises(ValidationError):
            TestChannelResult.model_validate({"success": [1], "message": "ok"})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            TestChannelResult.model_validate({})


# ===================================================================
# WebhookTestResult
# ===================================================================


class TestWebhookTestResultNegative:
    def test_missing_success(self) -> None:
        with pytest.raises(ValidationError, match="success"):
            WebhookTestResult.model_validate(
                {"statusCode": 200, "message": "OK", "durationMs": 5}
            )

    def test_wrong_status_code_type(self) -> None:
        with pytest.raises(ValidationError):
            WebhookTestResult.model_validate(
                {"success": True, "statusCode": "ok", "message": "OK", "durationMs": 5}
            )

    def test_wrong_duration_type(self) -> None:
        with pytest.raises(ValidationError):
            WebhookTestResult.model_validate(
                {
                    "success": True,
                    "statusCode": 200,
                    "message": "OK",
                    "durationMs": "fast",
                }
            )

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            WebhookTestResult.model_validate({})


# ===================================================================
# ReorderComponentsRequest
# ===================================================================


class TestReorderComponentsRequestNegative:
    def test_empty_positions(self) -> None:
        with pytest.raises(ValidationError):
            ReorderComponentsRequest.model_validate({"positions": []})

    def test_missing_positions(self) -> None:
        with pytest.raises(ValidationError, match="positions"):
            ReorderComponentsRequest.model_validate({})

    def test_wrong_positions_type(self) -> None:
        with pytest.raises(ValidationError):
            ReorderComponentsRequest.model_validate({"positions": "bad"})


# ===================================================================
# ComponentPosition
# ===================================================================


class TestComponentPositionNegative:
    def test_missing_component_id(self) -> None:
        with pytest.raises(ValidationError, match="componentId"):
            ComponentPosition.model_validate({})

    def test_invalid_component_id(self) -> None:
        with pytest.raises(ValidationError):
            ComponentPosition.model_validate({"componentId": "not-uuid"})


# ===================================================================
# ResolveIncidentRequest
# ===================================================================


class TestResolveIncidentRequestNegative:
    def test_missing_body(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            ResolveIncidentRequest.model_validate({})

    def test_null_body(self) -> None:
        with pytest.raises(ValidationError):
            ResolveIncidentRequest.model_validate({"body": None})

    def test_wrong_body_type(self) -> None:
        with pytest.raises(ValidationError):
            ResolveIncidentRequest.model_validate({"body": [1, 2]})


# ===================================================================
# AddIncidentUpdateRequest
# ===================================================================


class TestAddIncidentUpdateRequestNegative:
    def test_missing_notify_subscribers(self) -> None:
        with pytest.raises(ValidationError, match="notifySubscribers"):
            AddIncidentUpdateRequest.model_validate({"body": "update"})

    def test_invalid_new_status(self) -> None:
        with pytest.raises(ValidationError):
            AddIncidentUpdateRequest.model_validate(
                {"notifySubscribers": True, "newStatus": "BANANA"}
            )

    def test_wrong_notify_type(self) -> None:
        with pytest.raises(ValidationError):
            AddIncidentUpdateRequest.model_validate({"notifySubscribers": [1]})

    def test_empty_dict(self) -> None:
        with pytest.raises(ValidationError):
            AddIncidentUpdateRequest.model_validate({})
