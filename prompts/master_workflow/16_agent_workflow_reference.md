# Agent Reference — Workflow Reference
### For Claude / AI agent use. Human users: see docs/02_user_guide.md
*Version 1.0 — May 2026*
*This is the condensed agent-readable version of the workflow. For full phase details
see 03_config_prompt.md through 14_final_render_prompt.md. For skills and code patterns
see aec_skills.md.*

---

## Coordinate System
+X East · +Y North · +Z Up · 1 unit = 1 metre

## Project Paths
Root: `C:\Users\swags\Documents\aec_demo_master\`
Projects: `aa_demo_versions\[project_name]\`
Structure mirrors: `dummy_beach_house_01`

## Prompt Inheritance
Master prompts (`master_prompts/`) never modified per-project.
Project overrides in `[project]/prompts/` as delta documents.
Read master first, apply deltas on top.

## Checkpoint Rule
Save Rhino + Blender timestamped checkpoints at every gate approval.
Blender: `blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
Rhino: `rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`

## Phase Summary

| Phase | Key work | Output location |
|---|---|---|
| 0 Config | Dirs, OBS, paths | `[project]/` structure created |
| 1 Site | Terrain NURBS, pad, curtain wall | `rhino_assets/` |
| 2 Massing | Building volumes, roof, slabs | `rhino_assets/` |
| 3 Detailing | Glazing, entry, garage, driveway | `rhino_assets/` |
| 4 Landscaping | Rhino→Blender, site materials | `blender_assets/` |
| 5 Entourage | Patio, Hyper3D chairs, fire | `blender_assets/` |
| 6 Materials | All Principled BSDF materials | `blender_assets/` |
| 7 Camera | ocean_view, compass_cam, sweep_cam | `blender_assets/` |
| 8 Lighting | HDRI, rotation, gamma, fire light | `blender_assets/` |
| 9 Animation | Smoothstep sweep, 193 keyframes | `blender_assets/` |
| 10 Test Render | Half-res beauty + depth + seg | `test_renders/` |
| 11 Final Render | Full-res + EXR + ComfyUI | `renders/` + `comfy_output/` |

## Critical Rules (never skip)

- Set `rotation_mode = 'XYZ'` on every imported object immediately after import
- Keyframe insertion: set property first, then `keyframe_insert(frame=N)` — never `scene.frame_set()` in loop
- Depth maps: use View Distance emission + per-frame normalisation — never Workbench depth mode
- No flipud on Blender EXRs — OpenEXR Python is already top-down
- Segmentation: ALL bounce types = 0, world strength = 0, film_transparent = True
- OBS: verify sources at session start via `obs-get-source-screenshot` before any recording
- Trim (not BooleanDifference) for terrain cuts in Rhino

## Material Palette (defaults)

| Name | Objects | Colour (linear) | R | M |
|---|---|---|---|---|
| M_Wall_Ochre | walls, balconies, posts | 0.42,0.28,0.07 | 0.78 | 0 |
| M_Roof_Metal | roof, canopy | 0.06,0.08,0.18 | 0.55 | 0.55 |
| M_Glass | glazing, doors | 0.12,0.18,0.22 | 0.0 | 0 |
| M_Aluminum | mullions | 0.15,0.15,0.16 | 0.80 | 0.20 |
| M_Wood | doors | 0.12,0.07,0.02 | 0.72 | 0 |
| M_DarkConcrete | pad, drive, steps | 0.09,0.09,0.09 | 1.0 | 0 |
| M_Grass | terrain | 0.00375,0.010,0.00375 | 0.92 | 0 |
| M_Patio_Stone | patio, table | 0.12,0.11,0.10 | 0.88 | 0 |
| M_ChairWood | chairs | 0.35,0.22,0.10 | 0.72 | 0 |

## Segmentation Palette
walls=204,30,30 · glass=25,204,229 · roof=25,25,217 · slabs=229,140,25
mullions=153,153,153 · terrain=20,115,20 · steps=89,51,20
drive=51,51,51 · pad=102,102,102

## Render Settings Reference
| Level | Resolution | Samples | Use |
|---|---|---|---|
| Quick check | 640×360 | 64 | Single frame |
| Test | 960×540 | 128 | Full animation review |
| Final | 1920×1080 | 384 | Delivery |
