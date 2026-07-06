# Architectural Modelling Prompt — Contemporary Hillside Residence
### Ocean View / Outdoor Living Edition
*Authored for use with Claude + Blender + Rhino via MCP*
*Version 1.0 — May 2026*

---

## How to Use This Document

This prompt is a complete brief for modelling a contemporary hillside house from scratch.
It is written in plain architectural language so you can hand it to Claude and receive a
finished, renderable Blender scene with no further explanation.

**It is deliberately general.** Any dimension, material, or design decision marked with
`[adjustable]` can be changed to model a different house. Replace those values with your
own and the workflow adapts automatically.

**Approval gates** are marked with a ▶ REVIEW symbol. At each gate, stop, present renders
or screenshots to the client, and wait for written sign-off before continuing. Never
proceed past a gate without approval.

**Workflow tools assumed:**
- Rhino 3D (geometry source of truth)
- Blender (rendering and animation)
- BlenderMCP and RhinoMCP (Claude bridge)
- Hyper3D Rodin (AI-generated entourage objects)
- OBS (screen recording of each phase)

Start OBS recording at the beginning of each phase and stop at the approval gate.

---

## Phase 0 — Project Setup

Before any geometry is created, establish the file and coordinate structure.

### Scene Units and Orientation
- All dimensions in **metres**. One Blender/Rhino unit equals one metre.
- **North** is the positive Y axis. East is positive X. Up is positive Z.
- The lot sits on a **hillside** that slopes downward from east (street side) to west
  (ocean/view side). [adjustable — reverse slope for east-facing sites]
- The **street** runs along the eastern edge of the lot.
- The primary view orientation is **westward** — toward the ocean or landscape.
  [adjustable — change to any cardinal direction]

### File Structure
Every project lives in its own self-contained folder under `aa_demo_versions/`.
The folder structure mirrors the reference project `dummy_beach_house_01` exactly.
See `03_config_prompt.md` for the full setup procedure and directory tree.

```
C:\Users\swags\Documents\aec_demo_master\aa_demo_versions\[project_name]\
  blender_assets\     rhino_assets\     renders\     test_renders\
  hdr\     comfy_source\     comfy_output\     demo_captures\
  video_source\     video_edits\     scripts\     skills\     prompts\
```

Master prompts in `aec_demo_master/master_prompts/` are never modified per-project.
Project-specific changes go in `[project_name]/prompts/` as delta documents.
Claude reads master prompts first and applies project deltas on top.

Save a timestamped checkpoint for every modified scene file at each gate approval.

### Coordinate Origin
Place the world origin at a convenient point near the centre of the building footprint,
at finished ground-floor level. All terrain, building, and site elements are positioned
relative to this origin.

---

## Phase 1 — Site Preparation

### Goal
Establish a realistic, undulating hillside terrain that the building will sit on and
that reads convincingly in renders.

### Terrain Shape
- The terrain should feel like a **natural hillside** — gently sloping overall from
  east to west, with subtle organic undulation across its surface. [adjustable]
- It should be wide enough to extend well beyond the building footprint in every
  direction, so no render angle exposes a terrain edge.
- The high point of the terrain (street level, east side) sits noticeably above the
  low point (west/ocean side). The slope should feel comfortable for residential
  construction — neither cliff nor flat. [adjustable]
- Model the terrain as a **Rhino NURBS surface** driven by a grid of U and V control
  curves. This allows precise, smooth editing of the slope profile at any time.
  Export the surface to Blender as a smooth mesh.

### Lot Lines
- Define the lot boundary clearly in Rhino on a dedicated layer.
- The lot is roughly rectangular, oriented with its long axis running east–west.
  [adjustable — any lot shape]
- The street frontage is the eastern short edge.

### Building Pad
- The building sits on a **raised pad** — a thick slab of dark concrete that projects
  slightly above finished grade on all sides, giving the house a solid base and
  preventing the walls from appearing to float above or sink into the terrain.
- A **curtain wall** (a short retaining wall) wraps the perimeter of the pad wherever
  it meets the sloping terrain. It is the same material as the pad.
