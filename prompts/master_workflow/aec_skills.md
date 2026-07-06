# AEC Skills Library
### Complete Skill Reference for AI-Assisted Architectural Modelling
*Covers: Rhino 3D · Blender · BlenderMCP · RhinoMCP · Hyper3D · OBS · ComfyUI*
*Version 1.0 — May 2026*

---

## How to Use This Document

Each section describes one skill acquired through building the aec_demo_master
hillside residence project. Every skill is written so that you — or another Claude
instance reading this document — can apply it to a **new, different scene file**
without the original project context.

Where numbers are given (radii, Z values, rotations), treat them as examples from
the reference project. Always derive actual values from the current scene by
sampling, querying bounding boxes, or reading existing file properties.

Skills marked **[CRITICAL]** contain failure modes that are silent and hard to debug.
Read these sections carefully before any related task.

---

## Skill 01 — Project Directory Structure

### What it does
Creates a self-contained project folder that holds every asset, render, capture,
script, and prompt associated with one house iteration.

### Structure to create
Mirror `dummy_beach_house_01` exactly:
```
aa_demo_versions/[project_name]/
  blender_assets/    rhino_assets/    renders/    test_renders/
  hdr/               comfy_source/    comfy_output/
  demo_captures/     video_source/    video_edits/
  scripts/           skills/          prompts/
```

### Rules
- `[project_name]`: lowercase, underscores, version suffix (e.g. `hillside_house_01`)
- Never use spaces or special characters
- Each project is completely self-contained — no cross-project file dependencies
- Master prompts in `aec_demo_master/master_prompts/` are never modified per-project;
  project-specific overrides go in `[project]/prompts/` as delta documents
- Claude reads master prompts first, then applies project deltas on top

### Automation
```python
import os
ROOT = r"C:\Users\swags\Documents\aec_demo_master\aa_demo_versions"
subfolders = ["blender_assets","rhino_assets","renders","test_renders",
              "hdr","comfy_source","comfy_output","demo_captures",
              "video_source","video_edits","scripts","skills","prompts"]
for sub in subfolders:
    os.makedirs(os.path.join(ROOT, project_name, sub), exist_ok=True)
```

---

## Skill 02 — OBS Source Verification **[CRITICAL]**

### What it does
Confirms that every OBS Window Capture source is pointing to the correct
application window before any recording begins. After a system restart or
application update, OBS can silently lose window handles and capture the wrong
window or a black frame.

### When to run
At the start of every recording session — not just the first time.
Also re-verify each source immediately before its first use in each phase.

### Procedure
```
1. Call obs-get-input-list → confirm sources CLAUDE, RHINO, BLENDER, COMFYUI exist
2. For each source:
   a. obs-set-current-scene("[SOURCE_NAME]")
   b. obs-get-source-screenshot (returns Base64 PNG)
   c. Evaluate the screenshot — does it show the correct application?
3. Report pass/fail for each source
4. Do not begin recording until all needed sources pass
```

### What a correct screenshot looks like
| Source | Expected content |
|---|---|
| CLAUDE | Claude Desktop chat interface — message bubbles, text input |
| RHINO | Rhinoceros 3D viewport — 3D panes and Rhino UI |
| BLENDER | Blender interface — viewport, outliner, properties |
| COMFYUI | Chrome browser showing ComfyUI node graph |

### If a source is wrong
Report to user: "RHINO source appears incorrect — showing [description].
Please reassign the Window Capture source in OBS to the Rhinoceros 3D window."
Use `obs-open-input-properties` to open OBS's source properties dialog for reassignment.

---

## Skill 03 — OBS Recording State Management

### What it does
Controls OBS scene switching and record start/stop so every phase of work is
captured to the correct application window.

### Scene names (exact strings)
`CLAUDE` · `RHINO` · `BLENDER` · `COMFYUI`

### State machine
```
Start phase → CLAUDE scene → start-record
About to send Rhino commands → switch to RHINO
Rhino complete → switch to CLAUDE
About to send Blender commands → switch to BLENDER
Blender complete → switch to CLAUDE
About to drive ComfyUI → switch to COMFYUI
ComfyUI complete → switch to CLAUDE
Gate approved → stop-record → rename files
```

### Critical rules
- Switch scene BEFORE sending any command to the target application
- Never stop recording during a feedback or revision loop
- Never call scene switch based on assumption — always query `obs-get-current-scene` first
- Each application gets one continuous MKV per phase (use a/b/c suffix for separate sessions)

