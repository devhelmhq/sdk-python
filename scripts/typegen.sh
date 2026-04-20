#!/usr/bin/env bash
#
# Regenerate Pydantic models from the vendored OpenAPI spec.
#
# Uses @devhelm/openapi-tools for preprocessing (shared with all surfaces),
# then runs datamodel-codegen for Pydantic model generation.
#
# Preprocessing resolution order:
#   1. $OPENAPI_TOOLS env var (explicit override)
#   2. Local monorepo sibling (../mini/packages/openapi-tools)
#   3. npx from npm (CI / standalone)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT="$ROOT_DIR/docs/openapi/monitoring-api.json"
PREPROCESSED="$ROOT_DIR/.openapi-preprocessed.json"
OUTPUT="$ROOT_DIR/src/devhelm/_generated.py"

if [[ ! -f "$INPUT" ]]; then
  echo "error: OpenAPI spec not found at $INPUT" >&2
  exit 1
fi

resolve_openapi_tools() {
  if [[ -n "${OPENAPI_TOOLS:-}" ]]; then
    echo "$OPENAPI_TOOLS"
    return
  fi
  local local_cli="$ROOT_DIR/../mini/packages/openapi-tools/dist/cli.js"
  if [[ -f "$local_cli" ]]; then
    echo "node $local_cli"
    return
  fi
  echo "npx --yes --package=@devhelm/openapi-tools devhelm-openapi"
}

TOOLS_CMD=$(resolve_openapi_tools)

echo "=> Preprocessing OpenAPI spec (via @devhelm/openapi-tools)..."
$TOOLS_CMD preprocess "$INPUT" "$PREPROCESSED"

echo "=> Generating Pydantic models from preprocessed spec..."

uv run datamodel-codegen \
  --input "$PREPROCESSED" \
  --output "$OUTPUT" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.11 \
  --use-annotated \
  --field-constraints \
  --snake-case-field \
  --input-file-type openapi \
  --formatters ruff-format

rm -f "$PREPROCESSED"
echo "=> Generated: $OUTPUT"
