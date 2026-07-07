#!/usr/bin/env python3
"""Create the isolated Hermes profile used by automatic presentation mode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--lifetime", type=int, default=7500)
    args = parser.parse_args()

    root = args.root.resolve()
    home = args.home.resolve()
    if args.timeout < 1 or args.lifetime <= args.timeout:
        parser.error("--lifetime must be greater than --timeout, both positive")

    home.mkdir(parents=True, exist_ok=True)
    config = f"""\
model:
  default: {json.dumps(args.model)}
  provider: custom
  base_url: http://127.0.0.1:11434/v1
agent:
  max_turns: 48
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
  enabled: false
memory:
  memory_enabled: false
  user_profile_enabled: false
  nudge_interval: 0
  flush_min_turns: 999999
skills:
  creation_nudge_interval: 0
platform_toolsets:
  cli:
    - terminal
mcp_servers: {{}}
_config_version: 33
"""
    target = home / "config.yaml"
    temporary = target.with_suffix(".yaml.tmp")
    temporary.write_text(config, encoding="utf-8")
    temporary.replace(target)
    target.chmod(0o600)
    print(f"HERMES_AUTO_PROFILE_OK={target}")


if __name__ == "__main__":
    main()
