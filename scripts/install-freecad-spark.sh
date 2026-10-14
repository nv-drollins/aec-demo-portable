#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/platform-lib.sh
source "$ROOT/scripts/platform-lib.sh"
RUNTIME="$ROOT/runtime/freecad"
DOWNLOADS="$ROOT/runtime/downloads"
MCP_ROOT="$ROOT/runtime/freecad-mcp"
APPIMAGE="$RUNTIME/$AEC_FREECAD_APPIMAGE"
PART="$APPIMAGE.part"
URL="$AEC_FREECAD_URL"
SHA256="$AEC_FREECAD_SHA256"
MCP_URL="https://github.com/neka-nat/freecad-mcp.git"
MCP_COMMIT="1697aff99156f7361f87dae1fe23e7737acacba1"

mkdir -p "$RUNTIME" "$DOWNLOADS"

if [[ -f "$APPIMAGE" ]] && ! echo "$SHA256  $APPIMAGE" | sha256sum -c - >/dev/null 2>&1; then
    mv "$APPIMAGE" "$APPIMAGE.bad.$(date +%s)"
fi
if [[ ! -f "$APPIMAGE" ]]; then
    echo "FREECAD_DOWNLOAD_BEGIN url=$URL"
    curl -fL --progress-bar --show-error --retry 5 -C - -o "$PART" "$URL"
    echo "$SHA256  $PART" | sha256sum -c -
    mv "$PART" "$APPIMAGE"
fi
echo "$SHA256  $APPIMAGE" | sha256sum -c -
chmod +x "$APPIMAGE"

if command -v sudo >/dev/null 2>&1; then
    sudo apt-get install -y --no-install-recommends libfuse2t64 libxcb-cursor0
fi

if [[ ! -d "$MCP_ROOT/.git" ]]; then
    git clone --filter=blob:none "$MCP_URL" "$MCP_ROOT"
fi
git -C "$MCP_ROOT" fetch --depth 1 origin "$MCP_COMMIT"
git -C "$MCP_ROOT" checkout --detach "$MCP_COMMIT"

chmod +x \
    "$ROOT/scripts/check-freecad-rpc.py" \
    "$ROOT/scripts/repair-freecad-mcp-links.sh" \
    "$ROOT/scripts/start-freecad.sh"
"$ROOT/scripts/repair-freecad-mcp-links.sh"

echo "FREECAD_SPARK_RUNTIME_OK=$APPIMAGE"
echo "FREECAD_MCP_SOURCE_OK=$MCP_ROOT commit=$MCP_COMMIT"
