#!/usr/bin/env python3
"""Run the only supported portable Phase 8 camera-placement adapter."""

from __future__ import annotations

import json
from pathlib import Path
import socket


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "skills/build-portable-blender-camera/assets/portable-cliff-house-camera-v1.json"


def blender_request(kind: str, params: dict | None = None, timeout: int = 120) -> dict:
    payload = json.dumps({"type": kind, "params": params or {}}).encode()
    with socket.create_connection(("127.0.0.1", 9876), timeout=5) as client:
        client.settimeout(timeout)
        client.sendall(payload)
        response = b""
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            response += chunk
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                continue
    raise RuntimeError("Blender MCP returned no valid response")


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-camera-v1":
        raise RuntimeError("Portable camera specification has the wrong format")
    input_scene = (ROOT / spec["input_scene"]).resolve()
    output_scene = (ROOT / spec["output_scene"]).resolve()
    preview = (ROOT / spec["preview"]).resolve()
    if not input_scene.is_file():
        raise RuntimeError(f"Approved Phase 7 checkpoint is missing: {input_scene}")
    output_scene.parent.mkdir(parents=True, exist_ok=True)
    preview.parent.mkdir(parents=True, exist_ok=True)
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy,json,os\nfrom bpy_extras.object_utils import world_to_camera_view\nfrom mathutils import Vector\nspec=json.loads({embedded!r})\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(path) for path in {allowed!r}}}: raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\nsource=bpy.data.objects.get(spec["source_camera"])\nif source is None or source.type!="CAMERA": raise RuntimeError("Delivered source camera is missing")\nactual=list(source.location)+list(source.rotation_euler)+[source.data.lens]\nexpected=spec["source_location"]+spec["source_rotation"]+[spec["hero_lens"]]\nif any(abs(a-b)>1e-7 for a,b in zip(actual,expected)): raise RuntimeError("Delivered camera anchor mismatch")\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nif len(meshes)!=160 or any(not obj.get("material","") for obj in meshes): raise RuntimeError("Phase 7 checkpoint is incomplete")\nprint("PORTABLE_CAMERA_INPUT_DATA="+json.dumps({{"scene":bpy.data.filepath,"source":source.name,"lens":source.data.lens,"meshes":len(meshes)}},separators=(",",":"),sort_keys=True))\nfor name in (spec["hero_camera"],spec["compass_camera"],spec["patio_camera"],spec["target_empty"]):\n    old=bpy.data.objects.get(name)\n    if old is not None: bpy.data.objects.remove(old,do_unlink=True)\nhero_data=source.data.copy(); hero_data.name=spec["hero_camera"]+"_Data"; hero_data.lens=spec["hero_lens"]\nhero=bpy.data.objects.new(spec["hero_camera"],hero_data); bpy.context.scene.collection.objects.link(hero); hero.matrix_world=source.matrix_world.copy()\nforward=hero.matrix_world.to_quaternion() @ Vector((0,0,-1))\ntarget=bpy.data.objects.new(spec["target_empty"],None); bpy.context.scene.collection.objects.link(target); target.empty_display_type="SPHERE"; target.empty_display_size=0.001; target.location=hero.location+forward*0.04\nconstraint=hero.constraints.new(type="TRACK_TO"); constraint.name="AEC_Hero_Track"; constraint.target=target; constraint.track_axis="TRACK_NEGATIVE_Z"; constraint.up_axis="UP_Y"\nfor name,lens in ((spec["compass_camera"],spec["compass_lens"]),(spec["patio_camera"],spec["patio_lens"])):\n    data=source.data.copy(); data.name=name+"_Data"; data.lens=lens\n    obj=bpy.data.objects.new(name,data); bpy.context.scene.collection.objects.link(obj); obj.matrix_world=source.matrix_world.copy(); obj["aec_utility_camera"]=True\nscene=bpy.context.scene; scene.camera=hero; scene.render.resolution_x=spec["resolution"][0]; scene.render.resolution_y=spec["resolution"][1]; scene.render.resolution_percentage=100\nscene["aec_phase"]=8; scene["aec_phase_name"]="camera_placement"; scene["aec_camera_spec_id"]=spec["id"]\nbpy.context.view_layer.update()\nframing={{}}\nfor name,coordinate in spec["anchors"].items():\n    point=world_to_camera_view(scene,hero,Vector(coordinate)); framing[name]=[float(point.x),float(point.y),float(point.z)]\ninvalid=[name for name,p in framing.items() if not (0.02<=p[0]<=0.98 and 0.02<=p[1]<=0.98 and p[2]>0)]\nif invalid: raise RuntimeError("Hero framing lost anchors: "+repr(invalid))\nfor obj in bpy.context.selected_objects: obj.select_set(False)\nhero.select_set(True); bpy.context.view_layer.objects.active=hero\nfor window in bpy.context.window_manager.windows:\n    screen=window.screen\n    for area in screen.areas:\n        if area.type!="VIEW_3D": continue\n        area.spaces.active.shading.type="MATERIAL"\n        try:\n            region=next(r for r in area.regions if r.type=="WINDOW")\n            with bpy.context.temp_override(window=window,screen=screen,area=area,region=region): bpy.ops.view3d.view_camera()\n        except Exception as exc: print("PORTABLE_CAMERA_VIEW_WARNING="+repr(exc))\nos.makedirs(os.path.dirname({str(output_scene)!r}),exist_ok=True)\nbpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True)\nprint("PORTABLE_CAMERA_BUILD_DATA="+json.dumps({{"output":bpy.data.filepath,"active":scene.camera.name,"cameras":sorted(obj.name for obj in bpy.data.objects if obj.type=="CAMERA"),"target":target.name}},separators=(",",":"),sort_keys=True))\nprint("PORTABLE_CAMERA_FRAMING_DATA="+json.dumps({{"lens":hero.data.lens,"resolution":[scene.render.resolution_x,scene.render.resolution_y],"anchors":framing}},separators=(",",":"),sort_keys=True))\n'''
    response = blender_request("execute_code", {"code": code})
    if response.get("status") != "success":
        raise RuntimeError(f"Blender camera adapter failed: {response}")
    result = response.get("result", {}).get("result", "")
    markers = {"input":"PORTABLE_CAMERA_INPUT_DATA=","build":"PORTABLE_CAMERA_BUILD_DATA=","framing":"PORTABLE_CAMERA_FRAMING_DATA="}
    if any(marker not in result for marker in markers.values()):
        raise RuntimeError("Blender camera adapter returned incomplete markers")
    data = {key:json.loads(result.split(marker,1)[1].splitlines()[0]) for key,marker in markers.items()}
    if Path(data["build"]["output"]).resolve() != output_scene:
        raise RuntimeError(f"Camera checkpoint was saved to the wrong path: {data['build']}")
    screenshot = blender_request("get_viewport_screenshot", {"max_size":1200,"filepath":str(preview),"format":"png"}, timeout=60)
    shot = screenshot.get("result", {})
    if screenshot.get("status") != "success" or not shot.get("success") or not preview.is_file() or preview.stat().st_size < 10000:
        raise RuntimeError(f"Hero camera preview failed: {screenshot}")
    print(f"PORTABLE_CAMERA_INPUT_OK scene={data['input']['scene']} source={data['input']['source']} lens={data['input']['lens']} meshes={data['input']['meshes']}")
    print(f"PORTABLE_CAMERA_BUILD_OK output={output_scene} active={data['build']['active']} cameras={json.dumps(data['build']['cameras'],separators=(',',':'))} target={data['build']['target']}")
    print(f"PORTABLE_CAMERA_FRAMING_OK lens={data['framing']['lens']} resolution={data['framing']['resolution'][0]}x{data['framing']['resolution'][1]} anchors={json.dumps(data['framing']['anchors'],separators=(',',':'))}")
    print(f"PORTABLE_CAMERA_PREVIEW_OK path={preview} width={shot['width']} height={shot['height']} bytes={preview.stat().st_size}")
    print(f"PORTABLE_CAMERA_PREPARATION_OK output={output_scene} spec={spec['id']}")


if __name__ == "__main__":
    main()
