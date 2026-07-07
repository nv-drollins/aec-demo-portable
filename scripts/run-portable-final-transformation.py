#!/usr/bin/env python3
"""Run and validate canonical Phase 12 Blender-to-ComfyUI transformation."""
from __future__ import annotations
import importlib.util,json,re,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageStat
ROOT=Path(__file__).resolve().parent.parent; SPEC=ROOT/"skills/run-portable-blender-comfy-final/assets/portable-cliff-house-final-v1.json"; TRANSPORT=ROOT/"scripts/run-portable-landscaping.py"
def transport():
    s=importlib.util.spec_from_file_location("transport",TRANSPORT); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    cfg=json.loads(SPEC.read_text()); inp=(ROOT/cfg["input_scene"]).resolve(); final=(ROOT/cfg["final_scene"]).resolve(); outdir=(ROOT/cfg["final_output_dir"]).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    if not inp.is_file(): raise RuntimeError(f"Phase 11 checkpoint missing: {inp}")
    print(f"PORTABLE_FINAL_INPUT_OK scene={inp} controller=scripts/run-comfy-demo.py mode=fresh_render expected_images={cfg['expected_images']}")
    run=subprocess.run(["python3",str(ROOT/"scripts/run-comfy-demo.py"),"--render","--timeout",str(cfg["timeout"])],cwd=ROOT,text=True,capture_output=True,timeout=cfg["timeout"]+180)
    output=run.stdout+run.stderr
    if run.returncode: raise RuntimeError(output)
    camera_match=re.search(r"\[AEC\] RENDER_CAMERA_DATA=(\{[^\n]+\})",output)
    depth_match=re.search(r"\[AEC\] RENDERED_DEPTH_OK=(\{[^\n]+\})",output)
    structure_match=re.search(r"\[AEC\] STRUCTURAL_REFERENCE_DATA=(\{[^\n]+\})",output)
    if not camera_match or not depth_match or not structure_match: raise RuntimeError("Missing Phase 12 camera/depth contract markers:\n"+output)
    camera=json.loads(camera_match.group(1)); depth=json.loads(depth_match.group(1)); structure=json.loads(structure_match.group(1))
    close=lambda actual,expected: len(actual)==len(expected) and all(abs(float(a)-float(e))<=1e-7 for a,e in zip(actual,expected))
    if camera.get("name")!="ocean_view" or camera.get("camera_spec_id")!=cfg["camera_spec_id"] or camera.get("composition")!=cfg["camera_composition"] or not close(camera.get("location",[]),cfg["camera_location"]) or not close(camera.get("target",[]),cfg["camera_target"]) or abs(float(camera.get("lens",0))-float(cfg["camera_lens"]))>1e-7: raise RuntimeError("Phase 12 camera contract mismatch: "+repr(camera))
    depth_path=Path(depth.get("path",""))
    if not depth_path.is_file() or depth_path.name!="depth_input.png" or int(depth.get("bytes",0))<1000: raise RuntimeError("Exact depth render is missing or invalid: "+repr(depth))
    if structure.get("type")!=cfg["structural_reference"] or abs(float(structure.get("conditioning_strength",0))-float(cfg["structural_conditioning_strength"]))>1e-7: raise RuntimeError("Structural reference contract mismatch: "+repr(structure))
    queued=re.search(r"AEC_COMFY_QUEUED=([0-9a-f-]+)",output); complete=re.search(r"AEC_COMFY_COMPLETE=([0-9a-f-]+).*images=(\d+)",output)
    paths=[Path(value) for value in re.findall(r"AEC_COMFY_IMAGE=(.+)",output)]
    if not queued or not complete or int(complete.group(2))!=cfg["expected_images"] or len(paths)!=cfg["expected_images"]: raise RuntimeError("Incomplete ComfyUI result:\n"+output)
    delivered=[]
    for index,path in enumerate(paths,1):
        if not path.is_file(): raise RuntimeError(f"Missing ComfyUI image: {path}")
        image=Image.open(path).convert("RGB"); std=max(ImageStat.Stat(image).stddev)
        if image.width<512 or image.height<512 or std<2: raise RuntimeError(f"Invalid ComfyUI image: {path} size={image.size} std={std}")
        destination=outdir/f"final_{index}_{path.name}"; shutil.copy2(path,destination); delivered.append({"path":str(destination),"width":image.width,"height":image.height,"stddev":round(std,2),"bytes":destination.stat().st_size})
    code=f'''import bpy,os\nscene=bpy.context.scene; scene.camera=bpy.data.objects["ocean_view"]; scene["aec_phase"]=12; scene["aec_phase_name"]="final_blender_comfyui"; scene["aec_final_spec_id"]={cfg["id"]!r}\nos.makedirs(os.path.dirname({str(final)!r}),exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath={str(final)!r},compress=True); print("PORTABLE_FINAL_SCENE_OK="+bpy.data.filepath)\n'''
    r=transport().blender_execute(code)
    if r.get("status")!="success" or "PORTABLE_FINAL_SCENE_OK=" not in r.get("result",{}).get("result",""): raise RuntimeError(r)
    print(f"PORTABLE_FINAL_CAMERA_OK name={camera['name']} spec={camera['camera_spec_id']} composition={camera['composition']} location={json.dumps(camera['location'],separators=(',',':'))} target={json.dumps(camera['target'],separators=(',',':'))} lens={camera['lens']}")
    print(f"PORTABLE_FINAL_STRUCTURE_OK type={structure['type']} strength={structure['conditioning_strength']} depth={json.dumps(depth,separators=(',',':'))}")
    print(f"PORTABLE_FINAL_SUBMISSION_OK prompt_id={queued.group(1)} status={complete.group(1)} images={complete.group(2)}")
    print(f"PORTABLE_FINAL_IMAGES_OK count={len(delivered)} outputs={json.dumps(delivered,separators=(',',':'))}")
    print(f"PORTABLE_FINAL_PREPARATION_OK final_scene={final} output_dir={outdir} spec={cfg['id']}")
if __name__=="__main__": main()
