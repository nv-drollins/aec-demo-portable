"""Register and start the bundled Blender MCP socket server."""

from __future__ import annotations

import os
from pathlib import Path
import runpy

import bpy


ROOT = Path(__file__).resolve().parent.parent
ADDON = Path(os.environ.get(
    "AEC_PORTABLE_BLENDER_MCP_ADDON",
    ROOT / "setup/blender_addons/BlenderMCP_addon.py",
))
PORT = int(os.environ.get("AEC_PORTABLE_BLENDER_PORT", "9876"))

if not ADDON.is_file():
    raise RuntimeError(f"Bundled Blender MCP add-on is missing: {ADDON}")

namespace = runpy.run_path(str(ADDON), run_name="aec_portable_blender_mcp")
namespace["register"]()
bpy.context.scene.blendermcp_port = PORT
result = bpy.ops.blendermcp.start_server()
if "FINISHED" not in result:
    raise RuntimeError(f"Blender MCP server did not start: {result}")

print(f"AEC_BLENDER_MCP_READY port={PORT} addon={ADDON}")