### File naming convention
`{phase_number:02d}-{phase_topic}-{app}.mkv`
Example: `05-entourage-blender.mkv`

### MCP tools used
`obs-set-current-scene` · `obs-start-record` · `obs-stop-record`
`obs-get-record-status` · `obs-get-current-scene` · `obs-get-source-screenshot`
`obs-set-record-directory` · `obs-get-input-list`

---

## Skill 04 — Rhino NURBS Terrain

### What it does
Builds a smooth, organic hillside terrain from a grid of control curves,
suitable for residential site modelling.

### Approach
1. Create U curves (east–west profiles) on a `uCurves` layer
2. Create V curves (north–south profiles) on a `vCurves` layer
3. Use `NetworkSrf` or `Loft` to generate a smooth NURBS surface
4. Surface should extend well beyond any expected camera frustum

### Key decisions
- Slope direction: high east (street), low west (view) — adjust per site
- Organic undulation: manually shape intermediate control points so the terrain
  is not a perfect plane — add gentle rises and dips across the surface
- Terrain extent: at least 25–30m in all directions beyond the building footprint

### Layer organisation
- `terrain` — the surface object
- `Lot lines` → `uCurves`, `vCurves` — source curves
- Keep source curves visible for potential re-lofting if terrain needs adjustment

### Using terrain for Z-sampling
When placing objects relative to terrain, use BVH ray casting in Blender:
```python
from mathutils.bvhtree import BVHTree
terrain = bpy.data.objects.get("obj_1")
bvh = BVHTree.FromObject(terrain, bpy.context.evaluated_depsgraph_get())
hit, _, _, _ = bvh.ray_cast(
    mathutils.Vector((sx, sy, 20.0)), mathutils.Vector((0, 0, -1)))
terrain_z = hit.z if hit else 0.0
```
Sample at multiple points around any object's perimeter to find the maximum
terrain Z — use this to set the minimum depth for pads, patios, and walls.

---

## Skill 05 — Building Pad and Curtain Wall

### What it does
Creates the raised concrete base that the building sits on, and the retaining
wall that holds it against the sloped terrain.

### Rules
- Pad top surface: slightly above terrain grade at all pad edges
- Pad bottom: must extend BELOW the lowest terrain point within the pad footprint
  by at least 50mm. Sample terrain Z at all four corners and midpoints of each edge.
  Use `min_terrain_z - 0.05` as the pad bottom Z.
- Curtain wall: wraps the pad perimeter, same bottom depth rule
- No gap or floating edge visible between pad/wall and terrain from any angle

### Correct trimming method **[CRITICAL]**
Use Rhino's **Trim** operator — NOT BooleanDifference — to cut the curtain wall
where it meets the terrain:
1. Regenerate terrain from uCurves/vCurves
2. Use terrain surface as the cutting object
3. Select curtain wall as the object to trim
4. Delete the portion below terrain
BooleanDifference fails on open surfaces and leaves artefacts. Trim works cleanly.

### In Blender (if rebuilding procedurally)
```python
# Sample terrain at perimeter
zs = [bvh_sample(x, y) for x, y in perimeter_points]
min_z = min(zs)
cut_z = min_z - 0.05  # 50mm setback below terrain
# Rebuild pad with bottom at cut_z
```

---

## Skill 06 — Building Massing Hierarchy

### What it does
Builds the two-storey building volume as a set of simple solids with correct
proportional and geometric relationships.

### Rules (non-negotiable from project history)
- Upper floor footprint is LARGER than lower floor (lower is recessed east)
- Lower floor is set back creating a veranda on the west/view side
- Gap between L1 top and L2 bottom must be visible (floor slab thickness)
- Floor slab is ONE object per floor — not split by room divisions
- Roof is ONE object — single unified plane, no joints
- Garage is inside the lower floor footprint — not a separate wing

### Z stagger schedule (reference — adapt to new scene)
```
Building pad surface: ~0.0m (grade)
L1 walls bottom: 0.50m (pad clearance)
L1 walls top: 3.55m
Floor slab L1 (at L2 start): 3.55m–3.80m
L2 walls bottom: 3.80m
L2 walls top: 6.95m
Roof bottom (west): varies with slope
```

### Rhino approach
Build each component as a closed solid (`Box` or `ExtrudeSrf`). Name objects
to match Blender material assignment conventions (e.g. `wall_L1`, `roof_slab`,
`floor_L2`).

---

## Skill 07 — Curtain Wall Detailing

### What it does
Adds the glazing grid (mullions, transoms, glass panels) to the building facade.

