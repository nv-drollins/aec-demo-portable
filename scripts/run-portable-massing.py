#!/usr/bin/env python3
"""Run the only supported portable Phase 3 massing adapter."""

from __future__ import annotations

import json
from pathlib import Path
import socket
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "skills/build-portable-freecad-massing/assets/portable-cliff-house-massing-v1.json"
OUTPUT = ROOT / "projects/recorded_demo/freecad/portable_cliff_house_massing.FCStd"
BUILDER = ROOT / "scripts/build-portable-massing-freecad.py"


def blender_execute(code: str) -> dict:
    payload = json.dumps(
        {"type": "execute_code", "params": {"code": code}}
    ).encode()
    with socket.create_connection(("127.0.0.1", 9876), timeout=5) as client:
        client.settimeout(30)
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
    if spec.get("format") != "aec-portable-freecad-massing-v1":
        raise RuntimeError("Portable massing specification has the wrong format")
    if len(spec.get("objects", [])) != 11:
        raise RuntimeError("Portable massing specification must contain 11 envelopes")
    target_objects = sorted(
        {
            name
            for item in spec["objects"]
            for name in item["target_blender_objects"]
        }
    )
    target_scene = ROOT / spec["provenance"]["target_scene"]
    target_code = (
        "import json\n"
        f"expected_scene={str(target_scene)!r}\n"
        f"required={target_objects!r}\n"
        "missing=[name for name in required if name not in bpy.data.objects]\n"
        "print('PORTABLE_MASSING_TARGET_DATA=' + json.dumps({"
        "'scene': bpy.data.filepath, 'expected_scene': expected_scene, "
        "'required': len(required), 'missing': missing}, sort_keys=True))\n"
    )
    target_response = blender_execute(target_code)
    if target_response.get("status") != "success":
        raise RuntimeError(f"Blender target validation failed: {target_response}")
    target_output = target_response.get("result", {}).get("result", "")
    marker = "PORTABLE_MASSING_TARGET_DATA="
    if marker not in target_output:
        raise RuntimeError("Blender target validation returned no data marker")
    target_data = json.loads(target_output.split(marker, 1)[1].splitlines()[0])
    if Path(target_data["scene"]).resolve() != target_scene.resolve():
        raise RuntimeError(
            f"Wrong Blender target is open: {target_data['scene']}"
        )
    if target_data["missing"]:
        raise RuntimeError(
            f"Delivered Blender target is missing objects: {target_data['missing']}"
        )
    print(
        f"PORTABLE_MASSING_TARGET_OK scene={target_scene} "
        f"objects={target_data['required']} missing=0"
    )
    rpc = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True)
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC is not healthy on 127.0.0.1:9875")
    environment = {
        "AEC_PORTABLE_MASSING_SPEC": str(SPEC),
        "AEC_PORTABLE_MASSING_FCSTD": str(OUTPUT),
        "AEC_PORTABLE_REFERENCE_DOCUMENT": "PortableCliffHouseReference",
        "AEC_PORTABLE_SITE_DOCUMENT": "PortableCliffHouseSite",
        "AEC_PORTABLE_MASSING_DOCUMENT": "PortableCliffHouseMassing",
    }
    assignments = "".join(
        f"os.environ[{key!r}] = {value!r}\n"
        for key, value in environment.items()
    )
    code = (
        "import os\n"
        + assignments
        + f"exec(compile(open({str(BUILDER)!r}, encoding='utf-8').read(), "
        + f"{str(BUILDER)!r}, 'exec'))"
    )
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(result.get("error", result.get("message", str(result))))
    output = result["message"].rsplit("Output: ", 1)[-1].strip()
    print(output)
    if "PORTABLE_MASSING_BUILD_OK=" not in output:
        raise RuntimeError("Massing builder did not return its success marker")
    print(
        f"PORTABLE_MASSING_PREPARATION_OK output={OUTPUT} "
        f"spec={spec['id']} objects=11"
    )


if __name__ == "__main__":
    main()
