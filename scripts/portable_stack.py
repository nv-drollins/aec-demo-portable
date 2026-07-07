#!/usr/bin/env python3
"""Preflight and manage the local AEC Demo Portable service stack safely."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import shutil
import sys
import time
import urllib.request
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
LOGS = ROOT / "logs"
LOCAL_ENV = ROOT / "config" / "runtime.env"
EXAMPLE_ENV = ROOT / "config" / "runtime.env.example"
os.environ.setdefault("AEC_PORTABLE_ROOT", str(ROOT))

REQUIRED_MODELS = (
    "models/diffusion_models/flux/flux-2-klein-9b.safetensors",
    "models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors",
    "models/vae/flux/flux2-vae.safetensors",
)

REQUIRED_NODE_TYPES = (
    "AnyLineArtPreprocessor_aux",
    "BatchImagesNode",
    "ColorCode",
    "DepthAnythingPreprocessor",
    "GetImageSize",
    "Image Comparer (rgthree)",
    "ImageScaleToTotalPixels",
    "MaskFromColor+",
    "ResizeImageMaskNode",
    "SimpleInpaintCrop",
    "SimpleInpaintStitch",
    "Text Multiline",
)


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = os.path.expandvars(os.path.expanduser(value.strip()))


load_env_file(LOCAL_ENV if LOCAL_ENV.is_file() else EXAMPLE_ENV)


def setting(name: str, default: str) -> str:
    return os.environ.get(name, default)


def enabled(name: str, default: bool = False) -> bool:
    fallback = "1" if default else "0"
    return setting(name, fallback).lower() in {"1", "true", "yes", "on"}


HOST = setting("AEC_PORTABLE_HOST", "127.0.0.1")
FREECAD_PORT = int(setting("AEC_PORTABLE_FREECAD_PORT", "9875"))
BLENDER_PORT = int(setting("AEC_PORTABLE_BLENDER_PORT", "9876"))
COMFY_PORT = int(setting("AEC_PORTABLE_COMFY_PORT", "8188"))
BLENDER_EXE = setting("AEC_PORTABLE_BLENDER_EXE", "blender")
BLENDER_MCP_BOOTSTRAP = Path(setting(
    "AEC_PORTABLE_BLENDER_MCP_BOOTSTRAP",
    str(ROOT / "scripts/start_blender_mcp.py"),
))
BLENDER_SCENE = Path(setting(
    "AEC_PORTABLE_BLENDER_SCENE",
    str(ROOT / "sample_project/blender_assets/cliff_house_act2_textured_v3.blend"),
))
BLENDER_MIN_VERSION = tuple(
    int(part) for part in setting("AEC_PORTABLE_BLENDER_MIN_VERSION", "5.1").split(".")[:2]
)
COMFY_ROOT = Path(setting("AEC_PORTABLE_COMFY_ROOT", str(ROOT / "runtime/comfyui")))
COMFY_PYTHON = Path(setting(
    "AEC_PORTABLE_COMFY_PYTHON", str(COMFY_ROOT / ".venv/bin/python")
))
FREECAD_START = Path(setting(
    "AEC_PORTABLE_FREECAD_START", str(ROOT / "scripts/start-freecad.sh")
))
FREECAD_EXE = Path(setting(
    "AEC_PORTABLE_FREECAD_EXE", str(ROOT / "runtime/freecad/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage")
))


def tcp_open(port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((HOST, port), timeout=timeout):
            return True
    except OSError:
        return False


def freecad_healthy() -> bool:
    try:
        proxy = xmlrpc.client.ServerProxy(
            f"http://{HOST}:{FREECAD_PORT}", allow_none=True
        )
        return bool(proxy.ping())
    except Exception:
        return False


def blender_request(kind: str, params: dict | None = None) -> dict:
    payload = json.dumps({"type": kind, "params": params or {}}).encode()
    with socket.create_connection((HOST, BLENDER_PORT), timeout=2) as client:
        client.settimeout(5)
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


def blender_healthy() -> bool:
    try:
        return blender_request("get_scene_info").get("status") == "success"
    except Exception:
        return False


def blender_remote_version() -> tuple[tuple[int, int], str] | None:
    try:
        response = blender_request(
            "execute_code",
            {"code": "print('AEC_REMOTE_VERSION=' + bpy.app.version_string)"},
        )
        output = response["result"]["result"].strip()
        description = output.split("AEC_REMOTE_VERSION=", 1)[1].splitlines()[0]
        parts = description.split(".")
        return (int(parts[0]), int(parts[1])), description
    except (KeyError, IndexError, TypeError, ValueError, OSError, RuntimeError):
        return None


def comfy_healthy() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://{HOST}:{COMFY_PORT}/system_stats", timeout=3
        ) as response:
            return response.status == 200
    except Exception:
        return False


def blender_version() -> tuple[tuple[int, int], str]:
    try:
        completed = subprocess.run(
            [BLENDER_EXE, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return (0, 0), f"unavailable ({exc})"
    first = completed.stdout.splitlines()[0].strip()
    try:
        parts = first.split()[1].split(".")
        version = (int(parts[0]), int(parts[1]))
    except (IndexError, ValueError):
        version = (0, 0)
    return version, first


def missing_models() -> list[Path]:
    return [COMFY_ROOT / relative for relative in REQUIRED_MODELS if not (COMFY_ROOT / relative).is_file()]


def comfy_node_types() -> set[str] | None:
    if not comfy_healthy():
        return None
    try:
        with urllib.request.urlopen(
            f"http://{HOST}:{COMFY_PORT}/object_info", timeout=30
        ) as response:
            return set(json.load(response))
    except Exception:
        return None


def missing_workflow_nodes() -> list[str] | None:
    available = comfy_node_types()
    if available is None:
        return None
    return [name for name in REQUIRED_NODE_TYPES if name not in available]


def preflight() -> list[str]:
    errors: list[str] = []
    if not BLENDER_SCENE.is_file():
        errors.append(f"Blender scene is missing: {BLENDER_SCENE}")
    version, description = blender_version()
    print(f"BLENDER_VERSION={description}")
    if version < BLENDER_MIN_VERSION:
        errors.append(
            f"Blender {BLENDER_MIN_VERSION[0]}.{BLENDER_MIN_VERSION[1]} or newer is required "
            "for the delivered scenes; "
            f"configured executable reports {description}"
        )
    if blender_healthy():
        remote = blender_remote_version()
        print(f"BLENDER_MCP_VERSION={'unknown' if remote is None else remote[1]}")
        if remote is None or remote[0] < BLENDER_MIN_VERSION:
            errors.append(
                f"Blender MCP port {BLENDER_PORT} is occupied by an incompatible "
                f"instance ({'unknown version' if remote is None else remote[1]}); "
                "close that Blender instance before starting the portable stack"
            )
    if not BLENDER_MCP_BOOTSTRAP.is_file():
        errors.append(f"Blender MCP bootstrap is missing: {BLENDER_MCP_BOOTSTRAP}")
    if not COMFY_PYTHON.is_file():
        errors.append(f"ComfyUI Python is missing: {COMFY_PYTHON}")
    if not (COMFY_ROOT / "main.py").is_file():
        errors.append(f"ComfyUI main.py is missing under: {COMFY_ROOT}")
    missing = missing_models()
    for path in missing:
        print(f"MODEL_MISSING={path}")
    if missing and enabled("AEC_PORTABLE_REQUIRE_MODELS", True):
        errors.append(
            f"{len(missing)} required Flux.2 model files are missing; "
            "see comfyui/models/MODEL_MANIFEST.md"
        )
    missing_nodes = missing_workflow_nodes()
    if missing_nodes is None:
        print("WORKFLOW_NODE_CHECK=skipped_comfyui_not_running")
    else:
        for name in missing_nodes:
            print(f"WORKFLOW_NODE_MISSING={name}")
        if missing_nodes:
            errors.append(
                f"{len(missing_nodes)} required ComfyUI node classes are missing; "
                "see docs/REPLICATION_READINESS.md"
            )
    if enabled("AEC_PORTABLE_FREECAD_ENABLED", True):
        if not FREECAD_START.is_file():
            errors.append(f"FreeCAD launcher is missing: {FREECAD_START}")
        if not FREECAD_EXE.is_file():
            errors.append(f"FreeCAD executable is missing: {FREECAD_EXE}")
    if errors:
        print("PORTABLE_PREFLIGHT_BLOCKED")
        for error in errors:
            print(f"ERROR={error}")
    else:
        print("PORTABLE_PREFLIGHT_OK")
    return errors


def wait_for(check, seconds: int, label: str) -> None:
    for _ in range(seconds):
        if check():
            print(f"{label}_READY")
            return
        time.sleep(1)
    raise RuntimeError(f"{label} did not become ready within {seconds} seconds")


def spawn(name: str, command: list[str]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{name}.log"
    stream = log_path.open("ab")
    environment = os.environ.copy()
    if name == "blender":
        display = setting("AEC_PORTABLE_DISPLAY", "")
        xauthority = setting("AEC_PORTABLE_XAUTHORITY", "")
        if display:
            environment["DISPLAY"] = display
        if xauthority:
            environment["XAUTHORITY"] = xauthority
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdout=stream,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    (RUNTIME / f"{name}.pid").write_text(f"{process.pid}\n", encoding="utf-8")
    print(f"{name.upper()}_STARTED pid={process.pid} log={log_path}")


def archive_stale_freecad_recovery() -> None:
    """Move crash-recovery state aside before a fresh FreeCAD launch.

    A power loss leaves FreeCAD_Doc_* folders and FreeCAD_*.lock files. On the
    next GUI launch FreeCAD presents a modal Document Recovery window, which
    intentionally blocks MCP GUI dispatch. The portable demo checkpoints are
    already saved independently, so archive this stale state under runtime/
    instead of deleting it.
    """
    cache = Path.home() / ".cache/FreeCAD/v1-1/Cache"
    if not cache.is_dir():
        return
    candidates = sorted(cache.glob("FreeCAD_*.lock")) + sorted(
        path for path in cache.glob("FreeCAD_Doc_*") if path.is_dir()
    )
    if not candidates:
        return
    stamp = time.strftime("%Y%m%d_%H%M%S")
    archive = RUNTIME / "freecad-recovery-archive" / stamp
    archive.mkdir(parents=True, exist_ok=True)
    moved = 0
    for source in candidates:
        target = archive / source.name
        if target.exists():
            target = archive / f"{source.name}_{moved}"
        shutil.move(str(source), str(target))
        moved += 1
    print(
        f"FREECAD_RECOVERY_ARCHIVED items={moved} archive={archive}"
    )


def start() -> None:
    errors = preflight()
    if errors:
        raise SystemExit(2)
    if enabled("AEC_PORTABLE_FREECAD_ENABLED", True):
        if not freecad_healthy():
            archive_stale_freecad_recovery()
            subprocess.run([str(FREECAD_START)], check=True)
        wait_for(freecad_healthy, 60, "FREECAD_MCP")
    if not comfy_healthy():
        spawn(
            "comfyui",
            [str(COMFY_PYTHON), str(COMFY_ROOT / "main.py"), "--listen", HOST],
        )
    wait_for(comfy_healthy, 120, "COMFYUI")
    nodes = missing_workflow_nodes()
    if nodes:
        raise RuntimeError(f"ComfyUI is missing required workflow nodes: {nodes}")
    if not blender_healthy():
        spawn(
            "blender",
            [
                BLENDER_EXE,
                "--enable-autoexec",
                str(BLENDER_SCENE),
                "--python",
                str(BLENDER_MCP_BOOTSTRAP),
            ],
        )
    wait_for(blender_healthy, 90, "BLENDER_MCP")
    status()
    print("PORTABLE_STACK_OK")


def terminate_recorded(name: str) -> None:
    pid_path = RUNTIME / f"{name}.pid"
    if not pid_path.is_file():
        print(f"{name.upper()}_STOP_SKIPPED=not_started_by_this_project")
        return
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except (ValueError, PermissionError) as exc:
        raise RuntimeError(f"Could not stop recorded {name} process: {exc}") from exc
    for _ in range(30):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.25)
    pid_path.unlink(missing_ok=True)
    print(f"{name.upper()}_STOPPED pid={pid}")


def stop() -> None:
    terminate_recorded("blender")
    terminate_recorded("comfyui")
    print("FREECAD_STOP_SKIPPED=shared_service")
    print("PORTABLE_STACK_STOPPED")


def status() -> None:
    print(f"ROOT={ROOT}")
    print(f"FREECAD_MCP={'healthy' if freecad_healthy() else 'down'} endpoint={HOST}:{FREECAD_PORT}")
    blender_status = blender_healthy()
    remote = blender_remote_version() if blender_status else None
    print(f"BLENDER_MCP={'healthy' if blender_status else 'down'} endpoint={HOST}:{BLENDER_PORT} version={'unknown' if remote is None else remote[1]}")
    print(f"COMFYUI={'healthy' if comfy_healthy() else 'down'} endpoint={HOST}:{COMFY_PORT}")
    print(f"SCENE={'present' if BLENDER_SCENE.is_file() else 'missing'} path={BLENDER_SCENE}")
    print(f"FLUX_MODELS_MISSING={len(missing_models())}")
    nodes = missing_workflow_nodes()
    print(f"WORKFLOW_NODES_MISSING={'unknown' if nodes is None else len(nodes)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "start", "stop", "restart", "status"))
    args = parser.parse_args()
    if args.command == "preflight":
        raise SystemExit(2 if preflight() else 0)
    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    elif args.command == "restart":
        stop()
        start()
    else:
        status()


if __name__ == "__main__":
    main()