### Component structure
- Mullions: vertical aluminium extrusions — separate objects from glass
- Transoms: horizontal members — can be same mesh as mullions (combined)
- Glass panels: sit within the grid, slightly inset from mullion face
- Regular rhythm: consistent spacing across entire glazed facade

### Approach in Rhino
1. Divide the facade into a grid using `ArrayLinear` or manual spacing
2. Create mullion profiles as extruded rectangles along each grid line
3. Create glass panels as flat surfaces (or thin solids) within each cell
4. Name: `mullion_*`, `glass_panel_*`, `curtain_wall_*`

---

## Skill 08 — Rhino to Blender Export/Import

### What it does
Transfers all Rhino geometry to Blender while preserving object names and
preparing the scene for materials and rendering.

### Export from Rhino
- Format: OBJ or FBX (OBJ more reliable for geometry; FBX preserves names better)
- Export to `[project]/blender_assets/` folder
- Layer names should match intended material group names

### Import to Blender
- `File → Import → [format]`
- Confirm all expected objects appear in the outliner

### Rotation mode fix **[CRITICAL]**
Immediately after import, set rotation mode to XYZ on ALL imported objects:
```python
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.rotation_mode = 'XYZ'
```
Rhino-exported objects arrive in Blender with `rotation_mode = 'QUATERNION'`.
Setting `rotation_euler` on a Quaternion-mode object is **silently ignored**.
This is the most common cause of objects that appear to be positioned correctly
but don't respond to rotation commands. Always set before any transform work.

---

## Skill 09 — Blender Material Assignment (Principled BSDF)

### What it does
Creates and assigns physically-based materials to all scene objects.

### Pattern: create once, assign by name
```python
def make_mat(name, base_color, roughness, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value  = (*base_color, 1.0)
    b.inputs["Roughness"].default_value   = roughness
    b.inputs["Metallic"].default_value    = metallic
    return m

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
```

### Name-driven assignment
Assign materials based on object name keywords:
```python
for obj in bpy.data.objects:
    n = obj.name.lower()
    if "wall" in n or "balcony" in n:   assign(obj, M_Wall_Ochre)
    elif "roof" in n or "canopy" in n:  assign(obj, M_Roof_Metal)
    elif "glass" in n or "door" in n:   assign(obj, M_Glass)
    # etc.
```

### Glass material (Blender 5.x)
```python
b.inputs["Transmission Weight"].default_value = 0.25
b.inputs["Roughness"].default_value = 0.0
```
Note: parameter name may differ by Blender version. Check available inputs
via `[i.name for i in b.inputs]` if errors occur.

### Master palette reference
See `01_user_prompt.md` Appendix B for full colour values.

---

## Skill 10 — HDRI World Lighting

### What it does
Sets up a single HDRI sky dome as the sole light source, with gamma compression
and directional rotation for correct scene mood.

### Node chain
```
Environment Texture
    ↓ (Vector)
Mapping (Rotation Z = adjustable degrees)
    ↓ (Color)
Gamma (Value = ~4.0)
    ↓ (Color)
Background (Strength = ~1.0–2.0)
    ↓
World Output
```

### Setting up in Python
```python
world = bpy.context.scene.world
world.use_nodes = True
nt = world.node_tree
env  = next(n for n in nt.nodes if n.type == 'TEX_ENVIRONMENT')
mpp  = next(n for n in nt.nodes if n.type == 'MAPPING')
bg   = next(n for n in nt.nodes if n.type == 'BACKGROUND')
gamma = next((n for n in nt.nodes if n.type == 'GAMMA'), None)

env.image = bpy.data.images.load(hdr_path)
mpp.inputs["Rotation"].default_value[2] = math.radians(202.5)  # adjust per scene
bg.inputs["Strength"].default_value = 1.35
if gamma: gamma.inputs["Value"].default_value = 4.0
```

### Rotation convention
- Rotation is applied around the Z axis (vertical)
- Increase to rotate clockwise; decrease for counter-clockwise
- Target: warm zone of HDRI (embedded sun direction) coming from south-west
  for a west-facing ocean view site
- Always verify by reading rendered shadow directions — do not trust code alone

### Sun lamp — permanent removal
Move to `__hidden__` collection. Set `hide_render=True`, `hide_viewport=True`.
Lock all transforms. Exclude collection from all view layers. Document in project notes.

### Reducing brightness
`bg.inputs["Strength"].default_value *= factor` (e.g. × 0.4 for −60%)

