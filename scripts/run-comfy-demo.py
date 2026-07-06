#!/usr/bin/env python3
"""Submit the delivered Blender-to-Comfy workflow through Blender MCP."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import time
import urllib.request


ROOT = Path(__file__).resolve().parent.parent


def load_runtime_env() -> None:
    path = ROOT / "config/runtime.env"
    if not path.is_file():
        path = ROOT / "config/runtime.env.example"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, os.path.expanduser(value.strip()))


def blender_execute(code: str, host: str, port: int) -> dict:
    payload = json.dumps({"type": "execute_code", "params": {"code": code}}).encode()
    with socket.create_connection((host, port), timeout=5) as client:
        client.settimeout(90)
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


def stage_sample_inputs(comfy_root: Path) -> None:
    source = ROOT / "sample_project/renders"
    target = comfy_root / "input"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "beauty/beauty_0004.png", target / "beauty_input.png")
    shutil.copyfile(source / "seg/seg_0004.png", target / "seg_input.png")
    print(f"AEC_SAMPLE_INPUTS_READY={target}")


def wait_for_prompt(comfy_url: str, prompt_id: str, timeout: int) -> list[dict]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with urllib.request.urlopen(
            f"{comfy_url}/history/{prompt_id}", timeout=10
        ) as response:
            entry = json.load(response).get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("completed"):
                images = [
                    image
                    for output in entry.get("outputs", {}).values()
                    for image in output.get("images", [])
                ]
                print(
                    f"AEC_COMFY_COMPLETE={prompt_id} "
                    f"status={status.get('status_str')} images={len(images)}"
                )
                if len(images) != 3:
                    raise RuntimeError(f"Expected 3 Comfy images, received {len(images)}")
                return images
        time.sleep(2)
    raise TimeoutError(f"ComfyUI prompt did not finish within {timeout} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render fresh beauty and segmentation passes in Blender before submission.",
    )
    parser.add_argument(
        "--sample-inputs",
        action="store_true",
        help="Stage the supplied reference beauty/segmentation images and reuse them.",
    )
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    load_runtime_env()
    host = os.environ.get("AEC_PORTABLE_HOST", "127.0.0.1")
    blender_port = int(os.environ.get("AEC_PORTABLE_BLENDER_PORT", "9876"))
    comfy_root = Path(os.environ["AEC_PORTABLE_COMFY_ROOT"])
    comfy_url = os.environ.get("AEC_PORTABLE_COMFY_URL", "http://127.0.0.1:8188")

    if args.sample_inputs:
        stage_sample_inputs(comfy_root)
    script = ROOT / "scripts/submit_comfyui.py"
    code = (
        f"path={str(script)!r}; ns={{'bpy': bpy}}; "
        "exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), ns); "
        f"print('AEC_SUBMIT_RESULT=' + str(ns['submit'](render={args.render!r})))"
    )
    response = blender_execute(code, host, blender_port)
    if response.get("status") != "success":
        raise RuntimeError(response)
    output = response.get("result", {}).get("result", "")
    print(output, end="" if output.endswith("\n") else "\n")
    match = re.search(r"\[AEC\] Queued: ([0-9a-f-]+)", output)
    if not match:
        raise RuntimeError("Submission did not return a ComfyUI prompt ID")
    prompt_id = match.group(1)
    print(f"AEC_COMFY_QUEUED={prompt_id}")
    if args.no_wait:
        return

    images = wait_for_prompt(comfy_url, prompt_id, args.timeout)
    for image in images:
        path = comfy_root / image.get("type", "output") / image.get("subfolder", "") / image["filename"]
        print(f"AEC_COMFY_IMAGE={path}")


if __name__ == "__main__":
    main()
