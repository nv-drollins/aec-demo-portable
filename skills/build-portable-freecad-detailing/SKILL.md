---
name: build-portable-freecad-detailing
description: "Build canonical Phase 4 architectural detailing in FreeCAD from a fail-closed delivered-Blender target manifest: structural slabs, segmented walls, glazing, mullions, frames, doors, and railings. Use only for Phase 4 in AEC_Demo_Portable."
---

# Build the delivered portable architectural detailing

This is the only supported canonical Phase 4 procedure. It reconstructs native
FreeCAD detail solids from named target elements and target bounds. It does not
copy Blender meshes or claim recovered Rhino construction history.

## Authorization and prerequisites

- Require a new human approval for canonical Phase 4 under `AGENTS.md`.
- Require approved, saved Phase 2 and Phase 3 portable documents.
- Consume the approval when the runner begins.

## Procedure

1. Resolve `ROOT=/home/nvidia/AEC_Demo_Portable`; do not search elsewhere.
2. Run exactly one terminal command from `ROOT`:

   ```bash
   python3 scripts/run-portable-detailing.py
   ```

3. Require these ordered markers:

   ```text
   PORTABLE_DETAILING_TARGET_OK
   PORTABLE_DETAILING_OVERLAP_OK
   PORTABLE_DETAILING_BUILD_OK
   PORTABLE_DETAILING_PREPARATION_OK
   ```

4. Verify 112 target objects, 109 FreeCAD detail objects, six site links, 18
   wall-opening cuts, 28 glazing/frame cuts, and zero wall/glass, wall/door,
   and frame/glass overlaps.
5. Show Isometric, Front, and Right FreeCAD views. Cyan glazing is intentionally
   opaque in FreeCAD to avoid a FreeCAD 1.1 transparency-sorting defect; Blender
   remains the authoritative transparent-material view.
6. Stop with
   `PHASE_REVIEW_REQUIRED phase=4 name=architectural_detailing`.

## Prohibited actions

- Do not call FreeCAD `execute_code` directly.
- Do not edit or alias Phase 2/3 documents.
- Do not substitute the older Rhino detailing instructions or generate
  unversioned booleans.
- Do not proceed to landscaping.
