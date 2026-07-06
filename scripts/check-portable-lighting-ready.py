#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 9."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSPORT_PATH = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-lighting/assets/portable-cliff-house-lighting-v1.json"

def load_transport():
    module_spec = importlib.util.spec_from_file_location("portable_blender_transport", TRANSPORT_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load checked Blender transport: {TRANSPORT_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module

def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-lighting-v1":
        raise RuntimeError("Portable lighting specification has the wrong format")
    input_scene = (ROOT / spec["input_scene"]).resolve()
    output_scene = (ROOT / spec["output_scene"]).resolve()
    hdri = (ROOT / spec["hdri"]).resolve()
    if not input_scene.is_file() or not hdri.is_file():
        raise RuntimeError(f"Phase 9 input is missing: scene={input_scene} hdri={hdri}")
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy,json,os\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(path) for path in {allowed!r}}}: raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\nrequired={{"Camera_day","ocean_view","compass_cam","patio_sweep_cam"}}\ncameras={{obj.name for obj in bpy.data.objects if obj.type=="CAMERA"}}\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nlights=[{{"name":obj.name,"type":obj.data.type,"energy":obj.data.energy,"hide_render":obj.hide_render}} for obj in bpy.data.objects if obj.type=="LIGHT"]\nif not required.issubset(cameras) or len(meshes)!=160 or any(not obj.get("material","") for obj in meshes): raise RuntimeError("Phase 8 camera checkpoint is incomplete")\nprint("PORTABLE_LIGHTING_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"active_camera":bpy.context.scene.camera.name if bpy.context.scene.camera else None,"cameras":sorted(cameras),"meshes":len(meshes),"lights":lights,"hdri":{str(hdri)!r}}},separators=(",",":"),sort_keys=True))\n'''
    response = load_transport().blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender lighting readiness check failed: {response}")
    result = response.get("result", {}).get("result", "")
    marker = "PORTABLE_LIGHTING_READINESS_DATA="
    if marker not in result:
        raise RuntimeError("Lighting readiness check returned no data marker")
    data = json.loads(result.split(marker, 1)[1].splitlines()[0])
    print(f"PORTABLE_LIGHTING_READY_OK active_camera={data['active_camera']} meshes={data['meshes']} cameras={json.dumps(data['cameras'],separators=(',',':'))} lights={json.dumps(data['lights'],separators=(',',':'))} hdri={data['hdri']} mutation=none")

if __name__ == "__main__":
    main()
