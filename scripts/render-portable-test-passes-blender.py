"""Executed inside Blender by the checked Phase 11 runner."""

import bpy
import json
import os
from pathlib import Path
from mathutils import Vector

spec=json.loads(Path(os.environ["AEC_PORTABLE_TEST_SPEC"]).read_text())
output_scene=Path(os.environ["AEC_PORTABLE_TEST_SCENE"])
output_dir=Path(os.environ["AEC_PORTABLE_TEST_DIR"])
output_dir.mkdir(parents=True,exist_ok=True)
paths={name:output_dir/filename for name,filename in spec["files"].items()}
scene=bpy.context.scene
camera=bpy.data.objects.get(spec["hero_camera"])
meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]
if camera is None or len(meshes)!=spec["expected_meshes"]:
    raise RuntimeError("Phase 11 input camera or mesh count is invalid")
if any(not obj.get("material","") for obj in meshes):
    raise RuntimeError("Phase 11 requires every mesh to have a segmentation tag")
scene.camera=camera
print("PORTABLE_TEST_RENDER_INPUT_DATA="+json.dumps({"scene":bpy.data.filepath,"camera":camera.name,"meshes":len(meshes),"resolution":spec["resolution"]},separators=(",",":"),sort_keys=True))

state={
    "engine":scene.render.engine,"x":scene.render.resolution_x,"y":scene.render.resolution_y,
    "pct":scene.render.resolution_percentage,"filepath":scene.render.filepath,
    "format":scene.render.image_settings.file_format,"mode":scene.render.image_settings.color_mode,
    "depth":scene.render.image_settings.color_depth,"transparent":scene.render.film_transparent,
    "world":scene.world,"view":scene.view_settings.view_transform,
    "samples":scene.cycles.samples,"denoise":scene.cycles.use_denoising,
}
materials={obj.name:list(obj.data.materials) for obj in meshes}
hidden={obj.name:obj.hide_render for obj in meshes}

def restore_materials():
    for obj in meshes:
        obj.data.materials.clear()
        for material in materials[obj.name]:
            obj.data.materials.append(material)

def emission_material(name,color):
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes=True; nodes=material.node_tree.nodes; nodes.clear()
    emit=nodes.new("ShaderNodeEmission"); emit.inputs["Color"].default_value=color; emit.inputs["Strength"].default_value=1.0
    output=nodes.new("ShaderNodeOutputMaterial"); material.node_tree.links.new(emit.outputs["Emission"],output.inputs["Surface"])
    return material

def assign_single(obj,material):
    obj.data.materials.clear(); obj.data.materials.append(material)

black_world=bpy.data.worlds.get("AEC_Test_Black_World") or bpy.data.worlds.new("AEC_Test_Black_World")
black_world.use_nodes=True
background=next((n for n in black_world.node_tree.nodes if n.type=="BACKGROUND"),None)
if background is None: background=black_world.node_tree.nodes.new("ShaderNodeBackground")
background.inputs["Color"].default_value=(0,0,0,1); background.inputs["Strength"].default_value=0.0

