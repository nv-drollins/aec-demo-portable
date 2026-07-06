# Phase 4 — Landscaping
### Landscaping Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 4, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Export Rhino geometry to Blender and apply site materials: lawn/terrain, building
pad, curtain wall, driveway, and street. No entourage yet — just the ground plane
and constructed base reading as a coherent site.

---

## Inputs

- `[project]/rhino_assets/base_model.3dm` — Phase 3 complete
- `[project]/hdr/` — HDRI files for lighting (loaded but not tuned yet)
- Delta notes — check for: terrain material, ground cover type, driveway material

## Outputs

- `[project]/blender_assets/base_model.blend` — Rhino geometry imported, site
  materials assigned
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — two compass-point test stills (SW and NE)

---

## Pre-Phase Audit Checklist

- [ ] Phase 3 gate approved
- [ ] Rhino geometry is complete and layers are correctly named
- [ ] Blender is open with empty Phase 0 baseline file
- [ ] HDRI file(s) are in `[project]/hdr/`
- [ ] OBS BLENDER source verified (screenshot check)

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.
Confirm: "Recording started — `04-landscaping-claude`."

→ **OBS ACTION:** Before first Blender command, `obs-set-current-scene("BLENDER")`.

→ **OBS ACTION:** Blender work complete, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. Export Rhino geometry to Blender
- Export all Rhino geometry as OBJ or FBX into `[project]/blender_assets/`.
- Import into Blender, preserving layer/object names.
- Confirm all objects are present and correctly named in the Blender outliner.
- Set `rotation_mode = 'XYZ'` on all imported objects immediately after import —
  Rhino exports often arrive as Quaternion rotation mode. Never skip this step.

### 2. Set up HDRI world lighting
- Load the project HDRI from `[project]/hdr/` into the World shader.
- Set up: Environment Texture → Mapping node (for rotation) → Gamma node
  (initial value ~4.0) → Background node → World Output.
- Initial strength: start at 1.0 and adjust in Phase 8. Leave it neutral for now.
- Do not add a sun lamp. HDRI only throughout.

### 3. Terrain material — dark lawn
- Material name: `M_Grass`
- Dark muted green: approx (0.008, 0.020, 0.008) linear. [adjustable per delta]
- Roughness: 0.92 (fully matte). Metallic: 0.
- Apply to terrain mesh and any associated ground objects.

### 4. Building pad material — dark concrete
- Material name: `M_DarkConcrete`
- Near-black charcoal: approx (0.09, 0.09, 0.09). [adjustable per delta]
- Roughness: 1.0 (fully matte). Metallic: 0.
- Apply to: building_pad, building_pad_curtain_wall.

### 5. Driveway and street material
- Same `M_DarkConcrete` as the pad — unified paved system.
- Apply to: driveway, street.

### 6. Render two test stills
- Engine: Cycles GPU, 128 samples, OPTIX denoiser, 1280×720.
- SW compass view (showing ocean side + terrain) saved to `[project]/test_renders/`.
- NE compass view (showing entry + driveway) saved to `[project]/test_renders/`.

---

## Post-Phase Cleanup Checklist

- [ ] All Rhino objects imported with correct names
- [ ] All imported objects have `rotation_mode = 'XYZ'` applied
- [ ] Terrain material is visibly dark green — not pure black, not mid-grey
- [ ] Pad and driveway read as one unified dark concrete system
- [ ] HDRI is loading correctly (no black world, no import errors)
- [ ] Two test stills saved to `[project]/test_renders/`

---

## ▶ REVIEW GATE 4 — Landscaping

Present:
1. SW perspective test render
2. NE perspective test render

Confirm: terrain/pad/driveway read as coherent site composition.
Wait for written approval.

---

## Checkpoint Save

```python
# BlenderMCP
import bpy, datetime
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project]\blender_assets\base_model_checkpoint_{stamp}.blend", copy=True)
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project]\blender_assets\base_model.blend")
```

→ **OBS ACTION:** `obs-stop-record`.
Rename: `04-landscaping-claude.mkv`, `04-landscaping-blender.mkv`. Confirm.

Proceed to `08_entourage_prompt.md`.
