#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_ROOT="$ROOT/runtime/freecad-mcp"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
UV="${UV_BIN:-$HERMES_HOME/bin/uv}"

[[ -d "$MCP_ROOT" ]] || {
  echo "FreeCAD MCP source is missing: $MCP_ROOT" >&2
  exit 1
}
[[ -x "$UV" ]] || {
  echo "uv is missing: $UV" >&2
  echo "Install Hermes before preparing the FreeCAD MCP runtime." >&2
  exit 1
}

"$UV" --directory "$MCP_ROOT" sync --frozen
[[ -x "$MCP_ROOT/.venv/bin/freecad-mcp" ]] || {
  echo "FreeCAD MCP environment was not created: $MCP_ROOT/.venv" >&2
  exit 1
}

echo "FREECAD_MCP_RUNTIME_OK=$MCP_ROOT/.venv"
