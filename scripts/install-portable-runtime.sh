#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/platform-lib.sh
source "$ROOT/scripts/platform-lib.sh"
echo "PORTABLE_INSTALL_PLATFORM arch=$AEC_ARCH freecad=$AEC_FREECAD_APPIMAGE blender=$AEC_BLENDER_ARCHIVE"

"$ROOT/scripts/install-cad-tools.sh"
"$ROOT/scripts/install-freecad-spark.sh"
"$ROOT/scripts/install-hermes-spark.sh"
"$ROOT/scripts/prepare-freecad-mcp-runtime.sh"
"$HOME/.hermes/hermes-agent/venv/bin/python" "$ROOT/scripts/register-hermes-skills.py"
"$ROOT/scripts/install-blender-spark.sh"
"$ROOT/scripts/install-comfy-portable.sh"
cp -n "$ROOT/config/runtime.env.example" "$ROOT/config/runtime.env" 2>/dev/null || true
# Migrate the first portable release's dependency on the previous aec-demo
# checkout while preserving any other local overrides.
if grep -q '/home/nvidia/aec-demo' "$ROOT/config/runtime.env"; then
    sed -i "s|/home/nvidia/aec-demo|$ROOT|g" "$ROOT/config/runtime.env"
    echo "PORTABLE_RUNTIME_CONFIG_MIGRATED=$ROOT/config/runtime.env"
fi
# The checked example names the Spark AppImage. Point the local configuration
# at the AppImage that was actually installed for this architecture.
if ! grep -q "$AEC_FREECAD_APPIMAGE" "$ROOT/config/runtime.env"; then
    sed -i "s|FreeCAD_1\.1\.1-Linux-[a-z0-9_]*-py311\.AppImage|$AEC_FREECAD_APPIMAGE|g" \
        "$ROOT/config/runtime.env"
    echo "PORTABLE_RUNTIME_FREECAD_ARCH_SET=$AEC_FREECAD_APPIMAGE"
fi
# Assign GPUs and pin Ollama. Both are no-ops on a single-GPU Spark.
"$ROOT/scripts/configure-ollama-gpu.sh"
if [[ -n "${AEC_HERMES_MODEL:-}" ]]; then
    sed -i "s|^AEC_HERMES_MODEL=.*|AEC_HERMES_MODEL=$AEC_HERMES_MODEL|" "$ROOT/config/runtime.env"
fi
if [[ -n "${AEC_PORTABLE_OLLAMA_MODEL:-}" ]]; then
    sed -i "s|^AEC_PORTABLE_OLLAMA_MODEL=.*|AEC_PORTABLE_OLLAMA_MODEL=$AEC_PORTABLE_OLLAMA_MODEL|" "$ROOT/config/runtime.env"
fi
"$ROOT/scripts/preflight-portable-demo.sh"
