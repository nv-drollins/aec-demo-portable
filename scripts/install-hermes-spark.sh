#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DOWNLOADS="$ROOT/runtime/downloads"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"
HERMES_COMMIT="7c1a029553d87c43ecff8a3821336bc95872213b"
HERMES_VERSION="v2026.7.1"
HERMES_INSTALLER="$DOWNLOADS/hermes-install-$HERMES_VERSION.sh"
HERMES_URL="https://raw.githubusercontent.com/NousResearch/hermes-agent/$HERMES_VERSION/scripts/install.sh"
HERMES_SHA256="a93c65b01ea392e179cf872e182bd01a2b65c0c15f17833e9f9569033ef10e07"
OLLAMA_VERSION="0.31.1"
OLLAMA_INSTALLER="$DOWNLOADS/ollama-install-$OLLAMA_VERSION.sh"
OLLAMA_URL="https://raw.githubusercontent.com/ollama/ollama/v$OLLAMA_VERSION/scripts/install.sh"
OLLAMA_SHA256="25f64b810b947145095956533e1bdf56eacea2673c55a7e586be4515fc882c9f"
HERMES_MODEL="${AEC_HERMES_MODEL:-ollama/qwen3.6:latest}"
OLLAMA_MODEL="${AEC_PORTABLE_OLLAMA_MODEL:-$HERMES_MODEL}"
OLLAMA_MODEL="${OLLAMA_MODEL#ollama/}"

mkdir -p "$DOWNLOADS"

download_verified() {
    local url=$1 target=$2 sha=$3
    local part="$target.part"
    if [[ -f "$target" ]] && echo "$sha  $target" | sha256sum -c - >/dev/null 2>&1; then
        return
    fi
    if [[ -f "$target" ]]; then
        mv "$target" "$target.bad.$(date +%s)"
    fi
    echo "INSTALLER_DOWNLOAD_BEGIN target=$target"
    curl -fL --progress-bar --show-error --retry 5 -C - -o "$part" "$url"
    echo "$sha  $part" | sha256sum -c -
    mv "$part" "$target"
    echo "$sha  $target" | sha256sum -c -
}

if [[ ! -x "$HERMES_BIN" || ! -x "$HERMES_HOME/bin/uv" ]]; then
    download_verified "$HERMES_URL" "$HERMES_INSTALLER" "$HERMES_SHA256"
    HERMES_HOME="$HERMES_HOME" bash "$HERMES_INSTALLER" --commit "$HERMES_COMMIT" --skip-setup --skip-browser --non-interactive
else
    echo "HERMES_INSTALL_SKIPPED=already_present path=$HERMES_BIN"
fi

HERMES_PYTHON="$HERMES_HOME/hermes-agent/venv/bin/python"
if [[ ! -x "$HERMES_BIN" || ! -x "$HERMES_PYTHON" ]]; then
    echo "HERMES_INSTALL_FAILED bin=$HERMES_BIN python=$HERMES_PYTHON" >&2
    exit 1
fi
"$HERMES_BIN" --version

if ! command -v ollama >/dev/null 2>&1; then
    download_verified "$OLLAMA_URL" "$OLLAMA_INSTALLER" "$OLLAMA_SHA256"
    OLLAMA_VERSION="$OLLAMA_VERSION" bash "$OLLAMA_INSTALLER"
else
    echo "OLLAMA_INSTALL_SKIPPED=already_present version=$(ollama --version 2>/dev/null || true)"
fi

if command -v systemctl >/dev/null 2>&1 && ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    sudo systemctl enable --now ollama
fi

OLLAMA_READY=0
for _ in $(seq 1 60); do
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        OLLAMA_READY=1
        break
    fi
    sleep 1
done
if [[ "$OLLAMA_READY" != "1" ]]; then
    echo "OLLAMA_START_FAILED endpoint=http://127.0.0.1:11434" >&2
    exit 1
fi
echo "OLLAMA_RUNTIME_OK=$(ollama --version)"

if [[ "${AEC_SKIP_OLLAMA_MODEL_DOWNLOAD:-0}" != "1" ]]; then
    if ! ollama show "$OLLAMA_MODEL" >/dev/null 2>&1; then
        echo "OLLAMA_MODEL_DOWNLOAD_BEGIN model=$OLLAMA_MODEL"
        ollama pull "$OLLAMA_MODEL"
    fi
    ollama show "$OLLAMA_MODEL" >/dev/null
    echo "OLLAMA_MODEL_OK=$OLLAMA_MODEL"
else
    echo "OLLAMA_MODEL_DOWNLOAD_SKIPPED=$OLLAMA_MODEL"
fi

AEC_HERMES_MODEL="$HERMES_MODEL" AEC_FORCE_HERMES_MODEL_CONFIG=1 "$HERMES_PYTHON" "$ROOT/scripts/register-hermes-skills.py"

echo "HERMES_AGENT_RUNTIME_OK=$HERMES_BIN model=$HERMES_MODEL"
