#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/install-freecad-spark.sh"
"$ROOT/scripts/install-blender-spark.sh"
"$ROOT/scripts/install-comfy-portable.sh"
cp -n "$ROOT/config/runtime.env.example" "$ROOT/config/runtime.env" 2>/dev/null || true
# Migrate the first portable release's dependency on the previous aec-demo
# checkout while preserving any other local overrides.
if grep -q '/home/nvidia/aec-demo' "$ROOT/config/runtime.env"; then
    sed -i "s|/home/nvidia/aec-demo|$ROOT|g" "$ROOT/config/runtime.env"
    echo "PORTABLE_RUNTIME_CONFIG_MIGRATED=$ROOT/config/runtime.env"
fi
"$ROOT/scripts/preflight-portable-demo.sh"