try:
    scene.render.resolution_x=spec["resolution"][0]; scene.render.resolution_y=spec["resolution"][1]; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_depth="8"; scene.render.film_transparent=False

    scene.render.engine="CYCLES"; scene.cycles.device="GPU"; scene.cycles.samples=spec["beauty_samples"]; scene.cycles.use_denoising=True
    scene.render.image_settings.color_mode="RGB"; scene.render.filepath=str(paths["beauty"])
    bpy.ops.render.render(write_still=True)
    print("PORTABLE_TEST_RENDER_BEAUTY_DATA="+json.dumps({"path":str(paths["beauty"]),"bytes":paths["beauty"].stat().st_size,"samples":scene.cycles.samples},separators=(",",":"),sort_keys=True))

    points=[]
    for obj in meshes:
        if obj.name in {"Plane","Sphere"}: continue
        points.extend(obj.matrix_world@Vector(corner) for corner in obj.bound_box)
    distances=[(point-camera.location).length for point in points]
    near=max(min(distances),1e-6); far=max(distances)
    depth=bpy.data.materials.get("AEC_Test_Depth") or bpy.data.materials.new("AEC_Test_Depth")
    depth.use_nodes=True; nodes=depth.node_tree.nodes; nodes.clear(); links=depth.node_tree.links
    camera_data=nodes.new("ShaderNodeCameraData"); mapping=nodes.new("ShaderNodeMapRange"); emit=nodes.new("ShaderNodeEmission"); output=nodes.new("ShaderNodeOutputMaterial")
    mapping.inputs["From Min"].default_value=near; mapping.inputs["From Max"].default_value=far; mapping.inputs["To Min"].default_value=1.0; mapping.inputs["To Max"].default_value=0.0; mapping.clamp=True
    links.new(camera_data.outputs["View Distance"],mapping.inputs["Value"]); links.new(mapping.outputs["Result"],emit.inputs["Color"]); links.new(emit.outputs["Emission"],output.inputs["Surface"])
    for obj in meshes:
        if obj.name in {"Plane","Sphere"}: obj.hide_render=True
        else: assign_single(obj,depth)
    scene.world=black_world; scene.view_settings.view_transform="Raw"; scene.render.engine="BLENDER_EEVEE"; scene.render.image_settings.color_mode="RGB"; scene.render.filepath=str(paths["depth"])
    bpy.ops.render.render(write_still=True)
    print("PORTABLE_TEST_RENDER_DEPTH_DATA="+json.dumps({"path":str(paths["depth"]),"bytes":paths["depth"].stat().st_size,"near":near,"far":far},separators=(",",":"),sort_keys=True))

    restore_materials()
    palette={
        "wall":(0.784,0.427,0.404,1),"travertine_white":(0.784,0.427,0.404,1),"concrete_dark":(0.784,0.427,0.404,1),
        "window":(0.533,0.737,0.761,1),"aluminum_dark":(0.533,0.737,0.761,1),"glass_railing":(0.533,0.737,0.761,1),"water_blue":(0.533,0.737,0.761,1),
        "wood_walnut":(0.773,0.659,0.447,1),"roof":(0.373,0.447,0.780,1),"terrain":(0.08,0.25,0.08,1)
    }
    seg_mats={tag:emission_material("AEC_Test_Seg_"+tag,color) for tag,color in palette.items()}
    for obj in meshes:
        if obj.name in {"Plane","Sphere"}: obj.hide_render=True
        else: assign_single(obj,seg_mats.get(obj["material"],seg_mats["wall"]))
    scene.render.image_settings.color_mode="RGB"; scene.render.filepath=str(paths["segmentation"])
    bpy.ops.render.render(write_still=True)
    print("PORTABLE_TEST_RENDER_SEGMENTATION_DATA="+json.dumps({"path":str(paths["segmentation"]),"bytes":paths["segmentation"].stat().st_size,"categories":len(seg_mats)},separators=(",",":"),sort_keys=True))
finally:
    restore_materials()
    for obj in meshes: obj.hide_render=hidden[obj.name]
    scene.render.engine=state["engine"]; scene.render.resolution_x=state["x"]; scene.render.resolution_y=state["y"]; scene.render.resolution_percentage=state["pct"]
    scene.render.filepath=state["filepath"]; scene.render.image_settings.file_format=state["format"]; scene.render.image_settings.color_mode=state["mode"]; scene.render.image_settings.color_depth=state["depth"]
    scene.render.film_transparent=state["transparent"]; scene.world=state["world"]; scene.view_settings.view_transform=state["view"]; scene.cycles.samples=state["samples"]; scene.cycles.use_denoising=state["denoise"]

scene.camera=camera; scene["aec_phase"]=11; scene["aec_phase_name"]="test_renders"; scene["aec_test_render_spec_id"]=spec["id"]
output_scene.parent.mkdir(parents=True,exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=str(output_scene),compress=True)
print("PORTABLE_TEST_RENDER_RESTORE_DATA="+json.dumps({"output":bpy.data.filepath,"camera":scene.camera.name,"world":scene.world.name if scene.world else None,"meshes":len(meshes)},separators=(",",":"),sort_keys=True))
