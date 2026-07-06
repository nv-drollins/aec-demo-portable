#!/usr/bin/env python3
"""Run the only supported portable Phase 9 lighting adapter."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSPORT_PATH = ROOT / "scripts/run-portable-camera.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-lighting/assets/portable-cliff-house-lighting-v1.json"

def load_transport():
    module_spec = importlib.util.spec_from_file_location("portable_camera_transport", TRANSPORT_PATH)
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
    previews = {name:(ROOT / path).resolve() for name,path in spec["previews"].items()}
    if not input_scene.is_file() or not hdri.is_file():
        raise RuntimeError(f"Phase 9 input is missing: scene={input_scene} hdri={hdri}")
    output_scene.parent.mkdir(parents=True, exist_ok=True)
    for path in previews.values(): path.parent.mkdir(parents=True, exist_ok=True)
    transport = load_transport()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy,json,os\nspec=json.loads({embedded!r})\nif os.path.realpath(bpy.data.filepath) not in {{os.path.realpath(path) for path in {allowed!r}}}: raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\nrequired={{"Camera_day",spec["hero_camera"],spec["compass_camera"],"patio_sweep_cam"}}\ncameras={{obj.name for obj in bpy.data.objects if obj.type=="CAMERA"}}\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nif not required.issubset(cameras) or len(meshes)!=160 or any(not obj.get("material","") for obj in meshes): raise RuntimeError("Phase 8 checkpoint is incomplete")\nprint("PORTABLE_LIGHTING_INPUT_DATA="+json.dumps({{"scene":bpy.data.filepath,"active_camera":bpy.context.scene.camera.name if bpy.context.scene.camera else None,"meshes":len(meshes),"cameras":sorted(cameras)}},separators=(",",":"),sort_keys=True))\nold=bpy.data.worlds.get(spec["world"])\nif old is not None: bpy.data.worlds.remove(old,do_unlink=True)\nworld=bpy.data.worlds.new(spec["world"]); world.use_nodes=True; nodes=world.node_tree.nodes; nodes.clear(); links=world.node_tree.links\ntexcoord=nodes.new("ShaderNodeTexCoord"); mapping=nodes.new("ShaderNodeMapping"); environment=nodes.new("ShaderNodeTexEnvironment"); gamma=nodes.new("ShaderNodeGamma"); background=nodes.new("ShaderNodeBackground"); output=nodes.new("ShaderNodeOutputWorld")\ntexcoord.name="AEC_Texture_Coordinate"; mapping.name="AEC_HDRI_Mapping"; environment.name="AEC_HDRI_Environment"; gamma.name="AEC_HDRI_Gamma"; background.name="AEC_HDRI_Background"; output.name="AEC_World_Output"\nmapping.inputs["Rotation"].default_value[2]=spec["rotation_z"]; environment.image=bpy.data.images.load({str(hdri)!r},check_existing=True); gamma.inputs["Gamma"].default_value=spec["gamma"]; background.inputs["Strength"].default_value=spec["strength"]\nlinks.new(texcoord.outputs["Generated"],mapping.inputs["Vector"]); links.new(mapping.outputs["Vector"],environment.inputs["Vector"]); links.new(environment.outputs["Color"],gamma.inputs["Color"]); links.new(gamma.outputs["Color"],background.inputs["Color"]); links.new(background.outputs["Background"],output.inputs["Surface"]); bpy.context.scene.world=world\nhidden=bpy.data.collections.get(spec["hidden_collection"]) or bpy.data.collections.new(spec["hidden_collection"])\nif hidden.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(hidden)\nfor obj in [obj for obj in bpy.data.objects if obj.type=="LIGHT" and obj.data.type in {{"SUN","AREA"}}]:\n    obj.hide_render=True; obj.hide_viewport=True; obj.hide_set(True); obj.lock_location=(True,True,True); obj.lock_rotation=(True,True,True); obj.lock_scale=(True,True,True)\n    for collection in list(obj.users_collection): collection.objects.unlink(obj)\n    hidden.objects.link(obj)\nold_fire=bpy.data.objects.get(spec["firelight"]["name"])\nif old_fire is not None: bpy.data.objects.remove(old_fire,do_unlink=True)\nlight_data=bpy.data.lights.new(spec["firelight"]["name"]+"_Data",type="POINT"); light_data.energy=spec["firelight"]["energy"]; light_data.color=spec["firelight"]["color"]; light_data.shadow_soft_size=spec["firelight"]["radius"]\nfire=bpy.data.objects.new(spec["firelight"]["name"],light_data); bpy.context.scene.collection.objects.link(fire); fire.location=spec["firelight"]["location"]\nhero=bpy.data.objects[spec["hero_camera"]]; compass=bpy.data.objects[spec["compass_camera"]]\ntarget=bpy.data.objects.get(spec["compass_target"]) or bpy.data.objects.new(spec["compass_target"],None)\nif not target.users_collection: bpy.context.scene.collection.objects.link(target)\ntarget.location=spec["compass_center"]; target.empty_display_type="SPHERE"; target.empty_display_size=0.001\nfor constraint in list(compass.constraints): compass.constraints.remove(constraint)\ntrack=compass.constraints.new(type="TRACK_TO"); track.target=target; track.track_axis="TRACK_NEGATIVE_Z"; track.up_axis="UP_Y"\nscene=bpy.context.scene; scene.camera=hero; scene["aec_phase"]=9; scene["aec_phase_name"]="lighting"; scene["aec_lighting_spec_id"]=spec["id"]\nlights=[{{"name":obj.name,"type":obj.data.type,"energy":obj.data.energy,"hide_render":obj.hide_render}} for obj in bpy.data.objects if obj.type=="LIGHT"]\nrenderable_nonfire=[item for item in lights if item["name"]!=fire.name and not item["hide_render"]]\nif renderable_nonfire: raise RuntimeError("Unexpected renderable light: "+repr(renderable_nonfire))\nos.makedirs(os.path.dirname({str(output_scene)!r}),exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True)\nprint("PORTABLE_LIGHTING_WORLD_DATA="+json.dumps({{"world":world.name,"hdri":environment.image.filepath,"rotation_z":mapping.inputs["Rotation"].default_value[2],"gamma":gamma.inputs["Gamma"].default_value,"strength":background.inputs["Strength"].default_value}},separators=(",",":"),sort_keys=True))\nprint("PORTABLE_LIGHTING_LIGHTS_DATA="+json.dumps({{"lights":lights,"renderable_nonfire":len(renderable_nonfire)}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_request("execute_code", {"code":code})
    if response.get("status") != "success": raise RuntimeError(f"Blender lighting adapter failed: {response}")
    result = response.get("result",{}).get("result","")
    markers = {"input":"PORTABLE_LIGHTING_INPUT_DATA=","world":"PORTABLE_LIGHTING_WORLD_DATA=","lights":"PORTABLE_LIGHTING_LIGHTS_DATA="}
    if any(marker not in result for marker in markers.values()): raise RuntimeError("Lighting adapter returned incomplete markers")
    data = {key:json.loads(result.split(marker,1)[1].splitlines()[0]) for key,marker in markers.items()}
    shots = {}
    for name,(dx,dy) in {"NW":(-1,1),"NE":(1,1),"SE":(1,-1),"SW":(-1,-1)}.items():
        radius=spec["compass_radius"]/math.sqrt(2); location=[spec["compass_center"][0]+dx*radius,spec["compass_center"][1]+dy*radius,spec["compass_height"]]
        view = f'''import bpy\ncam=bpy.data.objects[{spec["compass_camera"]!r}]; cam.location={location!r}; bpy.context.scene.camera=cam; bpy.context.view_layer.update()\nfor window in bpy.context.window_manager.windows:\n for area in window.screen.areas:\n  if area.type=="VIEW_3D":\n   area.spaces.active.shading.type="MATERIAL"; area.spaces.active.shading.use_scene_world_render=True\n   try:\n    region=next(r for r in area.regions if r.type=="WINDOW")\n    with bpy.context.temp_override(window=window,screen=window.screen,area=area,region=region): bpy.ops.view3d.view_camera()\n   except Exception: pass\nprint("PORTABLE_LIGHTING_VIEW_OK={name}")\n'''
        transport.blender_request("execute_code", {"code":view})
        shot_response=transport.blender_request("get_viewport_screenshot",{"max_size":1200,"filepath":str(previews[name]),"format":"png"},timeout=60); shot=shot_response.get("result",{})
        if shot_response.get("status")!="success" or not shot.get("success") or not previews[name].is_file() or previews[name].stat().st_size<10000: raise RuntimeError(f"Lighting preview {name} failed: {shot_response}")
        shots[name]={"path":str(previews[name]),"width":shot["width"],"height":shot["height"],"bytes":previews[name].stat().st_size}
    finish=f'''import bpy\nscene=bpy.context.scene; scene.camera=bpy.data.objects[{spec["hero_camera"]!r}]\nfor window in bpy.context.window_manager.windows:\n for area in window.screen.areas:\n  if area.type=="VIEW_3D":\n   try:\n    region=next(r for r in area.regions if r.type=="WINDOW")\n    with bpy.context.temp_override(window=window,screen=window.screen,area=area,region=region): bpy.ops.view3d.view_camera()\n   except Exception: pass\nbpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True); print("PORTABLE_LIGHTING_FINISH_OK="+scene.camera.name)\n'''
    finish_response=transport.blender_request("execute_code",{"code":finish})
    if "PORTABLE_LIGHTING_FINISH_OK=ocean_view" not in finish_response.get("result",{}).get("result",""): raise RuntimeError("Lighting adapter did not restore hero camera")
    print(f"PORTABLE_LIGHTING_INPUT_OK scene={data['input']['scene']} active_camera={data['input']['active_camera']} meshes={data['input']['meshes']}")
    print(f"PORTABLE_LIGHTING_WORLD_OK world={data['world']['world']} hdri={data['world']['hdri']} rotation_z={data['world']['rotation_z']} gamma={data['world']['gamma']} strength={data['world']['strength']}")
    print(f"PORTABLE_LIGHTING_LIGHTS_OK lights={json.dumps(data['lights']['lights'],separators=(',',':'))} renderable_nonfire={data['lights']['renderable_nonfire']}")
    print(f"PORTABLE_LIGHTING_PREVIEWS_OK count={len(shots)} previews={json.dumps(shots,separators=(',',':'))}")
    print(f"PORTABLE_LIGHTING_PREPARATION_OK output={output_scene} hero=ocean_view spec={spec['id']}")

if __name__ == "__main__":
    main()