---

## Skill 11 — Hyper3D Rodin Model Generation **[CRITICAL]**

### What it does
Generates a 3D mesh from a text description using the Hyper3D Rodin AI system,
imports it into Blender, and scales it to real-world dimensions.

### Workflow
```python
# 1. Generate
result = blender.generate_hyper3d_model_via_text(
    text_prompt="Adirondack wooden garden chair...",
    bbox_condition=[0.8, 0.9, 1.0])   # approximate W×D×H in metres
task_uuid = result["task_uuid"]
subscription_key = result["subscription_key"]

# 2. Poll until complete
while True:
    status = blender.poll_rodin_job_status(subscription_key=subscription_key)
    if all(s == "Done" for s in status["status_list"]): break
    time.sleep(5)

# 3. Import
blender.import_generated_asset(name="my_object", task_uuid=task_uuid)
```

### Post-import REQUIRED steps (every time, no exceptions)
```python
obj = bpy.data.objects.get("my_object")

# Step 1: FIX ROTATION MODE IMMEDIATELY
obj.rotation_mode = 'XYZ'  # CRITICAL — Hyper3D imports use QUATERNION

# Step 2: Scale to real-world dimensions using bounding box
bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
current_h = max(v.z for v in bb) - min(v.z for v in bb)
target_h  = 1.0  # metres — adjust to real object dimensions
scale_z   = target_h / current_h
# Apply uniform or non-uniform scale as needed
obj.scale = (scale_xy, scale_xy, scale_z)

# Step 3: Apply transforms
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(scale=True, rotation=True)
```

### Why rotation_mode matters **[CRITICAL]**
Hyper3D (and all external 3D imports) arrive with `rotation_mode = 'QUATERNION'`.
In Quaternion mode, `obj.rotation_euler = (x, y, z)` stores the values but has
ZERO effect on the actual transform. The object will not move or rotate despite
the code appearing to run without errors. The only fix is to set
`obj.rotation_mode = 'XYZ'` first — every time, with no exceptions.

---

## Skill 12 — Radial Chair Arrangement **[CRITICAL]**

### What it does
Places seating in a circle around a central element (fire pit), with each chair
facing inward (backs outward, seats toward centre), like tick marks on a clock face.

### Chair placement formula
```python
import math, random

CENTER_X, CENTER_Y = -4.0, 0.0   # patio centre — adapt to new scene
CHAIR_RADIUS = 1.85               # metres from centre — adapt to new scene
N_CHAIRS = 5
PHASE_OFFSET = 20                 # degrees — prevents chair facing camera directly

for i in range(N_CHAIRS):
    base_angle = math.radians(i * (360/N_CHAIRS) + PHASE_OFFSET)

    # Organic variation
    pos_jitter    = math.radians(random.uniform(-5, 5))
    radius_jitter = random.uniform(-0.08, 0.08)
    rot_jitter    = math.radians(random.uniform(-8, 8))  # ±8° max for natural feel

    angle  = base_angle + pos_jitter
    radius = CHAIR_RADIUS + radius_jitter
    cx = CENTER_X + radius * math.cos(angle)
    cy = CENTER_Y + radius * math.sin(angle)

    # Z: origin must be above patio surface by (origin_to_bottom) offset
    bb    = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    z_off = obj.location.z - min(v.z for v in bb)   # origin above bottom
    cz    = PATIO_SURFACE_Z + z_off

    obj.location = (cx, cy, cz)

    # ROTATION — seat faces inward (backs outward)
    # theta = angle from centre TO chair
    theta = math.atan2(cy - CENTER_Y, cx - CENTER_X)
    # theta + pi/2 + pi: local +Y faces inward; +pi flips seat toward centre
    obj.rotation_mode = 'XYZ'   # MUST set before rotation_euler
    obj.rotation_euler = (0.0, 0.0, theta + math.pi/2 + math.pi + rot_jitter)
```

### Verification step
After placement, print the world-space direction of local +Y for each chair
and confirm it points toward the centre:
```python
rot_z = obj.rotation_euler.z
local_plus_y = (-math.sin(rot_z), math.cos(rot_z))
inward       = (CENTER_X - cx, CENTER_Y - cy)
inward_norm  = [v / (inward[0]**2 + inward[1]**2)**0.5 for v in inward]
# local_plus_y should approximately equal inward_norm
```

