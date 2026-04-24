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
  --enum-field-as-literal one \
  --use-one-literal-as-default \
  --input-file-type openapi \
  --formatters ruff-format

# Why --enum-field-as-literal=one + --use-one-literal-as-default?
#
# Without these, single-value enums (used as discriminators on sealed unions
# like AuditMetadata.kind) generate as `kind: Kind` where `Kind(StrEnum)` has
# one entry. Pydantic 2.12+ rejects this when the parent is a discriminated
# union: "Model 'X' needs field 'kind' to be of type `Literal`".
#
# These flags make the codegen emit `kind: Literal["..."] = "..."` instead,
# satisfying the discriminator requirement and making the field optional at
# construction (callers don't need to repeat the discriminator value).

# Post-process: inject `model_config = ConfigDict(extra='forbid')` into every
# generated class so that requests with unknown fields and responses with
# unknown fields BOTH fail loudly. Implements P1 + P2 from
# `mini/cowork/design/040-codegen-policies.md`.
echo "=> Injecting strict-fail config (extra='forbid') into generated models..."
uv run python "$SCRIPT_DIR/inject_strict_config.py" "$OUTPUT"

# Re-format after injection so the file stays ruff-clean. Non-fatal so the
# spec-evolution harness keeps moving even if ruff is misconfigured in the
# child env (e.g. inherited VIRTUAL_ENV from a pytest parent).
uv run ruff format --quiet "$OUTPUT" || echo "warning: ruff format skipped" >&2

rm -f "$PREPROCESSED"
echo "=> Generated: $OUTPUT"
