"""Spec parity tests.

These tests are the canary for *logical* drift between the vendored
``docs/openapi/monitoring-api.json`` and the SDK surface.  ``spec-check.yml``
already verifies that the spec re-generates without crashing and that the
package compiles, but it does **not** notice when:

* a public DTO that shipped in a previous SDK release silently disappears from
  the spec (or gets renamed), or
* a required field on a shipped request shrinks or grows, or
* a path used by a hand-written resource method is no longer present in the
  spec.

The hand-built dictionaries in ``test_schemas.py`` exercise the *runtime*
behaviour of the Pydantic models, but they are decoupled from the spec — they
will keep passing even if the spec drops the schema entirely (because they
import the generated class, which is also re-generated from the same spec).
The assertions below close that loop by reading the OpenAPI document at test
time and asserting structural agreement against the SDK's public surface.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, get_type_hints

import pytest
from pydantic import BaseModel

import devhelm
from devhelm import _generated
from devhelm.resources.alert_channels import AlertChannels
from devhelm.resources.api_keys import ApiKeys
from devhelm.resources.deploy_lock import DeployLock
from devhelm.resources.environments import Environments
from devhelm.resources.incidents import Incidents
from devhelm.resources.monitors import Monitors
from devhelm.resources.notification_policies import NotificationPolicies
from devhelm.resources.resource_groups import ResourceGroups
from devhelm.resources.secrets import Secrets
from devhelm.resources.status_pages import StatusPages
from devhelm.resources.status_pages import _Components as StatusPageComponents
from devhelm.resources.status_pages import _Domains as StatusPageCustomDomains
from devhelm.resources.status_pages import _Groups as StatusPageComponentGroups
from devhelm.resources.status_pages import _Incidents as StatusPageIncidents
from devhelm.resources.status_pages import _Subscribers as StatusPageSubscribers
from devhelm.resources.tags import Tags
from devhelm.resources.webhooks import Webhooks

SPEC_PATH = Path(__file__).parent.parent / "docs" / "openapi" / "monitoring-api.json"


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    """Load the vendored OpenAPI spec once per module."""
    return json.loads(SPEC_PATH.read_text())


@pytest.fixture(scope="module")
def schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec["components"]["schemas"]


@pytest.fixture(scope="module")
def paths(spec: dict[str, Any]) -> dict[str, Any]:
    return spec["paths"]


# ---------- 1. Schema parity: every public DTO must exist in the spec ----------


# DTOs that are intentionally hand-defined in the SDK (not from the spec) or
# that the spec omits because they are response wrappers materialised
# server-side.  Keep this list small and document each entry.
SCHEMAS_NOT_IN_SPEC: frozenset[str] = frozenset(
    {
        # Pagination wrappers — generated from `Page` / `CursorPage` generics
        # and not present as standalone schemas in the OpenAPI document.
        "Page",
        "CursorPage",
    }
)


def _public_dto_names() -> list[str]:
    """Public DTOs the SDK re-exports that map 1:1 to spec schemas."""
    candidates: list[str] = []
    for name in devhelm.__all__:
        obj = getattr(devhelm, name, None)
        if obj is None:
            continue
        if not isinstance(obj, type):
            continue
        if not issubclass(obj, BaseModel):
            continue
        if name in SCHEMAS_NOT_IN_SPEC:
            continue
        candidates.append(name)
    return sorted(candidates)


@pytest.mark.parametrize("dto_name", _public_dto_names())
def test_public_dto_exists_in_spec(dto_name: str, schemas: dict[str, Any]) -> None:
    """Every public DTO/Request type the SDK re-exports must exist in the spec."""
    assert dto_name in schemas, (
        f"{dto_name} is exported from `devhelm` but missing from the OpenAPI "
        "spec.  Either it was renamed/removed upstream (regenerate _generated.py) "
        "or it should be added to SCHEMAS_NOT_IN_SPEC with a comment."
    )


# ---------- 2. Required-field parity for request DTOs ----------


# ``RequestBody`` body parameters resolved per resource — every entry here is
# (model_class, ``method`` name) — kept narrow on purpose: these are the
# request shapes documented in the README and used in our typed examples.
REQUEST_DTO_NAMES: list[str] = sorted(
    {
        "AcquireDeployLockRequest",
        "AddCustomDomainRequest",
        "AddIncidentUpdateRequest",
        "AddResourceGroupMemberRequest",
        "AdminAddSubscriberRequest",
        "CreateAlertChannelRequest",
        "CreateApiKeyRequest",
        "CreateEnvironmentRequest",
        "CreateManualIncidentRequest",
        "CreateMonitorRequest",
        "CreateNotificationPolicyRequest",
        "CreateResourceGroupRequest",
        "CreateSecretRequest",
        "CreateStatusPageComponentGroupRequest",
        "CreateStatusPageComponentRequest",
        "CreateStatusPageIncidentRequest",
        "CreateStatusPageIncidentUpdateRequest",
        "CreateStatusPageRequest",
        "CreateTagRequest",
        "CreateWebhookEndpointRequest",
        "ReorderComponentsRequest",
        "ResolveIncidentRequest",
        "UpdateAlertChannelRequest",
        "UpdateEnvironmentRequest",
        "UpdateMonitorRequest",
        "UpdateNotificationPolicyRequest",
        "UpdateResourceGroupRequest",
        "UpdateSecretRequest",
        "UpdateStatusPageComponentGroupRequest",
        "UpdateStatusPageComponentRequest",
        "UpdateStatusPageIncidentRequest",
        "UpdateStatusPageRequest",
        "UpdateTagRequest",
        "UpdateWebhookEndpointRequest",
    }
)


@pytest.mark.parametrize("dto_name", REQUEST_DTO_NAMES)
def test_request_required_fields_match_spec(
    dto_name: str, schemas: dict[str, Any]
) -> None:
    """Required fields on the spec must be required on the Pydantic model.

    A request DTO going from required → optional in the spec without the
    Pydantic model following suit means the SDK silently rejects payloads
    the API would accept.  The reverse — required field added to the spec
    but missing on the model — means the SDK lets you send an obviously
    malformed payload.  Either way, this test catches the drift.
    """
    spec_schema = schemas.get(dto_name)
    assert spec_schema is not None, (
        f"{dto_name} listed in REQUEST_DTO_NAMES but missing from spec "
        "(see test_public_dto_exists_in_spec for details)."
    )

    spec_required = set(spec_schema.get("required", []))

    model_cls = getattr(_generated, dto_name)
    model_required = {
        # Pydantic stores the wire name as ``alias`` when one is set, and
        # falls back to the Python attribute name otherwise.
        (info.alias or field_name)
        for field_name, info in model_cls.model_fields.items()
        if info.is_required()
    }

    # The spec is the source of truth; model_required must be a *superset*
    # of spec_required.  Models may legitimately mark additional fields as
    # required for extra runtime safety, but they must never relax a field
    # the spec considers required.
    missing = spec_required - model_required
    assert not missing, (
        f"{dto_name}: fields {sorted(missing)} are required in the OpenAPI "
        "spec but optional on the generated Pydantic model.  Re-run "
        "`uv run datamodel-codegen` after pulling the latest spec, or align "
        "the manual override."
    )


# ---------- 3. Method body parameters accept ``Mapping[str, Any]`` ----------


# Resource classes whose mutating methods take ``RequestBody[T]`` body params.
# Listed here so a contributor adding a new resource gets the parity check
# for free.  Each tuple is (resource_class, [(method_name, expected_model)]).
RESOURCE_BODY_METHODS: list[tuple[type, list[tuple[str, str]]]] = [
    (
        Monitors,
        [("create", "CreateMonitorRequest"), ("update", "UpdateMonitorRequest")],
    ),
    (
        Incidents,
        [
            ("create", "CreateManualIncidentRequest"),
            ("resolve", "ResolveIncidentRequest"),
        ],
    ),
    (
        AlertChannels,
        [
            ("create", "CreateAlertChannelRequest"),
            ("update", "UpdateAlertChannelRequest"),
        ],
    ),
    (
        NotificationPolicies,
        [
            ("create", "CreateNotificationPolicyRequest"),
            ("update", "UpdateNotificationPolicyRequest"),
        ],
    ),
    (
        Environments,
        [
            ("create", "CreateEnvironmentRequest"),
            ("update", "UpdateEnvironmentRequest"),
        ],
    ),
    (Secrets, [("create", "CreateSecretRequest"), ("update", "UpdateSecretRequest")]),
    (Tags, [("create", "CreateTagRequest"), ("update", "UpdateTagRequest")]),
    (
        ResourceGroups,
        [
            ("create", "CreateResourceGroupRequest"),
            ("update", "UpdateResourceGroupRequest"),
            ("add_member", "AddResourceGroupMemberRequest"),
        ],
    ),
    (
        Webhooks,
        [
            ("create", "CreateWebhookEndpointRequest"),
            ("update", "UpdateWebhookEndpointRequest"),
        ],
    ),
    (ApiKeys, [("create", "CreateApiKeyRequest")]),
    (DeployLock, [("acquire", "AcquireDeployLockRequest")]),
    (
        StatusPages,
        [("create", "CreateStatusPageRequest"), ("update", "UpdateStatusPageRequest")],
    ),
    (
        StatusPageComponents,
        [
            ("create", "CreateStatusPageComponentRequest"),
            ("update", "UpdateStatusPageComponentRequest"),
            ("reorder", "ReorderComponentsRequest"),
        ],
    ),
    (
        StatusPageComponentGroups,
        [
            ("create", "CreateStatusPageComponentGroupRequest"),
            ("update", "UpdateStatusPageComponentGroupRequest"),
        ],
    ),
    (
        StatusPageIncidents,
        [
            ("create", "CreateStatusPageIncidentRequest"),
            ("update", "UpdateStatusPageIncidentRequest"),
            ("post_update", "CreateStatusPageIncidentUpdateRequest"),
        ],
    ),
    (StatusPageSubscribers, [("add", "AdminAddSubscriberRequest")]),
    (StatusPageCustomDomains, [("add", "AddCustomDomainRequest")]),
]


def _resource_method_params() -> list[tuple[type, str, str]]:
    return [
        (cls, method, expected)
        for cls, methods in RESOURCE_BODY_METHODS
        for method, expected in methods
    ]


@pytest.mark.parametrize(
    "resource_cls,method_name,expected_model",
    _resource_method_params(),
    ids=lambda v: v if isinstance(v, str) else v.__name__,
)
def test_resource_method_body_accepts_dict(
    resource_cls: type, method_name: str, expected_model: str
) -> None:
    """Every mutating resource method's ``body`` param accepts a dict.

    The ticket calls out the dict-vs-model ergonomics conflict: README
    examples show dicts (``client.monitors.create({"name": "foo"})``) but
    earlier signatures only accepted the Pydantic model.  We resolved this
    by widening the type to ``RequestBody[T] = T | Mapping[str, Any]``.
    The assertion below ensures every body parameter actually has the
    union — without it, ``mypy --strict`` would reject the documented
    usage.
    """
    method = getattr(resource_cls, method_name)
    hints = get_type_hints(method)
    assert "body" in hints, f"{resource_cls.__name__}.{method_name} has no body param"
    annotation = hints["body"]

    # ``RequestBody[T]`` resolves to a ``Union[T, Mapping[str, Any]]``.
    # ``get_type_hints`` returns it as ``typing.Union`` so we can introspect
    # the args directly.  Optional bodies (``RequestBody[T] | None``) carry
    # an extra ``NoneType`` arm.
    args = getattr(annotation, "__args__", ())
    assert args, (
        f"{resource_cls.__name__}.{method_name} body annotation is not a Union; "
        f"got {annotation!r}"
    )

    arg_names = {getattr(a, "__name__", str(a)) for a in args}
    # Mapping[str, Any] becomes typing.Mapping after ``get_type_hints``; its
    # origin is collections.abc.Mapping.  We accept either spelling.
    has_mapping = any(getattr(a, "__origin__", None) is Mapping for a in args)
    assert has_mapping, (
        f"{resource_cls.__name__}.{method_name} body should accept "
        f"Mapping[str, Any] for dict ergonomics; got args {arg_names}"
    )
    assert expected_model in arg_names, (
        f"{resource_cls.__name__}.{method_name} body should also accept "
        f"the typed {expected_model}; got args {arg_names}"
    )


# ---------- 4. Hand-written paths exist in the spec ----------


# Paths the SDK calls that aren't bound to a single resource method we want
# to enumerate above.  These are the substring matchers we use to assert the
# path appears in the spec at all (the SDK templates ``{id}`` etc. by hand,
# so we check the leading segments).
SDK_PATH_PREFIXES: list[str] = [
    "/api/v1/monitors",
    "/api/v1/incidents",
    "/api/v1/alert-channels",
    "/api/v1/notification-policies",
    "/api/v1/environments",
    "/api/v1/secrets",
    "/api/v1/tags",
    "/api/v1/resource-groups",
    "/api/v1/webhooks",
    "/api/v1/api-keys",
    "/api/v1/deploy/lock",
    "/api/v1/status-pages",
    "/api/v1/service-subscriptions",
]


@pytest.mark.parametrize("prefix", SDK_PATH_PREFIXES)
def test_sdk_path_prefix_in_spec(prefix: str, paths: dict[str, Any]) -> None:
    """Every top-level path the SDK hits must exist in the spec.

    Catches the case where the API renames an endpoint family (e.g.
    ``/v1/monitors`` → ``/v2/monitors``) and the SDK still calls the old
    one.  ``spec-check.yml`` would not catch this because the spec still
    parses cleanly.
    """
    assert any(p.startswith(prefix) for p in paths), (
        f"No spec path starts with {prefix}.  Either the API was renamed "
        "(update the SDK resources) or this prefix should be removed from "
        "SDK_PATH_PREFIXES."
    )
