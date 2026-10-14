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


def enable_cycles_gpu() -> None:
    """Enable a Cycles compute device in this Blender's preferences.

    The render adapters set `scene.cycles.device = "GPU"`, but that is only a
    request: if no compute device is enabled in the Cycles addon preferences,
    Blender silently renders on the CPU instead, which turns a ~1 minute
    beauty pass into many minutes. A fresh Blender install has no device
    enabled, so select one explicitly at startup.

    Only devices visible to this process are enumerated, so when the launcher
    pinned CUDA_VISIBLE_DEVICES to the render GPU, that is the only GPU this
    can enable.
    """
    preferences = bpy.context.preferences.addons.get("cycles")
    if preferences is None:
        bpy.ops.preferences.addon_enable(module="cycles")
        preferences = bpy.context.preferences.addons.get("cycles")
    if preferences is None:
        print("AEC_CYCLES_GPU_UNAVAILABLE=cycles_addon_missing")
        return
    settings = preferences.preferences
    for backend in ("OPTIX", "CUDA"):
        settings.compute_device_type = backend
        settings.get_devices()
        gpus = [
            device for device in settings.devices
            if device.type == backend
        ]
        if not gpus:
            continue
        for device in settings.devices:
            # Enable the GPUs only. Leaving the CPU enabled alongside them
            # makes Cycles split tiles onto the slower device.
            device.use = device.type == backend
        names = ",".join(device.name for device in gpus)
        print(f"AEC_CYCLES_GPU_READY backend={backend} devices={len(gpus)} names={names}")
        return
    settings.compute_device_type = "NONE"
    print("AEC_CYCLES_GPU_UNAVAILABLE=no_optix_or_cuda_device_visible")


if not ADDON.is_file():
    raise RuntimeError(f"Bundled Blender MCP add-on is missing: {ADDON}")

enable_cycles_gpu()

namespace = runpy.run_path(str(ADDON), run_name="aec_portable_blender_mcp")
namespace["register"]()
bpy.context.scene.blendermcp_port = PORT
result = bpy.ops.blendermcp.start_server()
if "FINISHED" not in result:
    raise RuntimeError(f"Blender MCP server did not start: {result}")

print(f"AEC_BLENDER_MCP_READY port={PORT} addon={ADDON}")
