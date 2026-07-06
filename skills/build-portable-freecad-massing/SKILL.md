---
name: build-portable-freecad-massing
description: "Build canonical Phase 3 massing in FreeCAD from the versioned delivered-target envelope specification, after validating the open Blender target and approved portable site. Use only for Phase 3 in AEC_Demo_Portable."
---

# Build the delivered portable massing

This is the only supported canonical Phase 3 procedure. The massing is an
explicit reconstruction from the delivered Blender target and upstream
`massing_v3` evidence; it is not recovered Rhino construction history.

## Authorization and prerequisites

- Require a new human approval for canonical Phase 3 under `AGENTS.md`.
- Require the approved Phase 2 documents `PortableCliffHouseReference` and
  `PortableCliffHouseSite` to be open and saved.
- Consume the approval when the runner begins.

## Procedure

1. Resolve `ROOT=/home/nvidia/AEC_Demo_Portable`; do not search elsewhere.
2. Run exactly one terminal command from `ROOT`:

   ```bash
   python3 scripts/run-portable-massing.py
   ```

3. Require these ordered markers:

   ```text
   PORTABLE_MASSING_TARGET_OK
   PORTABLE_MASSING_BUILD_OK
   PORTABLE_MASSING_PREPARATION_OK
   ```

4. Verify the target check reports zero missing Blender objects. Verify the
   build reports 11 FreeCAD objects, 11 solids, and six linked site-context
   objects.
5. Present the active FreeCAD isometric view and explain that the boxes are
   target-envelope reconstruction geometry.
6. Stop with `PHASE_REVIEW_REQUIRED phase=3 name=building_massing`.

## Prohibited actions

- Do not call FreeCAD `execute_code` directly.
- Do not create or rename `CliffHouseReference`, `CliffHouseRebuild`, or source
  anchors.
- Do not modify `PortableCliffHouseReference` or `PortableCliffHouseSite`.
- Do not proceed to architectural detailing.
