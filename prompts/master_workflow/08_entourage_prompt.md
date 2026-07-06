# Phase 5 — Entourage
### Entourage Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 5, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Populate the site with the outdoor living zone: circular patio, fire pit coffee
table, fire geometry, and seating. All entourage goes in Blender. AI-generated
objects (chairs, table) come from Hyper3D Rodin.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 4
- Delta notes — check for: patio location, seating type/count, fire pit style

## Outputs

- `[project]/blender_assets/base_model.blend` — patio group fully built
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — four patio compass-point stills (NW, NE, SE, SW)

---

## Pre-Phase Audit Checklist

- [ ] Phase 4 gate approved
- [ ] Blender scene is open with site materials applied
- [ ] BlenderMCP and Hyper3D connections confirmed
- [ ] Terrain BVH available for Z-sampling (terrain object named `obj_1`)

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.
Confirm: "Recording started — `05-entourage-claude`."

→ **OBS ACTION:** Before first Blender command, `obs-set-current-scene("BLENDER")`.
Stay on BLENDER for ALL Blender work including all revision rounds.
The Hyper3D import, chair rotation debugging, and fire geometry are all
key footage — do not switch away during any of this work.

→ **OBS ACTION:** Entourage complete, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. Sample terrain for patio Z placement
- Use BVH ray casting to sample terrain Z at the patio centre and at multiple
  points around the intended patio perimeter radius.
- Patio surface Z = max terrain Z at perimeter + desired clearance above grade.
  [adjustable — minimum 0.1m above terrain per delta notes]
- Store the patio surface Z and perimeter terrain max Z for reference.

### 2. Build patio disc
- Cylinder: radius = chair circle radius × 1.3 minimum. [adjustable]
- Top at patio surface Z; bottom extends well below terrain (at least −1.5m or lower).
- Material: `M_Patio_Stone` — dark charcoal stone, roughness 0.88. [adjustable]
- Smooth normals on the curved side only. Flat normals on top and bottom.
  Use Edge Split modifier with `use_edge_sharp=True` on the top and bottom ring edges.
  Mark ring edges as sharp in bmesh; do not use Auto Smooth alone.
- 96 vertices for a smooth circle.

### 3. Generate Adirondack chair via Hyper3D
- Text prompt: "Adirondack wooden garden chair, classic slatted back and wide
  armrests, outdoor furniture". Bounding box: approx 0.8×0.9×1.0m. [adjustable]
- Poll for completion before importing.
- After import: IMMEDIATELY call `obj.rotation_mode = 'XYZ'` before any other
  transform. Imported Hyper3D objects use Quaternion mode — setting rotation_euler
  on a Quaternion-mode object is silently ignored. This is the single most common
  failure mode in this phase.
- Scale to real-world size using bounding box measurement.
- Apply scale transform after sizing.

### 4. Generate fire pit coffee table via Hyper3D (optional)
- Alternatively: build procedurally as a cylinder with boolean pit recess.
  Procedural is more reliable for getting the right shape.
- If procedural: radius ~0.75m, height ~0.42m, pit depth ~0.30m, pit radius ~0.28m.
  Boolean the pit as a cylinder subtracted from the top.
- Material: same `M_Patio_Stone` as patio disc.

### 5. Duplicate chairs and arrange radially
- Count: 5 chairs (odd number avoids axis symmetry). [adjustable per delta]
- Radius from patio centre: approx 1.85m. [adjustable — should feel cozy around fire]
- Base angle spacing: 360° ÷ chair count, offset ~15–20° so no chair faces camera directly.
- For each chair: compute `theta = atan2(cy − CENTER_Y, cx − CENTER_X)`.
  Set `rotation_euler = (0, 0, theta + π/2 + π + jitter)`.
  This makes the seat face inward (toward fire), back faces outward.
  Verify by printing world-space +Y axis direction and confirming it points toward centre.
- Organic variation: ±5° arc position jitter, ±0.08m radius jitter, ±8° rotation jitter.
- All chairs: Z origin = patio surface Z + (chair bounding box: origin to bottom).
  Measure this offset from the actual bounding box — do not assume.
- Set `rotation_mode = 'XYZ'` on every chair before applying any rotation.

### 6. Build fire geometry
- Coal bed: flat cylinder at pit bottom, dark orange-red emission (strength ~12).
- Flame cones (7): varying heights (proportional to available pit depth − 0.1m
  clearance from rim), varying widths, varying tilts. Each a different orange/yellow
  emission strength and colour. No two identical.
- Core sphere: small, very bright yellow-white emission (strength ~80).
- Point light: warm orange, positioned just above pit rim, energy ~600–800.
- Fire top must not breach the pit rim — leave ~0.1m clearance below rim.

### 7. Parent to PATIO_GROUP
- Create a Plain Axes empty at the patio centre, named `PATIO_GROUP`.
- Parent all patio objects (disc, table, fire objects, chairs, point light) to it.
- Confirm parenting preserves world transforms.

### 8. Render four patio compass test stills
- Camera orbits patio centre at ~12m radius, 4.5m height. 35mm lens.
- NW, NE, SE, SW directions. 128 samples, 1280×720.
- Save to `[project]/test_renders/`.

---

## Post-Phase Cleanup Checklist

- [ ] All chairs face inward — verified with world-space +Y axis print
- [ ] Chair bottoms sit exactly on patio surface — no floating, no sinking
- [ ] Patio disc top is above terrain at all perimeter points
- [ ] Patio disc bottom is below terrain (penetrating cleanly)
- [ ] Curved side of patio disc is smooth — no faceting visible in test render
- [ ] Fire geometry is fully inside the pit bowl — no flames breaching rim
- [ ] PATIO_GROUP empty contains all patio objects
- [ ] Test renders show fire glowing in pit
- [ ] `rotation_mode = 'XYZ'` confirmed on all chairs

---

## ▶ REVIEW GATE 5 — Entourage

Present: four patio compass stills (NW, NE, SE, SW).
Confirm: chair orientation (backs out, seats in), fire visibility, patio scale,
chair count, patio material.
Wait for written approval.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `05-entourage-claude.mkv`, `05-entourage-blender.mkv`. Confirm.

Proceed to `09_materials_prompt.md`.