- Both the pad and its curtain wall must penetrate cleanly **below** the terrain surface
  with no visible gap or floating edge. Sample the terrain surface at multiple points
  around the pad perimeter to find the deepest terrain point, then extend the pad bottom
  well below it. [adjustable — pad thickness and setback]

### ▶ REVIEW GATE 1 — Site
Present a top-down viewport screenshot and a perspective view of the terrain.
Confirm slope direction, lot proportions, and terrain organic feel before proceeding.

---

## Phase 2 — Massing

### Goal
Establish the pure building volume — walls, floors, and roof as simple solids with
no surface detail. No windows, no doors, no trim.

### Overall Character
This is a **contemporary two-storey flat-roof residence** with a strong horizontal
emphasis. The architecture prioritises the western view through large expanses of glass,
and creates covered outdoor space through cantilevered overhangs. [adjustable]

### Lower Floor
- The lower floor is a solid rectangular volume sitting directly on the building pad.
  [adjustable — can be L-shaped, courtyard plan, etc.]
- Its footprint is **smaller** than the upper floor — it is set back toward the east,
  leaving a covered veranda on the west/ocean side beneath the upper-floor overhang.
  [adjustable — setback dimension and which sides]
- Ceiling height is comfortable residential — roughly three to three and a half metres
  clear. [adjustable]
- The lower floor contains living areas (not modelled internally at this stage).
- The **garage** is integrated into the lower-floor footprint on the street/east side,
  so the building mass reads as one unified volume from all directions. [adjustable]

### Upper Floor
- The upper floor sits directly on top of the lower floor walls, but its footprint
  extends **further west** than the lower floor, creating the cantilevered overhang
  that shelters the veranda below. [adjustable — overhang depth]
- Upper floor ceiling height matches the lower floor. [adjustable]
- A **gap** (the floor slab thickness) separates the top of the lower-floor walls from
  the bottom of the upper-floor walls. This articulation prevents the two storeys from
  reading as a single undifferentiated block.

### Roof
- The roof is a **large continuous shed (mono-pitch) surface** that slopes gently from
  east (high side, street) down toward the west (low side, ocean view). [adjustable —
  can be flat, butterfly, hip, or gabled]
- The roof overhangs the building perimeter on all sides, floating visually above the
  wall plane. This overhang provides sun shading for the glazing below.
- The roof reads as a single unified plane, not broken into separate sections.

### Floor Slabs
- Each floor slab is one solid object spanning the full footprint of that floor.
- Slabs are thick enough to read clearly as a horizontal datum in elevation.
- Do not model the interior floor structure — just the slab as a simple solid.

### ▶ REVIEW GATE 2 — Massing
Present four compass-point renders (N, E, S, W) in solid viewport shading.
Confirm the overall proportions, overhang depth, roof slope, and the relationship
between upper and lower volumes before adding any detail.

---

## Phase 3 — Detailing

### Goal
Add all architectural surface elements: glazing, frames, balconies, entry sequence.
No materials assigned yet — everything is neutral grey at this stage.

### Curtain Wall Glazing (Upper Floor)
- The upper floor west face is **fully glazed** — a curtain wall of large glass panels
  in a dark aluminium grid. [adjustable — can be partial glazing or punched openings]
- The curtain wall grid consists of vertical mullions (tall, narrow aluminium extrusions)
  and horizontal transoms, creating a regular rhythm across the facade.
- Glass panels sit flush within the grid. The glass is slightly inset from the outer
  face of the mullions.
- The curtain wall extends across the primary view facade and wraps partially around
  the side facades. [adjustable — extent of wrap]

### Balcony (Upper Floor)
- A continuous **cantilevered balcony** runs along the west/ocean face of the upper
  floor, projecting beyond the curtain wall. [adjustable — depth and which sides]
- The balcony slab is a clean flat plate, same material as the floor slabs.
- A solid **parapet** or railing sits on the outer edge of the balcony. At this stage
  it is a plain solid; material is added in Phase 6. [adjustable — can be glass railing,
  cable rail, or steel tube]

### Lower Floor Veranda
- The covered space beneath the upper-floor overhang on the west side functions as a
  **semi-outdoor veranda**.
