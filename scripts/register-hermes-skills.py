#!/usr/bin/env python3
"""Register this repository's source-controlled skills with Hermes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
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

    # Register the repository-pinned FreeCAD MCP server with Hermes. Hermes
    # bundles uv under ~/.hermes/bin; fall back to a system uv when present.
    uv = HERMES_HOME / "bin" / "uv"
    if not uv.is_file():
        located = shutil.which("uv")
        uv = Path(located) if located else uv
    freecad_mcp = ROOT / "runtime" / "freecad-mcp"
    if freecad_mcp.is_dir() and uv.is_file():
        servers = config.setdefault("mcp_servers", {})
        if not isinstance(servers, dict):
            raise RuntimeError("Hermes config key 'mcp_servers' must be a mapping")
        servers["freecad"] = {
            "command": str(uv.resolve()),
            "args": [
                "--directory",
                str(freecad_mcp.resolve()),
                "run",
                "freecad-mcp",
            ],
            "enabled": True,
        }

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
    if freecad_mcp.is_dir() and uv.is_file():
        print(f"HERMES_FREECAD_MCP_REGISTERED={freecad_mcp} command={uv}")


if __name__ == "__main__":
    main()
