#!/usr/bin/env bash
set -Eeuo pipefail

MODE=""
BUNDLE_DIR=""
START_SERVICES=false
TARGET="/home/nvidia/AEC_Demo_Portable"

usage() {
  cat <<'EOF'
Verify an AEC portable offline bundle or an installed offline deployment.

Usage:
  ./verify-portable-offline.sh --bundle DIRECTORY
  ./scripts/verify-portable-offline.sh --installed [--start-services]

Options:
  --bundle DIRECTORY  Verify the expanded bundle manifest and SHA256SUMS.
  --installed         Verify the installation under
                      /home/nvidia/AEC_Demo_Portable.
  --start-services    With --installed, restart GUI services and run the full
                      portable preflight. Requires an active desktop session.
  -h, --help          Show this help.

The installed verification performs no internet access. It checks only local
files, executables, CUDA availability, localhost Ollama, and optionally the
local FreeCAD/Blender/ComfyUI services.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle)
      [[ $# -ge 2 ]] || { echo "Missing value for --bundle" >&2; exit 2; }
      [[ -z "$MODE" ]] || { echo "Choose only one verification mode" >&2; exit 2; }
      MODE="bundle"
      BUNDLE_DIR="$2"
      shift 2
      ;;
    --installed)
      [[ -z "$MODE" ]] || { echo "Choose only one verification mode" >&2; exit 2; }
      MODE="installed"
      shift
      ;;
    --start-services)
      START_SERVICES=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$MODE" ]] || {
  usage >&2
  exit 2
}
if [[ "$MODE" == "bundle" && "$START_SERVICES" == true ]]; then
  echo "--start-services is valid only with --installed" >&2
  exit 2
fi

verify_manifest() {
  local manifest=$1
  python3 - "$manifest" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
if data.get("format") != "aec-portable-offline-v1":
    raise SystemExit(f"Unsupported offline manifest format: {data.get('format')!r}")
platform = data.get("source_platform", {})
if platform.get("os") != "ubuntu" or platform.get("version") != "24.04":
    raise SystemExit(f"Unsupported source platform in manifest: {platform!r}")
if platform.get("architecture") != "arm64":
    raise SystemExit(f"Unsupported source architecture in manifest: {platform!r}")
target = data.get("target", {})
if target.get("repository") != "/home/nvidia/AEC_Demo_Portable":
    raise SystemExit(f"Unexpected target repository: {target!r}")
ollama = data.get("ollama", {})
default_model = ollama.get("default_model")
models = ollama.get("models") or []
if not default_model or default_model not in models:
    raise SystemExit("Manifest default Ollama model is missing from its model list")
print(f"OFFLINE_MANIFEST_OK={path}")
print(f"OFFLINE_SOURCE_COMMIT={data.get('source_commit', '')}")
print(f"OFFLINE_DEFAULT_MODEL={default_model}")
for model in models:
    print(f"OFFLINE_INCLUDED_MODEL={model}")
PY
}

if [[ "$MODE" == "bundle" ]]; then
  BUNDLE_DIR="$(cd -- "$BUNDLE_DIR" && pwd)"
  [[ -f "$BUNDLE_DIR/offline-manifest.json" ]] || {
    echo "Bundle manifest is missing: $BUNDLE_DIR/offline-manifest.json" >&2
    exit 1
  }
  [[ -f "$BUNDLE_DIR/SHA256SUMS" ]] || {
    echo "Bundle checksums are missing: $BUNDLE_DIR/SHA256SUMS" >&2
    exit 1
  }
  verify_manifest "$BUNDLE_DIR/offline-manifest.json"
  echo "OFFLINE_BUNDLE_CHECKSUM_VERIFY_BEGIN=$BUNDLE_DIR"
  (
    cd "$BUNDLE_DIR"
    sha256sum -c SHA256SUMS
  )
  echo "OFFLINE_BUNDLE_VERIFY_OK=$BUNDLE_DIR"
  exit 0
fi

if [[ "$(dpkg --print-architecture)" != "arm64" ]]; then
  echo "Installed verification requires ARM64" >&2
  exit 1
fi
. /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
  echo "Installed verification requires Ubuntu 24.04" >&2
  exit 1
fi
if [[ "$HOME" != "/home/nvidia" ]]; then
  echo "Installed verification requires user nvidia and home /home/nvidia" >&2
  exit 1