- The veranda floor is the lower-floor slab exposed to the exterior.
- **Structural posts** support the upper floor at the outer west edge where the
  cantilever is greatest. They are the same material as the walls. [adjustable —
  can be steel columns or eliminated if structure permits]

### Entry Sequence (East Face)
- The entry is on the **east/street face** of the building. [adjustable]
- A **entry canopy** — a small secondary shed roof — projects over the front door,
  providing weather protection. The canopy slopes in the same direction as the main
  roof (east high, west low) for consistency. [adjustable]
- **Entry steps** lead from street/driveway level up to the front door, with a flat
  landing at the top. Steps and landing are dark concrete. [adjustable — step count]
- The **front door** is a solid panel door, same material as the garage doors.
  [adjustable — door style]

### Garage Doors
- The garage occupies the southern portion of the east face. [adjustable — north/south]
- **Garage doors** are large flat panel doors, flush with the wall face.
  [adjustable — swing-up, sliding, or roll-up style]

### Driveway
- A **driveway** connects the street to the garage, following the terrain slope.
  [adjustable — width and material]
- The driveway material matches the steps — dark exposed concrete or similar.

### ▶ REVIEW GATE 3 — Detailing
Present compass-point renders from all four sides plus a close-up of the entry.
Confirm glazing rhythm, balcony proportions, entry canopy slope, and garage placement
before moving to landscaping.

---

## Phase 4 — Landscaping

### Goal
Give the site context: lawn, planting zones, driveway surface, and street edge.
No entourage objects yet.

### Terrain Material
- The terrain reads as **lawn / rough grass** — a very dark, muted green.
  The colour is intentionally dark to prevent the ground from washing out the building
  in renders. [adjustable — can be desert scrub, gravel, or paving]
- Roughness is very high (fully matte) — grass absorbs light rather than reflecting it.

### Building Pad and Retaining Wall
- Both the building pad slab and its perimeter curtain wall are **dark exposed concrete**
  — a near-black charcoal tone, matte. This grounds the building and distinguishes
  the constructed base from the natural terrain.

### Driveway and Street
- The driveway and the street are the same dark concrete material as the pad.
  They read as a unified paved system that connects the building to the public realm.

### ▶ REVIEW GATE 4 — Landscaping
Present a wide-angle perspective from the SW (ocean side) and the NE (street side).
Confirm that the terrain, lawn, pad, and driveway read as a coherent site composition
before adding entourage.

---

## Phase 5 — Entourage

### Goal
Populate the site with human-scaled elements that communicate how the outdoor spaces
are used. All entourage is confined to one clearly defined outdoor living zone.

### Outdoor Patio — Concept
- A **circular patio** is located west of the building, slightly off-centre from
  the building's centreline, sitting directly on the sloping terrain.
  [adjustable — location, size, and shape]
- The patio is a thick circular disc of dark stone that is **proud of the surrounding
  terrain** — its top surface sits clearly above grade, giving it presence and
  separating it from the lawn. Its sides penetrate down through the terrain with
  no gap or floating edge.
- The patio outer edge should feel generous — wide enough to comfortably contain
  the seating group with clear circulation space around the chairs.
  [adjustable — approximately thirty percent more radius than the chair circle]
- The patio disc is a **single dark stone material**, matching the building pad in
  tone. The curved side is **smooth-shaded** (no faceting visible). The top surface
  is flat-shaded. Edge split is applied at the top and bottom rim transitions.

### Fire Pit Table
- A **round fire pit coffee table** is centred on the patio.
  [adjustable — table shape and size]
- It is a low cylindrical table of dark slate — the same material as the patio.
- The top surface has a circular recess in its centre — the fire pit bowl.
  The bowl is lined with a dark metal (steel) insert.
- The fire pit bowl is deep enough to contain a realistic fire without it spilling
  over the rim. The top of the fire should sit noticeably below the rim of the bowl
  — roughly the depth of a hand below the lip.

### Fire
- The fire geometry is built from **multiple emission-shaded objects** inside the bowl:
  a flat coal bed at the base (deep orange-red), several flame cones of varying heights,
  widths, and tilts arranged around a bright central core (yellow-white), and a warm
  orange point light above the pit to cast fire light onto surrounding surfaces.
- Flame objects use different shades from deep red-orange at the outer edges to
  bright yellow-white at the hottest centre. No two flames are identical.
