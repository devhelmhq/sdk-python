# Generated from src/devhelm/_async/resources/environments.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from uuid import UUID

from devhelm._generated import (
    CreateEnvironmentRequest,
    EnvironmentDto,
    UpdateEnvironmentRequest,
)
from devhelm._pages import Page
from devhelm._sync.pagination import fetch_all_pages, fetch_page
from devhelm._sync.transport import (
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class Environments:
    """Environment grouping (prod, staging, etc.)."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def list(self) -> list[EnvironmentDto]:
        """List all environments."""
        return fetch_all_pages(self._client, "/api/v1/environments", EnvironmentDto)

    def list_page(self, page: int, size: int) -> Page[EnvironmentDto]:
        """List environments with manual page control."""
        return fetch_page(
            self._client, "/api/v1/environments", EnvironmentDto, page, size
        )

    def get(self, slug: str) -> EnvironmentDto:
        """Get an environment by slug."""
        return parse_single(
            EnvironmentDto,
            api_get(self._client, f"/api/v1/environments/{path_param(slug)}"),
            f"GET /api/v1/environments/{slug}",
        )

    def create(self, body: RequestBody[CreateEnvironmentRequest]) -> EnvironmentDto:
        """Create an environment."""
        body = validate_request(CreateEnvironmentRequest, body, "environments.create")
        return parse_single(
            EnvironmentDto,
            api_post(self._client, "/api/v1/environments", body),
            "POST /api/v1/environments",
        )

    def update(
        self, slug: str, body: RequestBody[UpdateEnvironmentRequest]
    ) -> EnvironmentDto:
        """Update an environment."""
        body = validate_request(UpdateEnvironmentRequest, body, "environments.update")
        return parse_single(
            EnvironmentDto,
            api_put(self._client, f"/api/v1/environments/{path_param(slug)}", body),
            f"PUT /api/v1/environments/{slug}",
        )

    def delete(self, slug: str) -> None:
        """Delete an environment."""
        api_delete(self._client, f"/api/v1/environments/{path_param(slug)}")


def _looks_like_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def resolve_environment_id(client: Client, environment: str | UUID) -> UUID:
    """Resolve ``environment`` (a slug or an id) to the environment id.

    An id passes through without a call; a slug is looked up with
    ``GET /api/v1/environments/{slug}``.
    """
    if isinstance(environment, UUID):
        return environment
    if _looks_like_uuid(environment):
        return UUID(environment)
    path = f"/api/v1/environments/{path_param(environment)}"
    found = parse_single(EnvironmentDto, api_get(client, path), f"GET {path}")
    return found.id
