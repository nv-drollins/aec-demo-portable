#!/usr/bin/env python3
"""Run the only supported portable Phase 5 landscaping/site-context adapter."""

from __future__ import annotations

import json
from pathlib import Path
import socket
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "skills/build-portable-blender-landscaping/assets/portable-cliff-house-landscaping-v1.json"


def blender_execute(code: str, timeout: int = 120) -> dict:
    payload = json.dumps(
        {"type": "execute_code", "params": {"code": code}}
    ).encode()
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


def validate_freecad(spec: dict) -> dict:
    rpc = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True)
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC is not healthy on 127.0.0.1:9875")
    expected = spec["required_freecad_documents"]
    code = f'''import FreeCAD as App, json\nexpected={expected!r}\nrows=[]\nfor name in expected:\n    if name not in App.listDocuments():\n        raise RuntimeError("Missing approved FreeCAD document: " + name)\n    doc=App.getDocument(name)\n    shaped=sum(1 for obj in doc.Objects if hasattr(obj,"Shape") and not obj.Shape.isNull())\n    rows.append({{"name":name,"objects":len(doc.Objects),"shape_objects":shaped,"file":doc.FileName}})\nprint("PORTABLE_LANDSCAPING_FREECAD_DATA="+json.dumps(rows,separators=(",",":")))\n'''
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(result.get("error", result.get("message", str(result))))
    output = result["message"].rsplit("Output: ", 1)[-1].strip()
    marker = "PORTABLE_LANDSCAPING_FREECAD_DATA="
    if marker not in output:
        raise RuntimeError("FreeCAD validation returned no data marker")
    rows = json.loads(output.split(marker, 1)[1].splitlines()[0])
    if any(not row["file"] or row["shape_objects"] < 1 for row in rows):
        raise RuntimeError(f"FreeCAD prerequisite is unsaved or empty: {rows}")
    return {row["name"]: row for row in rows}


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-landscaping-v1":
        raise RuntimeError("Portable landscaping specification has the wrong format")
    source = (ROOT / spec["source_scene"]).resolve()
    output = (ROOT / spec["output_scene"]).resolve()
    if not source.is_file():
        raise RuntimeError(f"Delivered Blender target is missing: {source}")

    freecad = validate_freecad(spec)
    summary = ",".join(
        f"{name}:{row['shape_objects']}" for name, row in freecad.items()
    )
    print(
        f"PORTABLE_LANDSCAPING_FREECAD_OK documents={len(freecad)} "
        f"shape_objects={summary}"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed_paths = [str(source), str(output)]
    code = f'''import bpy, json, os\nfrom mathutils import Vector\nspec=json.loads({embedded!r})\nallowed={{os.path.realpath(path) for path in {allowed_paths!r}}}\nactive=os.path.realpath(bpy.data.filepath)\nif active not in allowed:\n    raise RuntimeError("Wrong Blender scene is open: " + bpy.data.filepath)\nrole_by_name={{name:role for role,names in spec["roles"].items() for name in names}}\nif set(role_by_name) != {{item["name"] for item in spec["targets"]}}:\n    raise RuntimeError("Landscaping role map and target list disagree")\nfor item in spec["targets"]:\n    obj=bpy.data.objects.get(item["name"])\n    if obj is None or obj.type != "MESH":\n        raise RuntimeError("Missing landscaping target mesh: " + item["name"] )\n    points=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]\n    actual=[min(point[i] for point in points) for i in range(3)]+[max(point[i] for point in points) for i in range(3)]\n    expected=item["min"]+item["max"]\n    if any(abs(a-b) > 1e-8 for a,b in zip(actual,expected)):\n        raise RuntimeError("Landscaping target anchor mismatch: " + item["name"] + " " + repr(actual))\n    materials=[slot.material.name if slot.material else None for slot in obj.material_slots]\n    if item["material"] not in materials:\n        raise RuntimeError("Landscaping material mismatch: %s expected %s got %r" % (item["name"],item["material"],materials))\nprint("PORTABLE_LANDSCAPING_TARGET_DATA="+json.dumps({{"scene":bpy.data.filepath,"objects":len(spec["targets"]),"roles":{{role:len(names) for role,names in spec["roles"].items()}},"materials":sorted({{item["material"] for item in spec["targets"]}})}},separators=(",",":"),sort_keys=True))\ncollection=bpy.data.collections.get(spec["collection"])\nif collection is None:\n    collection=bpy.data.collections.new(spec["collection"] )\n    bpy.context.scene.collection.children.link(collection)\nfor item in spec["targets"]:\n    obj=bpy.data.objects[item["name"]]\n    if collection.objects.get(obj.name) is None:\n        collection.objects.link(obj)\n    obj["aec_phase"]=5\n    obj["aec_role"]=role_by_name[obj.name]\ncollection["aec_phase"]=5\ncollection["aec_spec_id"]=spec["id"]\nbpy.context.scene["aec_phase"]=5\nbpy.context.scene["aec_phase_name"]="landscaping_site_context"\nbpy.context.scene["aec_provenance_note"]=spec["provenance_note"]\ntext=bpy.data.texts.get("AEC_PHASE5_README") or bpy.data.texts.new("AEC_PHASE5_README")\ntext.clear()\ntext.write(spec["provenance_note"]+"\\n\\nChecked objects: "+str(len(spec["targets"]))+"\\nRoles: "+json.dumps({{role:len(names) for role,names in spec["roles"].items()}},sort_keys=True)+"\\n")\nfor obj in bpy.context.selected_objects:\n    obj.select_set(False)\nfor item in spec["targets"]:\n    obj=bpy.data.objects[item["name"]]\n    obj.hide_set(False)\n    obj.hide_render=False\n    obj.select_set(True)\nif spec["targets"]:\n    bpy.context.view_layer.objects.active=bpy.data.objects[spec["targets"][0]["name"]]\nfor window in bpy.context.window_manager.windows:\n    screen=window.screen\n    for area in screen.areas:\n        if area.type != "VIEW_3D":\n            continue\n        space=area.spaces.active\n        space.shading.type="MATERIAL"\n        try:\n            with bpy.context.temp_override(window=window,screen=screen,area=area,region=next(r for r in area.regions if r.type=="WINDOW")):\n                bpy.ops.view3d.view_selected(use_all_regions=False)\n        except Exception as exc:\n            print("PORTABLE_LANDSCAPING_VIEW_WARNING="+repr(exc))\nos.makedirs(os.path.dirname({str(output)!r}),exist_ok=True)\nbpy.ops.wm.save_as_mainfile(filepath={str(output)!r},compress=True)\nprint("PORTABLE_LANDSCAPING_BUILD_DATA="+json.dumps({{"output":bpy.data.filepath,"collection":collection.name,"collection_objects":len(collection.objects),"selected":len(bpy.context.selected_objects)}},separators=(",",":"),sort_keys=True))\n'''
    response = blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender landscaping adapter failed: {response}")
    remote_output = response.get("result", {}).get("result", "")
    target_marker = "PORTABLE_LANDSCAPING_TARGET_DATA="
    build_marker = "PORTABLE_LANDSCAPING_BUILD_DATA="
    if target_marker not in remote_output or build_marker not in remote_output:
        raise RuntimeError("Blender landscaping adapter returned incomplete markers")
    target = json.loads(remote_output.split(target_marker, 1)[1].splitlines()[0])
    build = json.loads(remote_output.split(build_marker, 1)[1].splitlines()[0])
    if Path(build["output"]).resolve() != output:
        raise RuntimeError(f"Landscaping checkpoint was saved to the wrong path: {build}")
    if build["collection_objects"] != len(spec["targets"]):
        raise RuntimeError(f"Landscaping collection is incomplete: {build}")
    print(
        f"PORTABLE_LANDSCAPING_TARGET_OK scene={target['scene']} "
        f"objects={target['objects']} roles={json.dumps(target['roles'], separators=(',', ':'))} "
        f"materials={json.dumps(target['materials'], separators=(',', ':'))}"
    )
    print(
        f"PORTABLE_LANDSCAPING_BUILD_OK output={output} "
        f"collection={build['collection']} objects={build['collection_objects']} "
        f"selected={build['selected']}"
    )
    print(
        f"PORTABLE_LANDSCAPING_PREPARATION_OK output={output} "
        f"spec={spec['id']} representation={spec['representation']!r}"
    )


if __name__ == "__main__":
    main()
