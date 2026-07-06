# Phase 7 — Camera Placement
### Camera Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 7, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Create and position all cameras: the hero animation camera and the utility compass
test camera. Render one hero-camera still to confirm framing before animation setup.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 6
- Delta notes — check for: hero camera position, lens focal length, look target

## Outputs

- `[project]/blender_assets/base_model.blend` — cameras added
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — one hero-camera still

---

## Pre-Phase Audit Checklist

- [ ] Phase 6 gate approved
- [ ] All materials applied and confirmed

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender camera setup, `obs-set-current-scene("BLENDER")`.

→ **OBS ACTION:** Still rendered, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. Hero camera — ocean_view
- Name: `ocean_view`
- This is the primary camera for the main render sequence (Phase 11).
- Position: to the south-west of the building, looking north-east.
  [adjustable — camera azimuth and radius per delta notes]
- Lens: 28mm. [adjustable]
- Height: ~5–6m (slightly above standing eye level). [adjustable]
- Track-To constraint aimed at a target empty slightly above the building centre.
- Render one still at 1280×720, 128 samples.
- Save to `[project]/test_renders/hero_camera_test.png`.

### 2. Compass test camera — compass_cam
- Name: `compass_cam`
- Utility camera for test renders throughout all phases.
- No animation keyframes — repositioned per render via script.
- Lens: 35mm.
- Standard orbit: 45m radius from building centre, 5–6m height. [adjustable]
- Used for NW/NE/SE/SW test renders at any phase.

### 3. Patio sweep camera — patio_sweep_cam
- Name: `patio_sweep_cam`
- Animation camera for the patio sweep sequence (Phase 9).
- Lens: 24mm (wider — captures patio foreground + house background).
- Position and animation keyframes set in Phase 9.
- Create the camera object now; leave it unpositioned until Phase 9.

---

## Post-Phase Cleanup Checklist

- [ ] `ocean_view` camera renders correct framing — patio in foreground/midground,
      building west face dominant, roof plane in upper frame
- [ ] `compass_cam` object exists and is correctly named
- [ ] `patio_sweep_cam` object exists (unpositioned — will be set in Phase 9)
- [ ] Hero test still saved to `[project]/test_renders/`

---

## ▶ REVIEW GATE 7 — Camera

Present: hero camera test still.
Confirm: horizon line placement, patio visible, building framing.
Wait for written approval.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `07-camera-claude.mkv`, `07-camera-blender.mkv`. Confirm.

Proceed to `11_lighting_prompt.md`.
