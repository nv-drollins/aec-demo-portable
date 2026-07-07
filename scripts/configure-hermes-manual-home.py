#!/usr/bin/env python3
"""Create the isolated, non-learning Hermes profile for manual demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--lifetime", type=int, default=10800)
    args = parser.parse_args()

    root = args.root.resolve()
    home = args.home.resolve()
    if args.timeout < 1 or args.lifetime <= args.timeout:
        parser.error("--lifetime must be greater than --timeout, both positive")

    global_hermes = Path.home() / ".hermes"
    uv = global_hermes / "bin" / "uv"
    uvx = global_hermes / "bin" / "uvx"
    for label, path in (("uv", uv), ("uvx", uvx)):
        if not path.exists():
            raise RuntimeError(f"{label} is missing: {path}")
    freecad_candidates = [
        root / "runtime" / "freecad-mcp",
        Path.home() / "aes-demo" / "runtime" / "freecad-mcp",
        Path.home() / "aec-demo" / "runtime" / "freecad-mcp",
        Path.home() / "aec-demo" / "freecad-mcp",
    ]
    freecad_mcp = next(
        (candidate.resolve() for candidate in freecad_candidates if candidate.is_dir()),
        None,
    )
    if freecad_mcp is None:
        checked = ", ".join(str(path) for path in freecad_candidates)
        raise RuntimeError(f"FreeCAD MCP is missing; checked: {checked}")

    home.mkdir(parents=True, exist_ok=True)
    config = f"""\
model:
  default: {json.dumps(args.model)}
  provider: custom
  base_url: http://127.0.0.1:11434/v1
agent:
  max_turns: 60
  verbose: false
  reasoning_effort: medium
terminal:
  backend: local
  cwd: {json.dumps(str(root))}
  timeout: {args.timeout}
  lifetime_seconds: {args.lifetime}
display:
  compact: false
  show_reasoning: false
  streaming: true
  tool_progress: all
  long_running_notifications: true
  background_process_notifications: all
  memory_notifications: off
compression:
  enabled: true
  threshold: 0.7
  target_ratio: 0.35
  protect_last_n: 30
  protect_first_n: 3
memory:
  memory_enabled: false
  user_profile_enabled: false
  nudge_interval: 0
  flush_min_turns: 999999
skills:
  creation_nudge_interval: 0
  external_dirs:
    - {json.dumps(str(root / "skills"))}
platform_toolsets:
  cli:
    - hermes-cli
mcp_servers:
  freecad:
    command: {json.dumps(str(uv))}
    args:
      - --directory
      - {json.dumps(str(freecad_mcp))}
      - run
      - freecad-mcp
    enabled: true
  blender:
    command: {json.dumps(str(uvx))}
    args:
      - --python
      - "3.11"
      - blender-mcp
    env:
      DISABLE_TELEMETRY: "true"
      UV_PYTHON_PREFERENCE: only-managed
      BLENDER_HOST: 127.0.0.1
      BLENDER_PORT: "9876"
    enabled: true
_config_version: 33
"""
    target = home / "config.yaml"
    temporary = target.with_suffix(".yaml.tmp")
    temporary.write_text(config, encoding="utf-8")
    temporary.replace(target)
    target.chmod(0o600)
    print(f"HERMES_MANUAL_PROFILE_OK={target}")
    print("HERMES_MANUAL_SELF_IMPROVEMENT=disabled memory_nudge=0 skill_nudge=0")


if __name__ == "__main__":
    main()