- The fire geometry should fill the bowl but not breach the rim.

### Seating
- **Five Adirondack chairs** are arranged in a circle around the fire pit table.
  [adjustable — number, type, and material of chairs]
- Chair count is odd to avoid perfect symmetry across any axis.
- Chairs are generated using an AI 3D model generator (Hyper3D Rodin) from a text
  prompt describing the chair type and approximate bounding box.
- After import, apply transforms and set rotation mode to **XYZ Euler** before
  assigning any rotation. Imported AI models default to Quaternion rotation mode;
  setting rotation_euler on a Quaternion-mode object has no effect.
- Each chair faces **inward toward the fire** — the chair's back faces outward
  (away from the fire), the seat faces inward. Chairs are arranged like tick marks
  on a clock face: each chair's long axis aligns with its radius from the patio centre.
- Apply **organic variation** to each chair:
  - Slight variation in distance from centre (some a little closer, some a little farther)
  - Slight variation in arc position (chairs are not perfectly evenly spaced)
  - A small rotation offset on each chair (up to about ten degrees) as if people
    have settled in naturally and shifted their chairs slightly — not mechanically placed
- Chair material: **weathered teak** — a warm mid-brown, moderately rough.
  [adjustable — painted wood, metal, wicker, etc.]

### Grouping
- All patio elements (disc, table, fire objects, chairs, fire light) are parented to a
  single **empty object** named PATIO_GROUP so the entire outdoor living scene can be
  shown or hidden with one toggle in the outliner.

### ▶ REVIEW GATE 5 — Entourage
Present close-up renders from all four diagonal compass points (NW, NE, SE, SW) with
the camera orbiting the patio at close range.
Confirm chair orientation, fire visibility, patio scale, and grouping before materials.

---

## Phase 6 — Material Assignment

### Goal
Apply final materials to all objects. Every surface should read as a recognisable
real-world material under varied lighting conditions.

### Design Intent
The palette is warm and earthy — ochre walls, dark metal roof, dark concrete base,
dark glass. The goal is a building that feels grounded and warm, not cold or corporate.
[adjustable — substitute any palette]

### Wall Material — Ochre Render
- Applied to: all exterior wall surfaces, balcony fascias, structural posts, entry column
- A warm golden-yellow tone — the colour of raw ochre pigment or Roman stucco.
  [adjustable — any flat painted render colour]
- High roughness — matte, no sheen.
- This is the dominant visual element of the building and should read warmly in all
  lighting conditions.

### Roof Material — Dark Metal
- Applied to: main roof slab, entry canopy
- A very dark blue-black metallic tone — like weathered zinc or standing-seam steel.
  [adjustable — cor-ten, copper, or membrane]
- Moderate metallic value and low-to-moderate roughness — slight sheen visible at
  grazing angles, but not mirror-like.

### Glazing Material — Dark Tinted Glass
- Applied to: all curtain wall panels, front door glass, any other glazed openings
- Dark blue-grey tinted glass with very low roughness and significant light transmission.
  [adjustable — clear glass, green tint, mirror glass]
- Do not over-saturate — real architectural glass reads as very dark at most angles.

### Mullion / Frame Material — Dark Aluminium
- Applied to: all curtain wall mullions and transoms, window frames
- A dark painted aluminium — near-black, slightly warm grey undertone.
  [adjustable — mill-finish, bronze anodised, or black powder coat]
- Low metallic value (painted, not bare metal), moderate roughness.

### Door Material — Dark Timber
- Applied to: front door panel, garage doors
- A rich dark timber — like oiled walnut or ebony-stained wood.
  [adjustable — painted steel, glass panel, cedar]
- Low metallic value, moderate roughness with slight grain character.

### Concrete / Ground Material
- Applied to: building pad, curtain wall, entry steps and landing, driveway, street
- Near-black charcoal concrete — very dark, fully matte, high roughness.
  [adjustable — lighter board-formed concrete, exposed aggregate, brick]
- This is intentionally darker than real concrete to ground the building visually.

### Veranda Slab
- Applied to: the exposed lower-floor slab on the veranda side
- A light warm grey — lighter than the dark concrete but darker than the walls.
  [adjustable]

