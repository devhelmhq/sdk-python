#!/usr/bin/env bash
#
# Regenerate Pydantic models from the vendored OpenAPI spec.
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

echo "=> Preprocessing OpenAPI spec..."
python3 "$SCRIPT_DIR/preprocess_spec.py" "$INPUT" "$PREPROCESSED"

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