fi

required_paths=(
  "$TARGET/offline-manifest.json"
  "$TARGET/config/runtime.env"
  "$TARGET/scripts/blender-portable.sh"
  "$TARGET/scripts/run-freecad-mcp.sh"
  "$TARGET/scripts/restart-portable-demo.sh"
  "$TARGET/scripts/preflight-portable-demo.sh"
  "$TARGET/runtime/blender/bin/blender"
  "$TARGET/runtime/comfyui/.venv/bin/python"
  "$TARGET/runtime/comfyui/main.py"
  "$TARGET/runtime/cad-tools/bin/python"
  "$TARGET/runtime/freecad/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
  "$TARGET/runtime/freecad-mcp/.venv/bin/freecad-mcp"
  "$TARGET/sample_project/blender_assets/cliff_house_act2_textured_v3.blend"
  "$TARGET/sample_project/rhino_assets/beach_house_02.3dm"
  "$TARGET/assets/hdri/qwantani_puresky_2k.hdr"
  "$TARGET/setup/blender_addons/BlenderMCP_addon.py"
  "$HOME/.local/bin/hermes"
  "/usr/local/bin/ollama"
  "$HOME/.hermes/hermes-agent/venv/bin/python"
  "$HOME/.local/share/uv/python"
  "/usr/local/lib/ollama"
)
for path in "${required_paths[@]}"; do
  [[ -e "$path" ]] || {
    echo "OFFLINE_INSTALLED_PATH_MISSING=$path" >&2
    exit 1
  }
done

ollama_models_dir="/usr/share/ollama/.ollama/models"
sudo test -e "$ollama_models_dir" || {
  echo "OFFLINE_INSTALLED_PATH_MISSING=$ollama_models_dir" >&2
  exit 1
}

verify_manifest "$TARGET/offline-manifest.json"
DEFAULT_MODEL="$(python3 - "$TARGET/offline-manifest.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["ollama"]["default_model"])
PY
)"

echo "OFFLINE_HERMES_VERIFY_BEGIN"
"$HOME/.local/bin/hermes" --version
echo "OFFLINE_OLLAMA_VERIFY_BEGIN model=$DEFAULT_MODEL"
systemctl is-active --quiet ollama || {
  echo "Ollama system service is not active" >&2
  exit 1
}
ollama show "$DEFAULT_MODEL" >/dev/null
ollama list

echo "OFFLINE_BLENDER_VERIFY_BEGIN"
"$TARGET/scripts/blender-portable.sh" --version

echo "OFFLINE_CAD_VERIFY_BEGIN"
"$TARGET/runtime/cad-tools/bin/python" - <<'PY'
import rhino3dm
print("OFFLINE_RHINO3DM_OK", rhino3dm.__version__)
PY

echo "OFFLINE_FREECAD_MCP_VERIFY_BEGIN"
"$TARGET/runtime/freecad-mcp/.venv/bin/python" - <<'PY'
import freecad_mcp
print("OFFLINE_FREECAD_MCP_IMPORT_OK", freecad_mcp.__file__)
PY

echo "OFFLINE_COMFY_VERIFY_BEGIN"
"$TARGET/runtime/comfyui/.venv/bin/python" - <<'PY'
import torch
if not torch.cuda.is_available():
    raise SystemExit("ComfyUI PyTorch cannot access CUDA")
print("OFFLINE_COMFY_CUDA_OK", torch.__version__, torch.cuda.get_device_name(0))
PY

required_comfy_models=(
  "$TARGET/runtime/comfyui/models/diffusion_models/flux/flux-2-klein-9b.safetensors"
  "$TARGET/runtime/comfyui/models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors"
  "$TARGET/runtime/comfyui/models/vae/flux/flux2-vae.safetensors"
)
for path in "${required_comfy_models[@]}"; do
  [[ -s "$path" ]] || {
    echo "OFFLINE_COMFY_MODEL_MISSING=$path" >&2
    exit 1
  }
done

if [[ "$START_SERVICES" == true ]]; then
  echo "OFFLINE_SERVICE_VERIFY_BEGIN"
  "$TARGET/scripts/restart-portable-demo.sh"
  "$TARGET/scripts/preflight-portable-demo.sh"
fi

echo "OFFLINE_INSTALL_VERIFY_OK=$TARGET"
