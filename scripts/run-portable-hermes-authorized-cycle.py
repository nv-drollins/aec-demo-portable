#!/usr/bin/env python3
"""Run one deterministic demo cycle after an auto-Hermes operator launch."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run-portable-demo-loop.py"


def main() -> None:
    if os.environ.get("AEC_HERMES_AUTO_AUTHORIZED") != "1":
        print("HERMES_AUTO_AUTHORIZATION_REQUIRED=operator_launch", file=sys.stderr)
        raise SystemExit(2)
    authorization_id = os.environ.get("AEC_HERMES_AUTO_AUTHORIZATION_ID", "")
    if not authorization_id:
        print("HERMES_AUTO_AUTHORIZATION_ID_MISSING", file=sys.stderr)
        raise SystemExit(2)

    print(
        f"HERMES_AUTO_AUTHORIZATION_OK id={authorization_id} "
        "source=operator_launch scope=one_cycle phases=2-12",
        flush=True,
    )
    print("HERMES_AUTO_MODE=agent_driven_deterministic_adapter_cycle", flush=True)

    if os.environ.get("AEC_HERMES_AUTO_DRY_RUN") == "1":
        delay = float(os.environ.get("AEC_HERMES_AUTO_DRY_RUN_SECONDS", "0"))
        if delay < 0 or delay > 120:
            raise RuntimeError("AEC_HERMES_AUTO_DRY_RUN_SECONDS must be between 0 and 120")
        if delay:
            for step, message in enumerate((
                "authorization guard accepted",
                "background process monitoring available",
                "verbose progress channel verified",
            ), 1):
                print(
                    f"HERMES_AUTO_DRY_RUN_PROGRESS step={step}/3 "
                    f"message={message!r}",
                    flush=True,
                )
                time.sleep(delay / 3.0)
        print(
            "HERMES_AUTO_DRY_RUN_OK phases_executed=0 "
            "purpose=launcher_validation",
            flush=True,
        )
        return

    environment = os.environ.copy()
    environment["AEC_AUTOPLAY_HERMES_MODE"] = "driver"
    arguments = [
        sys.executable,
        str(RUNNER),
        "--cycles", "1",
        "--phase-delay", environment.get("AEC_AUTO_PHASE_DELAY", "5"),
        "--cycle-delay", "0",
        "--keep-final-sets", environment.get("AEC_AUTO_KEEP_FINAL_SETS", "12"),
    ]
    os.execve(sys.executable, arguments, environment)


if __name__ == "__main__":
    main()
