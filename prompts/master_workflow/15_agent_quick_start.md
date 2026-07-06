# Agent Reference — Quick Start Checklist
### For Claude / AI agent use. Human users: see docs/01_demo_quick_start_guide.md
*Version 1.0 — May 2026*

---

## Prerequisites Checklist

| Item | Check |
|---|---|
| Rhino 3D open, blank scene | ☐ |
| Blender open, blank scene | ☐ |
| BlenderMCP server running (port 9876) | ☐ |
| RhinoMCP server running | ☐ |
| OBS open, `aec_demo_master` profile loaded | ☐ |
| OBS sources verified (screenshot each — see 02_demo_prompt.md) | ☐ |
| Google Chrome available (reserved for ComfyUI) | ☐ |
| Project HDRI file(s) in `aa_demo_versions/[project]/hdr/` | ☐ |

---

## New Project — 7 Steps

1. Confirm project name: `lowercase_with_underscores_01`
2. Create folder tree mirroring `dummy_beach_house_01`
3. Write delta notes in `[project]/prompts/` if design differs from master brief
4. Verify OBS sources via `obs-get-source-screenshot` for each scene
5. Set OBS output → `[project]/demo_captures/` and Blender output → `[project]/renders/`
6. Init blank Rhino (`rhino_assets/base_model.3dm`) and Blender (`blender_assets/base_model.blend`)
7. `obs-set-current-scene("CLAUDE")` → `obs-start-record` → begin Phase 1

---

## Phase Execution Order

| # | Prompt file | Apps |
|---|---|---|
| 0 | `03_config_prompt.md` | Claude |
| 1 | `04_site_prep_prompt.md` | Claude + Rhino |
| 2 | `05_massing_prompt.md` | Claude + Rhino |
| 3 | `06_detailing_prompt.md` | Claude + Rhino |
| 4 | `07_landscaping_prompt.md` | Claude + Blender |
| 5 | `08_entourage_prompt.md` | Claude + Blender |
| 6 | `09_materials_prompt.md` | Claude + Blender |
| 7 | `10_camera_prompt.md` | Claude + Blender |
| 8 | `11_lighting_prompt.md` | Claude + Blender |
| 9 | `12_animation_prompt.md` | Claude + Blender |
| 10 | `13_test_render_prompt.md` | Claude + Blender |
| 11 | `14_final_render_prompt.md` | Claude + Blender + Chrome |

---

## At Every Gate

1. Keep OBS recording until gate approved
2. Present renders/screenshots
3. Iterate on feedback
4. User approves in writing
5. Save Rhino + Blender checkpoints
6. Stop OBS, rename files: `{phase:02d}-{topic}-{app}.mkv`
7. Proceed to next phase prompt

---

## OBS File Naming Reference

`{phase:02d}-{topic}-{app}.mkv` — e.g. `05-entourage-blender.mkv`

Phase topics: `project_setup`, `site_prep`, `massing`, `detailing`,
`landscaping`, `entourage`, `materials`, `camera`, `lighting`,
`animation`, `test_render`, `final_render`

Apps: `claude`, `rhino`, `blender`, `comfyui`

---

## Top 5 Agent Failure Modes

1. No `rotation_mode = 'XYZ'` on imports → rotation silently ignored
2. `scene.frame_set()` inside keyframe loop → all frames same position
3. `np.flipud()` on EXR depth maps → upside-down output
4. Recording before OBS source verification → wrong window captured
5. No checkpoint at gate → unrecoverable phase state
