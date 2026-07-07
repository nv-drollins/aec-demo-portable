#!/usr/bin/env python3
"""Record the checked optional Phase 10 animation skip."""

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
    cfg=json.loads(SPEC_PATH.read_text()); input_scene=(ROOT/cfg["input_scene"]).resolve(); output_scene=(ROOT/cfg["output_scene"]).resolve()
    if not input_scene.is_file(): raise RuntimeError(f"Phase 9 checkpoint is missing: {input_scene}")
    output_scene.parent.mkdir(parents=True,exist_ok=True); allowed=[str(input_scene),str(output_scene)]
    code=f'''import bpy,json,os\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(p) for p in {allowed!r}}}: raise RuntimeError("Wrong checkpoint")\nscene=bpy.context.scene; hero=bpy.data.objects.get({cfg["hero_camera"]!r}); anim=bpy.data.objects.get({cfg["animation_camera"]!r}); fire=bpy.data.objects.get("FireLight")\nif hero is None or anim is None or scene.world is None or scene.world.name!={cfg["required_world"]!r} or fire is None: raise RuntimeError("Phase 9 state incomplete")\nkeys=0 if anim.animation_data is None or anim.animation_data.action is None else sum(len(fc.keyframe_points) for fc in anim.animation_data.action.fcurves)\nif keys: raise RuntimeError("Refusing to skip after animation keyframes exist")\nprint("PORTABLE_ANIMATION_INPUT_DATA="+json.dumps({{"scene":bpy.data.filepath,"world":scene.world.name,"hero":hero.name,"animation_camera":anim.name,"keyframes":keys}},separators=(",",":"),sort_keys=True))\nscene.camera=hero; scene["aec_phase"]=10; scene["aec_phase_name"]="optional_animation_skipped"; scene["aec_animation_skip_reason"]={cfg["reason"]!r}; scene["aec_animation_skip_spec_id"]={cfg["id"]!r}\ntext=bpy.data.texts.get("AEC_PHASE10_README") or bpy.data.texts.new("AEC_PHASE10_README"); text.clear(); text.write("Optional animation skipped for the still-image Blender-to-ComfyUI demo.\\n")\nos.makedirs(os.path.dirname({str(output_scene)!r}),exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True)\nprint("PORTABLE_ANIMATION_SKIP_DATA="+json.dumps({{"output":bpy.data.filepath,"reason":scene["aec_animation_skip_reason"],"hero":scene.camera.name,"keyframes":keys}},separators=(",",":"),sort_keys=True))\n'''
    response=transport().blender_execute(code)
    if response.get("status")!="success": raise RuntimeError(response)
    result=response.get("result",{}).get("result",""); a="PORTABLE_ANIMATION_INPUT_DATA="; b="PORTABLE_ANIMATION_SKIP_DATA="
    if a not in result or b not in result: raise RuntimeError("Incomplete animation skip markers")
    before=json.loads(result.split(a,1)[1].splitlines()[0]); after=json.loads(result.split(b,1)[1].splitlines()[0])
    print(f"PORTABLE_ANIMATION_INPUT_OK scene={before['scene']} world={before['world']} hero={before['hero']} animation_camera={before['animation_camera']} keyframes={before['keyframes']}")
    print(f"PORTABLE_ANIMATION_SKIP_OK output={after['output']} reason={after['reason']} hero={after['hero']} keyframes={after['keyframes']}")
    print(f"PORTABLE_ANIMATION_PREPARATION_OK output={output_scene} spec={cfg['id']}")

if __name__=="__main__": main()
