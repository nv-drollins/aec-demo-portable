# Phase 8 — Lighting
### Lighting Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 8, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Tune the HDRI lighting: rotation (warm zone direction), strength, and gamma
compression. The sun lamp is permanently hidden. The fire pit provides its own
practical warm light. No artificial key lights.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 7
- `[project]/hdr/` — project HDRI file(s)
- Delta notes — check for: time of day, mood, HDRI file preference, warm zone direction

## Outputs

- `[project]/blender_assets/base_model.blend` — lighting tuned
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — four diagonal compass stills with final lighting

---

## Pre-Phase Audit Checklist

- [ ] Phase 7 gate approved
- [ ] HDRI file confirmed in `[project]/hdr/`
- [ ] No sun lamp in scene (if one exists, move to `__hidden__` collection,
      set `hide_render=True`, exclude from view layer — it must never appear again)

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender work, `obs-set-current-scene("BLENDER")`.
Stay on BLENDER through all lighting iterations — each test render visible
in the Blender render window is good footage.

→ **OBS ACTION:** Lighting confirmed, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. World shader node setup
Build the following node chain in the World shader if not already present:
```
Environment Texture → Mapping (Rotation Z: adjustable) →
Gamma (Value: ~4.0) → Background (Strength: adjustable) → World Output
```
- Gamma node compresses the sky dynamic range — increases perceived contrast
  without clipping wall highlights. Starting value 4.0. [adjustable]
- No sun lamp. No area lights. Fire point light only for practical warmth.

### 2. Load HDRI
- Load from `[project]/hdr/[filename]` into the Environment Texture node.

### 3. Rotate HDRI
- Rotate the HDRI Mapping node Z axis until the warm zone (embedded sun direction)
  reads as coming from the south-west — consistent with the building's west
  view orientation. [adjustable per delta — e.g. south-east for a different site]
- Verify by reading shadows and highlights in a test render, not from code alone.

### 4. Adjust strength and gamma
- Render compass test stills and compare:
  - Walls should read as warm, not washed out or too dark
  - Roof should catch the light with a slight metallic sheen
  - Balcony underside should have soft shadow, not complete blackness
  - Glass should reflect the sky with some depth
- Adjust Background Strength and Gamma node value iteratively.
- Typical final values: Strength 1.0–2.0, Gamma 3.5–5.0. [project-specific]

### 5. Permanently hide sun lamp
If any sun lamp exists:
- Move to `__hidden__` collection
- `hide_render = True`, `hide_viewport = True`
- Lock all transforms
- Exclude collection from all view layers
- This is permanent for the project — document in delta notes

### 6. Fire point light
- Confirm `FireLight` point light is present, energy ~600–800, colour warm orange.
- Confirm it casts visible warm contribution to the chairs nearest the fire
  in a test render.

### 7. Render four compass test stills
- `compass_cam` at NW, NE, SE, SW. 128 samples, 1280×720.
- Save to `[project]/test_renders/lighting_NW.png` etc.

---

## Post-Phase Cleanup Checklist

- [ ] No sun lamp in render (confirm by checking scene lights list)
- [ ] HDRI warm zone comes from south-west (or confirmed delta direction)
- [ ] Walls read as warm ochre — not white, not grey
- [ ] Roof catches directional light from correct side
- [ ] Glass shows sky reflection
- [ ] Fire light visible as orange glow in patio test render
- [ ] Four lighting test stills saved to `[project]/test_renders/`

---

## ▶ REVIEW GATE 8 — Lighting

Present: four diagonal compass stills with final materials and lighting.
Confirm: overall mood, warm zone direction, no blown highlights, fire light visible.
Wait for written approval.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `08-lighting-claude.mkv`, `08-lighting-blender.mkv`. Confirm.

Proceed to `12_animation_prompt.md`.