### Grass / Terrain
- Applied to: the terrain mesh and any grass objects
- Very dark muted green — intentionally darker than natural grass to read well in
  renders and prevent the ground from dominating the composition. [adjustable]
- Fully matte.

### Patio and Fire Pit Table
- Applied to: patio disc and fire pit coffee table top
- Dark charcoal stone — a single material shared between both, reinforcing their
  visual relationship. Slightly warmer than the concrete. [adjustable]
- Smooth normals on the patio curved side; flat normals on top and bottom faces.

### Chairs
- Weathered teak as described in Phase 5.

### ▶ REVIEW GATE 6 — Materials
Present eight test renders: four diagonal compass-point views of the whole house from
mid-range, and four close-up views of the patio group.
Review material palette, check that no surface reads as pure white or pure black in
typical lighting, and confirm material legibility at both render scales.

---

## Phase 7 — Camera Placement

### Camera Conventions
- All cameras use a moderate wide-angle lens — roughly twenty-four to thirty-five
  millimetres (full-frame equivalent). [adjustable]
- No extreme fish-eye or telephoto lenses. Perspectives should feel natural.
- Camera height is always human-scaled — eye level for a standing adult, or slightly
  above for drone-style shots. Never lower than seated eye level unless intentional.
  [adjustable]

### Hero Camera — Ocean View
- This is the **primary still and animation camera** for the sequence.
- Positioned to the south-west of the building, looking north-east.
- Framing: the full west face of the building is visible, with the roof plane dominant
  in the upper portion of frame and the building pad anchoring the bottom.
  The outdoor patio is visible in the foreground-to-midground.
- This camera follows a curved animation path (see Phase 9). [adjustable]

### Compass Test Camera
- A utility camera used for quick test renders during each phase.
- It orbits the building or the patio at a fixed radius and height, rendering from
  the four diagonal compass points (NW, NE, SE, SW) as still frames.
- The test camera is separate from the hero camera and is not used in final renders.

### ▶ REVIEW GATE 7 — Camera
Present a single still render from the hero camera position.
Confirm framing, horizon line placement, and whether both building and patio read
together in the composition. Adjust before animation setup.

---

## Phase 8 — Lighting

### Approach
Use a **single HDRI sky dome** as the only light source. No sun lamps, no area lights,
no artificial key lights. The fire pit provides its own practical light via an orange
point light. [adjustable — sun lamp can be added for hard-shadow midday look]

### HDRI Selection
- Choose an HDRI that reads as **overcast to partly cloudy** — enough directional
  quality to create soft shadows and catch highlights on the roof plane, but without
  harsh direct-sun contrast that would blow out the wall surfaces. [adjustable]
- Rotate the HDRI around the vertical axis until the warm zone (the sun direction
  embedded in the sky texture) reads as coming from the **south-west** — consistent
  with the building's western view orientation. [adjustable]
- Adjust HDRI strength until the overall scene luminance reads as natural daylight —
  not overexposed, not murky. A Gamma correction node after the HDRI environment
  texture node helps compress the sky dynamic range and increase perceived contrast
  without clipping.

### Fire Light
- The fire point light is warm orange, moderate intensity.
- It casts soft shadows and contributes orange bounce to the underside of the table
  and the seat surfaces of the chairs nearest the fire.

### ▶ REVIEW GATE 8 — Lighting
Present the four diagonal compass-point renders with final materials and lighting.
Check for blown highlights on walls, blocked shadows under balconies, and whether
the fire light registers in the patio scene. Adjust HDRI rotation, strength, or
gamma before animation.

---

## Phase 9 — Animation

### Camera Sweep — Patio Focus
- This animation focuses on the **outdoor patio** with the building's west face as
  the background. [adjustable — can focus on entry, roof, or full site fly-around]
- The camera orbits around the patio at a radius large enough to fit the full patio
  disc and a substantial portion of the building behind it.
- The arc of the sweep is **one hundred degrees**, passing through due West — starting
  south-west and ending north-west. This keeps the building's west facade in frame
  throughout. [adjustable — wider arc for more building reveal, tighter for slower]
