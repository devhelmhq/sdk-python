# Generated from src/devhelm/_async/resources/secrets.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

import builtins
from uuid import UUID

from devhelm._generated import (
    CreateSecretRequest,
    SecretDto,
    SecretUsageDto,
    UpdateSecretRequest,
    WriteSecretEnvironmentValueRequest,
)
from devhelm._pages import Page
from devhelm._sync.pagination import fetch_all_pages, fetch_page
from devhelm._sync.transport import (
    Client,
    Transport,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request
from devhelm.resources.environments import resolve_environment_id


class SecretValues:
    """Per-environment secret values. Values are written, never read back."""

    def __init__(self, client: Transport) -> None:
        self._client = client

    def _path(self, key: str, environment: str | UUID) -> str:
        env_id = resolve_environment_id(self._client, environment)
        return f"/api/v1/secrets/{path_param(key)}/environments/{path_param(env_id)}"

    def set(self, key: str, *, environment: str | UUID, value: str) -> None:
        """Set ``key``'s value in one environment (a slug or id)."""
        body = WriteSecretEnvironmentValueRequest(value=value)
        api_put(self._client, self._path(key, environment), body)

    def delete(self, key: str, *, environment: str | UUID) -> None:
        """Remove ``key``'s value from one environment."""
        api_delete(self._client, self._path(key, environment))


class Secrets:
    """Encrypted secrets for monitor auth."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)
        self.values = SecretValues(self._client)

    def list(
        self, *, environment: str | UUID | None = None
    ) -> builtins.list[SecretDto]:
        """List all secrets (metadata only, never values).

        With ``environment`` (slug or id) each secret carries that
        environment's value stamp.
        """
        params = None
        if environment is not None:
            env_id = resolve_environment_id(self._client, environment)
            params = {"environmentId": str(env_id)}
        return fetch_all_pages(
            self._client, "/api/v1/secrets", SecretDto, extra_params=params
        )

    def list_page(self, page: int, size: int) -> Page[SecretDto]:
        """List secrets with manual page control."""
        return fetch_page(self._client, "/api/v1/secrets", SecretDto, page, size)

    def usage(self, key: str) -> SecretUsageDto:
        """Monitors that use this secret."""
        path = f"/api/v1/secrets/{path_param(key)}/usage"
        return parse_single(SecretUsageDto, api_get(self._client, path), f"GET {path}")

    def create(self, body: RequestBody[CreateSecretRequest]) -> SecretDto:
        """Create a secret."""
        body = validate_request(CreateSecretRequest, body, "secrets.create")
        return parse_single(
            SecretDto,
            api_post(self._client, "/api/v1/secrets", body),
            "POST /api/v1/secrets",
        )

    def update(self, key: str, body: RequestBody[UpdateSecretRequest]) -> SecretDto:
        """Update a secret by key."""
        body = validate_request(UpdateSecretRequest, body, "secrets.update")
        return parse_single(
            SecretDto,
            api_put(self._client, f"/api/v1/secrets/{path_param(key)}", body),
            f"PUT /api/v1/secrets/{key}",
        )

    def delete(self, key: str) -> None:
        """Delete a secret by key."""
        api_delete(self._client, f"/api/v1/secrets/{path_param(key)}")
