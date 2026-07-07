#!/usr/bin/env python3
"""Read-only readiness check for canonical Phase 12."""
from __future__ import annotations
import importlib.util,json,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent; SPEC=ROOT/"skills/run-portable-blender-comfy-final/assets/portable-cliff-house-final-v1.json"; TRANSPORT=ROOT/"scripts/run-portable-landscaping.py"
def transport():
    s=importlib.util.spec_from_file_location("transport",TRANSPORT); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    cfg=json.loads(SPEC.read_text()); inp=(ROOT/cfg["input_scene"]).resolve(); final=(ROOT/cfg["final_scene"]).resolve(); phase11=(ROOT/cfg["phase11_dir"]).resolve()
    if not inp.is_file(): raise RuntimeError(f"Phase 11 checkpoint missing: {inp}")
    files=[phase11/name for name in ("beauty.png","depth.png","segmentation.png")]
    if any(not p.is_file() or Image.open(p).size!=(512,512) for p in files): raise RuntimeError("Phase 11 images missing or invalid")
    preflight=subprocess.run([str(ROOT/"scripts/preflight-portable-demo.sh")],cwd=ROOT,text=True,capture_output=True,timeout=120)
    if preflight.returncode or "PORTABLE_PREFLIGHT_OK" not in preflight.stdout: raise RuntimeError(preflight.stdout+preflight.stderr)
    allowed=[str(inp),str(final)]; code=f'''import bpy,json,os\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(p) for p in {allowed!r}}}: raise RuntimeError("Wrong checkpoint")\nmeshes=[o for o in bpy.data.objects if o.type=="MESH"]; cam=bpy.context.scene.camera\nif len(meshes)!=160 or cam is None or cam.name!="ocean_view" or any(not o.get("material","") for o in meshes): raise RuntimeError("Phase 11 scene incomplete")\nprint("PORTABLE_FINAL_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"camera":cam.name,"meshes":len(meshes),"world":bpy.context.scene.world.name if bpy.context.scene.world else None}},separators=(",",":"),sort_keys=True))\n'''
    r=transport().blender_execute(code); result=r.get("result",{}).get("result",""); marker="PORTABLE_FINAL_READINESS_DATA="
    if r.get("status")!="success" or marker not in result: raise RuntimeError(r)
    d=json.loads(result.split(marker,1)[1].splitlines()[0]); print(f"PORTABLE_FINAL_READY_OK camera={d['camera']} meshes={d['meshes']} world={d['world']} phase11_images=3 preflight=ok scene={d['scene']} mutation=none")
if __name__=="__main__": main()
