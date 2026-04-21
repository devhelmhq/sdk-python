#!/usr/bin/env bash
#
# Regenerate _generated.py from an arbitrary OpenAPI spec file.
#
# Usage: scripts/regen-from.sh <path-to-spec.json>
#
# This script is the per-artifact entry point used by the spec-evolution
# harness (`mono/tests/surfaces/evolution/`). It MUST be idempotent and MUST
# leave the working tree clean enough that subsequent runs see the new spec.
#
# Behavior:
#   - copies <path-to-spec.json> over docs/openapi/monitoring-api.json
#   - invokes the existing typegen.sh pipeline
#   - prints absolute path to the regenerated _generated.py on stdout
#
# The caller (harness fixture) is responsible for:
#   - backing up the original spec before the first call
#   - restoring it at session teardown
#   - invalidating Python's module cache between runs (via subprocess isolation)
#
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <path-to-spec.json>" >&2
  exit 1
fi

INPUT_SPEC="$1"
if [[ ! -f "$INPUT_SPEC" ]]; then
  echo "error: spec not found at $INPUT_SPEC" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_SPEC="$ROOT_DIR/docs/openapi/monitoring-api.json"
OUTPUT="$ROOT_DIR/src/devhelm/_generated.py"

# Resolve to absolute paths so we can detect the (legitimate) case where the
# caller passes the vendored spec back in directly (e.g. post-session teardown
# in the harness re-regens from the restored baseline). Skipping the copy in
# that case avoids `cp: 'X' and 'X' are identical` failing under set -e.
INPUT_ABS="$(cd "$(dirname "$INPUT_SPEC")" && pwd)/$(basename "$INPUT_SPEC")"
TARGET_ABS="$(cd "$(dirname "$TARGET_SPEC")" && pwd)/$(basename "$TARGET_SPEC")"
if [[ "$INPUT_ABS" != "$TARGET_ABS" ]]; then
  cp "$INPUT_SPEC" "$TARGET_SPEC"
fi

"$SCRIPT_DIR/typegen.sh" >&2

echo "$OUTPUT"
