#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_ROOT="${AEC_PORTABLE_BLENDER_ROOT:-$ROOT/runtime/blender}"
BLENDER_BIN="$BLENDER_ROOT/bin/blender"

if [[ ! -x "$BLENDER_BIN" ]]; then
    echo "BLENDER_PORTABLE_MISSING=$BLENDER_BIN" >&2
    exit 2
fi

export LD_LIBRARY_PATH="$BLENDER_ROOT/libExt${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$BLENDER_BIN" "$@"
