#!/usr/bin/env python3
"""Run the checked portable AEC demo once or continuously without Hermes approvals."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
SOURCE_SCENE = (
    ROOT / "sample_project/blender_assets/cliff_house_act2_textured_v3.blend"
)
PROFILE = ROOT / "profiles/delivered_cliff_house_demo/prompt_profile.md"
FINAL_OUTPUTS = ROOT / "projects/recorded_demo/final_outputs"
BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 9876


@dataclass(frozen=True)
class Phase:
    number: int
    name: str
    script: str


PHASES = (
    Phase(2, "site_preparation", "run-portable-site-preparation.py"),
    Phase(3, "building_massing", "run-portable-massing.py"),
    Phase(4, "architectural_detailing", "run-portable-detailing.py"),
    Phase(5, "landscaping_site_context", "run-portable-landscaping.py"),
    Phase(6, "entourage_outdoor_living", "run-portable-entourage.py"),
    Phase(7, "materials", "run-portable-materials.py"),
    Phase(8, "camera_placement", "run-portable-camera.py"),
    Phase(9, "lighting", "run-portable-lighting.py"),
    Phase(10, "optional_animation_skipped", "run-portable-animation-skip.py"),
    Phase(11, "test_renders", "run-portable-test-renders.py"),
    Phase(12, "final_blender_comfyui", "run-portable-final-transformation.py"),
)


def emit(marker: str, **values: object) -> None:
    fields = " ".join(f"{key}={value}" for key, value in values.items())
    print(f"{marker}{' ' if fields else ''}{fields}", flush=True)


def run(command: list[str], *, label: str) -> None:
    emit("AUTOPLAY_COMMAND_BEGIN", label=label)
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{label} failed with exit code {completed.returncode}"
        )
    emit("AUTOPLAY_COMMAND_OK", label=label)


def blender_request(kind: str, params: dict | None = None, timeout: int = 120) -> dict:
    payload = json.dumps({"type": kind, "params": params or {}}).encode()
    with socket.create_connection(
        (BLENDER_HOST, BLENDER_PORT), timeout=5
    ) as client:
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


def reset_blender_source() -> None:
    if not SOURCE_SCENE.is_file():
        raise RuntimeError(f"Delivered Blender source is missing: {SOURCE_SCENE}")
    code = (
        "import bpy, os\n"
        f"path={str(SOURCE_SCENE)!r}\n"
        "bpy.ops.wm.open_mainfile(filepath=path)\n"
        "print('AUTOPLAY_BLENDER_SOURCE_DATA=' + bpy.data.filepath)\n"
    )
    response = blender_request("execute_code", {"code": code})
    if response.get("status") != "success":
        raise RuntimeError(f"Could not reset Blender source scene: {response}")
    output = response.get("result", {}).get("result", "")
    if f"AUTOPLAY_BLENDER_SOURCE_DATA={SOURCE_SCENE}" not in output:
        raise RuntimeError(f"Blender opened an unexpected source scene: {output}")
    emit("AUTOPLAY_BLENDER_SOURCE_OK", scene=SOURCE_SCENE)


FINAL_PATTERN = re.compile(
    r"^final_[123]_Comfy_(\d{8}_\d{6})_.+\.png$"
)


def prune_final_sets(keep: int) -> None:
    if keep <= 0 or not FINAL_OUTPUTS.is_dir():
        return
    grouped: dict[str, list[Path]] = {}
    for path in FINAL_OUTPUTS.iterdir():
        match = FINAL_PATTERN.match(path.name)
        if match:
            grouped.setdefault(match.group(1), []).append(path)
    timestamps = sorted(grouped, reverse=True)
    removed_sets = 0
    removed_files = 0
    for timestamp in timestamps[keep:]:
        for path in grouped[timestamp]:
            path.unlink()
            removed_files += 1
        removed_sets += 1
    emit(
        "AUTOPLAY_RETENTION_OK",
        keep_sets=keep,
        removed_sets=removed_sets,
        removed_files=removed_files,
    )


def pause(seconds: float, *, reason: str) -> None:
    if seconds <= 0:
        return
    emit("AUTOPLAY_PAUSE", seconds=seconds, reason=reason)
    time.sleep(seconds)


def phase_one(cycle: int) -> None:
    emit("AUTOPLAY_PHASE_BEGIN", cycle=cycle, phase=1, name="config_source_audit")
    run(
        [sys.executable, "scripts/prompt_profile.py", "validate", str(PROFILE)],
        label="profile_validation",
    )
    run(
        [sys.executable, "scripts/portable_stack.py", "status"],
        label="stack_status",
    )
    emit("AUTOPLAY_PHASE_OK", cycle=cycle, phase=1, name="config_source_audit")


def run_cycle(cycle: int, phase_delay: float, keep_final_sets: int) -> None:
    started = time.monotonic()
    emit("AUTOPLAY_CYCLE_BEGIN", cycle=cycle)
    phase_one(cycle)
    pause(phase_delay, reason="phase_1_review")

    # Phases 3 and 4 validate the immutable delivered Blender target. Reset it
    # once before the checked adapters begin. Phase 5 then starts the versioned
    # Blender checkpoint chain.
    reset_blender_source()

    for phase in PHASES:
        emit(
            "AUTOPLAY_PHASE_BEGIN",
            cycle=cycle,
            phase=phase.number,
            name=phase.name,
        )
        run(
            [sys.executable, str(ROOT / "scripts" / phase.script)],
            label=f"phase_{phase.number}_{phase.name}",
        )
        emit(
            "AUTOPLAY_PHASE_OK",
            cycle=cycle,
            phase=phase.number,
            name=phase.name,
        )
        pause(phase_delay, reason=f"phase_{phase.number}_review")

    prune_final_sets(keep_final_sets)
    elapsed = round(time.monotonic() - started, 1)
    emit("AUTOPLAY_CYCLE_OK", cycle=cycle, elapsed_seconds=elapsed)


def acquire_lock() -> object:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    stream = (RUNTIME / "portable-auto-demo.lock").open("w", encoding="utf-8")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("Another portable auto-demo loop is already running") from exc
    stream.write(f"{os.getpid()}\n")
    stream.flush()
    return stream


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Number of complete cycles; 0 means loop until Ctrl+C.",
    )
    parser.add_argument(
        "--phase-delay",
        type=float,
        default=5.0,
        help="Seconds to leave each completed phase visible.",
    )
    parser.add_argument(
        "--cycle-delay",
        type=float,
        default=60.0,
        help="Seconds to leave final images visible before the next cycle.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=30.0,
        help="Seconds before retrying a failed infinite-loop cycle.",
    )
    parser.add_argument(
        "--keep-final-sets",
        type=int,
        default=0,
        help="Retain this many timestamped 3-image sets; 0 keeps all.",
    )
    parser.add_argument(
        "--no-start-stack",
        action="store_true",
        help="Require the caller to have already started the service stack.",
    )
    args = parser.parse_args()
    if args.cycles < 0 or args.keep_final_sets < 0:
        parser.error("--cycles and --keep-final-sets cannot be negative")

    lock = acquire_lock()  # Keep the stream alive so the process owns the lock.
    emit(
        "AUTOPLAY_MODE",
        approvals="not_used",
        hermes="not_launched",
        checked_adapters=len(PHASES),
        cycles="infinite" if args.cycles == 0 else args.cycles,
    )
    if not args.no_start_stack:
        run(
            [sys.executable, "scripts/portable_stack.py", "start"],
            label="stack_start",
        )

    cycle = 1
    try:
        while args.cycles == 0 or cycle <= args.cycles:
            try:
                run_cycle(cycle, args.phase_delay, args.keep_final_sets)
            except Exception as exc:
                emit(
                    "AUTOPLAY_CYCLE_FAILED",
                    cycle=cycle,
                    error=json.dumps(str(exc)),
                )
                if args.cycles:
                    raise
                pause(args.retry_delay, reason="failure_retry")
                run(
                    [sys.executable, "scripts/portable_stack.py", "start"],
                    label="stack_recovery",
                )
                continue
            if args.cycles and cycle >= args.cycles:
                break
            pause(args.cycle_delay, reason="final_review")
            cycle += 1
    except KeyboardInterrupt:
        emit("AUTOPLAY_STOPPED", reason="keyboard_interrupt", cycle=cycle)
        return
    emit("AUTOPLAY_COMPLETE", cycles=cycle)


if __name__ == "__main__":
    main()
