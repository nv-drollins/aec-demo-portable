#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 11."""

from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; TRANSPORT=ROOT/"scripts/run-portable-landscaping.py"; SPEC=ROOT/"skills/render-portable-blender-test-passes/assets/portable-cliff-house-test-renders-v1.json"
def module():
    s=importlib.util.spec_from_file_location("transport",TRANSPORT); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    cfg=json.loads(SPEC.read_text()); inp=(ROOT/cfg["input_scene"]).resolve(); out=(ROOT/cfg["output_scene"]).resolve()
    if not inp.is_file(): raise RuntimeError(f"Phase 10 checkpoint missing: {inp}")
    code=f'''import bpy,json,os\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(p) for p in {[str(inp),str(out)]!r}}}: raise RuntimeError("Wrong checkpoint")\nmeshes=[o for o in bpy.data.objects if o.type=="MESH"]; cam=bpy.data.objects.get({cfg["hero_camera"]!r})\nif len(meshes)!={cfg["expected_meshes"]} or cam is None or any(not o.get("material","") for o in meshes): raise RuntimeError("Phase 10 state incomplete")\nprint("PORTABLE_TEST_RENDER_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"camera":cam.name,"meshes":len(meshes),"world":bpy.context.scene.world.name if bpy.context.scene.world else None,"skip_reason":bpy.context.scene.get("aec_animation_skip_reason","")}},separators=(",",":"),sort_keys=True))\n'''
    r=module().blender_execute(code); result=r.get("result",{}).get("result",""); marker="PORTABLE_TEST_RENDER_READINESS_DATA="
    if r.get("status")!="success" or marker not in result: raise RuntimeError(r)
    d=json.loads(result.split(marker,1)[1].splitlines()[0]); print(f"PORTABLE_TEST_RENDER_READY_OK camera={d['camera']} meshes={d['meshes']} world={d['world']} skip_reason={d['skip_reason']} resolution={cfg['resolution'][0]}x{cfg['resolution'][1]} mutation=none")
if __name__=="__main__": main()