### Common failure modes
1. **rotation_mode = 'QUATERNION'** → rotation_euler has no effect → all chairs face same direction
2. **scene.frame_set() in loop** → all chairs bake to same position (keyframe bug — see Skill 15)
3. **Jitter too large** (>15°) → chairs look unnatural and disorganised
4. **Z position wrong** → chairs float above or sink into patio surface

---

## Skill 13 — Patio Disc with Smooth Perimeter

### What it does
Creates a circular raised patio disc that sits on sloped terrain, with smooth
shading on the curved side and flat shading on top/bottom, and sharp edge
transitions at the top and bottom rims.

### Creation
```python
bpy.ops.mesh.primitive_cylinder_add(
    radius=PATIO_RADIUS,   # 30% larger than chair circle radius
    depth=(PATIO_SURFACE_Z - PATIO_BOTTOM_Z),
    vertices=96,           # enough for smooth circle
    location=(CENTER_X, CENTER_Y, (PATIO_SURFACE_Z + PATIO_BOTTOM_Z) / 2))
```

### Z placement
- `PATIO_SURFACE_Z` = max terrain Z at perimeter + desired clearance (0.1m minimum)
- `PATIO_BOTTOM_Z` = deep enough to penetrate terrain fully (sample terrain min first)
- Sample terrain at 24–36 evenly spaced points around the patio perimeter radius

### Smooth normals — correct approach **[CRITICAL]**
Do NOT use `obj.shade_smooth()` alone — it bleeds into the top/bottom flat faces.
Do NOT use Workbench normal shading — produces incorrect results.

Correct approach:
```python
import bpy, bmesh

obj = bpy.data.objects.get("patio_disc")
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)

all_z   = [v.co.z for v in bm.verts]
top_z   = max(all_z); bot_z = min(all_z); TOL = 0.01

for face in bm.faces: face.smooth = True  # shade all smooth first

for edge in bm.edges:
    v0z = edge.verts[0].co.z; v1z = edge.verts[1].co.z
    on_top = abs(v0z - top_z) < TOL and abs(v1z - top_z) < TOL
    on_bot = abs(v0z - bot_z) < TOL and abs(v1z - bot_z) < TOL
    edge.smooth = not (on_top or on_bot)  # False = sharp

bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

# Edge Split modifier to honour sharp edges
es = obj.modifiers.new("EdgeSplit","EDGE_SPLIT")
es.use_edge_angle = False
es.use_edge_sharp  = True
```

---

## Skill 14 — Fire Geometry

### What it does
Creates a realistic-looking fire inside a fire pit bowl using emission-shaded
geometry objects: coal bed, flame cones, bright core, and a practical point light.

### Component overview
| Object | Shape | Emission colour | Strength |
|---|---|---|---|
| `fire_coals` | Flat cylinder at pit bottom | Deep orange-red (1.0, 0.18, 0.02) | 12 |
| `fire_flame_0–6` | Cones, 7 total, varying | Yellow-orange spectrum | 15–45 |
| `fire_core` | Small sphere, centre | Near-white (1.0, 1.0, 0.85) | 80 |
| `FireLight` | Point light above pit | Warm orange (1.0, 0.45, 0.10) | 600–800 |

### Flame sizing rule
`flame_height = (PIT_TOP_Z - 0.10 - PIT_BOT_Z) × height_fraction`
Flames must not breach the pit rim — maintain 0.10m clearance below the rim.

### Emission material pattern
```python
def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    emit = nt.nodes.new("ShaderNodeEmission")
    out  = nt.nodes.new("ShaderNodeOutputMaterial")
    emit.inputs["Color"].default_value    = (*color, 1.0)
    emit.inputs["Strength"].default_value = strength
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m
```

### Variation rules
- Each of 7 flames: different height fraction (0.48–1.0), different base radius
  (0.028–0.055m), different tilt (4–22°), different azimuth, different colour
- Randomise positions slightly (±0.04m from centre) for organic feel
- No two flames identical

---

## Skill 15 — Camera Animation with Smoothstep Easing

### What it does
Animates a camera along an arc around a scene element, with ease-in and ease-out
so the motion feels cinematic rather than mechanical.

### Smoothstep formula
```python
def smoothstep(t):
    """Hermite ease-in/ease-out. t in [0,1], output in [0,1].
    Very slow at t=0 and t=1, full speed at t=0.5."""
    return t * t * (3.0 - 2.0 * t)
```

### Keyframe insertion — CRITICAL RULES **[CRITICAL]**

**Rule 1:** Always set `cam_obj.rotation_mode = 'XYZ'` before any keyframe work.

