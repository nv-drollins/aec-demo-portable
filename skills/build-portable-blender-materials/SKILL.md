---
name: build-portable-blender-materials
description: "Build canonical Phase 7 materials in Blender by preserving the delivered target shaders, finalizing procedural entourage materials, and completing exact segmentation tags. Use only for Phase 7 in AEC_Demo_Portable."
---

# Build the delivered portable materials checkpoint

This is the only supported canonical Phase 7 procedure. The delivered Blender
target already carries the authoritative building/site materials. This skill
preserves those shaders, assigns the final palette to Phase 6 entourage, and
fills the exact missing object tags required by the segmentation pipeline.

## Read-only readiness check

Before approval, run only:

```bash
python3 scripts/check-portable-materials-ready.py
```

Require `PORTABLE_MATERIALS_READY_OK` and stop with
`WAITING_FOR_HUMAN_APPROVAL phase=7 name=materials`.

## Authorization and procedure

- Require and consume one new Phase 7 human approval under `AGENTS.md`.
- Run only `python3 scripts/run-portable-materials.py` from the repository root.
- Require these ordered markers:

  ```text
  PORTABLE_MATERIALS_INPUT_OK
  PORTABLE_MATERIALS_ASSIGNMENT_OK
  PORTABLE_MATERIALS_SHADER_OK
  PORTABLE_MATERIALS_PREPARATION_OK
  ```

- Verify 160 tagged/materialized meshes, 150 preserved source meshes, ten
  finalized entourage meshes, and all three delivered glass shaders.
- Show the material-preview result and stop with
  `PHASE_REVIEW_REQUIRED phase=7 name=materials`.

## Prohibited actions

- Do not overwrite Phase 6 or the delivered target.
- Do not replace the delivered building/site shaders from prose.
- Do not change geometry, camera, world, or lighting.
- Do not render passes or submit to ComfyUI.
- Do not proceed to Phase 8.
