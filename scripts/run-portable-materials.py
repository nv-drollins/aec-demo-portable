#!/usr/bin/env python3
"""Run the only supported portable Phase 7 materials adapter."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TRANSPORT_PATH = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-materials/assets/portable-cliff-house-materials-v1.json"


def load_transport():
    module_spec = importlib.util.spec_from_file_location("portable_blender_transport", TRANSPORT_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load checked Blender transport: {TRANSPORT_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-materials-v1":
        raise RuntimeError("Portable materials specification has the wrong format")
    input_scene = (ROOT / spec["input_scene"]).resolve()
    output_scene = (ROOT / spec["output_scene"]).resolve()
    if not input_scene.is_file():
        raise RuntimeError(f"Approved Phase 6 checkpoint is missing: {input_scene}")
    output_scene.parent.mkdir(parents=True, exist_ok=True)
    transport = load_transport()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy, json, os\nspec=json.loads({embedded!r})\nactive=os.path.realpath(bpy.data.filepath)\nallowed={{os.path.realpath(path) for path in {allowed!r}}}\nif active not in allowed:\n    expected_input=os.path.realpath({str(input_scene)!r})\n    if os.path.isfile(expected_input):\n        print("PORTABLE_MATERIALS_INPUT_RELOAD="+expected_input)\n        bpy.ops.wm.open_mainfile(filepath=expected_input, load_ui=False)\n        active=os.path.realpath(bpy.data.filepath)\nif active not in allowed:\n    raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nphase6=bpy.data.collections.get(spec["phase6_collection"])\nmissing_material=[obj.name for obj in meshes if not any(slot.material for slot in obj.material_slots)]\nmissing_tag=[obj.name for obj in meshes if not obj.get("material","")]\nif len(meshes)!=spec["expected_meshes"] or phase6 is None or len(phase6.objects)!=10 or missing_material:\n    raise RuntimeError("Phase 7 input mismatch")\nexpected=set(spec["tag_assignments"])|{{obj.name for obj in phase6.objects}}\nif set(missing_tag) not in (expected,set()):\n    raise RuntimeError("Unexpected untagged mesh set")\nprint("PORTABLE_MATERIALS_INPUT_DATA="+json.dumps({{"scene":bpy.data.filepath,"meshes":len(meshes),"preserved":len(meshes)-len(phase6.objects),"entourage":len(phase6.objects),"missing_tags":len(missing_tag)}},separators=(",",":"),sort_keys=True))\nfor name,values in spec["final_materials"].items():\n    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)\n    mat.use_nodes=True\n    bsdf=next((node for node in mat.node_tree.nodes if node.type=="BSDF_PRINCIPLED"),None)\n    if bsdf is None: raise RuntimeError("Missing Principled BSDF for "+name)\n    bsdf.inputs["Base Color"].default_value=values["base_color"]\n    bsdf.inputs["Roughness"].default_value=values["roughness"]\n    bsdf.inputs["Metallic"].default_value=values["metallic"]\n    mat.diffuse_color=values["base_color"]\nfor obj in phase6.objects:\n    role=obj.get("aec_role","")\n    if role not in spec["role_materials"]: raise RuntimeError("Unexpected Phase 6 role: "+role)\n    material_name,tag=spec["role_materials"][role]\n    obj.data.materials.clear(); obj.data.materials.append(bpy.data.materials[material_name]); obj["material"]=tag\nfor name,tag in spec["tag_assignments"].items():\n    obj=bpy.data.objects.get(name)\n    if obj is None or obj.type!="MESH": raise RuntimeError("Missing tag target: "+name)\n    obj["material"]=tag\nallowed_tags=set(spec["allowed_tags"])\nmissing_material=[obj.name for obj in meshes if not any(slot.material for slot in obj.material_slots)]\nmissing_tag=[obj.name for obj in meshes if not obj.get("material","")]\ninvalid_tag=[obj.name+":"+str(obj.get("material")) for obj in meshes if obj.get("material","") not in allowed_tags]\nif missing_material or missing_tag or invalid_tag:\n    raise RuntimeError("Material cleanup failed: missing_material=%r missing_tag=%r invalid_tag=%r" % (missing_material,missing_tag,invalid_tag))\ntag_counts={{}}\nfor obj in meshes:\n    tag=obj["material"]; tag_counts[tag]=tag_counts.get(tag,0)+1\nglass_data=[]\nfor name in spec["required_glass_materials"]:\n    mat=bpy.data.materials.get(name)\n    if mat is None or not mat.use_nodes: raise RuntimeError("Missing delivered glass material: "+name)\n    bsdf=next((node for node in mat.node_tree.nodes if node.type=="BSDF_PRINCIPLED"),None)\n    if bsdf is None: raise RuntimeError("Missing glass Principled shader: "+name)\n    key="Transmission Weight" if "Transmission Weight" in bsdf.inputs else "Transmission"\n    transmission=float(bsdf.inputs[key].default_value)\n    if transmission < 0.24: raise RuntimeError("Delivered glass transmission is too low: "+name)\n    glass_data.append({{"name":name,"transmission":transmission}})\nprincipled=sum(1 for mat in {{slot.material for obj in meshes for slot in obj.material_slots if slot.material}} if mat.use_nodes and any(node.type=="BSDF_PRINCIPLED" for node in mat.node_tree.nodes))\nscene=bpy.context.scene; scene["aec_phase"]=7; scene["aec_phase_name"]="materials"; scene["aec_material_spec_id"]=spec["id"]\ntext=bpy.data.texts.get("AEC_PHASE7_README") or bpy.data.texts.new("AEC_PHASE7_README")\ntext.clear(); text.write("Delivered building/site shaders preserved. Phase 6 entourage finalized.\\nTags: "+json.dumps(tag_counts,sort_keys=True)+"\\n")\nfor obj in bpy.context.selected_objects: obj.select_set(False)\nfor obj in meshes:\n    if obj.name not in {{"Plane","Sphere"}}: obj.select_set(True)\nif phase6.objects: bpy.context.view_layer.objects.active=phase6.objects[0]\nfor window in bpy.context.window_manager.windows:\n    screen=window.screen\n    for area in screen.areas:\n        if area.type!="VIEW_3D": continue\n        area.spaces.active.shading.type="MATERIAL"\n        try:\n            region=next(r for r in area.regions if r.type=="WINDOW")\n            with bpy.context.temp_override(window=window,screen=screen,area=area,region=region): bpy.ops.view3d.view_selected(use_all_regions=False)\n        except Exception as exc: print("PORTABLE_MATERIALS_VIEW_WARNING="+repr(exc))\nos.makedirs(os.path.dirname({str(output_scene)!r}),exist_ok=True)\nbpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True)\nprint("PORTABLE_MATERIALS_ASSIGNMENT_DATA="+json.dumps({{"output":bpy.data.filepath,"meshes":len(meshes),"preserved":spec["preserved_source_meshes"],"entourage":len(phase6.objects),"tag_counts":tag_counts}},separators=(",",":"),sort_keys=True))\nprint("PORTABLE_MATERIALS_SHADER_DATA="+json.dumps({{"principled_materials":principled,"glass":glass_data,"final_materials":sorted(spec["final_materials"])}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender materials adapter failed: {response}")
    result = response.get("result", {}).get("result", "")
    markers = {
        "input": "PORTABLE_MATERIALS_INPUT_DATA=",
        "assignment": "PORTABLE_MATERIALS_ASSIGNMENT_DATA=",
        "shader": "PORTABLE_MATERIALS_SHADER_DATA=",
    }
    if any(marker not in result for marker in markers.values()):
        raise RuntimeError("Blender materials adapter returned incomplete markers")
    data = {key: json.loads(result.split(marker, 1)[1].splitlines()[0]) for key, marker in markers.items()}
    if Path(data["assignment"]["output"]).resolve() != output_scene:
        raise RuntimeError(f"Materials checkpoint was saved to the wrong path: {data['assignment']}")
    print(
        f"PORTABLE_MATERIALS_INPUT_OK scene={data['input']['scene']} meshes={data['input']['meshes']} "
        f"preserved={data['input']['preserved']} entourage={data['input']['entourage']} "
        f"missing_tags={data['input']['missing_tags']}"
    )
    print(
        f"PORTABLE_MATERIALS_ASSIGNMENT_OK output={output_scene} meshes={data['assignment']['meshes']} "
        f"preserved={data['assignment']['preserved']} entourage={data['assignment']['entourage']} "
        f"tags={json.dumps(data['assignment']['tag_counts'], separators=(',', ':'))}"
    )
    print(
        f"PORTABLE_MATERIALS_SHADER_OK principled_materials={data['shader']['principled_materials']} "
        f"glass={json.dumps(data['shader']['glass'], separators=(',', ':'))} "
        f"final_materials={json.dumps(data['shader']['final_materials'], separators=(',', ':'))}"
    )
    print(f"PORTABLE_MATERIALS_PREPARATION_OK output={output_scene} spec={spec['id']}")


if __name__ == "__main__":
    main()
