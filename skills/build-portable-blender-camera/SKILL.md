---
name: build-portable-blender-camera
description: "Build canonical Phase 8 camera placement in Blender from the delivered Camera_day framing, add utility cameras, and save a review still. Use only for Phase 8 in AEC_Demo_Portable."
---

# Build the delivered portable camera checkpoint

This is the only supported canonical Phase 8 procedure. It preserves the
delivered `Camera_day` framing as the authoritative hero composition, creates
the named hero and utility cameras required by the original prompt, and saves a
separate checkpoint plus a viewport review image.

## Read-only readiness check

Before approval, run only:

```bash
python3 scripts/check-portable-camera-ready.py
```

Require `PORTABLE_CAMERA_READY_OK` and stop with
`WAITING_FOR_HUMAN_APPROVAL phase=8 name=camera_placement`.

## Authorization and procedure

- Require and consume one new Phase 8 human approval under `AGENTS.md`.
- Run only `python3 scripts/run-portable-camera.py` from the repository root.
- Require `PORTABLE_CAMERA_INPUT_OK`, `PORTABLE_CAMERA_BUILD_OK`,
  `PORTABLE_CAMERA_FRAMING_OK`, `PORTABLE_CAMERA_PREVIEW_OK`, and
  `PORTABLE_CAMERA_PREPARATION_OK`.
- Verify `ocean_view`, `compass_cam`, and `patio_sweep_cam`; confirm the pool,
  patio, building center, and entry anchors remain inside the hero frame.
- Show the camera-view preview and stop with
  `PHASE_REVIEW_REQUIRED phase=8 name=camera_placement`.

## Prohibited actions

- Do not overwrite Phase 7 or delete `Camera_day`.
- Do not change geometry, materials, world lighting, or render passes.
- Do not substitute the prompt’s adjustable 28mm default for the delivered
  20.5mm authoritative framing.
- Do not proceed to Phase 9.
