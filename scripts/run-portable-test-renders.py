#!/usr/bin/env python3
"""Run the checked Phase 11 still-image test renders."""

from __future__ import annotations
import importlib.util,json,os
from pathlib import Path
from PIL import Image,ImageStat
ROOT=Path(__file__).resolve().parent.parent; TRANSPORT=ROOT/"scripts/run-portable-camera.py"; SPEC=ROOT/"skills/render-portable-blender-test-passes/assets/portable-cliff-house-test-renders-v1.json"; BUILDER=ROOT/"scripts/render-portable-test-passes-blender.py"
def module():
    s=importlib.util.spec_from_file_location("transport",TRANSPORT); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    cfg=json.loads(SPEC.read_text()); inp=(ROOT/cfg["input_scene"]).resolve(); out=(ROOT/cfg["output_scene"]).resolve(); directory=(ROOT/cfg["output_dir"]).resolve(); directory.mkdir(parents=True,exist_ok=True)
    if not inp.is_file(): raise RuntimeError(f"Phase 10 checkpoint missing: {inp}")
    env={"AEC_PORTABLE_TEST_SPEC":str(SPEC),"AEC_PORTABLE_TEST_SCENE":str(out),"AEC_PORTABLE_TEST_DIR":str(directory)}
    assigns="".join(f"os.environ[{k!r}]={v!r}\n" for k,v in env.items()); code="import os\n"+assigns+f"exec(compile(open({str(BUILDER)!r},encoding='utf-8').read(),{str(BUILDER)!r},'exec'))"
    r=module().blender_request("execute_code",{"code":code},timeout=600)
    if r.get("status")!="success": raise RuntimeError(r)
    result=r.get("result",{}).get("result",""); markers={"input":"PORTABLE_TEST_RENDER_INPUT_DATA=","beauty":"PORTABLE_TEST_RENDER_BEAUTY_DATA=","depth":"PORTABLE_TEST_RENDER_DEPTH_DATA=","seg":"PORTABLE_TEST_RENDER_SEGMENTATION_DATA=","restore":"PORTABLE_TEST_RENDER_RESTORE_DATA="}
    if any(v not in result for v in markers.values()): raise RuntimeError("Incomplete test-render markers")
    data={k:json.loads(result.split(v,1)[1].splitlines()[0]) for k,v in markers.items()}
    images={name:Image.open(directory/filename).convert("RGB") for name,filename in cfg["files"].items()}
    if any(image.size!=tuple(cfg["resolution"]) for image in images.values()): raise RuntimeError("Test-render dimensions differ")
    beauty_std=max(ImageStat.Stat(images["beauty"]).stddev); depth_extrema=images["depth"].convert("L").getextrema(); colors=images["segmentation"].getcolors(maxcolors=1000000) or []
    if beauty_std<3 or depth_extrema[1]-depth_extrema[0]<10 or len(colors)<3: raise RuntimeError(f"Invalid passes: beauty_std={beauty_std} depth={depth_extrema} colors={len(colors)}")
    print(f"PORTABLE_TEST_RENDER_INPUT_OK scene={data['input']['scene']} camera={data['input']['camera']} meshes={data['input']['meshes']} resolution={cfg['resolution'][0]}x{cfg['resolution'][1]}")
    print(f"PORTABLE_TEST_RENDER_BEAUTY_OK path={data['beauty']['path']} bytes={data['beauty']['bytes']} samples={data['beauty']['samples']} stddev={beauty_std:.2f}")
    print(f"PORTABLE_TEST_RENDER_DEPTH_OK path={data['depth']['path']} bytes={data['depth']['bytes']} near={data['depth']['near']} far={data['depth']['far']} extrema={depth_extrema}")
    print(f"PORTABLE_TEST_RENDER_SEGMENTATION_OK path={data['seg']['path']} bytes={data['seg']['bytes']} categories={data['seg']['categories']} colors={len(colors)}")
    print(f"PORTABLE_TEST_RENDER_RESTORE_OK output={data['restore']['output']} camera={data['restore']['camera']} world={data['restore']['world']} meshes={data['restore']['meshes']}")
    print(f"PORTABLE_TEST_RENDER_PREPARATION_OK output={out} spec={cfg['id']}")
if __name__=="__main__": main()
