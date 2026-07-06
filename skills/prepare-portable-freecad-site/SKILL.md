---
name: prepare-portable-freecad-site
description: "Import the delivered beach_house_02.3dm template into an immutable FreeCAD reference and build its source-derived terrain, lot boundary, building pad, driveway, patio, and stairs through the checked portable adapter. Use only for canonical Phase 2 site preparation in AEC_Demo_Portable."
---

# Prepare the delivered FreeCAD site

This is the only supported Phase 2 procedure for the delivered portable demo.
Never recreate its FreeCAD code in chat and never substitute guessed geometry.

## Authorization

- Require a current human-user approval for canonical Phase 2 under
  `AGENTS.md`.
- The approval is consumed when the runner begins.
- Do not use this skill for massing or any later phase.

## Procedure

1. Resolve `ROOT=/home/nvidia/AEC_Demo_Portable`; do not search elsewhere.
2. Run exactly one command through the terminal tool from `ROOT`:

   ```bash
   python3 scripts/run-portable-site-preparation.py
   ```

3. Require these ordered markers:

   ```text
   PORTABLE_RHINO_EXTRACT_OK
   PORTABLE_FREECAD_REFERENCE_OK
   PORTABLE_SITE_BUILD_OK
   PORTABLE_SITE_PREPARATION_OK
   ```

4. Verify the reported reference count is 11 curves with zero unsupported
   objects. Verify the site count is six objects, four slabs, 5,913 terrain
   vertices, and 11,520 terrain faces.
5. Present the active FreeCAD isometric view for human review.
6. Stop. Report
   `PHASE_REVIEW_REQUIRED phase=2 name=site_preparation` and wait for a new
   human approval.

## Prohibited actions

- Do not call FreeCAD `execute_code` directly during this phase.
- Do not create B-splines, dimensions, terrain, pads, or walls ad hoc.
- Do not launch Rhino or OBS.
- Do not proceed to massing.
