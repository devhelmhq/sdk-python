"""Comprehensive tests for generated Pydantic schemas.

Validates field constraints, enum values, nullable handling, aliased fields,
nested models, and negative cases (missing required fields, wrong types,
invalid enum values, constraint violations).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from devhelm._generated import (
    AddCustomDomainRequest,
    AdminAddSubscriberRequest,
    CheckTypeDetailsDto,
    ComponentPosition,
    CreateManualIncidentRequest,
    CreateMonitorRequest,
    CreateStatusPageComponentRequest,
    CreateStatusPageIncidentRequest,
    CreateStatusPageIncidentUpdateRequest,
    CreateStatusPageRequest,
    CreateTagRequest,
    IncidentDetailDto,
    IncidentDto,
    MonitorDto,
    ReorderComponentsRequest,
    ResolveIncidentRequest,
    ResourceGroupDto,
    ServiceSubscriptionDto,
    StatusPageBranding,
    StatusPageComponentDto,
    StatusPageDto,
    StatusPageIncidentDto,
    SubscribedEvent,
    WebhookTestResult,
)

UID = str(uuid4())
ORG_ID = 1
WS_ID = 1
NOW = "2026-01-01T00:00:00Z"


# ---------- Request DTOs ----------


class TestCreateStatusPageRequest:
    def test_minimal_valid(self) -> None:
        r = CreateStatusPageRequest.model_validate(
            {"name": "My Page", "slug": "my-page"}
        )
        assert r.name == "My Page"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateStatusPageRequest.model_validate({"slug": "my-page"})

    def test_missing_slug_raises(self) -> None:
        with pytest.raises(ValidationError, match="slug"):
            CreateStatusPageRequest.model_validate({"name": "X"})

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "", "slug": "x"})

    def test_slug_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "X", "slug": "a" * 256})

    def test_slug_invalid_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageRequest.model_validate({"name": "X", "slug": "UPPER CASE!"})


class TestCreateStatusPageComponentRequest:
    def test_minimal_valid(self) -> None:
        r = CreateStatusPageComponentRequest.model_validate(
            {"name": "API", "type": "STATIC"}
        )
        assert r.name == "API"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateStatusPageComponentRequest.model_validate({"type": "STATIC"})

    def test_missing_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            CreateStatusPageComponentRequest.model_validate({"name": "API"})

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentRequest.model_validate(
                {"name": "API", "type": "BANANA"}
            )


class TestCreateStatusPageIncidentRequest:
    def test_minimal_valid(self) -> None:
        r = CreateStatusPageIncidentRequest.model_validate(
            {"title": "Incident", "impact": "MINOR", "body": "Initial update text"}
        )
        assert r.title == "Incident"

    def test_missing_title_raises(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CreateStatusPageIncidentRequest.model_validate(
                {"impact": "MINOR", "body": "text"}
            )

    def test_missing_body_raises(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "X", "impact": "MINOR"}
            )

    def test_invalid_impact_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "X", "impact": "CATASTROPHIC", "body": "text"}
            )


class TestCreateStatusPageIncidentUpdateRequest:
    def test_valid(self) -> None:
        r = CreateStatusPageIncidentUpdateRequest.model_validate(
            {"body": "Fixed", "status": "RESOLVED"}
        )
        assert r.body == "Fixed"

    def test_missing_body_raises(self) -> None:
        with pytest.raises(ValidationError, match="body"):
            CreateStatusPageIncidentUpdateRequest.model_validate({"status": "RESOLVED"})

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentUpdateRequest.model_validate(
                {"body": "X", "status": "INVALID"}
            )


class TestAdminAddSubscriberRequest:
    def test_valid_email(self) -> None:
        r = AdminAddSubscriberRequest.model_validate({"email": "test@example.com"})
        assert r.email == "test@example.com"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdminAddSubscriberRequest.model_validate({"email": "not-an-email"})

    def test_empty_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdminAddSubscriberRequest.model_validate({"email": ""})

    def test_missing_email_raises(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            AdminAddSubscriberRequest.model_validate({})


class TestAddCustomDomainRequest:
    def test_valid_hostname(self) -> None:
        r = AddCustomDomainRequest.model_validate({"hostname": "status.example.com"})
        assert r.hostname == "status.example.com"

    def test_invalid_hostname_raises(self) -> None:
        with pytest.raises(ValidationError):
            AddCustomDomainRequest.model_validate({"hostname": "INVALID HOST!"})

    def test_empty_hostname_raises(self) -> None:
        with pytest.raises(ValidationError):
            AddCustomDomainRequest.model_validate({"hostname": ""})


class TestReorderComponentsRequest:
    def test_valid(self) -> None:
        r = ReorderComponentsRequest.model_validate(
            {"positions": [{"componentId": str(uuid4()), "displayOrder": 0}]}
        )
        assert len(r.positions) == 1

    def test_empty_positions_raises(self) -> None:
        with pytest.raises(ValidationError):
            ReorderComponentsRequest.model_validate({"positions": []})


class TestComponentPosition:
    def test_valid(self) -> None:
        cp = ComponentPosition.model_validate(
            {"componentId": str(uuid4()), "displayOrder": 1}
        )
        assert cp.component_id is not None

    def test_missing_component_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="componentId"):
            ComponentPosition.model_validate({})


class TestResolveIncidentRequest:
    def test_valid(self) -> None:
        r = ResolveIncidentRequest.model_validate({"body": "All clear"})
        assert r.body == "All clear"

    def test_missing_body_accepted(self) -> None:
        r = ResolveIncidentRequest.model_validate({})
        assert r.body is None


class TestCreateManualIncidentRequest:
    def test_valid(self) -> None:
        r = CreateManualIncidentRequest.model_validate(
            {"title": "Outage", "severity": "DOWN"}
        )
        assert r.title == "Outage"

    def test_missing_title_raises(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CreateManualIncidentRequest.model_validate({"severity": "DOWN"})

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": "X", "severity": "SEV1"}
            )

    def test_valid_severity_values(self) -> None:
        for sev in ["DOWN", "DEGRADED", "MAINTENANCE"]:
            r = CreateManualIncidentRequest.model_validate(
                {"title": "X", "severity": sev}
            )
            assert r.severity.value == sev


class TestCreateTagRequest:
    def test_valid(self) -> None:
        r = CreateTagRequest.model_validate({"name": "production"})
        assert r.name == "production"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateTagRequest.model_validate({})


class TestCreateMonitorRequest:
    def test_missing_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            CreateMonitorRequest.model_validate(
                {
                    "name": "Test",
                    "config": {"url": "https://example.com", "method": "GET"},
                    "frequencySeconds": 60,
                }
            )

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateMonitorRequest.model_validate(
                {
                    "type": "HTTP",
                    "config": {"url": "https://example.com", "method": "GET"},
                    "frequencySeconds": 60,
                }
            )


# ---- Response DTO validation ----


def _monitor_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "organizationId": ORG_ID,
        "name": "Test Monitor",
        "type": "HTTP",
        "config": {"url": "https://example.com", "method": "GET"},
        "frequencySeconds": 60,
        "enabled": True,
        "regions": ["us-east"],
        "managedBy": "DASHBOARD",
        "createdAt": NOW,
        "updatedAt": NOW,
        "assertions": [],
        "tags": [],
        "pingUrl": None,
        "alertChannelIds": [],
        "environment": None,
        "auth": None,
        "incidentPolicy": None,
    }
    base.update(overrides)
    return base


def _incident_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "monitorId": UID,
        "organizationId": ORG_ID,
        "source": "MANUAL",
        "status": "TRIGGERED",
        "severity": "DOWN",
        "title": "Test Incident",
        "triggeredByRule": None,
        "affectedRegions": [],
        "reopenCount": 0,
        "createdByUserId": None,
        "statusPageVisible": False,
        "serviceIncidentId": None,
        "serviceId": None,
        "externalRef": None,
        "affectedComponents": [],
        "shortlink": None,
        "resolutionReason": None,
        "startedAt": NOW,
        "confirmedAt": None,
        "resolvedAt": None,
        "cooldownUntil": None,
        "createdAt": NOW,
        "updatedAt": NOW,
        "monitorName": None,
        "serviceName": None,
        "serviceSlug": None,
        "monitorType": None,
        "resourceGroupId": None,
        "resourceGroupName": None,
    }
    base.update(overrides)
    return base


def _rg_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "organizationId": ORG_ID,
        "name": "Test RG",
        "slug": "test-rg",
        "description": None,
        "alertPolicyId": None,
        "defaultFrequency": None,
        "defaultRegions": [],
        "defaultAlertChannels": [],
        "defaultEnvironmentId": None,
        "healthThresholdType": "PERCENTAGE",
        "healthThresholdValue": 100,
        "suppressMemberAlerts": False,
        "confirmationDelaySeconds": 0,
        "recoveryCooldownMinutes": 0,
        "members": [],
        "createdAt": NOW,
        "updatedAt": NOW,
        "defaultRetryStrategy": None,
        "health": {
            "status": "operational",
            "thresholdStatus": None,
            "failingCount": None,
            "totalMembers": 2,
            "operationalCount": 2,
            "activeIncidents": 0,
        },
    }
    base.update(overrides)
    return base


def _status_page_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "organizationId": ORG_ID,
        "workspaceId": WS_ID,
        "name": "Status",
        "slug": "status",
        "description": None,
        "branding": {
            "logoUrl": None,
            "faviconUrl": None,
            "brandColor": None,
            "pageBackground": None,
            "cardBackground": None,
            "textColor": None,
            "borderColor": None,
            "headerStyle": None,
            "theme": None,
            "reportUrl": None,
            "hidePoweredBy": False,
            "customCss": None,
            "customHeadHtml": None,
        },
        "visibility": "PUBLIC",
        "enabled": True,
        "incidentMode": "MANUAL",
        "componentCount": 0,
        "subscriberCount": 0,
        "overallStatus": "OPERATIONAL",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(overrides)
    return base


def _sp_component_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "statusPageId": UID,
        "groupId": None,
        "name": "API",
        "description": None,
        "type": "STATIC",
        "monitorId": None,
        "resourceGroupId": None,
        "currentStatus": "OPERATIONAL",
        "showUptime": True,
        "displayOrder": 0,
        "pageOrder": 0,
        "excludeFromOverall": False,
        "startDate": NOW,
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(overrides)
    return base


def _sp_incident_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": UID,
        "statusPageId": UID,
        "title": "Incident",
        "status": "INVESTIGATING",
        "impact": "MINOR",
        "scheduled": False,
        "scheduledFor": None,
        "scheduledUntil": None,
        "autoResolve": False,
        "incidentId": None,
        "startedAt": NOW,
        "publishedAt": None,
        "resolvedAt": None,
        "createdByUserId": None,
        "postmortemBody": None,
        "postmortemUrl": None,
        "affectedComponents": [],
        "updates": [],
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(overrides)
    return base


def _service_sub_fixture(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "subscriptionId": UID,
        "serviceId": UID,
        "slug": "github",
        "name": "GitHub",
        "category": "Development",
        "officialStatusUrl": "https://www.githubstatus.com",
        "adapterType": "COMPONENT_SCRAPER",
        "pollingIntervalSeconds": 300,
        "enabled": True,
        "logoUrl": "https://example.com/logo.png",
        "overallStatus": "operational",
        "componentId": None,
        "alertSensitivity": "ALL",
        "subscribedAt": NOW,
        "component": None,
    }
    base.update(overrides)
    return base


class TestMonitorDtoNullableFields:
    def test_all_nullable_fields_null(self) -> None:
        m = MonitorDto.model_validate(_monitor_fixture())
        assert m.environment is None
        assert m.auth is None
        assert m.incident_policy is None

    def test_wrong_type_for_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate(_monitor_fixture(name=12345))

    def test_missing_required_field_raises(self) -> None:
        data = _monitor_fixture()
        del data["name"]
        with pytest.raises(ValidationError, match="name"):
            MonitorDto.model_validate(data)


class TestResourceGroupDtoNullableFields:
    def test_nullable_fields_null(self) -> None:
        rg = ResourceGroupDto.model_validate(_rg_fixture())
        assert rg.default_retry_strategy is None
        assert rg.health is not None
        assert rg.health.status == "operational"


class TestIncidentDtoNullableFields:
    def test_nullable_fields_null(self) -> None:
        inc = IncidentDto.model_validate(_incident_fixture())
        assert inc.monitor_name is None
        assert inc.service_name is None
        assert inc.resource_group_id is None


class TestServiceSubscriptionDtoNullableFields:
    def test_nullable_component(self) -> None:
        sub = ServiceSubscriptionDto.model_validate(_service_sub_fixture())
        assert sub.component is None


class TestStatusPageDto:
    def test_valid(self) -> None:
        dto = StatusPageDto.model_validate(_status_page_fixture())
        assert dto.name == "Status"

    def test_missing_required_raises(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageDto.model_validate({"id": UID})


class TestStatusPageIncidentDto:
    def test_valid(self) -> None:
        dto = StatusPageIncidentDto.model_validate(_sp_incident_fixture())
        assert dto.title == "Incident"

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            StatusPageIncidentDto.model_validate(_sp_incident_fixture(status="BANANA"))


class TestStatusPageComponentDto:
    def test_valid(self) -> None:
        dto = StatusPageComponentDto.model_validate(_sp_component_fixture())
        assert dto.name == "API"


class TestStatusPageBranding:
    def test_all_nullable(self) -> None:
        b = StatusPageBranding.model_validate(
            {
                "logoUrl": None,
                "faviconUrl": None,
                "brandColor": None,
                "pageBackground": None,
                "cardBackground": None,
                "textColor": None,
                "borderColor": None,
                "headerStyle": None,
                "theme": None,
                "reportUrl": None,
                "hidePoweredBy": False,
                "customCss": None,
                "customHeadHtml": None,
            }
        )
        assert b.hide_powered_by is False

    def test_empty_branding_uses_defaults(self) -> None:
        b = StatusPageBranding.model_validate({})
        assert b.hide_powered_by is False


class TestWebhookTestResult:
    def test_valid(self) -> None:
        r = WebhookTestResult.model_validate(
            {"success": True, "statusCode": 200, "message": "OK", "durationMs": 42}
        )
        assert r.success is True
        assert r.status_code == 200

    def test_missing_field_raises(self) -> None:
        with pytest.raises(ValidationError, match="success"):
            WebhookTestResult.model_validate(
                {"statusCode": 200, "message": "OK", "durationMs": 42}
            )


class TestIncidentDetailDto:
    def test_valid(self) -> None:
        dto = IncidentDetailDto.model_validate(
            {"incident": _incident_fixture(), "updates": [], "statusPageIncidents": []}
        )
        assert dto.incident.title == "Test Incident"

    def test_missing_incident_raises(self) -> None:
        with pytest.raises(ValidationError, match="incident"):
            IncidentDetailDto.model_validate({"updates": [], "statusPageIncidents": []})


class TestAliasedFieldAccess:
    def test_webhook_result_alias(self) -> None:
        r = WebhookTestResult.model_validate(
            {"success": True, "statusCode": 201, "message": "OK", "durationMs": 10}
        )
        assert r.status_code == 201
        assert r.duration_ms == 10

    def test_serialization_uses_alias(self) -> None:
        r = WebhookTestResult.model_validate(
            {"success": True, "statusCode": 200, "message": "OK", "durationMs": 5}
        )
        dumped = r.model_dump(by_alias=True)
        assert "statusCode" in dumped
        assert "durationMs" in dumped

    def test_incident_dto_aliases(self) -> None:
        inc = IncidentDto.model_validate(_incident_fixture())
        dumped = inc.model_dump(by_alias=True)
        assert "monitorId" in dumped
        assert "organizationId" in dumped
        assert "createdAt" in dumped


class TestWrongTypesRaisePydanticErrors:
    def test_string_where_int_expected(self) -> None:
        with pytest.raises(ValidationError):
            WebhookTestResult.model_validate(
                {
                    "success": True,
                    "statusCode": "not-a-number",
                    "message": "OK",
                    "durationMs": 5,
                }
            )

    def test_list_where_string_expected(self) -> None:
        with pytest.raises(ValidationError):
            ResolveIncidentRequest.model_validate({"body": ["not", "a", "string"]})

    def test_missing_all_fields(self) -> None:
        with pytest.raises(ValidationError):
            MonitorDto.model_validate({})

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDto.model_validate("not a dict")


class TestEnumValidationRejectsInvalid:
    def test_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            CreateManualIncidentRequest.model_validate(
                {"title": "X", "severity": "SEV1"}
            )

    def test_invalid_incident_impact(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageIncidentRequest.model_validate(
                {"title": "X", "impact": "CATASTROPHIC", "body": "X"}
            )

    def test_invalid_component_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateStatusPageComponentRequest.model_validate(
                {"name": "X", "type": "INVALID_TYPE"}
            )


class TestSubscribedEventStrictness:
    """`SubscribedEvent` is a closed enum in the spec — datamodel-codegen
    emits it as a `StrEnum`, so unknown values fail at construction and
    inside Pydantic models. These tests pin the closed-set contract so a
    spec rename or type-loosening trips CI rather than silently accepting
    new event names (P1)."""

    def test_subscribed_event_accepts_known_value(self) -> None:
        ev = SubscribedEvent("monitor.created")
        assert ev.value == "monitor.created"

    def test_subscribed_event_rejects_non_string(self) -> None:
        with pytest.raises(ValueError):
            SubscribedEvent(42)  # type: ignore[arg-type]

    def test_subscribed_event_rejects_unknown_event(self) -> None:
        with pytest.raises(ValueError):
            SubscribedEvent("monitor.exploded")

    def test_subscribed_event_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError):
            SubscribedEvent("")

    def test_check_type_details_routes_by_discriminator(self) -> None:
        details = CheckTypeDetailsDto.model_validate({"check_type": "http"})
        assert details.root.check_type == "http"

    def test_check_type_details_rejects_unknown_discriminator(self) -> None:
        with pytest.raises(ValidationError):
            CheckTypeDetailsDto.model_validate({"check_type": "graphql"})

    def test_check_type_details_inner_variant_rejects_extra_keys(self) -> None:
        # The Http inner variant has `extra='forbid'`. If anyone ever drops
        # it, this test fails — that's the whole point of having explicit
        # coverage for RootModel-wrapped inners (P1).
        with pytest.raises(ValidationError, match="extra"):
            CheckTypeDetailsDto.model_validate(
                {"check_type": "http", "totally_made_up_key": True}
            )

    def test_check_type_details_dns_variant_rejects_extra_keys(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            CheckTypeDetailsDto.model_validate(
                {"check_type": "dns", "rogue_field": "x"}
            )

    def test_check_type_details_tcp_variant_rejects_extra_keys(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            CheckTypeDetailsDto.model_validate({"check_type": "tcp", "tls_extra": True})
