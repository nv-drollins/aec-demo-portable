#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 5."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-landscaping/assets/portable-cliff-house-landscaping-v1.json"


def load_runner():
    module_spec = importlib.util.spec_from_file_location(
        "portable_landscaping_runner", RUNNER_PATH
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load checked Phase 5 runner: {RUNNER_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != "aec-portable-blender-landscaping-v1":
        raise RuntimeError("Portable landscaping specification has the wrong format")
    source = (ROOT / spec["source_scene"]).resolve()
    output = (ROOT / spec["output_scene"]).resolve()
    if not source.is_file():
        raise RuntimeError(f"Delivered Blender target is missing: {source}")

    runner = load_runner()
    freecad = runner.validate_freecad(spec)

    embedded = json.dumps(spec, separators=(",", ":"))
    allowed_paths = [str(source), str(output)]
    code = f'''import bpy, json, os\nfrom mathutils import Vector\nspec=json.loads({embedded!r})\nallowed={{os.path.realpath(path) for path in {allowed_paths!r}}}\nactive=os.path.realpath(bpy.data.filepath)\nif active not in allowed:\n    raise RuntimeError("Wrong Blender scene is open: " + bpy.data.filepath)\nrole_by_name={{name:role for role,names in spec["roles"].items() for name in names}}\nif set(role_by_name) != {{item["name"] for item in spec["targets"]}}:\n    raise RuntimeError("Landscaping role map and target list disagree")\nfor item in spec["targets"]:\n    obj=bpy.data.objects.get(item["name"])\n    if obj is None or obj.type != "MESH":\n        raise RuntimeError("Missing landscaping target mesh: " + item["name"] )\n    points=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]\n    actual=[min(point[i] for point in points) for i in range(3)]+[max(point[i] for point in points) for i in range(3)]\n    expected=item["min"]+item["max"]\n    if any(abs(a-b) > 1e-8 for a,b in zip(actual,expected)):\n        raise RuntimeError("Landscaping target anchor mismatch: " + item["name"] )\n    materials=[slot.material.name if slot.material else None for slot in obj.material_slots]\n    if item["material"] not in materials:\n        raise RuntimeError("Landscaping material mismatch: " + item["name"] )\nprint("PORTABLE_LANDSCAPING_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"objects":len(spec["targets"]),"roles":len(spec["roles"])}},separators=(",",":"),sort_keys=True))\n'''
    response = runner.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender landscaping readiness check failed: {response}")
    remote_output = response.get("result", {}).get("result", "")
    marker = "PORTABLE_LANDSCAPING_READINESS_DATA="
    if marker not in remote_output:
        raise RuntimeError("Blender readiness check returned no data marker")
    blender = json.loads(remote_output.split(marker, 1)[1].splitlines()[0])
    print(
        f"PORTABLE_LANDSCAPING_READY_OK documents={len(freecad)} "
        f"targets={blender['objects']} roles={blender['roles']} "
        f"scene={blender['scene']} mutation=none"
    )


if __name__ == "__main__":
    main()
