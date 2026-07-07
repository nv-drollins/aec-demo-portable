#!/usr/bin/env python3
"""Read-only readiness check for the optional canonical Phase 10 skip."""

from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
TRANSPORT=ROOT/"scripts/run-portable-landscaping.py"
SPEC_PATH=ROOT/"skills/skip-portable-blender-animation/assets/portable-cliff-house-animation-skip-v1.json"

def transport():
    spec=importlib.util.spec_from_file_location("portable_transport",TRANSPORT)
    if spec is None or spec.loader is None: raise RuntimeError("Could not load Blender transport")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main():
    cfg=json.loads(SPEC_PATH.read_text())
    input_scene=(ROOT/cfg["input_scene"]).resolve(); output_scene=(ROOT/cfg["output_scene"]).resolve()
    if not input_scene.is_file(): raise RuntimeError(f"Phase 9 checkpoint is missing: {input_scene}")
    allowed=[str(input_scene),str(output_scene)]
    code=f'''import bpy,json,os\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(p) for p in {allowed!r}}}: raise RuntimeError("Wrong checkpoint")\nhero=bpy.data.objects.get({cfg["hero_camera"]!r}); anim=bpy.data.objects.get({cfg["animation_camera"]!r})\nworld=bpy.context.scene.world\nfire=bpy.data.objects.get("FireLight"); suns=[o for o in bpy.data.objects if o.type=="LIGHT" and o.data.type=="SUN"]\nif hero is None or anim is None or world is None or world.name!={cfg["required_world"]!r} or fire is None: raise RuntimeError("Phase 9 state incomplete")\nkeys=0 if anim.animation_data is None or anim.animation_data.action is None else sum(len(fc.keyframe_points) for fc in anim.animation_data.action.fcurves)\nif keys: raise RuntimeError("Animation camera already has keyframes")\nprint("PORTABLE_ANIMATION_SKIP_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"hero":hero.name,"animation_camera":anim.name,"keyframes":keys,"world":world.name,"sun_hidden":all(o.hide_render for o in suns),"firelight":fire.name}},separators=(",",":"),sort_keys=True))\n'''
    response=transport().blender_execute(code)
    if response.get("status")!="success": raise RuntimeError(response)
    result=response.get("result",{}).get("result",""); marker="PORTABLE_ANIMATION_SKIP_READINESS_DATA="
    if marker not in result: raise RuntimeError("No skip readiness marker")
    data=json.loads(result.split(marker,1)[1].splitlines()[0])
    print(f"PORTABLE_ANIMATION_SKIP_READY_OK hero={data['hero']} animation_camera={data['animation_camera']} keyframes={data['keyframes']} world={data['world']} sun_hidden={data['sun_hidden']} firelight={data['firelight']} scene={data['scene']} mutation=none")

if __name__=="__main__": main()
