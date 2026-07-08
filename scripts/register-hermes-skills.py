#!/usr/bin/env python3
"""Register this repository's source-controlled skills with Hermes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile

import yaml


ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = str((ROOT / "skills").resolve())
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
CONFIG_PATH = HERMES_HOME / "config.yaml"


def existing_directories(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if stripped.startswith("["):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                decoded = None
            if isinstance(decoded, list):
                return [str(item) for item in decoded if str(item).strip()]
        return [stripped]
    return []


def main():
    HERMES_HOME.mkdir(parents=True, exist_ok=True)
    config = (
        yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        if CONFIG_PATH.exists()
        else {}
    )
    if not isinstance(config, dict):
        raise RuntimeError(f"Hermes config must be a mapping: {CONFIG_PATH}")
    model = config.setdefault("model", {})
    if not isinstance(model, dict):
        raise RuntimeError("Hermes config key 'model' must be a mapping")
    selected_model = os.environ.get("AEC_HERMES_MODEL", "ollama/qwen3.6:latest")
    force_model = os.environ.get("AEC_FORCE_HERMES_MODEL_CONFIG", "0") == "1"
    if force_model:
        model.update(default=selected_model, provider="custom", base_url="http://127.0.0.1:11434/v1")
    else:
        model.setdefault("default", selected_model)
        model.setdefault("provider", "custom")
        model.setdefault("base_url", "http://127.0.0.1:11434/v1")
    terminal = config.setdefault("terminal", {})
    if not isinstance(terminal, dict):
        raise RuntimeError("Hermes config key 'terminal' must be a mapping")
    terminal.setdefault("cwd", str(ROOT))
    skills = config.setdefault("skills", {})
    if not isinstance(skills, dict):
        raise RuntimeError("Hermes config key 'skills' must be a mapping")
    directories = existing_directories(skills.get("external_dirs"))
    resolved = []
    for directory in directories + [SKILLS_DIR]:
        expanded = str(Path(directory).expanduser().resolve())
        if expanded not in resolved:
            resolved.append(expanded)
    skills["external_dirs"] = resolved

    # Use the repository-pinned, already-resolved FreeCAD MCP environment.
    # This avoids an implicit uv sync (and network access) when a demo starts.
    freecad_mcp = ROOT / "runtime" / "freecad-mcp"
    freecad_runner = ROOT / "scripts" / "run-freecad-mcp.sh"
    freecad_binary = freecad_mcp / ".venv" / "bin" / "freecad-mcp"
    freecad_registered = False
    if freecad_mcp.is_dir():
        if freecad_runner.is_file() and freecad_binary.is_file():
            servers = config.setdefault("mcp_servers", {})
            if not isinstance(servers, dict):
                raise RuntimeError("Hermes config key 'mcp_servers' must be a mapping")
            servers["freecad"] = {
                "command": str(freecad_runner.resolve()),
                "args": [],
                "enabled": True,
            }
            freecad_registered = True
        else:
            print(
                "HERMES_FREECAD_MCP_SKIPPED=runtime_not_prepared "
                "run=scripts/prepare-freecad-mcp-runtime.sh"
            )

    mode = stat.S_IMODE(CONFIG_PATH.stat().st_mode) if CONFIG_PATH.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(
        dir=HERMES_HOME, prefix=".config.yaml."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(config, stream, sort_keys=False, allow_unicode=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, CONFIG_PATH)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"HERMES_SKILLS_REGISTERED={SKILLS_DIR} config={CONFIG_PATH}")
    print(f"HERMES_MODEL_CONFIGURED={model['default']} base_url={model.get('base_url', '')}")
    if freecad_registered:
        print(f"HERMES_FREECAD_MCP_REGISTERED={freecad_mcp} command={freecad_runner}")


if __name__ == "__main__":
    main()
