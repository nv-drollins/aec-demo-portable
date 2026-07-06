#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 7."""

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
    transport = load_transport()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy, json, os\nspec=json.loads({embedded!r})\nactive=os.path.realpath(bpy.data.filepath)\nif active not in {{os.path.realpath(path) for path in {allowed!r}}}:\n    raise RuntimeError("Wrong Blender checkpoint is open: "+bpy.data.filepath)\nmeshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]\nmissing_material=[obj.name for obj in meshes if not any(slot.material for slot in obj.material_slots)]\nmissing_tag=[obj.name for obj in meshes if not obj.get("material","")]\nphase6=bpy.data.collections.get(spec["phase6_collection"])\nif len(meshes)!=spec["expected_meshes"] or missing_material or phase6 is None or len(phase6.objects)!=10:\n    raise RuntimeError("Materials readiness mismatch: meshes=%d missing_material=%r phase6=%r" % (len(meshes),missing_material,None if phase6 is None else len(phase6.objects)))\nexpected=set(spec["tag_assignments"])|{{obj.name for obj in phase6.objects}}\nif set(missing_tag) not in (expected,set()):\n    raise RuntimeError("Unexpected untagged mesh set")\nprint("PORTABLE_MATERIALS_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"meshes":len(meshes),"source_meshes":len(meshes)-len(phase6.objects),"entourage":len(phase6.objects),"missing_materials":len(missing_material),"missing_tags":len(missing_tag),"glass":spec["required_glass_materials"]}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender materials readiness check failed: {response}")
    result = response.get("result", {}).get("result", "")
    marker = "PORTABLE_MATERIALS_READINESS_DATA="
    if marker not in result:
        raise RuntimeError("Materials readiness check returned no data marker")
    data = json.loads(result.split(marker, 1)[1].splitlines()[0])
    print(
        f"PORTABLE_MATERIALS_READY_OK meshes={data['meshes']} "
        f"source_meshes={data['source_meshes']} entourage={data['entourage']} "
        f"missing_materials={data['missing_materials']} missing_tags={data['missing_tags']} "
        f"glass={json.dumps(data['glass'], separators=(',', ':'))} "
        f"scene={data['scene']} mutation=none"
    )


if __name__ == "__main__":
    main()