**Rule 2:** Set the property value THEN call keyframe_insert with explicit frame.
Do NOT call `scene.frame_set()` inside the loop.

```python
# CORRECT
for frame in range(N_FRAMES + 1):
    t_smooth = smoothstep(frame / N_FRAMES)
    az = math.radians(START_AZ + t_smooth * (END_AZ - START_AZ))
    cx = CENTER_X + CAM_R * math.sin(az)
    cy = CENTER_Y + CAM_R * math.cos(az)
    cam_obj.location = (cx, cy, CAM_Z)
    direction = (LOOK_AT - mathutils.Vector((cx, cy, CAM_Z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    # keyframe_insert with explicit frame= parameter — NO scene.frame_set() here
    cam_obj.keyframe_insert(data_path="location",       frame=frame)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
```

**Why `scene.frame_set()` breaks animation:**
`scene.frame_set(N)` evaluates the animation at frame N and OVERRIDES
`cam_obj.location` with the animated value at that frame. If you call it
inside the loop, it reverses your manually set location — all frames bake
to the position of the last `frame_set()` call. The symptom is that the
"camera moved" check shows identical positions at frame 0 and frame 192.

**Rule 3:** Insert a keyframe at EVERY frame (not just start/end).
Sparse keyframes rely on Blender's spline interpolation, which can be
incorrect for objects with Quaternion rotation mode. Per-frame insertion
guarantees the motion curve regardless of rotation mode.

### Verification
```python
# After insertion — confirm motion exists
scene.frame_set(0)
pos0 = tuple(cam_obj.location)
scene.frame_set(N_FRAMES)
posN = tuple(cam_obj.location)
assert pos0 != posN, "Camera did not animate — check for frame_set() in loop"
```

### Typical patio sweep parameters (adapt to new scene)
- Centre: patio_group location
- Radius: 20–25m (enough to see patio + house together)
- Height: 5–7m (above standing eye level)
- Arc: 100° through due West for west-facing house
- Duration: 8 seconds = 192 frames at 24fps
- Look target: midpoint between patio and building, elevated ~1.5m

---

## Skill 16 — True Depth Map Extraction **[CRITICAL]**

### What it does
Renders per-frame depth maps as 16-bit greyscale PNG files, where near objects
are white and far/background is black, with per-frame auto-normalisation for
maximum contrast regardless of camera distance.

### Why standard Blender depth methods fail
- Workbench depth mode: includes AO, cavity, and shadow effects — NOT a true depth map
- Z pass with fixed range: if range is wider than the scene, everything maps to a
  narrow mid-grey band with no differentiation
- `np.flipud()` on Blender EXRs: OpenEXR Python returns already top-down — flipud inverts the image

### Correct approach: emission material + raw EXR + per-frame normalisation

**Step 1 — Create raw depth emission material:**
```python
mat = bpy.data.materials.new("_DepthRaw")
mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
cam  = nt.nodes.new("ShaderNodeCameraData")
emit = nt.nodes.new("ShaderNodeEmission")
out  = nt.nodes.new("ShaderNodeOutputMaterial")
# View Distance = true spherical distance from camera to surface
nt.links.new(cam.outputs["View Distance"], emit.inputs["Color"])
emit.inputs["Strength"].default_value = 1.0
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
```

**Step 2 — Assign to all objects and set render settings:**
```python
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.rotation_mode = 'XYZ'      # always
        obj.data.materials.clear()
        obj.data.materials.append(depth_mat)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.cycles.max_bounces = 0          # zero ALL bounce types
scene.cycles.diffuse_bounces = 0
scene.cycles.glossy_bounces  = 0
scene.cycles.transmission_bounces = 0
scene.cycles.volume_bounces  = 0
scene.cycles.use_denoising   = False

# Kill world completely
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs["Strength"].default_value = 0.0
scene.render.film_transparent = True  # transparent BG = black in PNG

scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.exr_codec   = 'NONE'  # uncompressed for readability
scene.render.image_settings.color_depth = '32'
```

