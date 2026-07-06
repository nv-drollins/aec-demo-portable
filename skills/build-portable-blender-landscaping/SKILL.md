---
name: build-portable-blender-landscaping
description: "Create canonical Phase 5 landscaping/site context in Blender from the checked delivered target while validating the saved FreeCAD reconstruction. Use only for Phase 5 in AEC_Demo_Portable."
---

# Build the delivered portable landscaping checkpoint

This is the only supported canonical Phase 5 procedure. It validates the
approved FreeCAD reconstruction, checks exact site objects and materials in the
delivered Blender target, and saves a separate Blender landscaping checkpoint.
It does not overwrite the delivered target or add Phase 6 entourage.

## Authorization and prerequisites

- Require a new human approval for canonical Phase 5 under `AGENTS.md`.
- Require approved, saved Phase 2, Phase 3, and Phase 4 portable documents.
- Consume the approval when the runner begins.

## Read-only readiness check

Before approval, run only:

```bash
python3 scripts/check-portable-landscaping-ready.py
```

Require `PORTABLE_LANDSCAPING_READY_OK`, report the six-role Phase 5 scope,
and stop with
`WAITING_FOR_HUMAN_APPROVAL phase=5 name=landscaping_site_context`.
Do not use system-Python FreeCAD imports, raw MCP code, or generated shell
snippets for this check.

## Procedure

1. Resolve `ROOT=/home/nvidia/AEC_Demo_Portable`; do not search elsewhere.
2. Run exactly one terminal command from `ROOT`:

   ```bash
   python3 scripts/run-portable-landscaping.py
   ```

3. Require these ordered markers:

   ```text
   PORTABLE_LANDSCAPING_FREECAD_OK
   PORTABLE_LANDSCAPING_TARGET_OK
   PORTABLE_LANDSCAPING_BUILD_OK
   PORTABLE_LANDSCAPING_PREPARATION_OK
   ```

4. Verify 15 checked target objects across six site roles, exact material
   assignments, the `AEC_Phase5_Landscaping` collection, and a separately saved
   Blender checkpoint.
5. Show the Blender material-preview site view and explain that this phase uses
   the delivered Blender scene as the authoritative visual target while the
   saved FreeCAD files remain the reconstruction record.
6. Stop with `PHASE_REVIEW_REQUIRED phase=5 name=landscaping_site_context`.

## Prohibited actions

- Do not call Blender MCP `execute_code` directly.
- Do not overwrite a delivered Blender scene.
- Do not add furniture, vehicles, people, planters, or other Phase 6 entourage.
- Do not change camera, lighting, final materials, or submit to ComfyUI.
- Do not proceed to Phase 6.