- Camera height is slightly above standing eye level — the observer feels like they
  are walking slowly around the fire.
- The lens is wide enough to capture both patio foreground and building background
  simultaneously. [adjustable]

### Timing and Easing
- Total animation duration is **eight seconds at twenty-four frames per second**
  (one hundred and ninety-three frames). [adjustable]
- Apply **ease-in and ease-out** to the camera motion using a smoothstep (Hermite)
  interpolation curve. The camera begins almost stationary, accelerates gently through
  the middle of the arc, then decelerates to almost stationary at the end.
  This creates a cinematic, organic feeling of camera movement rather than a mechanical
  pan. [adjustable — can use linear for a drone/machine aesthetic]
- Insert a keyframe at **every frame** using the smoothstep-remapped azimuth position.
  Do not rely on Blender's built-in spline interpolation between sparse keyframes —
  imported objects may use Quaternion rotation mode which ignores euler keyframes.
  Per-frame insertion guarantees the motion regardless of rotation mode.

### Animation Workflow Note
- When inserting keyframes, always set the object's property value first, then call
  `keyframe_insert(frame=N)`. Never call `scene.frame_set()` inside the keyframe loop —
  it overrides the property value you just set from the animation data, causing all
  frames to bake to the same position.

### ▶ REVIEW GATE 9 — Animation Preview
Render a **Workbench preview animation** (solid shading, material colours, studio
lighting) at quarter resolution before committing to a full Cycles render.
Also render still frames at every ten-frame interval for quick review.
Confirm camera movement, easing feel, and framing throughout the arc.
Adjust arc width, camera distance, or timing before final render.

---

## Phase 10 — Test Rendering

### Goal
Validate the scene before the final high-resolution render. Catch material issues,
lighting problems, and geometry errors at low cost.

### Test Protocol
1. Render four diagonal compass-point stills from the hero camera path at
   **half resolution** using Cycles GPU with moderate samples and OPTIX denoising.
2. Review for: blown highlights, overly dark shadows, floating geometry, incorrect
   materials, fire visibility, glass reflections.
3. Render the full animation at **half resolution** (960 × 540 for a 1920 × 1080
   final, for example) with the same sample count as the final render.
   [adjustable — quarter resolution for even faster iteration]
4. Review the animated MP4 for motion smoothness, easing quality, and framing.

### AI-Ready Passes
For any sequence intended for AI training or compositing workflows, also render:

- **Depth maps**: render each frame with an emission material driven by the camera's
  true spherical distance (View Distance from the Camera Data node). Use raw float
  output to a temporary EXR folder, then normalise per-frame using the actual min/max
  depth values in that frame. Save as sixteen-bit greyscale PNG, near=white, far=black.
  Do NOT use Blender's Workbench depth mode — it produces AO-contaminated output.
  Do NOT apply flipud when reading Blender EXRs via the OpenEXR Python library —
  they are already top-down.

- **Segmentation masks**: assign flat emission materials (zero light bounces, zero HDRI,
  transparent background) to object categories using a consistent colour palette.
  Typical palette for residential AEC: walls=red, glazing=cyan, roof=blue,
  floor slabs=orange, mullions=mid-grey, terrain=green, concrete=dark grey.
  Always set `rotation_mode = 'XYZ'` and zero all bounces before rendering.

### ▶ REVIEW GATE 10 — Test Renders
Client reviews the half-resolution animated MP4 and the four compass-point stills.
Any material, lighting, geometry, or motion changes are made here.
Do not proceed to final rendering until the client signs off on this preview.

---

## Phase 11 — Final Rendering

### Beauty Pass
- Render the full animation at **full resolution** (1920 × 1080 or higher) [adjustable]
- Cycles GPU, high sample count, OPTIX or OpenImageDenoise denoising.
- Output as PNG image sequence to a timestamped versioned folder:
  `renders/ocean_view/v_YYYYMMDD_HHMM/png/`
- Also output a thirty-two-bit float EXR sequence in a parallel `exr/` folder
  for compositing headroom.

### Depth and Segmentation Passes
- Render depth maps and segmentation masks for the full sequence as described
  in Phase 10. Store in `depth/` and `segmentation/` subfolders within the same
  versioned render folder.

