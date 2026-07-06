# Phase 6 — Material Assignment
### Materials Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 6 + Appendix B, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Apply final Principled BSDF materials to all building surfaces. Render test frames
progressively after each material category so the video shows materials appearing
on the model one system at a time.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 5
- Delta notes — check for: colour palette overrides, any non-standard materials
- Appendix B of `01_user_prompt.md` — master material reference table

## Outputs

- `[project]/blender_assets/base_model.blend` — all materials applied
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — eight test stills (four building + four patio)

---

## Pre-Phase Audit Checklist

- [ ] Phase 5 gate approved
- [ ] All geometry objects are named correctly (material assignment is name-driven)
- [ ] Delta notes read for palette overrides

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before first Blender command, `obs-set-current-scene("BLENDER")`.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

Apply each material category below, render a quick 64-sample test after each one
so progress is visible in the Blender render window (good footage for the demo).

### Material palette (master defaults — override with delta notes)

| Material name | Objects | Colour (linear) | Roughness | Metallic |
|---|---|---|---|---|
| `M_Wall_Ochre` | walls, balconies, railings, posts, floor_L2 | (0.42, 0.28, 0.07) | 0.78 | 0 |
| `M_Roof_Metal` | roof_slab, entry_canopy | (0.06, 0.08, 0.18) | 0.55 | 0.55 |
| `M_Glass` | all glass panels, doors | (0.12, 0.18, 0.22) | 0.0 | 0 |
| `M_Aluminum` | mullions, frames | (0.15, 0.15, 0.16) | 0.80 | 0.20 |
| `M_Wood` | front_door, garage_doors | (0.12, 0.07, 0.02) | 0.72 | 0 |
| `M_DarkConcrete` | steps, driveway, street, floor_L1, pad, curtain_wall | (0.09, 0.09, 0.09) | 1.0 | 0 |
| `M_Slab_LightGray` | veranda slab | (0.50, 0.50, 0.50) | 0.80 | 0 |
| `M_Grass` | terrain | (0.00375, 0.010, 0.00375) | 0.92 | 0 |
| `M_Patio_Stone` | patio_disc, firepit_coffee_table | (0.12, 0.11, 0.10) | 0.88 | 0 |
| `M_ChairWood` | all adirondack chairs | (0.35, 0.22, 0.10) | 0.72 | 0 |

Glass: set `Transmission Weight = 0.25` (or equivalent in Blender 5.x).

### Assignment order (for visual progression in the demo recording)
1. Walls and ochre elements
2. Roof and canopy
3. Glazing and mullions
4. Doors
5. Concrete and ground elements
6. Terrain (if not already from Phase 4)
7. Patio and chairs

Render a quick test still after steps 1, 3, 5, and 7.

---

## Post-Phase Cleanup Checklist

- [ ] No surface reads as pure white or pure black in a test render at default lighting
- [ ] Glass has transmission — visible as translucent/reflective, not opaque
- [ ] Roof metallic sheen is visible at grazing angles in a render
- [ ] Ochre walls read as warm and matte — no sheen
- [ ] Terrain is distinctly darker than walls — does not dominate the composition
- [ ] Patio and fire pit table are same dark stone material
- [ ] Chairs are warm teak brown — distinct from the dark concrete

---

## ▶ REVIEW GATE 6 — Materials

Present:
1. Four diagonal compass stills of the whole house (NW, NE, SE, SW) at 640×360
2. Four close-up patio stills (NW, NE, SE, SW) at 640×360

Confirm: palette reads warmly and coherently, glass reads correctly,
no surface is too light or too dark. Wait for written approval.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `06-materials-claude.mkv`, `06-materials-blender.mkv`. Confirm.

Proceed to `10_camera_prompt.md`.
