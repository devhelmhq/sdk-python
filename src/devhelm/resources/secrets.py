from __future__ import annotations

import httpx

from devhelm._generated import CreateSecretRequest, SecretDto, UpdateSecretRequest
from devhelm._http import api_delete, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class Secrets:
    """Encrypted secrets for monitor auth."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[SecretDto]:
        """List all secrets (metadata only, not values)."""
        return fetch_all_pages(self._client, "/api/v1/secrets", SecretDto)

    def list_page(self, page: int, size: int) -> Page[SecretDto]:
        """List secrets with manual page control."""
        return fetch_page(self._client, "/api/v1/secrets", SecretDto, page, size)

    def create(self, body: CreateSecretRequest) -> SecretDto:
        """Create a secret."""
        body = validate_request(CreateSecretRequest, body, "secrets.create")
        return parse_single(
            SecretDto,
            api_post(self._client, "/api/v1/secrets", body),
            "POST /api/v1/secrets",
        )

    def update(self, key: str, body: UpdateSecretRequest) -> SecretDto:
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
