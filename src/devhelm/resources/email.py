"""Inbound email capture.

``address()`` returns a full mailbox. The first call allocates a DevHelm-owned
host; later calls reuse it and mint a new local-part. ``domains.create(name=)``
is the custom-domain path.
"""

from __future__ import annotations

import builtins
import secrets
from datetime import datetime, timezone
from pathlib import Path

import httpx

from devhelm._generated import (
    CreateEmailDomainRequest,
    EmailDnsRecordDto,
    EmailDomainDto,
    EmailMessageDto,
    InboundEmailAttachment,
    InboundEmailLink,
    InboundOtpCode,
    InjectEmailMessageRequest,
    InjectEmailMessageResponse,
    UpdateEmailDomainRequest,
    WaitEmailMessageRequest,
)
from devhelm._http import api_delete, api_get, api_patch, api_post, path_param
from devhelm._pagination import (
    CursorPage,
    Page,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
)
from devhelm._validation import (
    RequestBody,
    parse_keyed_envelope,
    parse_single,
    validate_request,
)
from devhelm.resources.signed_download import (
    DEFAULT_WAIT_MS,
    fetch_signed,
    wait_timeout_seconds,
    write_download,
)

DOMAINS = "/api/v1/email/domains"


def _domain_segment(name: str) -> str:
    return path_param(name).replace("%2E", ".").replace("%2e", ".")


class Attachment:
    """Attachment metadata plus a download of the signed URL."""

    def __init__(
        self, email: Email, domain: str, message_id: str, dto: InboundEmailAttachment
    ) -> None:
        self._email = email
        self._domain = domain
        self._message_id = message_id
        self.id = dto.id
        self.filename = dto.filename
        self.content_type = dto.content_type
        self.size_bytes = dto.size_bytes

    def bytes(self) -> builtins.bytes:
        _filename, data = self._download()
        return data

    def save(self, path: str | Path) -> Path:
        filename, data = self._download()
        return write_download(data, filename, path)

    def _download(self) -> tuple[str, builtins.bytes]:
        path = (
            f"{DOMAINS}/{_domain_segment(self._domain)}/messages/"
            f"{path_param(self._message_id)}/attachments/{path_param(str(self.id))}"
        )
        signed, data = fetch_signed(self._email._client, path)
        return signed.filename, data


class Message:
    """A captured message. ``otp`` and ``links`` are the extracted fields."""

    def __init__(self, email: Email, domain: str, dto: EmailMessageDto) -> None:
        self._email = email
        self._domain = domain
        self.id = dto.id
        self.domain_id = dto.domain_id
        self.inbox = dto.inbox
        self.received_at = dto.received_at
        self.size_bytes = dto.size_bytes
        self.from_ = dto.from_
        self.to = dto.to
        self.subject = dto.subject
        self.headers = dto.headers
        self.body_preview = dto.body_preview
        self.otp = dto.otp
        self.links = dto.links
        self.sha256 = dto.sha256
        self.attachments = [
            Attachment(email, domain, str(dto.id), item)
            for item in dto.attachments or []
        ]

    def raw(self) -> bytes:
        _signed, data = fetch_signed(self._email._client, self._raw_path())
        return data

    def save(self, path: str | Path) -> Path:
        signed, data = fetch_signed(self._email._client, self._raw_path())
        return write_download(data, signed.filename, path)

    def delete(self) -> None:
        api_delete(self._email._client, self._message_path())

    def list_otp(self) -> list[InboundOtpCode]:
        return fetch_all_pages(
            self._email._client, f"{self._message_path()}/otp", InboundOtpCode
        )

    def list_links(self) -> list[InboundEmailLink]:
        return fetch_all_pages(
            self._email._client, f"{self._message_path()}/links", InboundEmailLink
        )

    def _message_path(self) -> str:
        return (
            f"{DOMAINS}/{_domain_segment(self._domain)}/messages/"
            f"{path_param(str(self.id))}"
        )

    def _raw_path(self) -> str:
        return f"{self._message_path()}/raw"


