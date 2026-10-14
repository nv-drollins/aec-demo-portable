#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_ROOT="${AEC_PORTABLE_BLENDER_ROOT:-$ROOT/runtime/blender}"

# The community ARM64 build nests the binary under bin/; the official upstream
# x86_64 build puts it at the archive root. Accept either layout so the same
# launcher works on DGX Spark and on an amd64 workstation.
BLENDER_BIN=""
for candidate in "$BLENDER_ROOT/bin/blender" "$BLENDER_ROOT/blender"; do
    if [[ -x "$candidate" ]]; then
        BLENDER_BIN="$candidate"
        break
    fi
done

if [[ -z "$BLENDER_BIN" ]]; then
    echo "BLENDER_PORTABLE_MISSING=$BLENDER_ROOT/{bin/,}blender" >&2
    exit 2
fi

export LD_LIBRARY_PATH="$BLENDER_ROOT/libExt${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$BLENDER_BIN" "$@"