**Step 3 — Per-frame normalisation (subprocess script):**
```python
# normalise_depth.py — run via subprocess from Blender
import sys, os
sys.path.insert(0, r"PATH_TO_BLENDER\python\lib\site-packages")
import OpenEXR, numpy as np
from PIL import Image as PILImage

for fname in sorted(f for f in os.listdir(TEMP_DIR) if f.endswith('.exr')):
    f   = OpenEXR.File(os.path.join(TEMP_DIR, fname))
    px  = list(f.channels().values())[0].pixels    # (H, W, 3) float32
    raw = px[:, :, 0].astype(np.float32)
    # DO NOT apply np.flipud() — EXR is already top-down via OpenEXR Python

    valid = raw[raw > 0.01]  # exclude transparent background
    if len(valid) == 0:
        norm = np.zeros_like(raw, dtype=np.uint16)
    else:
        d_min, d_max = float(valid.min()), float(valid.max())
        n = np.clip(1.0 - (raw - d_min) / max(d_max - d_min, 0.001), 0.0, 1.0)
        n[raw <= 0.01] = 0.0  # background = black
        norm = (n * 65535).astype(np.uint16)

    img = PILImage.fromarray(norm.astype(np.int32), mode='I')
    img.save(os.path.join(OUT_DIR, f"depth_{frame_num}.png"))
    # NOTE: mode='I' not 'I;16' — the I;16 mode is deprecated in Pillow 13+
```

### Required Python libraries (Blender's pip)
`openexr` and `Pillow` — install via:
```
sys.executable -m pip install openexr Pillow
```
Import via subprocess script with `sys.path.insert(0, blender_site_packages)`.
These cannot be imported directly in `bpy` context — always use subprocess.

---

## Skill 17 — Segmentation Mask Rendering

### What it does
Renders per-frame semantic segmentation masks — flat solid-colour images where
each colour represents one object category, with no lighting effects whatsoever.

### Standard palette (do not change — breaks dataset compatibility)
| Category | RGB |
|---|---|
| Walls / balconies / posts | 204, 30, 30 |
| Glass / windows / doors | 25, 204, 229 |
| Roof / canopy | 25, 25, 217 |
| Floor slabs | 229, 140, 25 |
| Mullions / frames | 153, 153, 153 |
| Terrain / grass | 20, 115, 20 |
| Steps / landing | 89, 51, 20 |
| Driveway / street | 51, 51, 51 |
| Building pad / curtain wall | 102, 102, 102 |

### Flat emission material pattern
```python
def seg_mat(name, r, g, b):
    m = bpy.data.materials.new(f"_Seg_{name}")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    emit = nt.nodes.new("ShaderNodeEmission")
    out  = nt.nodes.new("ShaderNodeOutputMaterial")
    emit.inputs["Color"].default_value    = (r/255, g/255, b/255, 1.0)
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m
```

### Render settings (same as depth maps)
- Cycles GPU, 1 sample, ALL bounces = 0 (max_bounces, diffuse, glossy,
  transmission, volume — must ALL be zero)
- World strength = 0, `film_transparent = True`
- PNG RGB 8-bit output

### Why all bounces must be zero
Even one diffuse bounce allows ambient light from emission objects to contaminate
nearby surfaces, creating gradient effects and colour bleeding. Segmentation masks
must be flat — pure colour, zero shading of any kind.

---

## Skill 18 — Versioned Render Output

### What it does
Organises render output into timestamped folders so no render is ever overwritten
and any version can be retrieved.

### Pattern
```python
import datetime
stamp   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = os.path.join(PROJECT_ROOT, "renders", sequence_name, f"v_{stamp}")
PNG_DIR = os.path.join(OUT_DIR, "png")
EXR_DIR = os.path.join(OUT_DIR, "exr")
os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(EXR_DIR, exist_ok=True)
scene.render.filepath = os.path.join(PNG_DIR, "frame_")
```

### MP4 encoding
```python
import subprocess
ffmpeg_path = r"...\ffmpeg.exe"   # adapt to system
cmd = [ffmpeg_path, "-y", "-framerate", "24", "-start_number", "0",
       "-i", os.path.join(PNG_DIR, "frame_%04d.png"),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
       os.path.join(OUT_DIR, "output.mp4")]
subprocess.run(cmd, timeout=300)
```

### Checkpoint saves at every gate
```python
# Blender
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
bpy.ops.wm.save_as_mainfile(
    filepath=os.path.join(PROJECT_ROOT, "blender_assets",
                          f"base_model_checkpoint_{stamp}.blend"), copy=True)
bpy.ops.wm.save_as_mainfile(
    filepath=os.path.join(PROJECT_ROOT, "blender_assets", "base_model.blend"))
```
```csharp
// Rhino (RhinoMCP)
string stamp = DateTime.Now.ToString("yyyyMMdd_HHmm");
doc.WriteFile($@"{projectRoot}\rhino_assets\base_model_checkpoint_{stamp}.3dm",
    new Rhino.FileIO.FileWriteOptions());
```

