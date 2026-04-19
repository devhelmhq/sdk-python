#!/usr/bin/env python3
"""Preprocess the vendored OpenAPI spec before running datamodel-codegen.

Applies structural fixes that code generators need:
1. setRequiredFields — mark non-nullable fields as required
2. pushRequiredIntoAllOf — propagate required into allOf members
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


_REQUEST_PREFIXES = (
    "Create", "Update", "Add", "Acquire", "Resolve", "Reorder",
    "Test", "Change", "Admin", "Bulk", "Monitor",
)


def set_required_fields(spec: dict) -> None:
    schemas = spec.get("components", {}).get("schemas", {})
    for schema_name, schema in schemas.items():
        if schema.get("type") != "object" or "properties" not in schema:
            continue

        if isinstance(schema.get("required"), list):
            is_req = schema_name.endswith("Request") and schema_name.startswith(
                _REQUEST_PREFIXES
            )
            if not is_req:
                for prop, prop_schema in schema.get("properties", {}).items():
                    if prop_schema.get("nullable"):
                        continue
                    if prop in schema["required"]:
                        continue
                    if prop_schema.get("allOf"):
                        continue
                    if "default" in prop_schema:
                        continue
                    schema["required"].append(prop)
            continue

        is_request = schema_name.endswith("Request") and schema_name.startswith(
            _REQUEST_PREFIXES
        )
        if is_request:
            continue

        required = []
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop_schema.get("nullable"):
                continue
            if prop_schema.get("allOf"):
                continue
            if "default" in prop_schema:
                continue
            required.append(prop)
        if required:
            schema["required"] = required


def push_required_into_all_of(spec: dict) -> None:
    schemas = spec.get("components", {}).get("schemas", {})
    for schema in schemas.values():
        if not isinstance(schema.get("required"), list):
            continue
        if not isinstance(schema.get("allOf"), list):
            continue
        for member in schema["allOf"]:
            if "properties" not in member:
                continue
            member_required = [f for f in schema["required"] if f in member["properties"]]
            if member_required:
                existing = member.get("required", [])
                member["required"] = list(set(existing + member_required))



# fix_missing_nullable — REMOVED.
# The root cause (Lombok not copying @Nullable to getters) was fixed in the API
# by adding `jakarta.annotation.Nullable` to lombok.copyableAnnotations. The
# generated OpenAPI spec now correctly marks nullable fields via the existing
# PropertyCustomizer in OpenApiConfig.java. All DTO fields also have explicit
# @Nullable or @NotNull/@NotBlank annotations, enforced by DtoAnnotationTest.


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    spec = json.loads(input_path.read_text())
    set_required_fields(spec)
    push_required_into_all_of(spec)

    output_path.write_text(json.dumps(spec, indent=2))
    print(f"Preprocessed: {input_path} -> {output_path}")


if __name__ == "__main__":
    main()
