from __future__ import annotations

import builtins
from uuid import UUID

from devhelm._async.pagination import fetch_all_pages, fetch_page
from devhelm._async.resources.environments import resolve_environment_id
from devhelm._async.transport import (
    AsyncTransport,
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._generated import (
    CreateSecretRequest,
    SecretDto,
    SecretUsageDto,
    UpdateSecretRequest,
    WriteSecretEnvironmentValueRequest,
)
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class SecretValues:
    """Per-environment secret values. Values are written, never read back."""

    def __init__(self, client: AsyncTransport) -> None:
        self._client = client

    async def _path(self, key: str, environment: str | UUID) -> str:
        env_id = await resolve_environment_id(self._client, environment)
        return f"/api/v1/secrets/{path_param(key)}/environments/{path_param(env_id)}"

    async def set(self, key: str, *, environment: str | UUID, value: str) -> None:
        """Set ``key``'s value in one environment (a slug or id)."""
        body = WriteSecretEnvironmentValueRequest(value=value)
        await api_put(self._client, await self._path(key, environment), body)

    async def delete(self, key: str, *, environment: str | UUID) -> None:
        """Remove ``key``'s value from one environment."""
        await api_delete(self._client, await self._path(key, environment))


class Secrets:
    """Encrypted secrets for monitor auth."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)
        self.values = SecretValues(self._client)

    async def list(
        self, *, environment: str | UUID | None = None
    ) -> builtins.list[SecretDto]:
        """List all secrets (metadata only, never values).

        With ``environment`` (slug or id) each secret carries that
        environment's value stamp.
        """
        params = None
        if environment is not None:
            env_id = await resolve_environment_id(self._client, environment)
            params = {"environmentId": str(env_id)}
        return await fetch_all_pages(
            self._client, "/api/v1/secrets", SecretDto, extra_params=params
        )

    async def list_page(self, page: int, size: int) -> Page[SecretDto]:
        """List secrets with manual page control."""
        return await fetch_page(self._client, "/api/v1/secrets", SecretDto, page, size)

    async def usage(self, key: str) -> SecretUsageDto:
        """Monitors that use this secret."""
        path = f"/api/v1/secrets/{path_param(key)}/usage"
        return parse_single(
            SecretUsageDto, await api_get(self._client, path), f"GET {path}"
        )

    async def create(self, body: RequestBody[CreateSecretRequest]) -> SecretDto:
        """Create a secret."""
        body = validate_request(CreateSecretRequest, body, "secrets.create")
        return parse_single(
            SecretDto,
            await api_post(self._client, "/api/v1/secrets", body),
            "POST /api/v1/secrets",
        )

    async def update(
        self, key: str, body: RequestBody[UpdateSecretRequest]
    ) -> SecretDto:
        """Update a secret by key."""
        body = validate_request(UpdateSecretRequest, body, "secrets.update")
        return parse_single(
            SecretDto,
            await api_put(self._client, f"/api/v1/secrets/{path_param(key)}", body),
            f"PUT /api/v1/secrets/{key}",
        )

    async def delete(self, key: str) -> None:
        """Delete a secret by key."""
        await api_delete(self._client, f"/api/v1/secrets/{path_param(key)}")
