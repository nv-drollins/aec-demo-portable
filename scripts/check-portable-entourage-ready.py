#!/usr/bin/env python3
"""Read-only readiness check for canonical portable Phase 6."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PHASE5_RUNNER = ROOT / "scripts/run-portable-landscaping.py"
SPEC_PATH = ROOT / "skills/build-portable-blender-entourage/assets/portable-cliff-house-entourage-v1.json"


def load_phase5_runner():
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

    transport = load_phase5_runner()
    embedded = json.dumps(spec, separators=(",", ":"))
    allowed = [str(input_scene), str(output_scene)]
    code = f'''import bpy, json, os\nspec=json.loads({embedded!r})\nactive=os.path.realpath(bpy.data.filepath)\nallowed={{os.path.realpath(path) for path in {allowed!r}}}\nif active not in allowed:\n    raise RuntimeError("Wrong Blender checkpoint is open: " + bpy.data.filepath)\ncollection=bpy.data.collections.get(spec["input_collection"])\nif collection is None or len(collection.objects) != 15:\n    raise RuntimeError("Phase 5 landscaping collection is missing or incomplete")\nroles={{}}\nfor item in spec["items"]:\n    roles[item["role"]]=roles.get(item["role"],0)+1\nprint("PORTABLE_ENTOURAGE_READINESS_DATA="+json.dumps({{"scene":bpy.data.filepath,"phase5_objects":len(collection.objects),"items":len(spec["items"]),"roles":roles}},separators=(",",":"),sort_keys=True))\n'''
    response = transport.blender_execute(code)
    if response.get("status") != "success":
        raise RuntimeError(f"Blender entourage readiness check failed: {response}")
    remote_output = response.get("result", {}).get("result", "")
    marker = "PORTABLE_ENTOURAGE_READINESS_DATA="
    if marker not in remote_output:
        raise RuntimeError("Entourage readiness check returned no data marker")
    data = json.loads(remote_output.split(marker, 1)[1].splitlines()[0])
    print(
        f"PORTABLE_ENTOURAGE_READY_OK phase5_objects={data['phase5_objects']} "
        f"items={data['items']} roles={json.dumps(data['roles'], separators=(',', ':'))} "
        f"scene={data['scene']} mutation=none"
    )


if __name__ == "__main__":
    main()
