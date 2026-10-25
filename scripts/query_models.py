#!/usr/bin/env python3
"""Add a request model per list endpoint's query parameters to the spec.

The API declares list filters as flat query parameters (doc 42 W0-1), and
datamodel-code-generator only generates ``components.schemas``. This pass
copies the query parameters of the operations below into a component schema
so the SDK validates filters with a generated ``*Params`` model (strict:
``extra='forbid'``, see inject_strict_config.py) instead of hand-written
kwargs. Run on the preprocessed spec, before code generation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# operationId -> generated model name
QUERY_MODELS = {
    "listRuns": "RunListParams",
    "listRunCases": "RunCaseListParams",
    "getRunConsoleRaw": "RunConsoleParams",
    "listRunNetwork": "RunNetworkParams",
}


def main() -> int:
    path = Path(sys.argv[1])
    spec = json.loads(path.read_text())
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    found: set[str] = set()
    for ops in spec.get("paths", {}).values():
        for op in ops.values():
            if not isinstance(op, dict):
                continue
            name = QUERY_MODELS.get(op.get("operationId", ""))
            if name is None:
                continue
            found.add(op["operationId"])
            props: dict[str, object] = {}
            required: list[str] = []
            for param in op.get("parameters", []):
                if param.get("in") != "query":
                    continue
                schema = dict(param.get("schema", {}))
                if "description" in param:
                    schema.setdefault("description", param["description"])
                props[param["name"]] = schema
                if param.get("required"):
                    required.append(param["name"])
            model: dict[str, object] = {"type": "object", "properties": props}
            if required:
                model["required"] = required
            schemas[name] = model
    missing = sorted(set(QUERY_MODELS) - found)
    if missing:
        print(f"query_models: operations not in spec: {missing}", file=sys.stderr)
        return 1
    path.write_text(json.dumps(spec, indent=2))
    print(f"query_models: added {len(found)} query model(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
