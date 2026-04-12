#!/usr/bin/env bash
#
# Regenerate Pydantic models from the vendored OpenAPI spec.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT="$ROOT_DIR/docs/openapi/monitoring-api.json"
OUTPUT="$ROOT_DIR/src/devhelm/_generated.py"

if [[ ! -f "$INPUT" ]]; then
  echo "error: OpenAPI spec not found at $INPUT" >&2
  exit 1
fi

echo "=> Generating Pydantic models from OpenAPI spec..."

uv run datamodel-codegen \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.11 \
  --use-annotated \
  --field-constraints \
  --snake-case-field \
  --input-file-type openapi \
  --formatters ruff-format

echo "=> Generated: $OUTPUT"
