# Generated from src/devhelm/_async/resources/bundles.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Code bundles: upload a check's files and get the digest a revision uses.

See ``devhelm._bundle`` for the three ``code`` forms, the bundle root and the
default include set. The server resolves the import closure; the SDK checks
that the ``uploadDigest`` it gets back matches the files it sent.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from devhelm._bundle import CodeInput, CollectedBundle, collect
from devhelm._errors import client_error
from devhelm._generated import (
    BundleCheckResultDto,
    BundleDto,
    CodeSource,
    CreateBundleRequest,
    MonitorCodeSpec,
)
from devhelm._sync.transport import Client, api_post, api_post_bytes, as_transport
from devhelm._validation import RequestValue, parse_single, validate_request

_PATH = "/api/v1/bundles"


def upload_collected(
    client: Client, bundle: CollectedBundle, *, runtime_id: str | None = None
) -> BundleDto:
    """``POST /bundles`` as JSON when every file is UTF-8 text, else as a zip."""
    text = bundle.as_text()
    if text is not None:
        fields: dict[str, RequestValue] = {
            "files": text,
            "entrypoint": bundle.entrypoint,
            "runtimeId": runtime_id,
        }
        if bundle.include:
            # Files nothing imports that the closure must keep.
            fields["include"] = list(bundle.include)
        body = validate_request(CreateBundleRequest, fields, "bundles.create")
        raw = api_post(client, _PATH, body)
    else:
        raw = api_post_bytes(
            client,
            _PATH,
            bundle.as_zip(),
            "application/zip",
            params={
                "entrypoint": bundle.entrypoint,
                "runtimeId": runtime_id,
                "include": list(bundle.include) or None,
            },
        )
    uploaded = parse_single(BundleDto, raw, f"POST {_PATH}")
    if uploaded.upload_digest != bundle.digest:
        raise client_error(
            "validation",
            "BUNDLE_DIGEST_MISMATCH",
            f"The server hashed the uploaded files as {uploaded.upload_digest}, "
            f"but they hash to {bundle.digest} here. Nothing was created.",
            details={"local": bundle.digest, "server": uploaded.upload_digest},
        )
    return uploaded


def code_spec(
    client: Client,
    code: CodeInput | MonitorCodeSpec,
    *,
    root: str | os.PathLike[str] | None = None,
    runtime_id: str | None = None,
    source: CodeSource | None = None,
) -> MonitorCodeSpec:
    """Turn any ``code`` form into the ``{bundle, entrypoint, source}`` spec.

    A ``MonitorCodeSpec`` for an already uploaded bundle passes through.
    """
    if isinstance(code, MonitorCodeSpec):
        return code
    bundle = collect(code, root=root)
    uploaded = upload_collected(client, bundle, runtime_id=runtime_id)
    return MonitorCodeSpec(
        bundle=uploaded.digest,
        entrypoint=bundle.entrypoint,
        source=source or bundle.source,
    )


class Bundles:
    """Upload check files (``POST /bundles``) and check imports."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def create(
        self,
        code: CodeInput,
        *,
        runtime_id: str | None = None,
        root: str | os.PathLike[str] | None = None,
    ) -> BundleDto:
        """Upload ``code`` and return the bundle (its ``digest`` names the closure).

        ``runtime_id`` picks the runtime whose packages imports are checked
        against; omit it for the newest runtime that can run.
        """
        bundle = collect(code, root=root)
        return upload_collected(self._client, bundle, runtime_id=runtime_id)

    def check(
        self,
        files: Mapping[str, str],
        *,
        entrypoint: str | None = None,
        runtime_id: str | None = None,
    ) -> BundleCheckResultDto:
        """Report every import problem in ``files`` without storing anything."""
        body = CreateBundleRequest(
            files=dict(files), entrypoint=entrypoint, runtime_id=runtime_id
        )
        return parse_single(
            BundleCheckResultDto,
            api_post(self._client, f"{_PATH}/check", body),
            f"POST {_PATH}/check",
        )
