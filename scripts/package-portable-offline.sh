#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT=""
COMPRESSION="gzip"
DEFAULT_MODEL=""
CONTEXT_LENGTH="262144"
OLLAMA_MODELS_DIR="${OLLAMA_MODELS_DIR:-/usr/share/ollama/.ollama/models}"
INCLUDE_PROJECTS=true
KEEP_STAGING=false
AUDIT_ONLY=false
STAGING_PARENT="${AEC_OFFLINE_STAGING_PARENT:-$ROOT/transfer}"

APT_PACKAGES=(
  libfuse2t64
  libxcb-cursor0
  libavcodec60
  libavdevice60
  libavformat60
  libavutil58
  libswscale7
  libblosc1
  libfftw3-double3
  libopenexr-3-1-30
  libimath-3-1-29t64
  libosdcpu3.5.0t64
  libosdgpu3.5.0t64
  libpotrace0
  libpugixml1v5
  libpystring0
  libyaml-cpp0.8
)

usage() {
  cat <<'EOF'
Create a self-contained offline deployment archive for the AEC portable demo.

Usage:
  ./scripts/package-portable-offline.sh [options]

Options:
  --output FILE             Archive path. The default is a timestamped file
                            under transfer/.
  --compression gzip|none   Archive compression (default: gzip).
  --default-model MODEL     Ollama model configured for Hermes. Required when
                            more than one model remains in the Ollama store.
  --context-length TOKENS   Ollama context length stored in the manifest
                            (default: 262144).
  --ollama-models-dir DIR   Ollama model store (default:
                            /usr/share/ollama/.ollama/models).
  --without-projects        Exclude projects/recorded_demo checkpoints and
                            fallback final outputs.
  --staging-parent DIR      Directory used for the temporary bundle tree.
  --keep-staging            Preserve the expanded staging tree after packaging.
  --audit-only              Validate and print the bundle inventory without
                            copying, downloading packages, or writing an archive.
  -h, --help                Show this help.

The bundle targets Ubuntu 24.04 ARM64, user nvidia, and installation path
/home/nvidia/AEC_Demo_Portable. It includes the tracked repository, delivered
assets, portable runtime, prepared FreeCAD MCP environment, sanitized Hermes
runtime, Ollama binary/libraries/model store, recursive Ubuntu .deb packages,
checksums, and optional recorded-demo checkpoints.

Before packaging, remove unused Ollama models and stop active model sessions.
No Hermes credentials, conversation history, SSH keys, GPU UUIDs, or local
runtime.env file are included.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || { echo "Missing value for --output" >&2; exit 2; }
      OUTPUT="$2"
      shift 2
      ;;
    --compression)
      [[ $# -ge 2 ]] || { echo "Missing value for --compression" >&2; exit 2; }
      COMPRESSION="$2"
      shift 2
      ;;
    --default-model)
      [[ $# -ge 2 ]] || { echo "Missing value for --default-model" >&2; exit 2; }
      DEFAULT_MODEL="$2"
      shift 2
      ;;
    --context-length)
      [[ $# -ge 2 ]] || { echo "Missing value for --context-length" >&2; exit 2; }
      CONTEXT_LENGTH="$2"
      shift 2
      ;;
    --ollama-models-dir)
      [[ $# -ge 2 ]] || { echo "Missing value for --ollama-models-dir" >&2; exit 2; }
      OLLAMA_MODELS_DIR="$2"
      shift 2
      ;;
    --without-projects)
      INCLUDE_PROJECTS=false
      shift
      ;;
    --staging-parent)
      [[ $# -ge 2 ]] || { echo "Missing value for --staging-parent" >&2; exit 2; }
      STAGING_PARENT="$2"
      shift 2
      ;;
    --keep-staging)
      KEEP_STAGING=true
      shift
      ;;
    --audit-only)
      AUDIT_ONLY=true
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

[[ "$COMPRESSION" == "gzip" || "$COMPRESSION" == "none" ]] || {
  echo "--compression must be gzip or none" >&2
  exit 2
}
[[ "$CONTEXT_LENGTH" =~ ^[1-9][0-9]*$ ]] || {
  echo "--context-length must be a positive integer" >&2
  exit 2
}

required_commands=(
  apt-get
  awk
  dpkg-scanpackages
  gzip
  cp
  df
  du
  find
  git
  python3
  sha256sum
  sort
  stat
  tar
  xargs
)
for command_name in "${required_commands[@]}"; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Required command is missing: $command_name" >&2
    exit 1
  }
done

ARCH="$(dpkg --print-architecture)"
. /etc/os-release
if [[ "$ARCH" != "arm64" || "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
  echo "Unsupported source platform: arch=$ARCH os=${ID:-unknown} version=${VERSION_ID:-unknown}" >&2
  echo "The offline bundle currently targets Ubuntu 24.04 ARM64 only." >&2
  exit 1
fi
if [[ "$HOME" != "/home/nvidia" ]]; then
  echo "Unsupported source home: $HOME" >&2
  echo "Relocatable Python environments require the standard /home/nvidia path." >&2
  exit 1
fi

WORKTREE_STATUS="$(git -C "$ROOT" status --porcelain --untracked-files=normal)"
if [[ -n "$WORKTREE_STATUS" ]]; then
  if [[ "$AUDIT_ONLY" == true ]]; then
    echo "OFFLINE_AUDIT_WARNING=source_tree_has_uncommitted_changes" >&2
  else
    echo "Refusing to package a source tree with uncommitted changes:" >&2
    printf '%s\n' "$WORKTREE_STATUS" >&2
    exit 1
  fi
fi
SOURCE_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"

required_paths=(
  "$ROOT/runtime/blender/bin/blender"
  "$ROOT/runtime/comfyui/.venv/bin/python"
  "$ROOT/runtime/comfyui/main.py"
  "$ROOT/runtime/cad-tools/bin/python"
  "$ROOT/runtime/freecad/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
  "$ROOT/runtime/freecad-mcp/.venv/bin/freecad-mcp"
  "$ROOT/sample_project/blender_assets/cliff_house_act2_textured_v3.blend"
  "$ROOT/sample_project/rhino_assets/beach_house_02.3dm"
  "$ROOT/assets/hdri/qwantani_puresky_2k.hdr"
  "$ROOT/setup/blender_addons/BlenderMCP_addon.py"
  "$HOME/.hermes/bin/uv"
  "$HOME/.hermes/hermes-agent/venv/bin/hermes"
  "$HOME/.local/bin/hermes"
  "$HOME/.local/share/uv/python"
  "/usr/local/bin/ollama"
  "/usr/local/lib/ollama"
  "$OLLAMA_MODELS_DIR"
)
if [[ "$INCLUDE_PROJECTS" == true ]]; then
  required_paths+=("$ROOT/projects/recorded_demo")
fi
for path in "${required_paths[@]}"; do
  [[ -e "$path" ]] || {
    echo "Required offline component is missing: $path" >&2
    exit 1
  }
done

mapfile -t OLLAMA_MODELS < <(ollama list 2>/dev/null | awk 'NR > 1 && NF {print $1}')
if (( ${#OLLAMA_MODELS[@]} == 0 )); then
  echo "No Ollama models are installed in the active service store." >&2
  exit 1
fi
if [[ -z "$DEFAULT_MODEL" ]]; then
  if (( ${#OLLAMA_MODELS[@]} == 1 )); then
    DEFAULT_MODEL="${OLLAMA_MODELS[0]}"
  else
    echo "More than one Ollama model is installed:" >&2
    printf '  %s\n' "${OLLAMA_MODELS[@]}" >&2
    echo "Remove unused models or pass --default-model MODEL." >&2
    exit 2
  fi
fi
MODEL_FOUND=false
for model in "${OLLAMA_MODELS[@]}"; do
  if [[ "$model" == "$DEFAULT_MODEL" ]]; then
    MODEL_FOUND=true
  fi
done
[[ "$MODEL_FOUND" == true ]] || {
  echo "Default model is not installed: $DEFAULT_MODEL" >&2
  printf 'INSTALLED_MODEL=%s\n' "${OLLAMA_MODELS[@]}" >&2
  exit 1
}

echo "OFFLINE_BUNDLE_AUDIT_OK commit=$SOURCE_COMMIT"
echo "SOURCE_PLATFORM=ubuntu-24.04-arm64"
echo "DEFAULT_OLLAMA_MODEL=$DEFAULT_MODEL"
printf 'INCLUDED_OLLAMA_MODEL=%s\n' "${OLLAMA_MODELS[@]}"
echo "INCLUDE_RECORDED_PROJECTS=$INCLUDE_PROJECTS"
du -sh \
  "$ROOT/runtime" \
  "$ROOT/sample_project" \
  "$ROOT/assets" \
  "$ROOT/setup" \
  "$HOME/.hermes/hermes-agent" \
  "$HOME/.local/share/uv/python" \
  "/usr/local/lib/ollama" \
  "$OLLAMA_MODELS_DIR"
if [[ "$INCLUDE_PROJECTS" == true ]]; then
  du -sh "$ROOT/projects/recorded_demo"
fi

if [[ "$AUDIT_ONLY" == true ]]; then
  exit 0
fi

STAMP="$(date -u +%Y%m%d_%H%M%S)"
if [[ -z "$OUTPUT" ]]; then
  if [[ "$COMPRESSION" == "gzip" ]]; then
    OUTPUT="$ROOT/transfer/aec-demo-portable-offline-$STAMP.tar.gz"
  else
    OUTPUT="$ROOT/transfer/aec-demo-portable-offline-$STAMP.tar"
  fi
elif [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PWD/$OUTPUT"
fi
case "$COMPRESSION:$OUTPUT" in
  gzip:*.tar.gz|none:*.tar) ;;
  gzip:*)
    echo "gzip output must end in .tar.gz: $OUTPUT" >&2
    exit 2
    ;;
  none:*)
    echo "uncompressed output must end in .tar: $OUTPUT" >&2
    exit 2
    ;;
esac

mkdir -p "$STAGING_PARENT" "$(dirname "$OUTPUT")"
STAGE_PARENT="$STAGING_PARENT/offline-stage-$STAMP"
BUNDLE_NAME="aec-demo-portable-offline-$STAMP"
BUNDLE="$STAGE_PARENT/$BUNDLE_NAME"
mkdir -p \
  "$BUNDLE/repo" \
  "$BUNDLE/components/hermes/home/.hermes" \
  "$BUNDLE/components/hermes/home/.local/bin" \
  "$BUNDLE/components/hermes/home/.local/share/uv" \
  "$BUNDLE/components/ollama/bin" \
  "$BUNDLE/components/ollama/lib" \
  "$BUNDLE/components/ollama/models" \
  "$BUNDLE/apt/debs"

OLLAMA_WAS_ACTIVE=false
cleanup() {
  local status=$?
  if [[ "$OLLAMA_WAS_ACTIVE" == true ]]; then
    sudo systemctl start ollama >/dev/null 2>&1 || true
  fi
  if [[ "$KEEP_STAGING" != true && -d "$STAGE_PARENT" ]]; then
    rm -rf "$STAGE_PARENT"
  elif [[ -d "$STAGE_PARENT" ]]; then
    echo "OFFLINE_STAGING_PRESERVED=$STAGE_PARENT"
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

payload_bytes=0
for path in runtime sample_project assets setup; do
  size="$(du -sb "$ROOT/$path" | awk '{print $1}')"
  payload_bytes=$((payload_bytes + size))
done
if [[ "$INCLUDE_PROJECTS" == true ]]; then
  size="$(du -sb "$ROOT/projects/recorded_demo" | awk '{print $1}')"
  payload_bytes=$((payload_bytes + size))
fi
for path in "$HOME/.hermes/hermes-agent" "$HOME/.local/share/uv/python" /usr/local/lib/ollama "$OLLAMA_MODELS_DIR"; do
  size="$(sudo du -sb "$path" | awk '{print $1}')"
  payload_bytes=$((payload_bytes + size))
done
available_bytes="$(df --output=avail -B1 "$STAGING_PARENT" | tail -1 | tr -d ' ')"
required_bytes=$((payload_bytes * 2 + 10 * 1024 * 1024 * 1024))
if (( available_bytes < required_bytes )); then
  echo "Insufficient free space for staging plus archive." >&2
  echo "REQUIRED_BYTES=$required_bytes AVAILABLE_BYTES=$available_bytes" >&2
  exit 1
fi

echo "OFFLINE_REPOSITORY_EXPORT_BEGIN commit=$SOURCE_COMMIT"
git -C "$ROOT" archive --format=tar HEAD | tar -xf - -C "$BUNDLE/repo"

echo "OFFLINE_PAYLOAD_COPY_BEGIN"
tar \
  --exclude='runtime/*.pid' \
  --exclude='runtime/comfyui/output/*' \
  --exclude='runtime/comfyui/temp/*' \
  --exclude='runtime/freecad-recovery-archive/*' \
  --exclude='runtime/downloads/*.part' \
  --exclude='runtime/downloads/*.part.*' \
  --exclude='runtime/downloads/*.bad.*' \
  -C "$ROOT" \
  -cf - \
  runtime sample_project assets setup |
  tar -xf - -C "$BUNDLE/repo"
if [[ "$INCLUDE_PROJECTS" == true ]]; then
  tar -C "$ROOT" -cf - projects/recorded_demo | tar -xf - -C "$BUNDLE/repo"
fi

echo "OFFLINE_HERMES_COPY_BEGIN"
tar \
  --exclude='hermes-agent/.git' \
  -C "$HOME/.hermes" \
  -cf - \
  bin hermes-agent |
  tar -xf - -C "$BUNDLE/components/hermes/home/.hermes"
tar -C "$HOME/.local/share/uv" -cf - python |
  tar -xf - -C "$BUNDLE/components/hermes/home/.local/share/uv"

cp -a "$HOME/.local/bin/hermes" "$BUNDLE/components/hermes/home/.local/bin/hermes"

echo "OFFLINE_OLLAMA_COPY_BEGIN"
if systemctl is-active --quiet ollama; then
  OLLAMA_WAS_ACTIVE=true
  sudo systemctl stop ollama
fi
cp -a /usr/local/bin/ollama "$BUNDLE/components/ollama/bin/ollama"
tar -C /usr/local/lib -cf - ollama | tar -xf - -C "$BUNDLE/components/ollama/lib"
sudo tar -C "$OLLAMA_MODELS_DIR" -cf - . |
  tar --no-same-owner -xf - -C "$BUNDLE/components/ollama/models"
if [[ "$OLLAMA_WAS_ACTIVE" == true ]]; then
  sudo systemctl start ollama
  OLLAMA_WAS_ACTIVE=false
fi
printf '%s\n' "${OLLAMA_MODELS[@]}" >"$BUNDLE/components/ollama/model-list.txt"
/usr/local/bin/ollama --version >"$BUNDLE/components/ollama/version.txt" 2>&1 || true

echo "OFFLINE_APT_DOWNLOAD_BEGIN packages=${#APT_PACKAGES[@]}"
APT_STATUS="$STAGE_PARENT/empty-dpkg-status"
: >"$APT_STATUS"
mkdir -p "$BUNDLE/apt/debs/partial"
sudo apt-get \
  --download-only \
  --reinstall \
  --no-install-recommends \
  -y \
  -o "Dir::Cache::archives=$BUNDLE/apt/debs/" \
  -o "Dir::State::status=$APT_STATUS" \
  -o "Debug::NoLocking=1" \
  install "${APT_PACKAGES[@]}"
sudo chown -R "$(id -u):$(id -g)" "$BUNDLE/apt"
find "$BUNDLE/apt/debs" -maxdepth 1 -type f -name '*.deb' -printf '%f\n' |
  LC_ALL=C sort >"$BUNDLE/apt/package-files.txt"
printf '%s\n' "${APT_PACKAGES[@]}" >"$BUNDLE/apt/requested-packages.txt"
[[ -s "$BUNDLE/apt/package-files.txt" ]] || {
  echo "Offline apt dependency download produced no .deb files." >&2
  exit 1
}
(
  cd "$BUNDLE/apt"
  dpkg-scanpackages -m debs /dev/null >Packages
  gzip -9c Packages >Packages.gz
)

cp -a "$ROOT/scripts/install-portable-offline.sh" "$BUNDLE/install-portable-offline.sh"
cp -a "$ROOT/scripts/verify-portable-offline.sh" "$BUNDLE/verify-portable-offline.sh"

MODELS_FILE="$BUNDLE/components/ollama/model-list.txt"
export BUNDLE_MANIFEST_PATH="$BUNDLE/offline-manifest.json"
export BUNDLE_CREATED_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export BUNDLE_SOURCE_COMMIT="$SOURCE_COMMIT"
export BUNDLE_DEFAULT_MODEL="$DEFAULT_MODEL"
export BUNDLE_CONTEXT_LENGTH="$CONTEXT_LENGTH"
export BUNDLE_MODELS_FILE="$MODELS_FILE"
export BUNDLE_INCLUDE_PROJECTS="$INCLUDE_PROJECTS"
python3 <<'PY'
import json
import os
from pathlib import Path

models = [
    line.strip()
    for line in Path(os.environ["BUNDLE_MODELS_FILE"]).read_text().splitlines()
    if line.strip()
]
manifest = {
    "format": "aec-portable-offline-v1",
    "created_utc": os.environ["BUNDLE_CREATED_UTC"],
    "source_commit": os.environ["BUNDLE_SOURCE_COMMIT"],
    "source_platform": {
        "os": "ubuntu",
        "version": "24.04",
        "architecture": "arm64",
    },
    "target": {
        "user": "nvidia",
        "home": "/home/nvidia",
        "repository": "/home/nvidia/AEC_Demo_Portable",
    },
    "ollama": {
        "default_model": os.environ["BUNDLE_DEFAULT_MODEL"],
        "models": models,
        "context_length": int(os.environ["BUNDLE_CONTEXT_LENGTH"]),
        "keep_alive": -1,
    },
    "includes_recorded_projects": os.environ["BUNDLE_INCLUDE_PROJECTS"] == "true",
}
Path(os.environ["BUNDLE_MANIFEST_PATH"]).write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

cat >"$BUNDLE/README-OFFLINE.txt" <<EOF
AEC Demo Portable offline deployment bundle

Source commit: $SOURCE_COMMIT
Default Ollama model: $DEFAULT_MODEL
Recorded checkpoints included: $INCLUDE_PROJECTS

Destination requirements:
- Ubuntu 24.04 ARM64 with current NVIDIA/DGX drivers
- user nvidia with sudo access
- installation path /home/nvidia/AEC_Demo_Portable

From this extracted directory run:

  ./verify-portable-offline.sh --bundle .
  ./install-portable-offline.sh
  /home/nvidia/AEC_Demo_Portable/scripts/verify-portable-offline.sh --installed
  /home/nvidia/AEC_Demo_Portable/scripts/restart-portable-demo.sh
  /home/nvidia/AEC_Demo_Portable/scripts/preflight-portable-demo.sh

No source-machine GPU UUID is included. Apply the optional dual-GPU override
from docs/INSTALL_GUIDE.md only after installation on the destination.
EOF

echo "OFFLINE_INTERNAL_CHECKSUM_BEGIN"
(
  cd "$BUNDLE"
  find     README-OFFLINE.txt     apt     components     install-portable-offline.sh     offline-manifest.json     repo     verify-portable-offline.sh     -type f -print0 |
    LC_ALL=C sort -z |
    xargs -0 sha256sum >SHA256SUMS
)

echo "OFFLINE_ARCHIVE_BEGIN output=$OUTPUT"
if [[ "$COMPRESSION" == "gzip" ]]; then
  if command -v pigz >/dev/null 2>&1; then
    tar -C "$STAGE_PARENT" -cf - "$BUNDLE_NAME" | pigz -1 >"$OUTPUT"
    pigz -dc "$OUTPUT" | tar -tf - >"$OUTPUT.contents.txt"
  else
    tar -C "$STAGE_PARENT" -czf "$OUTPUT" "$BUNDLE_NAME"
    tar -tzf "$OUTPUT" >"$OUTPUT.contents.txt"
  fi
else
  tar -C "$STAGE_PARENT" -cf "$OUTPUT" "$BUNDLE_NAME"
  tar -tf "$OUTPUT" >"$OUTPUT.contents.txt"
fi

OUTPUT_DIR="$(dirname "$OUTPUT")"
OUTPUT_NAME="$(basename "$OUTPUT")"
(
  cd "$OUTPUT_DIR"
  sha256sum "$OUTPUT_NAME" >"$OUTPUT_NAME.sha256"
)
ARCHIVE_BYTES="$(stat --format '%s' "$OUTPUT")"
ARCHIVE_SHA256="$(sha256sum "$OUTPUT" | awk '{print $1}')"
echo "OFFLINE_BUNDLE_OK archive=$OUTPUT bytes=$ARCHIVE_BYTES sha256=$ARCHIVE_SHA256"
echo "OFFLINE_BUNDLE_CHECKSUM=$OUTPUT.sha256"
echo "OFFLINE_BUNDLE_CONTENTS=$OUTPUT.contents.txt"
