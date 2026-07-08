#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_ROOT="$ROOT/runtime/freecad-mcp"
MCP_BIN="$MCP_ROOT/.venv/bin/freecad-mcp"

[[ -x "$MCP_BIN" ]] || {
  echo "FreeCAD MCP runtime is missing: $MCP_BIN" >&2
  echo "Run $ROOT/scripts/prepare-freecad-mcp-runtime.sh while online." >&2
  exit 1
}

cd "$MCP_ROOT"
exec "$MCP_BIN" "$@"
