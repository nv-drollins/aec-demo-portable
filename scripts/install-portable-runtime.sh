#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/install-blender-spark.sh"
"$ROOT/scripts/install-comfy-portable.sh"
cp -n "$ROOT/config/runtime.env.example" "$ROOT/config/runtime.env" 2>/dev/null || true
"$ROOT/scripts/preflight-portable-demo.sh"
