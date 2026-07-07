---
name: run-portable-blender-comfy-final
description: "Run canonical Phase 12 final Blender-to-ComfyUI transformation, validate exactly three outputs, and save the final checkpoint. Use only for Phase 12 in AEC_Demo_Portable."
---

# Run the final Blender-to-ComfyUI transformation

- Before approval run only `python3 scripts/check-portable-final-ready.py`.
- Require `PORTABLE_FINAL_READY_OK`, then stop with
  `WAITING_FOR_HUMAN_APPROVAL phase=12 name=final_blender_comfyui`.
- After one new human approval run only
  `python3 scripts/run-portable-final-transformation.py`.
- Require `PORTABLE_FINAL_INPUT_OK`, `PORTABLE_FINAL_CAMERA_OK`,
  `PORTABLE_FINAL_STRUCTURE_OK`, `PORTABLE_FINAL_SUBMISSION_OK`,
  `PORTABLE_FINAL_IMAGES_OK`, and `PORTABLE_FINAL_PREPARATION_OK`.
- Stop with `FINAL_REVIEW_REQUIRED phase=12 name=final_blender_comfyui`.

Do not use sample inputs, inferred DepthAnything geometry, raw ComfyUI requests,
or claim completion without the camera-v4 exact depth contract, three validated output images and a saved final Blender checkpoint.
