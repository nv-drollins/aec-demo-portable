#!/usr/bin/env python3
"""Run the only supported portable Phase 6 entourage adapter."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PHASE5_RUNNER = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-entourage/assets/portable-cliff-house-entourage-v1.json"


def load_transport():
    module_spec = importlib.util.spec_from_file_location(
        "portable_landscaping_runner", PHASE5_RUNNER
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load checked Blender transport: {PHASE5_RUNNER}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-entourage-v1":
        raise RuntimeError("Portable entourage specification has the wrong format")
    input_scene = (ROOT / spec["input_scene"]).resolve()
    output_scene = (ROOT / spec["output_scene"]).resolve()
    if not input_scene.is_file():
        raise RuntimeError(f"Approved Phase 5 checkpoint is missing: {input_scene}")
    output_scene.parent.mkdir(parents=True, exist_ok=True)

    transport = load_transport()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy, json, math, os\nfrom bpy_extras.object_utils import world_to_camera_view\nfrom mathutils import Vector\nspec=json.loads({embedded!r})\nactive=os.path.realpath(bpy.data.filepath)\nallowed={{os.path.realpath(path) for path in {allowed!r}}}\nif active not in allowed:\n    raise RuntimeError("Wrong Blender checkpoint is open: " + bpy.data.filepath)\nphase5=bpy.data.collections.get(spec["input_collection"])\nif phase5 is None or len(phase5.objects) != 15:\n    raise RuntimeError("Phase 5 landscaping collection is missing or incomplete")\nprint("PORTABLE_ENTOURAGE_INPUT_DATA="+json.dumps({{"scene":bpy.data.filepath,"phase5_collection":phase5.name,"phase5_objects":len(phase5.objects)}},separators=(",",":"),sort_keys=True))\nold=bpy.data.collections.get(spec["output_collection"])\nif old is not None:\n    for obj in list(old.objects):\n        bpy.data.objects.remove(obj,do_unlink=True)\n    bpy.data.collections.remove(old)\ncollection=bpy.data.collections.new(spec["output_collection"])\nbpy.context.scene.collection.children.link(collection)\nfor name,color in spec["materials"].items():\n    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)\n    mat.use_nodes=True\n    bsdf=mat.node_tree.nodes.get("Principled BSDF")\n    if bsdf:\n        bsdf.inputs["Base Color"].default_value=color\n        bsdf.inputs["Roughness"].default_value=0.62 if "Wood" in name else 0.42\n    mat.diffuse_color=color\n\ndef components(kind):\n    if kind=="lounge":\n        return [((0,0,0.45),(0.75,1.8,0.12)),((0,0.79,0.88),(0.75,0.12,0.9)),((-0.3,-0.65,0.2),(0.08,0.08,0.4)),((0.3,-0.65,0.2),(0.08,0.08,0.4)),((-0.3,0.65,0.2),(0.08,0.08,0.4)),((0.3,0.65,0.2),(0.08,0.08,0.4))]\n    if kind=="side_table":\n        return [((0,0,0.55),(0.55,0.55,0.08)),((0,0,0.27),(0.1,0.1,0.54))]\n    if kind=="firepit":\n        return [((0,0,0.18),(1.2,1.2,0.36)),((0,0,0.39),(0.72,0.72,0.06))]\n    if kind=="dining_table":\n        return [((0,0,0.75),(1.2,2.0,0.1)),((-0.45,-0.75,0.36),(0.1,0.1,0.72)),((0.45,-0.75,0.36),(0.1,0.1,0.72)),((-0.45,0.75,0.36),(0.1,0.1,0.72)),((0.45,0.75,0.36),(0.1,0.1,0.72))]\n    if kind=="dining_chair":\n        return [((0,0,0.48),(0.55,0.55,0.1)),((0,0.24,0.88),(0.55,0.08,0.85)),((-0.2,-0.2,0.22),(0.07,0.07,0.44)),((0.2,-0.2,0.22),(0.07,0.07,0.44)),((-0.2,0.2,0.22),(0.07,0.07,0.44)),((0.2,0.2,0.22),(0.07,0.07,0.44))]\n    if kind=="planter":\n        return [((0,0,0.35),(0.65,0.65,0.7)),((0,0,0.92),(0.12,0.12,0.5)),((-0.18,0,1.08),(0.3,0.18,0.25)),((0.18,0,1.08),(0.3,0.18,0.25))]\n    if kind=="vehicle":\n        return [((0,0,0.38),(1.9,4.5,0.76)),((0,0.15,0.98),(1.55,2.35,0.72)),((-0.98,-1.35,0.25),(0.18,0.62,0.5)),((0.98,-1.35,0.25),(0.18,0.62,0.5)),((-0.98,1.35,0.25),(0.18,0.62,0.5)),((0.98,1.35,0.25),(0.18,0.62,0.5))]\n    raise RuntimeError("Unknown entourage kind: "+kind)\n\ndef build_item(item):\n    verts=[]; faces=[]; scale=spec["scene_scale"]; angle=math.radians(item["rotation_degrees"]); c=math.cos(angle); s=math.sin(angle)\n    for center,size in components(item["kind"]):\n        base=len(verts); cx,cy,cz=center; sx,sy,sz=size\n        for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):\n            lx=(cx+x*sx/2)*scale; ly=(cy+y*sy/2)*scale; lz=(cz+z*sz/2)*scale\n            verts.append((item["location"][0]+lx*c-ly*s,item["location"][1]+lx*s+ly*c,item["location"][2]+lz))\n        faces.extend(tuple(base+i for i in face) for face in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)))\n    mesh=bpy.data.meshes.new(item["name"]+"_Mesh")\n    mesh.from_pydata(verts,[],faces); mesh.update()\n    obj=bpy.data.objects.new(item["name"],mesh)\n    collection.objects.link(obj)\n    obj.data.materials.append(bpy.data.materials[item["material"]])\n    obj["aec_phase"]=6; obj["aec_role"]=item["role"]; obj["aec_kind"]=item["kind"]; obj["aec_spec_id"]=spec["id"]\n    return obj\nobjects=[build_item(item) for item in spec["items"]]\nbpy.context.view_layer.update()\ndef bounds(obj):\n    pts=[obj.matrix_world@Vector(corner) for corner in obj.bound_box]\n    return ([min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)])\ndef overlap(a,b):\n    return all(a[0][i] < b[1][i]-1e-10 and a[1][i] > b[0][i]+1e-10 for i in range(3))\nboxes={{obj.name:bounds(obj) for obj in objects}}\npairs=[]\nfor i,left in enumerate(objects):\n    for right in objects[i+1:]:\n        if overlap(boxes[left.name],boxes[right.name]): pairs.append([left.name,right.name])\npool=(spec["pool_forbidden_bounds"]["min"],spec["pool_forbidden_bounds"]["max"])\npool_hits=[obj.name for obj in objects if overlap(boxes[obj.name],pool)]\nif pairs or pool_hits:\n    raise RuntimeError("Entourage layout collision: pairs=%r pool=%r" % (pairs,pool_hits))\nscene=bpy.context.scene; camera=scene.camera\nif camera is None:\n    raise RuntimeError("Phase 6 requires the existing render camera")\nvisibility={{}}\nfor obj in objects:\n    p=world_to_camera_view(scene,camera,obj.location)\n    visibility[obj.name]=[float(p.x),float(p.y),float(p.z)]\nnot_visible=[name for name,p in visibility.items() if not (0.0 <= p[0] <= 1.0 and 0.0 <= p[1] <= 1.0 and p[2] > 0.0)]\nif not_visible:\n    raise RuntimeError("Entourage item is outside the established camera: "+repr(not_visible))\nroles={{}}\nfor item in spec["items"]: roles[item["role"]]=roles.get(item["role"],0)+1\ncollection["aec_phase"]=6; collection["aec_spec_id"]=spec["id"]\nscene["aec_phase"]=6; scene["aec_phase_name"]="entourage_outdoor_living"; scene["aec_provenance_note"]=spec["provenance_note"]\ntext=bpy.data.texts.get("AEC_PHASE6_README") or bpy.data.texts.new("AEC_PHASE6_README")\ntext.clear(); text.write(spec["provenance_note"]+"\\n\\nItems: "+str(len(objects))+"\\nRoles: "+json.dumps(roles,sort_keys=True)+"\\n")\nfor obj in bpy.context.selected_objects: obj.select_set(False)\nfor obj in list(phase5.objects)+objects:\n    obj.hide_set(False); obj.select_set(True)\nbpy.context.view_layer.objects.active=objects[0]\nfor window in bpy.context.window_manager.windows:\n    screen=window.screen\n    for area in screen.areas:\n        if area.type != "VIEW_3D": continue\n        area.spaces.active.shading.type="MATERIAL"\n        try:\n            region=next(r for r in area.regions if r.type=="WINDOW")\n            with bpy.context.temp_override(window=window,screen=screen,area=area,region=region): bpy.ops.view3d.view_selected(use_all_regions=False)\n        except Exception as exc: print("PORTABLE_ENTOURAGE_VIEW_WARNING="+repr(exc))\nos.makedirs(os.path.dirname({str(output_scene)!r}),exist_ok=True)\nbpy.ops.wm.save_as_mainfile(filepath={str(output_scene)!r},compress=True)\nprint("PORTABLE_ENTOURAGE_BUILD_DATA="+json.dumps({{"output":bpy.data.filepath,"collection":collection.name,"objects":len(objects),"roles":roles}},separators=(",",":"),sort_keys=True))\nprint("PORTABLE_ENTOURAGE_LAYOUT_DATA="+json.dumps({{"camera":camera.name,"visible":len(visibility),"pair_overlaps":len(pairs),"pool_overlaps":len(pool_hits)}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender entourage adapter failed: {response}")
    remote_output = response.get("result", {}).get("result", "")
    markers = {
        "input": "PORTABLE_ENTOURAGE_INPUT_DATA=",
        "build": "PORTABLE_ENTOURAGE_BUILD_DATA=",
        "layout": "PORTABLE_ENTOURAGE_LAYOUT_DATA=",
    }
    if any(marker not in remote_output for marker in markers.values()):
        raise RuntimeError("Blender entourage adapter returned incomplete markers")
    data = {
        key: json.loads(remote_output.split(marker, 1)[1].splitlines()[0])
        for key, marker in markers.items()
    }
    if Path(data["build"]["output"]).resolve() != output_scene:
        raise RuntimeError(f"Entourage checkpoint was saved to the wrong path: {data['build']}")
    print(
        f"PORTABLE_ENTOURAGE_INPUT_OK scene={data['input']['scene']} "
        f"phase5_collection={data['input']['phase5_collection']} "
        f"phase5_objects={data['input']['phase5_objects']}"
    )
    print(
        f"PORTABLE_ENTOURAGE_BUILD_OK output={output_scene} "
        f"collection={data['build']['collection']} objects={data['build']['objects']} "
        f"roles={json.dumps(data['build']['roles'], separators=(',', ':'))}"
    )
    print(
        f"PORTABLE_ENTOURAGE_LAYOUT_OK camera={data['layout']['camera']} "
        f"visible={data['layout']['visible']} pair_overlaps={data['layout']['pair_overlaps']} "
        f"pool_overlaps={data['layout']['pool_overlaps']}"
    )
    print(
        f"PORTABLE_ENTOURAGE_PREPARATION_OK output={output_scene} "
        f"spec={spec['id']}"
    )


if __name__ == "__main__":
    main()
