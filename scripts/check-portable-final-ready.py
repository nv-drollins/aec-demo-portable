#!/usr/bin/env python3
"""Read-only readiness check for canonical Phase 12."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "skills/run-portable-blender-comfy-final/assets/portable-cliff-house-final-v1.json"
TRANSPORT = ROOT / "scripts/run-portable-landscaping.py"


def transport():
    module_spec = importlib.util.spec_from_file_location("transport", TRANSPORT)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main():
    cfg = json.loads(SPEC.read_text())
    input_scene = (ROOT / cfg["input_scene"]).resolve()
    final_scene = (ROOT / cfg["final_scene"]).resolve()
    phase11 = (ROOT / cfg["phase11_dir"]).resolve()
    if not input_scene.is_file():
        raise RuntimeError(f"Phase 11 checkpoint missing: {input_scene}")
    files = [phase11 / name for name in ("beauty.png", "depth.png", "segmentation.png")]
    if any(not path.is_file() or Image.open(path).size != (512, 512) for path in files):
        raise RuntimeError("Phase 11 images missing or invalid")
    preflight = subprocess.run(
        [str(ROOT / "scripts/preflight-portable-demo.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if preflight.returncode or "PORTABLE_PREFLIGHT_OK" not in preflight.stdout:
        raise RuntimeError(preflight.stdout + preflight.stderr)

    allowed = [str(input_scene), str(final_scene)]
    code = f'''import bpy,json,os
if os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(path) for path in {allowed!r}}}: raise RuntimeError("Wrong checkpoint")
scene=bpy.context.scene; meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]; camera=scene.camera; target=bpy.data.objects.get("ocean_view_target")
expected_location={cfg["camera_location"]!r}; expected_target={cfg["camera_target"]!r}
if len(meshes)!=160 or camera is None or camera.name!="ocean_view" or target is None or any(not obj.get("material","") for obj in meshes): raise RuntimeError("Phase 11 scene incomplete")
if scene.get("aec_camera_spec_id")!={cfg["camera_spec_id"]!r} or scene.get("aec_camera_composition")!={cfg["camera_composition"]!r}: raise RuntimeError("Phase 11 camera identity mismatch")
if any(abs(a-b)>1e-7 for a,b in zip(camera.location,expected_location)) or any(abs(a-b)>1e-7 for a,b in zip(target.location,expected_target)) or abs(camera.data.lens-{cfg["camera_lens"]!r})>1e-7: raise RuntimeError("Phase 11 camera transform mismatch")
print("PORTABLE_FINAL_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"camera":camera.name,"camera_spec_id":scene.get("aec_camera_spec_id"),"composition":scene.get("aec_camera_composition"),"location":list(camera.location),"target":list(target.location),"lens":camera.data.lens,"meshes":len(meshes),"world":scene.world.name if scene.world else None}},separators=(",",":"),sort_keys=True))
'''
    response = transport().blender_execute(code)
    result = response.get("result", {}).get("result", "")
    marker = "PORTABLE_FINAL_READINESS_DATA="
    if response.get("status") != "success" or marker not in result:
        raise RuntimeError(response)
    data = json.loads(result.split(marker, 1)[1].splitlines()[0])
    print(
        f"PORTABLE_FINAL_READY_OK camera={data['camera']} "
        f"camera_spec={data['camera_spec_id']} composition={data['composition']} "
        f"location={json.dumps(data['location'], separators=(',', ':'))} "
        f"target={json.dumps(data['target'], separators=(',', ':'))} "
        f"lens={data['lens']} meshes={data['meshes']} world={data['world']} "
        f"phase11_images=3 preflight=ok scene={data['scene']} mutation=none"
    )


if __name__ == "__main__":
    main()
