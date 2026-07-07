#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/runtime/freecad"
DOWNLOADS="$ROOT/runtime/downloads"
MCP_ROOT="$ROOT/runtime/freecad-mcp"
APPIMAGE="$RUNTIME/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
PART="$APPIMAGE.part"
URL="https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
SHA256="8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827"
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
