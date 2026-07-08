#!/usr/bin/env bash
set -Eeuo pipefail

BUNDLE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET="/home/nvidia/AEC_Demo_Portable"
SKIP_CHECKSUMS=false
MODEL_OVERRIDE=""
AUDIT_ONLY=false

usage() {
  cat <<'EOF'
Install an extracted AEC portable offline deployment bundle.

Usage:
  ./install-portable-offline.sh [options]

Options:
  --model MODEL       Select a bundled Ollama model instead of the manifest
                      default.
  --skip-checksums    Skip the expanded bundle SHA-256 verification. Use only
                      when verify-portable-offline.sh --bundle already passed.
  --audit-only        Validate the bundle and installation plan without making
                      changes.
  -h, --help          Show this help.

Run this script as the nvidia desktop user, not as root. It uses sudo only for
Ubuntu packages, Ollama files, ownership, and the systemd service. The target
must be Ubuntu 24.04 ARM64 with working NVIDIA/DGX drivers.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || { echo "Missing value for --model" >&2; exit 2; }
      MODEL_OVERRIDE="$2"
      shift 2
      ;;
    --skip-checksums)
      SKIP_CHECKSUMS=true
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

if (( EUID == 0 )); then
  echo "Run this installer as user nvidia, not with sudo." >&2
  exit 1
fi
if [[ "$USER" != "nvidia" || "$HOME" != "/home/nvidia" ]]; then
  echo "Offline installation currently requires user nvidia and /home/nvidia." >&2
  exit 1
fi
if [[ "$(dpkg --print-architecture)" != "arm64" ]]; then
  echo "Offline installation currently requires ARM64." >&2
  exit 1
fi
. /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
  echo "Offline installation currently requires Ubuntu 24.04." >&2
  exit 1
fi

required_bundle_paths=(
  "$BUNDLE_ROOT/offline-manifest.json"
  "$BUNDLE_ROOT/SHA256SUMS"
  "$BUNDLE_ROOT/repo"
  "$BUNDLE_ROOT/apt/debs"
  "$BUNDLE_ROOT/components/hermes/home/.hermes/hermes-agent"
  "$BUNDLE_ROOT/components/hermes/home/.hermes/bin"
  "$BUNDLE_ROOT/components/hermes/home/.local/bin/hermes"
  "$BUNDLE_ROOT/components/ollama/bin/ollama"
  "$BUNDLE_ROOT/components/hermes/home/.local/share/uv/python"
  "$BUNDLE_ROOT/components/ollama/lib/ollama"
  "$BUNDLE_ROOT/components/ollama/models"
  "$BUNDLE_ROOT/verify-portable-offline.sh"
)
for path in "${required_bundle_paths[@]}"; do
  [[ -e "$path" ]] || {
    echo "Offline bundle component is missing: $path" >&2
    exit 1
  }
done

if [[ "$SKIP_CHECKSUMS" != true ]]; then
  "$BUNDLE_ROOT/verify-portable-offline.sh" --bundle "$BUNDLE_ROOT"
else
  echo "OFFLINE_BUNDLE_CHECKSUM_VERIFY_SKIPPED"
fi

readarray -t MANIFEST_VALUES < <(
  python3 - "$BUNDLE_ROOT/offline-manifest.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
if data.get("format") != "aec-portable-offline-v1":
    raise SystemExit("Unsupported offline manifest format")
print(data["ollama"]["default_model"])
print(data["ollama"]["context_length"])
for model in data["ollama"]["models"]:
    print(model)
PY
)
DEFAULT_MODEL="${MANIFEST_VALUES[0]}"
CONTEXT_LENGTH="${MANIFEST_VALUES[1]}"
BUNDLED_MODELS=("${MANIFEST_VALUES[@]:2}")
if [[ -n "$MODEL_OVERRIDE" ]]; then
  DEFAULT_MODEL="$MODEL_OVERRIDE"
fi
MODEL_FOUND=false
for model in "${BUNDLED_MODELS[@]}"; do
  if [[ "$model" == "$DEFAULT_MODEL" ]]; then
    MODEL_FOUND=true
  fi
done
[[ "$MODEL_FOUND" == true ]] || {
  echo "Requested model is not present in the offline bundle: $DEFAULT_MODEL" >&2
  printf 'BUNDLED_MODEL=%s\n' "${BUNDLED_MODELS[@]}" >&2
  exit 1
}

