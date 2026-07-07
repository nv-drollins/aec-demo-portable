#!/usr/bin/env python3
"""List, validate, and materialize reusable AEC prompt profiles."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parent.parent
PRESETS = {
    "delivered_cliff_house_demo": (
        ROOT / "profiles/delivered_cliff_house_demo/prompt_profile.md"
    ),
}
GENERIC_TEMPLATE = ROOT / "prompts/project_template/project_design_brief_template.md"
PLACEHOLDERS = (
    re.compile(r"\[FILL IN\]", re.IGNORECASE),
    re.compile(r"\[TBD\]", re.IGNORECASE),
    re.compile(r"REPLACE_WITH", re.IGNORECASE),
)
REQUIRED_PROFILE_TEXT = (
    "profile_format: aec-demo-prompt-profile-v1",
    "status: ready_for_human_gated_demo",
    "execution_phases_authorized: none",
    "execution_approval_source: current_human_user_turn_only",
    "## 2. Authoritative instructions",
    "## 4. Authoritative assets",
    "## 6. Human-gated phase sequence",
    "## 8. Review and success gates",
    "Do not begin or execute the phase",
    "WAITING_FOR_HUMAN_APPROVAL",
    "scripts/run-portable-site-preparation.py",
    "scripts/run-portable-massing.py",
    "scripts/run-portable-detailing.py",
    "scripts/check-portable-landscaping-ready.py",
    "scripts/run-portable-landscaping.py",
    "scripts/check-portable-entourage-ready.py",
    "scripts/run-portable-entourage.py",
    "scripts/check-portable-materials-ready.py",
    "scripts/run-portable-materials.py",
    "scripts/check-portable-camera-ready.py",
    "scripts/run-portable-camera.py",
    "scripts/check-portable-lighting-ready.py",
    "scripts/run-portable-lighting.py",
    "scripts/check-portable-animation-skip-ready.py",
    "scripts/run-portable-animation-skip.py",
    "scripts/check-portable-test-renders-ready.py",
    "scripts/run-portable-test-renders.py",
    "scripts/check-portable-final-ready.py",
    "scripts/run-portable-final-transformation.py",
)
PATH_REFERENCE = re.compile(
    r"`((?:sample_project|prompts|comfyui|scripts)/[^`]+)`"
)
LIST_ITEM = re.compile(r"^(?:[-*]|\d+\.)\s+")


def unresolved(text: str) -> list[str]:
    return [pattern.pattern for pattern in PLACEHOLDERS if pattern.search(text)]


def referenced_paths(text: str) -> list[Path]:
    candidates = PATH_REFERENCE.findall(text)
    return [ROOT / candidate.rstrip(".,") for candidate in candidates]


def optional_referenced_paths(text: str) -> set[Path]:
    """Return paths under list items explicitly labeled as optional.

    A path may continue on the line following its list-item label. A blank line
    ends that item's scope so an optional marker cannot leak into later prose.
    """
    optional = False
    paths: set[Path] = set()
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            optional = False
            continue
        if LIST_ITEM.match(stripped):
            label = LIST_ITEM.sub("", stripped, count=1).casefold()
            optional = label.startswith("optional ")
        if optional:
            paths.update(
                ROOT / candidate.rstrip(".,")
                for candidate in PATH_REFERENCE.findall(raw)
            )
    return paths


def validate(path: Path, allow_placeholders: bool = False) -> None:
    if not path.is_file():
        raise RuntimeError(f"Prompt profile does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    missing_sections = [token for token in REQUIRED_PROFILE_TEXT if token not in text]
    if missing_sections:
        raise RuntimeError(f"Profile is missing required content: {missing_sections}")
    found = unresolved(text)
    if found and not allow_placeholders:
        raise RuntimeError(f"Profile contains unresolved placeholders: {found}")
    references = referenced_paths(text)
    optional_paths = optional_referenced_paths(text)
    missing_paths = [
        item for item in references
        if item not in optional_paths and not item.exists()
    ]
    if missing_paths:
        raise RuntimeError(f"Profile references missing project files: {missing_paths}")
    missing_optional = [
        item for item in references
        if item in optional_paths and not item.exists()
    ]
    for item in missing_optional:
        print(f"PROMPT_PROFILE_OPTIONAL_REFERENCE_MISSING={item}")
    print(
        f"PROMPT_PROFILE_OK={path.resolve()} "
        f"placeholders={len(found)} references={len(references)} "
        f"optional_missing={len(missing_optional)}"
    )


def copy_checked(source: Path, output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise RuntimeError(f"Refusing to replace existing profile: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
    print(f"PROMPT_PROFILE_MATERIALIZED={output.resolve()} source={source.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("profile", type=Path)
    validate_parser.add_argument("--allow-placeholders", action="store_true")

    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--preset", choices=sorted(PRESETS), required=True)
    materialize.add_argument("--output", type=Path, required=True)
    materialize.add_argument("--force", action="store_true")

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("--output", type=Path, required=True)
    new_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()
    if args.command == "list":
        for name, path in PRESETS.items():
            print(f"PROMPT_PROFILE_PRESET name={name} path={path}")
    elif args.command == "validate":
        validate(args.profile.resolve(), args.allow_placeholders)
    elif args.command == "materialize":
        source = PRESETS[args.preset]
        validate(source)
        copy_checked(source, args.output, args.force)
        validate(args.output.resolve())
    else:
        copy_checked(GENERIC_TEMPLATE, args.output, args.force)
        print("PROMPT_PROFILE_TEMPLATE_READY placeholders_expected=true")


if __name__ == "__main__":
    main()