class AddressMessages:
    def __init__(self, email: Email, domain: str, local_part: str) -> None:
        self._email = email
        self._domain = domain
        self._local_part = local_part

    def list(
        self, *, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[Message]:
        path = f"{DOMAINS}/{_domain_segment(self._domain)}/messages"
        page = fetch_cursor_page(
            self._email._client,
            path,
            EmailMessageDto,
            cursor,
            limit,
            extra_params={"inbox": self._local_part},
        )
        return CursorPage(
            data=[Message(self._email, self._domain, row) for row in page.data],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )

    def get(self, message_id: str) -> Message:
        path = (
            f"{DOMAINS}/{_domain_segment(self._domain)}/messages/"
            f"{path_param(message_id)}"
        )
        row = parse_single(
            EmailMessageDto, api_get(self._email._client, path), f"GET {path}"
        )
        return Message(self._email, self._domain, row)


class Address:
    """A mailbox the test owns: ``local_part@domain``."""

    def __init__(
        self, email: Email, *, address: str, domain: str, local_part: str
    ) -> None:
        self._email = email
        self.email = address
        self.domain = domain
        self.local_part = local_part
        self.messages = AddressMessages(email, domain, local_part)

    def wait(
        self,
        *,
        timeout_ms: int = DEFAULT_WAIT_MS,
        received_after: datetime | None = None,
        subject_contains: str | None = None,
    ) -> Message:
        return self._email.wait(
            to=self.email,
            timeout_ms=timeout_ms,
            received_after=received_after,
            subject_contains=subject_contains,
        )

    def receive(
        self,
        *,
        from_: str,
        subject: str | None = None,
        text: str | None = None,
        html: str | None = None,
        headers: dict[str, list[str]] | None = None,
    ) -> InjectEmailMessageResponse:
        raw: dict[str, object] = {"to": self.email, "from": from_}
        if subject is not None:
            raw["subject"] = subject
        if text is not None:
            raw["text"] = text
        if html is not None:
            raw["html"] = html
        if headers is not None:
            raw["headers"] = headers
        body = validate_request(InjectEmailMessageRequest, raw, "email.receive")
        path = f"{DOMAINS}/{_domain_segment(self.domain)}/messages/inject"
        return parse_single(
            InjectEmailMessageResponse,
            api_post(self._email._client, path, body),
            f"POST {path}",
        )

    def clear(self) -> None:
        api_delete(
            self._email._client,
            f"{DOMAINS}/{_domain_segment(self.domain)}/inboxes/"
            f"{path_param(self.local_part)}",
        )


class Domain:
    def __init__(self, domains: EmailDomains, dto: EmailDomainDto) -> None:
        self._domains = domains
        self.id = dto.id
        self.name = dto.name
        self.workspace_id = dto.workspace_id
        self.kind = dto.kind
        self.status = dto.status
        self.mx_verified = dto.mx_verified
        self.verification_token = dto.verification_token
        self.verification_error = dto.verification_error
        self.verified_at = dto.verified_at
        self.dns_records: list[EmailDnsRecordDto] = dto.dns_records
        self.created_at = dto.created_at
        self.updated_at = dto.updated_at

    def verify(self) -> Domain:
        return self._domains.verify(self.name)

    def update(self, body: RequestBody[UpdateEmailDomainRequest]) -> Domain:
        return self._domains.update(self.name, body)

    def delete(self) -> None:
        self._domains.delete(self.name)


class EmailDomains:
    def __init__(self, email: Email) -> None:
        self._email = email

    def list(self) -> list[Domain]:
        rows = fetch_all_pages(self._email._client, DOMAINS, EmailDomainDto)
        return [Domain(self, row) for row in rows]

    def list_page(self, page: int, size: int) -> Page[Domain]:
        result = fetch_page(self._email._client, DOMAINS, EmailDomainDto, page, size)
        return Page(
            data=[Domain(self, row) for row in result.data],
            has_next=result.has_next,
            has_prev=result.has_prev,
            total_elements=result.total_elements,
            total_pages=result.total_pages,
            next_cursor=result.next_cursor,
        )

    def get(self, name: str) -> Domain:
        path = f"{DOMAINS}/{_domain_segment(name)}"
        row = parse_single(
            EmailDomainDto, api_get(self._email._client, path), f"GET {path}"
        )
        return Domain(self, row)

    def create(self, *, name: str | None = None) -> Domain:
        raw: dict[str, object] = {"kind": "custom", "name": name} if name else {}
        body = validate_request(CreateEmailDomainRequest, raw, "email.domains.create")
        row = parse_single(
            EmailDomainDto,
            api_post(self._email._client, DOMAINS, body),
            f"POST {DOMAINS}",
        )
        return Domain(self, row)

    def update(self, name: str, body: RequestBody[UpdateEmailDomainRequest]) -> Domain:
        payload = validate_request(
            UpdateEmailDomainRequest, body, "email.domains.update"
        )
        path = f"{DOMAINS}/{_domain_segment(name)}"
        row = parse_single(
            EmailDomainDto,
            api_patch(self._email._client, path, payload),
            f"PATCH {path}",
        )
        return Domain(self, row)

    def verify(self, name: str) -> Domain:
        path = f"{DOMAINS}/{_domain_segment(name)}/verify"
        row = parse_single(
            EmailDomainDto, api_post(self._email._client, path), f"POST {path}"
        )
        return Domain(self, row)

    def delete(self, name: str) -> None:
        api_delete(self._email._client, f"{DOMAINS}/{_domain_segment(name)}")


class Email:
    """Mailboxes for signup and notification tests."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self.domains = EmailDomains(self)

    def address(
        self, *, label: str | None = None, domain: str | None = None
    ) -> Address:
        host = domain if domain is not None else self._assigned_domain()
        suffix = secrets.token_hex(4)
        local_part = f"{label}-{suffix}" if label else suffix
        return Address(
            self, address=f"{local_part}@{host}", domain=host, local_part=local_part
        )

    def wait(
        self,
        *,
        to: str,
        timeout_ms: int = DEFAULT_WAIT_MS,
        received_after: datetime | None = None,
        subject_contains: str | None = None,
    ) -> Message:
        body = self._wait_body(
            timeout_ms=timeout_ms,
            received_after=received_after,
            subject_contains=subject_contains,
            extra={"to": to},
        )
        path = "/api/v1/email/wait"
        raw = api_post(
            self._client, path, body, timeout=wait_timeout_seconds(timeout_ms)
        )
        message = parse_keyed_envelope(EmailMessageDto, raw, "message", f"POST {path}")
        host = to.rsplit("@", 1)[-1]
        return Message(self, host, message)

    def wait_local_part(
        self,
        local_part: str,
        *,
        domain: str,
        timeout_ms: int = DEFAULT_WAIT_MS,
        received_after: datetime | None = None,
        subject_contains: str | None = None,
    ) -> Message:
        body = self._wait_body(
            timeout_ms=timeout_ms,
            received_after=received_after,
            subject_contains=subject_contains,
            extra={"domain": domain},
        )
        path = f"/api/v1/email/{path_param(local_part)}/wait"
        raw = api_post(
            self._client, path, body, timeout=wait_timeout_seconds(timeout_ms)
        )
        message = parse_keyed_envelope(EmailMessageDto, raw, "message", f"POST {path}")
        return Message(self, domain, message)

    def _assigned_domain(self) -> str:
        for domain in self.domains.list():
            if domain.kind == "assigned" and domain.status == "active":
                return domain.name
        return self.domains.create().name

    def _wait_body(
        self,
        *,
        timeout_ms: int,
        received_after: datetime | None,
        subject_contains: str | None,
        extra: dict[str, str],
    ) -> WaitEmailMessageRequest:
        fields: dict[str, object] = {
            "timeoutMs": timeout_ms,
            "receivedAfter": received_after or datetime.now(timezone.utc),
            **extra,
        }
        if subject_contains is not None:
            fields["subjectContains"] = subject_contains
        return validate_request(WaitEmailMessageRequest, fields, "email.wait")