echo "OFFLINE_APT_INSTALL_BEGIN"
[[ -s "$BUNDLE_ROOT/apt/Packages" ]] || {
  echo "Offline APT repository index is missing." >&2
  exit 1
}
mapfile -t APT_REQUESTED <"$BUNDLE_ROOT/apt/requested-packages.txt"
if (( ${#APT_REQUESTED[@]} == 0 )); then
  echo "Offline requested package list is empty." >&2
  exit 1
fi
if [[ "$AUDIT_ONLY" == true ]]; then
  echo "OFFLINE_INSTALL_AUDIT_OK"
  echo "OFFLINE_INSTALL_TARGET=$TARGET"
  echo "OFFLINE_INSTALL_MODEL=$DEFAULT_MODEL"
  echo "OFFLINE_INSTALL_CONTEXT_LENGTH=$CONTEXT_LENGTH"
  echo "OFFLINE_INSTALL_APT_PACKAGES=${#APT_REQUESTED[@]}"
  exit 0
fi
APT_SOURCE="$(mktemp)"
printf 'deb [trusted=yes] file:%s ./\n' "$BUNDLE_ROOT/apt" >"$APT_SOURCE"
APT_OPTIONS=(
  -o "Dir::Etc::sourcelist=$APT_SOURCE"
  -o "Dir::Etc::sourceparts=-"
  -o "Acquire::Languages=none"
  -o "Acquire::AllowInsecureRepositories=true"
)
sudo apt-get "${APT_OPTIONS[@]}" update
sudo apt-get \
  "${APT_OPTIONS[@]}" \
  --no-install-recommends \
  -y \
  install "${APT_REQUESTED[@]}"
rm -f "$APT_SOURCE"
echo "OFFLINE_APT_INSTALL_OK requested=${#APT_REQUESTED[@]}"

echo "OFFLINE_REPOSITORY_INSTALL_BEGIN target=$TARGET"
if [[ -x "$TARGET/scripts/stop-portable-demo.sh" ]]; then
  "$TARGET/scripts/stop-portable-demo.sh" >/dev/null 2>&1 || true
fi
mkdir -p "$TARGET"
tar -C "$BUNDLE_ROOT/repo" -cf - . | tar -xf - -C "$TARGET"
cp -a "$BUNDLE_ROOT/offline-manifest.json" "$TARGET/offline-manifest.json"
printf '%s\n' "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source_commit"])' "$BUNDLE_ROOT/offline-manifest.json")" \
  >"$TARGET/.offline-source-commit"

if [[ -f "$TARGET/config/runtime.env" ]]; then
  cp -a "$TARGET/config/runtime.env"     "$TARGET/config/runtime.env.before-offline-$(date -u +%Y%m%d_%H%M%S)"
fi
cp -a "$TARGET/config/runtime.env.example" "$TARGET/config/runtime.env"
python3 - "$TARGET/config/runtime.env" "$DEFAULT_MODEL" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
model = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
replacements = {
    "AEC_HERMES_MODEL": f"ollama/{model}",
    "AEC_PORTABLE_OLLAMA_MODEL": model,
}
result = []
seen = set()
for line in lines:
    key = line.split("=", 1)[0] if "=" in line else ""
    if key in replacements:
        result.append(f"{key}={replacements[key]}")
        seen.add(key)
    else:
        result.append(line)
for key, value in replacements.items():
    if key not in seen:
        result.append(f"{key}={value}")
path.write_text("\n".join(result) + "\n", encoding="utf-8")
PY
chmod 600 "$TARGET/config/runtime.env"
echo "OFFLINE_REPOSITORY_INSTALL_OK=$TARGET"

echo "OFFLINE_HERMES_INSTALL_BEGIN"
mkdir -p "$HOME/.hermes" "$HOME/.local/bin" "$HOME/.local/share/uv"
tar -C "$BUNDLE_ROOT/components/hermes/home/.hermes" -cf - bin hermes-agent |
  tar -xf - -C "$HOME/.hermes"
tar -C "$BUNDLE_ROOT/components/hermes/home/.local/share/uv" -cf - python |
  tar -xf - -C "$HOME/.local/share/uv"
install -m 755 \
  "$BUNDLE_ROOT/components/hermes/home/.local/bin/hermes" \
  "$HOME/.local/bin/hermes"
[[ -x "$HOME/.hermes/hermes-agent/venv/bin/hermes" ]] || {
  echo "Bundled Hermes environment is not executable." >&2
  exit 1
}
"$HOME/.local/bin/hermes" --version
echo "OFFLINE_HERMES_INSTALL_OK=$HOME/.hermes/hermes-agent"

echo "OFFLINE_OLLAMA_INSTALL_BEGIN"
if systemctl is-active --quiet ollama 2>/dev/null; then
  sudo systemctl stop ollama
fi
if ! getent group ollama >/dev/null; then
  sudo groupadd --system ollama
fi
if ! id ollama >/dev/null 2>&1; then
  sudo useradd \
    --system \
    --gid ollama \
    --home-dir /usr/share/ollama \
    --create-home \
    --shell /usr/sbin/nologin \
    ollama
fi
for group in render video; do
  if getent group "$group" >/dev/null; then
    sudo usermod -a -G "$group" ollama
  fi
done

sudo install -m 755 "$BUNDLE_ROOT/components/ollama/bin/ollama" /usr/local/bin/ollama
OLLAMA_LIB_NEW="/usr/local/lib/ollama.aec-offline-new"
sudo rm -rf "$OLLAMA_LIB_NEW"
sudo mkdir -p "$OLLAMA_LIB_NEW"
sudo tar -C "$BUNDLE_ROOT/components/ollama/lib/ollama" -cf - . |
  sudo tar -xf - -C "$OLLAMA_LIB_NEW"
if [[ -d /usr/local/lib/ollama ]]; then
  OLLAMA_LIB_BACKUP="/usr/local/lib/ollama.before-aec-offline-$(date -u +%Y%m%d_%H%M%S)"
  sudo mv /usr/local/lib/ollama "$OLLAMA_LIB_BACKUP"
  echo "OLLAMA_LIBRARY_BACKUP=$OLLAMA_LIB_BACKUP"
fi
sudo mv "$OLLAMA_LIB_NEW" /usr/local/lib/ollama

sudo mkdir -p /usr/share/ollama/.ollama/models
sudo tar -C "$BUNDLE_ROOT/components/ollama/models" -cf - . |
  sudo tar -xf - -C /usr/share/ollama/.ollama/models
sudo chown -R ollama:ollama /usr/share/ollama

if [[ ! -f /etc/systemd/system/ollama.service ]]; then
  sudo tee /etc/systemd/system/ollama.service >/dev/null <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF
fi
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/10-aec-offline.conf >/dev/null <<EOF
[Service]
Environment="OLLAMA_MODELS=/usr/share/ollama/.ollama/models"
Environment="OLLAMA_CONTEXT_LENGTH=$CONTEXT_LENGTH"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_VULKAN=0"
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now ollama

python3 <<'PY'
import time
import urllib.request

for _ in range(120):
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            if response.status == 200:
                print("OFFLINE_OLLAMA_ENDPOINT_OK")
                break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Ollama did not become ready within 120 seconds")
PY
ollama show "$DEFAULT_MODEL" >/dev/null
echo "OFFLINE_OLLAMA_INSTALL_OK model=$DEFAULT_MODEL"

echo "OFFLINE_INTEGRATION_CONFIG_BEGIN"
"$TARGET/scripts/repair-freecad-mcp-links.sh"
AEC_HERMES_MODEL="ollama/$DEFAULT_MODEL" \
AEC_FORCE_HERMES_MODEL_CONFIG=1 \
  "$HOME/.hermes/hermes-agent/venv/bin/python" \
  "$TARGET/scripts/register-hermes-skills.py"

"$TARGET/scripts/verify-portable-offline.sh" --installed

cat <<EOF

OFFLINE_INSTALL_OK=$TARGET
DEFAULT_OLLAMA_MODEL=$DEFAULT_MODEL

The bundle did not copy a source-machine GPU UUID. If this destination has a
second NVIDIA GPU, apply the optional UUID-based Ollama override from:
  $TARGET/docs/INSTALL_GUIDE.md

With the desktop session active, complete the service test:

  $TARGET/scripts/restart-portable-demo.sh
  $TARGET/scripts/preflight-portable-demo.sh

Then start the manual demonstration:

  $TARGET/scripts/start-portable-manual-demo.sh
EOF