---

## Skill 19 — BVH Terrain Sampling

### What it does
Accurately finds the terrain surface Z at any XY coordinate by ray-casting
downward from above. Essential for correct placement of pads, patios, chairs,
and any object that must sit on or below the terrain.

### Usage pattern
```python
from mathutils.bvhtree import BVHTree
import mathutils, bpy

terrain = bpy.data.objects.get("obj_1")   # adapt name to scene
bvh = BVHTree.FromObject(terrain, bpy.context.evaluated_depsgraph_get())

def sample_terrain_z(x, y, above=20.0):
    hit, _, _, _ = bvh.ray_cast(
        mathutils.Vector((x, y, above)),
        mathutils.Vector((0, 0, -1)))
    return hit.z if hit else None

# Sample around a perimeter
import math
def perimeter_max_z(center_x, center_y, radius, n_samples=24):
    zs = []
    for i in range(n_samples):
        a = math.radians(i * 360 / n_samples)
        z = sample_terrain_z(center_x + radius*math.cos(a),
                             center_y + radius*math.sin(a))
        if z is not None: zs.append(z)
    return max(zs) if zs else 0.0
```

---

## Skill 20 — Blender Scene Saving and Checkpoint Protocol

### Rules
1. Save a checkpoint (copy=True) AND the working file at every gate approval
2. Name checkpoints with timestamp: `base_model_checkpoint_YYYYMMDD_HHMM.blend`
3. Never overwrite the working `base_model.blend` without first saving a checkpoint
4. Store all checkpoints in `[project]/blender_assets/` — not in the project root

### Checking current file path
```python
print(bpy.data.filepath)  # confirms which file is currently open
```

### Loading a checkpoint
```python
bpy.ops.wm.open_mainfile(filepath=checkpoint_path)
```

---

## Skill 21 — ComfyUI via Claude in Chrome MCP

### What it does
Drives a ComfyUI workflow (AI image processing) running in Google Chrome,
using the Claude in Chrome MCP extension for programmatic control.

### Why Chrome specifically
Claude in Chrome MCP provides: navigate to URLs, read DOM, inject JavaScript,
monitor workflow completion — without user interaction. No other browser has this.

### Setup requirements
- Google Chrome (only Chrome window open during ComfyUI session)
- ComfyUI running locally or remotely, accessible via browser URL
- Claude in Chrome MCP extension installed and connected
- ComfyUI workflow JSON in `[project]/comfy_source/`

### General approach
1. Navigate Chrome to ComfyUI URL
2. Load workflow JSON via Claude in Chrome DOM manipulation
3. Set input nodes (e.g. image folder path, resolution)
4. Trigger queue/run
5. Monitor progress via DOM — look for completion indicators
6. Read output file paths from DOM or filesystem

### OBS setup for ComfyUI
Scene name: `COMFYUI` → Window Capture → Google Chrome
Verify via `obs-get-source-screenshot` before recording.
The ComfyUI node graph updating and progress indicators are compelling footage.

---

## Known Failure Modes Quick Reference

| Symptom | Root cause | Fix |
|---|---|---|
| Rotation command has no effect | rotation_mode = QUATERNION | Set rotation_mode = 'XYZ' first |
| All keyframes bake to same position | scene.frame_set() inside keyframe loop | Remove frame_set(); use keyframe_insert(frame=N) |
| Depth maps are flat mid-grey | Range too wide for scene depth | Per-frame auto-normalise from actual min/max |
| Depth maps are upside-down | Applied np.flipud() unnecessarily | Remove flipud — OpenEXR Python is already top-down |
| Segmentation has shadows/gradients | Not all bounces zeroed | Set ALL bounce types to 0, world strength to 0 |
| Pad floats above terrain | Pad bottom not deep enough | Sample terrain, set bottom 50mm below minimum |
| Curtain wall gap at terrain | Wrong trim method | Use Rhino Trim, not BooleanDifference |
| Patio perimeter faceted | Smooth shading bleeds to top face | Mark ring edges sharp + Edge Split modifier |
| OBS captures wrong window | Source lost after restart | Run source verification (obs-get-source-screenshot) |
| PIL 16-bit PNG fails | I;16 mode deprecated | Use fromarray(arr.astype(np.int32), mode='I') |
| OPEN_EXR_MULTILAYER not found | Not available in render settings | Use compositor File Output node for multilayer |
| Chair faces outward | Wrong rotation formula sign | Use theta + pi/2 + pi, not theta - pi/2 |
