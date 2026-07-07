#!/usr/bin/env python3
"""Run the only supported delivered-template site-preparation adapter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sample_project/rhino_assets/beach_house_02.3dm"
EXPECTED_SHA256 = "607e86bbf425f2344ffbe8fe70ba8522da8de4d27d8c499ef950e4568c32b027"
MANIFEST = ROOT / "runtime/generated/portable-beach-house-reference.json"
FREECAD_DIR = ROOT / "projects/recorded_demo/freecad"
REFERENCE_FCSTD = FREECAD_DIR / "portable_cliff_house_reference.FCStd"
SITE_FCSTD = FREECAD_DIR / "portable_cliff_house_site.FCStd"
REFERENCE_DOCUMENT = "PortableCliffHouseReference"
SITE_DOCUMENT = "PortableCliffHouseSite"
CAD_PYTHON = Path(os.environ.get(
    "AEC_PORTABLE_CAD_PYTHON",
    str(ROOT / "runtime/cad-tools/bin/python"),
))


def require(output: str, marker: str) -> None:
    if marker not in output:
        raise RuntimeError(f"Missing required marker {marker!r}:\n{output}")


def freecad_execute(rpc, script: Path, environment: dict[str, str]) -> str:
    assignments = "".join(
        f"os.environ[{key!r}] = {value!r}\n"
        for key, value in environment.items()
    )
    code = (
        "import os\n"
        + assignments
        + f"exec(compile(open({str(script)!r}, encoding='utf-8').read(), "
        + f"{str(script)!r}, 'exec'))"
    )
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(result.get("error", result.get("message", str(result))))
    output = result["message"].rsplit("Output: ", 1)[-1].strip()
    print(output)
    return output


def main() -> None:
    if not SOURCE.is_file():
        raise RuntimeError(f"Delivered Rhino template is missing: {SOURCE}")
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(
            f"Delivered Rhino template fingerprint changed: {digest}"
        )
    if not CAD_PYTHON.is_file():
        raise RuntimeError(f"Portable CAD Python is missing: {CAD_PYTHON}")

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    extraction = subprocess.run(
        [
            str(CAD_PYTHON),
            str(ROOT / "scripts/extract-portable-rhino-reference.py"),
            str(SOURCE),
            str(MANIFEST),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout.strip()
    print(extraction)
    require(extraction, "PORTABLE_RHINO_EXTRACT_OK=")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = manifest["counts"]
    if counts != {
        "layers": 10,
        "objects": 11,
        "curves": 11,
        "unsupported": 0,
        "types": {
            "PolylineCurve": 5,
            "NurbsCurve": 5,
            "PolyCurve": 1,
        },
    }:
        raise RuntimeError(f"Unexpected delivered-template manifest: {counts}")

    rpc = xmlrpc.client.ServerProxy(
        "http://127.0.0.1:9875", allow_none=True
    )
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC is not healthy on 127.0.0.1:9875")
    environment = {
        "AEC_PORTABLE_RHINO_MANIFEST": str(MANIFEST),
        "AEC_PORTABLE_REFERENCE_FCSTD": str(REFERENCE_FCSTD),
        "AEC_PORTABLE_SITE_FCSTD": str(SITE_FCSTD),
        "AEC_PORTABLE_REFERENCE_DOCUMENT": REFERENCE_DOCUMENT,
        "AEC_PORTABLE_SITE_DOCUMENT": SITE_DOCUMENT,
    }
    imported = freecad_execute(
        rpc,
        ROOT / "scripts/import-portable-rhino-reference-freecad.py",
        environment,
    )
    require(imported, "PORTABLE_FREECAD_REFERENCE_OK=")
    built = freecad_execute(
        rpc,
        ROOT / "scripts/build-portable-site-preparation-freecad.py",
        environment,
    )
    require(built, "PORTABLE_SITE_BUILD_OK=")
    print(
        f"PORTABLE_SITE_PREPARATION_OK reference={REFERENCE_FCSTD} "
        f"site={SITE_FCSTD} source_sha256={digest}"
    )


if __name__ == "__main__":
    main()
