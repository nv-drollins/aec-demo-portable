#!/usr/bin/env python3
"""Run the only supported portable Phase 4 architectural-detailing adapter."""

from __future__ import annotations

import json
from pathlib import Path
import socket
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "skills/build-portable-freecad-detailing/assets/portable-cliff-house-detailing-v1.json"
MANIFEST = ROOT / "runtime/generated/portable-detailing-target.json"
OUTPUT = ROOT / "projects/recorded_demo/freecad/portable_cliff_house_detailing.FCStd"
BUILDER = ROOT / "scripts/build-portable-detailing-freecad.py"


def blender_execute(code: str) -> dict:
    payload = json.dumps(
        {"type": "execute_code", "params": {"code": code}}
    ).encode()
    with socket.create_connection(("127.0.0.1", 9876), timeout=5) as client:
        client.settimeout(60)
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
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-freecad-detailing-v1":
        raise RuntimeError("Portable detailing specification has the wrong format")
    target_scene = ROOT / spec["target_scene"]
    embedded = json.dumps(spec, separators=(",", ":"))
    code = f'''import bpy, json\nfrom mathutils import Vector\nspec=json.loads({embedded!r})\n\ndef object_bounds(names):\n    points=[]\n    for name in names:\n        obj=bpy.data.objects.get(name)\n        if obj is None or obj.type != "MESH":\n            raise RuntimeError("Missing target mesh: " + name)\n        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)\n    return {{"min":[min(point[i] for point in points) for i in range(3)],"max":[max(point[i] for point in points) for i in range(3)]}}\n\ndef matches(name, selector):\n    if "names" in selector:\n        return name in selector["names"]\n    if not name.startswith(selector.get("prefix", "")):\n        return False\n    needles=selector.get("contains_any", [])\n    return not needles or any(needle in name for needle in needles)\n\nfor check in spec["target_checks"]:\n    bounds=object_bounds([check["object"]])\n    actual=bounds["min"]+bounds["max"]\n    expected=check["min"]+check["max"]\n    if any(abs(a-b) > 1e-8 for a,b in zip(actual,expected)):\n        raise RuntimeError("Target anchor mismatch: " + check["object"] + " " + repr(actual))\nrecords=[]\nused=set()\nfor entry in spec["structural_entries"]:\n    for name in entry["targets"]:\n        if name in used:\n            raise RuntimeError("Duplicate target object: " + name)\n        used.add(name)\n    records.append({{"name":entry["name"],"target_objects":entry["targets"],"bounds":object_bounds(entry["targets"]),"role":entry["role"],"group":entry["group"]}})\nselector_counts={{}}\nfor selector in spec["selectors"]:\n    names=sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH" and matches(obj.name, selector))\n    if len(names) != selector["expected_count"]:\n        raise RuntimeError("Selector count mismatch for %s: %d != %d" % (selector["id"],len(names),selector["expected_count"]))\n    selector_counts[selector["id"]]=len(names)\n    for name in names:\n        if name in used:\n            raise RuntimeError("Duplicate target object: " + name)\n        used.add(name)\n        records.append({{"name":selector["id"]+"__"+name,"target_objects":[name],"bounds":object_bounds([name]),"role":selector["role"],"group":selector["group"]}})\ndata={{"format":"aec-portable-detailing-target-v1","spec_id":spec["id"],"scene":bpy.data.filepath,"expected_scene":str({str(target_scene)!r}),"blender_units_to_mm":spec["blender_units_to_mm"],"translation_mm":spec["translation_mm"],"representation":spec["representation"],"provenance_note":spec["provenance_note"],"groups":spec["groups"],"role_style":spec["role_style"],"selector_counts":selector_counts,"target_object_count":len(used),"record_count":len(records),"records":records}}\nprint("PORTABLE_DETAILING_TARGET_DATA="+json.dumps(data,separators=(",",":"),sort_keys=True))\n'''
    response = blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender detailing validation failed: {response}")
    output = response.get("result", {}).get("result", "")
    marker = "PORTABLE_DETAILING_TARGET_DATA="
    if marker not in output:
        raise RuntimeError("Blender detailing validation returned no data marker")
    data = json.loads(output.split(marker, 1)[1].splitlines()[0])
    if Path(data["scene"]).resolve() != target_scene.resolve():
        raise RuntimeError(f"Wrong Blender target is open: {data['scene']}")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(
        f"PORTABLE_DETAILING_TARGET_OK scene={target_scene} "
        f"target_objects={data['target_object_count']} records={data['record_count']} "
        f"selectors={json.dumps(data['selector_counts'], separators=(',', ':'))}"
    )

    rpc = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True)
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC is not healthy on 127.0.0.1:9875")
    environment = {
        "AEC_PORTABLE_DETAILING_MANIFEST": str(MANIFEST),
        "AEC_PORTABLE_DETAILING_FCSTD": str(OUTPUT),
        "AEC_PORTABLE_SITE_DOCUMENT": "PortableCliffHouseSite",
        "AEC_PORTABLE_MASSING_DOCUMENT": "PortableCliffHouseMassing",
        "AEC_PORTABLE_DETAILING_DOCUMENT": "PortableCliffHouseDetailing",
    }
    assignments = "".join(
        f"os.environ[{key!r}] = {value!r}\n"
        for key, value in environment.items()
    )
    freecad_code = (
        "import os\n"
        + assignments
        + f"exec(compile(open({str(BUILDER)!r}, encoding='utf-8').read(), "
        + f"{str(BUILDER)!r}, 'exec'))"
    )
    result = rpc.execute_code(freecad_code)
    if not result.get("success"):
        raise RuntimeError(result.get("error", result.get("message", str(result))))
    build_output = result["message"].rsplit("Output: ", 1)[-1].strip()
    print(build_output)
    if "PORTABLE_DETAILING_BUILD_OK=" not in build_output:
        raise RuntimeError("Detailing builder did not return its success marker")
    print(
        f"PORTABLE_DETAILING_PREPARATION_OK output={OUTPUT} "
        f"spec={spec['id']} objects={data['record_count']}"
    )


if __name__ == "__main__":
    main()
