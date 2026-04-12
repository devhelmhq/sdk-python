#!/usr/bin/env python3
"""Thin test harness invoked by monorepo pytest surface tests.

Usage: python tests/run_sdk.py <resource> <action> [args...] --token=<t> --api-url=<u>

Prints JSON to stdout on success, exits non-zero with error JSON on stderr.
This mirrors the CLI's `--output json` behavior so pytest tests can parse results uniformly.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from devhelm import Devhelm, DevhelmError
from devhelm._pagination import CursorPage, Page


def extract_flag(args: list[str], name: str) -> str | None:
    prefix = f"--{name}="
    for i, arg in enumerate(args):
        if arg.startswith(prefix):
            val = arg[len(prefix) :]
            args.pop(i)
            return val
    return None


def to_json(obj: Any) -> Any:
    """Convert SDK result to JSON-serializable dict."""
    if obj is None:
        return None
    if isinstance(obj, Page):
        return {"data": obj.data, "hasNext": obj.has_next, "hasPrev": obj.has_prev}
    if isinstance(obj, CursorPage):
        return {
            "data": obj.data,
            "nextCursor": obj.next_cursor,
            "hasMore": obj.has_more,
        }
    return obj


def run(client: Devhelm, resource: str, action: str, rest: list[str]) -> Any:  # noqa: C901
    op = f"{resource}.{action}"

    # -- Monitors --
    if op == "monitors.list":
        return client.monitors.list()
    if op == "monitors.get":
        return client.monitors.get(rest[0])
    if op == "monitors.create":
        return client.monitors.create(json.loads(rest[0]))
    if op == "monitors.update":
        return client.monitors.update(rest[0], json.loads(rest[1]))
    if op == "monitors.delete":
        client.monitors.delete(rest[0])
        return None
    if op == "monitors.pause":
        return client.monitors.pause(rest[0])
    if op == "monitors.resume":
        return client.monitors.resume(rest[0])
    if op == "monitors.test":
        return client.monitors.test(rest[0])
    if op == "monitors.results":
        opts = json.loads(rest[1]) if len(rest) > 1 and rest[1] else {}
        return client.monitors.results(rest[0], **opts)
    if op == "monitors.versions":
        opts = json.loads(rest[1]) if len(rest) > 1 and rest[1] else {}
        return client.monitors.versions(rest[0], **opts)

    # -- Incidents --
    if op == "incidents.list":
        return client.incidents.list()
    if op == "incidents.get":
        return client.incidents.get(rest[0])
    if op == "incidents.create":
        return client.incidents.create(json.loads(rest[0]))
    if op == "incidents.resolve":
        msg = rest[1] if len(rest) > 1 else None
        return client.incidents.resolve(rest[0], msg)
    if op == "incidents.delete":
        client.incidents.delete(rest[0])
        return None

    # -- Alert Channels --
    if op == "alert-channels.list":
        return client.alert_channels.list()
    if op == "alert-channels.get":
        return client.alert_channels.get(rest[0])
    if op == "alert-channels.create":
        return client.alert_channels.create(json.loads(rest[0]))
    if op == "alert-channels.update":
        return client.alert_channels.update(rest[0], json.loads(rest[1]))
    if op == "alert-channels.delete":
        client.alert_channels.delete(rest[0])
        return None
    if op == "alert-channels.test":
        return client.alert_channels.test(rest[0])

    # -- Notification Policies --
    if op == "notification-policies.list":
        return client.notification_policies.list()
    if op == "notification-policies.get":
        return client.notification_policies.get(rest[0])
    if op == "notification-policies.create":
        return client.notification_policies.create(json.loads(rest[0]))
    if op == "notification-policies.update":
        return client.notification_policies.update(rest[0], json.loads(rest[1]))
    if op == "notification-policies.delete":
        client.notification_policies.delete(rest[0])
        return None
    if op == "notification-policies.test":
        client.notification_policies.test(rest[0])
        return None

    # -- Environments --
    if op == "environments.list":
        return client.environments.list()
    if op == "environments.get":
        return client.environments.get(rest[0])
    if op == "environments.create":
        return client.environments.create(json.loads(rest[0]))
    if op == "environments.update":
        return client.environments.update(rest[0], json.loads(rest[1]))
    if op == "environments.delete":
        client.environments.delete(rest[0])
        return None

    # -- Secrets --
    if op == "secrets.list":
        return client.secrets.list()
    if op == "secrets.create":
        return client.secrets.create(json.loads(rest[0]))
    if op == "secrets.update":
        return client.secrets.update(rest[0], json.loads(rest[1]))
    if op == "secrets.delete":
        client.secrets.delete(rest[0])
        return None

    # -- Tags --
    if op == "tags.list":
        return client.tags.list()
    if op == "tags.get":
        return client.tags.get(rest[0])
    if op == "tags.create":
        return client.tags.create(json.loads(rest[0]))
    if op == "tags.update":
        return client.tags.update(rest[0], json.loads(rest[1]))
    if op == "tags.delete":
        client.tags.delete(rest[0])
        return None

    # -- Resource Groups --
    if op == "resource-groups.list":
        return client.resource_groups.list()
    if op == "resource-groups.get":
        return client.resource_groups.get(rest[0])
    if op == "resource-groups.create":
        return client.resource_groups.create(json.loads(rest[0]))
    if op == "resource-groups.update":
        return client.resource_groups.update(rest[0], json.loads(rest[1]))
    if op == "resource-groups.delete":
        client.resource_groups.delete(rest[0])
        return None
    if op == "resource-groups.add-member":
        return client.resource_groups.add_member(rest[0], json.loads(rest[1]))
    if op == "resource-groups.remove-member":
        client.resource_groups.remove_member(rest[0], rest[1])
        return None

    # -- Webhooks --
    if op == "webhooks.list":
        return client.webhooks.list()
    if op == "webhooks.get":
        return client.webhooks.get(rest[0])
    if op == "webhooks.create":
        return client.webhooks.create(json.loads(rest[0]))
    if op == "webhooks.update":
        return client.webhooks.update(rest[0], json.loads(rest[1]))
    if op == "webhooks.delete":
        client.webhooks.delete(rest[0])
        return None
    if op == "webhooks.test":
        return client.webhooks.test(rest[0])

    # -- API Keys --
    if op == "api-keys.list":
        return client.api_keys.list()
    if op == "api-keys.create":
        return client.api_keys.create(json.loads(rest[0]))
    if op == "api-keys.revoke":
        client.api_keys.revoke(rest[0])
        return None
    if op == "api-keys.delete":
        client.api_keys.delete(rest[0])
        return None

    # -- Dependencies --
    if op == "dependencies.list":
        return client.dependencies.list()
    if op == "dependencies.get":
        return client.dependencies.get(rest[0])
    if op == "dependencies.track":
        return client.dependencies.track(rest[0])
    if op == "dependencies.delete":
        client.dependencies.delete(rest[0])
        return None

    # -- Deploy Lock --
    if op == "deploy-lock.acquire":
        return client.deploy_lock.acquire(json.loads(rest[0]))
    if op == "deploy-lock.current":
        return client.deploy_lock.current()
    if op == "deploy-lock.release":
        client.deploy_lock.release(rest[0])
        return None
    if op == "deploy-lock.force-release":
        client.deploy_lock.force_release()
        return None

    # -- Status --
    if op == "status.overview":
        return client.status.overview()

    sys.stderr.write(json.dumps({"error": f"Unknown operation: {op}"}))
    sys.exit(2)


def main() -> None:
    args = sys.argv[1:]

    token = extract_flag(args, "token") or os.environ.get(
        "DEVHELM_API_TOKEN", "devhelm-dev-token"
    )
    api_url = extract_flag(args, "api-url") or os.environ.get(
        "TEST_API_URL", "http://localhost:8081"
    )
    org_id = extract_flag(args, "org-id") or os.environ.get("DEVHELM_ORG_ID", "1")
    workspace_id = extract_flag(args, "workspace-id") or os.environ.get(
        "DEVHELM_WORKSPACE_ID", "1"
    )

    if len(args) < 2:
        sys.stderr.write(
            json.dumps({"error": "Usage: run_sdk.py <resource> <action> [args...]"})
        )
        sys.exit(2)

    resource, action, *rest = args

    client = Devhelm(
        token=token, base_url=api_url, org_id=org_id, workspace_id=workspace_id
    )

    try:
        result = run(client, resource, action, rest)
        result = to_json(result)
        if result is not None:
            sys.stdout.write(json.dumps(result))
    except DevhelmError as err:
        sys.stderr.write(
            json.dumps({"error": err.message, "code": err.code, "status": err.status})
        )
        sys.exit(1)
    except Exception as err:
        sys.stderr.write(
            json.dumps({"error": str(err), "code": "UNKNOWN", "status": 0})
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
