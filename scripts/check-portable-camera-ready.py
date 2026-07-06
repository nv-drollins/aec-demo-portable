#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 8."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TRANSPORT_PATH = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-camera/assets/portable-cliff-house-camera-v1.json"


def load_transport():
    module_spec = importlib.util.spec_from_file_location("portable_blender_transport", TRANSPORT_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load checked Blender transport: {TRANSPORT_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-camera-v1":
        raise RuntimeError("Portable camera specification has the wrong format")
    input_scene = (ROOT / spec["input_scene"]).resolve()
    output_scene = (ROOT / spec["output_scene"]).resolve()
    if not input_scene.is_file():
        raise RuntimeError(f"Approved Phase 7 checkpoint is missing: {input_scene}")
    transport = load_transport()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy,json,os\nspec=json.loads({embedded!r})\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(path) for path in {allowed!r}}}: raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\ncam=bpy.data.objects.get(spec["source_camera"])\nif cam is None or cam.type!="CAMERA": raise RuntimeError("Delivered Camera_day is missing")\nactual=list(cam.location)+list(cam.rotation_euler)+[cam.data.lens]\nexpected=spec["source_location"]+spec["source_rotation"]+[spec["hero_lens"]]\nif any(abs(a-b)>1e-7 for a,b in zip(actual,expected)): raise RuntimeError("Delivered camera anchor mismatch: "+repr(actual))\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nif len(meshes)!=160 or any(not obj.get("material","") for obj in meshes): raise RuntimeError("Phase 7 materials checkpoint is incomplete")\nprint("PORTABLE_CAMERA_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"source_camera":cam.name,"lens":cam.data.lens,"meshes":len(meshes),"resolution":[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y]}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender camera readiness check failed: {response}")
    result = response.get("result", {}).get("result", "")
    marker = "PORTABLE_CAMERA_READINESS_DATA="
    if marker not in result:
        raise RuntimeError("Camera readiness check returned no data marker")
    data = json.loads(result.split(marker, 1)[1].splitlines()[0])
    print(
        f"PORTABLE_CAMERA_READY_OK source_camera={data['source_camera']} lens={data['lens']} "
        f"meshes={data['meshes']} resolution={data['resolution'][0]}x{data['resolution'][1]} "
        f"scene={data['scene']} mutation=none"
    )


if __name__ == "__main__":
    main()
