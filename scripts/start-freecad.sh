#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FREECAD="${AEC_PORTABLE_FREECAD_EXE:-$ROOT/runtime/freecad/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage}"

export DISPLAY="${AEC_PORTABLE_DISPLAY:-${DISPLAY:-:1}}"
export XAUTHORITY="${AEC_PORTABLE_XAUTHORITY:-${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

if [[ ! -x "$FREECAD" ]]; then
    echo "FreeCAD executable is missing: $FREECAD" >&2
    echo "Run $ROOT/scripts/install-portable-runtime.sh and retry." >&2
    exit 1
fi

"$ROOT/scripts/repair-freecad-mcp-links.sh"

if pgrep -x freecad >/dev/null; then
    if "$ROOT/scripts/check-freecad-rpc.py" >/dev/null 2>&1; then
        echo "FreeCAD is already running and its MCP RPC is healthy."
        exit 0
    fi
    echo "FreeCAD is running, but its MCP RPC is unavailable." >&2
    echo "The add-on links are now correct; close FreeCAD and rerun this launcher." >&2
    exit 1
fi

mkdir -p "$ROOT/logs" "$ROOT/runtime"
nohup "$FREECAD" >"$ROOT/logs/freecad.log" 2>&1 &
echo $! >"$ROOT/runtime/freecad.pid"
echo "Started FreeCAD (PID $(cat "$ROOT/runtime/freecad.pid")) on $DISPLAY"
