---
name: render-portable-blender-test-passes
description: "Render canonical Phase 11 still-image beauty, depth, and segmentation test passes from ocean_view, validate them, and restore the scene. Use only for Phase 11 in AEC_Demo_Portable."
---

# Render the delivered portable test passes

This is the only supported canonical Phase 11 procedure for the accepted
still-image path. It renders one aligned beauty, depth, and segmentation frame,
validates the files, restores the approved scene, and saves a new checkpoint.

## Procedure

- Before approval run only `python3 scripts/check-portable-test-renders-ready.py`.
- Require `PORTABLE_TEST_RENDER_READY_OK`, then stop with
  `WAITING_FOR_HUMAN_APPROVAL phase=11 name=test_renders`.
- After one new human approval run only
  `python3 scripts/run-portable-test-renders.py`.
- Require all `PORTABLE_TEST_RENDER_*_OK` markers through
  `PORTABLE_TEST_RENDER_PREPARATION_OK`.
- Stop with `PHASE_REVIEW_REQUIRED phase=11 name=test_renders`.

Do not submit ComfyUI, alter the hero camera, or proceed to Phase 12.