### Video Encoding
- Encode the PNG sequence to H.264 MP4 at CRF 18 (high quality) using ffmpeg:
  twenty-four frames per second, yuv420p pixel format.
- The encoded video goes in the root of the versioned render folder alongside the
  PNG and EXR subfolders.

### Versioned Render Folder Structure
```
renders/
  patio_sweep/
    v_YYYYMMDD_HHMM/
      patio_sweep.mp4          ← encoded video
      png/   frame_0000.png … ← beauty sequence
  ocean_view/
    v_YYYYMMDD_HHMM/
      ocean_view.mp4
      png/   frame_0000.png …
      exr/   frame_0000.exr …
      depth/ depth_0000.png …
      segmentation/ seg_0000.png …
      depth_raw_temp/  raw_0000.exr …  ← delete after depth extraction
```

### ▶ FINAL REVIEW — Delivery
Present the encoded MP4 and three representative stills from the sequence.
Archive the checkpoint blend file and the versioned render folder.
Document any design decisions made during modelling that deviate from this prompt
so the prompt can be updated for future projects.

---

## Appendix A — Known Pitfalls

These issues were encountered during the development of this workflow and should be
checked proactively on every new project.

| Issue | Symptom | Fix |
|---|---|---|
| Quaternion rotation mode on imported objects | Setting rotation_euler has no effect; geometry doesn't move | Always set `rotation_mode = 'XYZ'` before setting rotation_euler |
| frame_set() inside keyframe loop | All frames bake to the same position | Set property, then keyframe_insert(frame=N). Never call frame_set inside the loop |
| Depth map range too wide | Flat mid-grey image, no differentiation | Use per-frame auto-normalisation from actual min/max pixel values |
| flipud on Blender EXR | Depth maps are upside-down | Do NOT apply flipud — OpenEXR Python returns Blender EXRs already top-down |
| HDRI not fully zeroed for passes | Segmentation/depth maps have ambient shading | Set world background strength to zero AND set film_transparent=True |
| Pad/curtain wall floating above terrain | Visible gap between base and ground | Sample terrain Z at many perimeter points; extend pad bottom below the minimum |
| Chair faces wrong direction | Backs to fire instead of seats | Verify rotation with a printed world-space axis check; +Y toward centre = seat faces centre when using (theta + π/2) |
| OPEN_EXR_MULTILAYER unavailable in render settings | Error when setting file format | Use OPEN_EXR for render output; multilayer is only available via compositor File Output node |
| PIL I;16 mode deprecated | 16-bit PNG save fails in Pillow 13+ | Use fromarray(uint16.astype(np.int32), mode='I') |
| Patio normal smoothing bleeding to top face | Top face appears smoothly shaded | Mark top and bottom ring edges as sharp; add Edge Split modifier with use_edge_sharp=True |

---

## Appendix B — Material Reference

| Surface | Base Colour (approx.) | Roughness | Metallic |
|---|---|---|---|
| Ochre walls | Warm golden yellow | 0.78 | 0.0 |
| Dark metal roof | Very dark blue-black | 0.55 | 0.55 |
| Tinted glass | Dark blue-grey | 0.0 | 0.0 |
| Dark aluminium mullions | Near-black warm grey | 0.80 | 0.20 |
| Dark timber doors | Rich dark brown | 0.72 | 0.0 |
| Dark concrete (base/pad/drive) | Near-black charcoal | 1.0 | 0.0 |
| Light grey veranda slab | Warm light grey | 0.80 | 0.0 |
| Dark grass terrain | Very dark muted green | 0.92 | 0.0 |
| Dark patio stone | Dark charcoal warm | 0.88 | 0.0 |
| Weathered teak chairs | Warm mid-brown | 0.72 | 0.0 |
| Fire coals | Deep orange-red emission | — | — |
| Fire core | Bright yellow-white emission | — | — |

---

## Appendix C — Segmentation Colour Palette

For AI training workflows, use this palette consistently across all projects.
Changing the palette breaks compatibility with previously labelled datasets.

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

---

*End of prompt document.*
*Save this file as `01_user_prompt.md` in the master_prompts folder.*
*Update the Appendices whenever a new pitfall is discovered or a palette decision is changed.*
