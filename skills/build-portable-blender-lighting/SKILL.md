---
name: build-portable-blender-lighting
description: "Build canonical Phase 9 HDRI-only lighting in Blender, hide the delivered Sun, add the fire practical, and save four compass previews. Use only for Phase 9 in AEC_Demo_Portable."
---

# Build the delivered portable lighting checkpoint

This is the only supported canonical Phase 9 procedure. It creates a clean
world from the bundled HDRI, permanently hides the delivered Sun, adds the warm
fire practical, and generates four compass review screenshots.

## Read-only readiness check

Before approval, run only `python3 scripts/check-portable-lighting-ready.py`.
Require `PORTABLE_LIGHTING_READY_OK` and stop with
`WAITING_FOR_HUMAN_APPROVAL phase=9 name=lighting`.

## Authorization and procedure

- Require and consume one new Phase 9 human approval under `AGENTS.md`.
- Run only `python3 scripts/run-portable-lighting.py`.
- Require `PORTABLE_LIGHTING_INPUT_OK`, `PORTABLE_LIGHTING_WORLD_OK`,
  `PORTABLE_LIGHTING_LIGHTS_OK`, `PORTABLE_LIGHTING_PREVIEWS_OK`, and
  `PORTABLE_LIGHTING_PREPARATION_OK`.
- Verify the bundled HDRI, gamma 4.0, strength 1.2, hidden Sun, warm FireLight,
  four compass previews, and restored `ocean_view` camera.
- Stop with `PHASE_REVIEW_REQUIRED phase=9 name=lighting`.

## Prohibited actions

- Do not overwrite Phase 8 or alter geometry, materials, or camera framing.
- Do not leave any Sun or area light renderable.
- Do not download an HDRI or use a missing legacy texture path.
- Do not proceed to Phase 10.
