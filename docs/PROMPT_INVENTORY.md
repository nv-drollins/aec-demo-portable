# AEC Demo Portable — Prompt Inventory
### Complete reference for all prompts included in this package
*Version 1.0 — May 2026*

> **UPSTREAM INVENTORY AND PORTING EVIDENCE.** References to Claude, Rhino,
> RhinoMCP, Windows paths, and OBS describe the delivered source workflow. The
> supported DGX Spark demo uses Hermes, FreeCAD MCP, Blender MCP, and ComfyUI.
> Follow [INSTALL_GUIDE.md](INSTALL_GUIDE.md) and
> [SPARK_RUNBOOK.md](SPARK_RUNBOOK.md) for execution.

---

## Overview

This package contains three categories of prompts:

| Category | Folder | Count | Purpose |
|----------|--------|-------|---------|
| **Project Design Brief** | `prompts/project_template/` | 1 | Human fills this in to define a new project |
| **Workflow Phase Prompts** | `prompts/master_workflow/` | 18 | Claude reads these to execute each phase of the demo |
| **AI Generation Prompts** | `prompts/comfyui/` | 1 | Controls Flux.2 Klein image generation output |

---

## How Prompts Are Used

```
You (human) fill in:
  project_template/project_design_brief_template.md
        ↓
Claude reads at session start:
  master_workflow/01_user_prompt.md       ← design spec
  master_workflow/02_demo_prompt.md       ← recording protocol
        ↓
Claude executes phases in order:
  03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14
        ↓
At render time, Claude uses:
  comfyui/generation_prompts.yaml         ← AI image prompts
```

Agent reference prompts (15, 16, 17) are always-available lookups — Claude
reads them whenever it needs to check a checklist, find a code pattern, or
diagnose a failure. They do not need to be loaded in a specific order.

---

## Category 1 — Project Design Brief

### `prompts/project_template/project_design_brief_template.md`

**Who uses it:** You — the human designer  
**When:** Before starting any project — fill this in first  
**How:** Type answers directly, use voice dictation, or ask Claude to interview you  

A structured fill-in-the-blank design brief covering 13 sections:

| Section | What you define |
|---------|----------------|
| 1 — Project Identity | Name, one-sentence description, who it's for |
| 2 — Site & Terrain | Landscape, slope direction, ground cover, retaining walls, patio, driveway |
| 3 — Building Overview | Architectural style, number of stories, floor area, key features, things to avoid |
| 4 — Garage | Capacity, door location and style |
| 5 — Windows & Glazing | Glass area, tint, reflectivity, mullion colour |
| 6 — Balconies & Outdoor | Which floors, which faces, railing style, verandas |
| 7 — Entry | Arrival sequence, door style, canopy |
| 8 — Materials & Palette | Exterior walls, roof, slabs, accents |
| 9 — Outdoor Living | Patio surface, firepit, seating |
| 10 — Lighting & Environment | Time of day, sky character, interior glow |
| 11 — Camera & Render Style | Hero shot description, animation, visual style |
| 12 — Anything Else | Constraints, references, things to emphasise |
| 13 — Reference Material | Auto-populated by Claude during Phase 0 |
| 0 — Scene Elements | Auto-populated by Claude after Rhino scan |

When complete, say: *"I've filled in my project prompt. Let's start."*

---

## Category 2 — Workflow Phase Prompts

These are read by Claude at the start of each phase. They contain
the rules, geometry specifications, code patterns, validation checks,
and gate conditions for that phase. You do not edit these — they are
the authoritative source of truth for how Claude executes the demo.

---

### `prompts/master_workflow/01_user_prompt.md`
**Title:** Architectural Modelling Prompt — Contemporary Hillside Residence  
**Read by:** Claude at the start of every session  
**What it does:**  
The master design specification for the ocean view hillside residence. Defines every
dimension, material, geometry rule, and constraint that Claude must follow across all
phases. This is the reference document Claude checks whenever it needs to know what
the building should look like. Covers site geometry, building massing, balcony rules,
window placement logic, patio/stair dimensions, material palette, and render spec.

---

### `prompts/master_workflow/02_demo_prompt.md`
**Title:** Demo Capture Prompt — AI-Assisted Architectural Modelling  
**Read by:** Claude before starting any recording session  
**What it does:**  
The screen capture and OBS recording protocol. Tells Claude which OBS scenes to use,
how to verify sources are working, when to start and stop recording, how to structure
the footage for video editing, and how to name the capture files. Also covers the
ComfyUI browser source and per-project file structure for demo captures.

---

### `prompts/master_workflow/03_config_prompt.md`
**Title:** Phase 0 — Project Configuration  
**Phase:** 0 — first to run  
**Apps:** Claude only  
**What it does:**  
Session setup and project initialisation. Claude reads this to create the project
folder structure, verify all MCP connections (Blender, Rhino, OBS), set up OBS
recording, confirm the design brief with you, and prepare the blank Rhino and
Blender scenes. Nothing gets modelled until this phase passes all checks.

---

### `prompts/master_workflow/04_site_prep_prompt.md`
**Title:** Phase 1 — Site Preparation  
**Phase:** 1  
**Apps:** Claude + Rhino  
**What it does:**  
Builds the terrain, building pad, retaining walls, driveway, and patio outline in
Rhino. Claude reads the site dimensions from `01_user_prompt.md`, constructs the
terrain network from u/v curves, places the building pad at the correct elevation,
adds retaining walls that follow the terrain, and creates the patio curve. Includes
validation checks that all geometry is watertight and correctly layered.

---

### `prompts/master_workflow/05_massing_prompt.md`
**Title:** Phase 2 — Massing  
**Phase:** 2  
**Apps:** Claude + Rhino  
**What it does:**  
Extrudes the building footprint into a full massing model. Creates upper and lower
floor volumes, the cantilevered section, roof slabs, balcony slabs, and the garage
volume — all as solid Breps with correct dimensions from the design brief. Defines
the setback rules (veranda depth, balcony projection, cantilever limits) and the
exact Y extents for each floor. Gate: all volumes must be IsSolid = True.

---

### `prompts/master_workflow/06_detailing_prompt.md`
**Title:** Phase 3 — Detailing  
**Phase:** 3  
**Apps:** Claude + Rhino  
**What it does:**  
Adds architectural detail to the massing: window and door openings (Boolean cuts),
column elements, fascia overhangs, entry canopy, railing geometry, and stair runs
from patio to pad. Enforces the rule that glass elements must sit in Boolean-cut
openings and never be buried in walls. Includes overlap and coplanar-face checks.

---

### `prompts/master_workflow/07_landscaping_prompt.md`
**Title:** Phase 4 — Landscaping  
**Phase:** 4  
**Apps:** Claude + Rhino + Blender  
**What it does:**  
Adds terrain-level landscaping: ground surface mesh, planting areas, path surfaces,
and the patio hardscape. Exports the Rhino scene to Blender. In Blender, applies
a terrain material, places scattered plant instances (succulents, grasses, shrubs)
using particle systems, and adds the driveway surface. Verifies the export import
matches the Rhino dimensions.

---

### `prompts/master_workflow/08_entourage_prompt.md`
**Title:** Phase 5 — Entourage  
**Phase:** 5  
**Apps:** Claude + Blender  
**What it does:**  
Adds human-scale context elements to the Blender scene: outdoor furniture on the
patio (chairs, firepit, table), any visible vehicle in the driveway, and decorative
planters or objects near the entry. Positions everything consistent with the design
brief's outdoor living description. Objects are sourced from the Blender asset
library or generated procedurally.

---

### `prompts/master_workflow/09_materials_prompt.md`
**Title:** Phase 6 — Material Assignment  
**Phase:** 6  
**Apps:** Claude + Blender  
**What it does:**  
Assigns all Principled BSDF materials to the Blender scene. Reads material
definitions from `01_user_prompt.md` Appendix B. Covers travertine, concrete,
aluminium, glass (clear and tinted), wood, water, and terrain. Sets the `material`
custom property on every mesh object — this tag drives the segmentation pass colour
mapping. Verifies that every object has a material assigned and no defaults remain.

---

### `prompts/master_workflow/10_camera_prompt.md`
**Title:** Phase 7 — Camera Placement  
**Phase:** 7  
**Apps:** Claude + Blender  
**What it does:**  
Places and configures the render camera. Reads the hero shot description from
`01_user_prompt.md` and positions `RenderCam` at the correct location, distance,
height, and angle. Sets focal length, clipping planes, and depth-of-field if
specified. For animation projects, places keyframes along the camera path defined
in the design brief.

---

### `prompts/master_workflow/11_lighting_prompt.md`
**Title:** Phase 8 — Lighting  
**Phase:** 8  
**Apps:** Claude + Blender  
**What it does:**  
Sets up the world lighting using an HDRI environment map. Reads the time-of-day and
sky description from `01_user_prompt.md`. Configures the world shader node tree
(TexCoord → Mapping → EnvironmentTexture → Background → WorldOutput), sets HDRI
rotation for sun direction, and sets a grey camera-background using a Light Path
node so the background colour is visible but the HDRI still drives lighting.

---

### `prompts/master_workflow/12_animation_prompt.md`
**Title:** Phase 9 — Animation  
**Phase:** 9 (optional)  
**Apps:** Claude + Blender  
**What it does:**  
Creates the camera animation path if the project includes a flythrough or sweep.
Sets keyframes, configures easing curves, verifies frame count and duration, and
does a low-sample preview render to check the motion. For still-only projects,
this phase is skipped.

---

### `prompts/master_workflow/13_test_render_prompt.md`
**Title:** Phase 10 — Test Rendering  
**Phase:** 10  
**Apps:** Claude + Blender  
**What it does:**  
Renders the three pass types (beauty, depth, segmentation) at reduced quality to
verify the pipeline before the final render. Checks that: beauty has correct
lighting and materials, depth is normalised 0–1 with no clipping, seg has clean
flat colours with transparent background, all three files land in the correct
`renders/` subfolders with sequential numbering. Gate: all three pass types must
produce valid files before proceeding to Phase 11.

---

### `prompts/master_workflow/14_final_render_prompt.md`
**Title:** Phase 11 — Final Rendering  
**Phase:** 11 — last to run  
**Apps:** Claude + Blender + ComfyUI  
**What it does:**  
Renders the full-quality pass set (128 samples beauty, 4 samples depth, EEVEE seg)
and submits to ComfyUI via `scripts/submit_comfyui.py`. Monitors the ComfyUI queue,
loads the three output images (Make Real, Change Environment, Time of Day) into
Blender's Image Editor, and saves a timestamped snapshot of the Blender scene.
Stops OBS recording and saves the session capture file.

---

### `prompts/master_workflow/15_agent_quick_start.md`
**Title:** Agent Reference — Quick Start Checklist  
**Type:** Agent reference (not a phase prompt)  
**Read by:** Claude at session start and whenever restarting  
**What it does:**  
A concise checklist Claude uses to verify prerequisites before beginning any phase:
MCP connections, OBS sources, file structure, HDRI files. Also contains the 7-step
new project setup procedure and the phase execution order table. Claude reads this
to self-check that nothing is missing before touching Rhino or Blender.

---

### `prompts/master_workflow/16_agent_workflow_reference.md`
**Title:** Agent Reference — Workflow Reference  
**Type:** Agent reference (not a phase prompt)  
**Read by:** Claude when it needs to look up a pattern or procedure  
**What it does:**  
The condensed agent-readable version of the entire workflow. Contains the canonical
layer naming conventions, object naming rules, material tag list, geometry
constraints (cantilever limits, balcony extents, slab thickness), and the exact
Python patterns for common Blender and Rhino operations. Claude consults this
when it needs to recall a specific rule or code pattern without re-reading the
full phase prompts.

---

### `prompts/master_workflow/17_agent_failure_index.md`
**Title:** Agent Reference — Failure Mode Index  
**Type:** Agent reference (not a phase prompt)  
**Read by:** Claude when something goes wrong  
**What it does:**  
An indexed catalogue of known failure modes, their symptoms, root causes, and
confirmed fixes. Covers BlenderMCP connection failures, ComfyUI validation errors,
Rhino geometry issues (non-solid Breps, coplanar faces), material assignment
failures, render output problems, and MCP server restarts. Claude reads the
relevant entry when it encounters an error, rather than guessing at a fix.

---

### `prompts/master_workflow/aec_skills.md`
**Title:** AEC Skills Library  
**Type:** Agent skills reference  
**Read by:** Claude throughout all phases  
**What it does:**  
The master skill reference covering every tool Claude uses in the demo: Rhino 3D,
Blender, BlenderMCP, RhinoMCP, Hyper3D (3D model generation), OBS, and ComfyUI.
Each skill entry contains the correct Python/API call, parameter names, expected
return values, and common pitfalls. This is the most frequently consulted file —
Claude checks it before making any API call it hasn't made recently in a session.

---

## Category 3 — AI Generation Prompts

### `prompts/comfyui/generation_prompts.yaml`

**Who uses it:** `scripts/submit_comfyui.py` reads it at submission time  
**When:** Every time a render is submitted to ComfyUI  
**Edit freely:** Yes — this is the main file you edit to change the AI output  

Contains three main prompts, each with alternates, plus the segmentation colour map:

| Key | Node ID | Controls | Alternates included |
|-----|---------|----------|---------------------|
| `make_real` | 1124 | Photorealistic material and lighting treatment of the architecture | Desert modern, Pacific Northwest |
| `change_environment` | 1128 | Background landscape and environment replacement | Italian hillside, Mountain forest, Urban rooftop |
| `time_of_day` | 1129 | Sky, lighting time, atmosphere, interior glow | Golden hour, Overcast day, Deep night |
| `segmentation_colours` | — | Material-to-colour mapping for the seg pass | — |

**Default prompts (shipped in this package):**

*Make Real:*
> Luxury modernist home, photorealistic architectural photography, travertine stone
> and glass, flat roof, deep overhanging eaves, ocean view hillside, warm natural
> light, high-end residential architecture

*Change Environment:*
> Dramatic Pacific ocean view, coastal California hillside, golden hour sunlight
> over the water, dry sage and succulents, sweeping panoramic vista, low cliff
> above the ocean

*Time of Day:*
> Early dusk, warm golden sunset on the horizon, deep blue twilight sky with
> visible stars emerging in the darker upper sky, warm amber interior light
> spilling through floor-to-ceiling windows, glowing underwater pool lights
> illuminating the water from below, architectural exterior lighting, fire pit
> on terrace, serene coastal California evening

**To use an alternate:** Copy the text from the `alternates:` list in the YAML
and paste it into the main `prompt:` field, then call `submit(render=False)`.

**To write your own:** Replace any `prompt:` value with your own text. Keep it
descriptive and specific — Flux.2 Klein responds well to material nouns, lighting
adjectives, and architectural terminology. No negative prompts needed.

---

## Prompt Loading Order — Session Startup Sequence

When starting a new session, give Claude these prompts in this order:

```
1. prompts/master_workflow/01_user_prompt.md      (design spec — always first)
2. prompts/master_workflow/02_demo_prompt.md      (recording protocol)
3. prompts/master_workflow/03_config_prompt.md    (Phase 0 — session setup)
```

For continuing an existing session, Claude only needs:
```
1. prompts/master_workflow/01_user_prompt.md      (re-establishes context)
3. prompts/master_workflow/[next phase prompt]    (whatever phase you're on)
```

Agent reference files (15, 16, 17, aec_skills.md) do not need to be loaded
explicitly — Claude reads them on demand when it needs to look something up.

---

## Quick Reference — Which Prompt for What

| I want to... | Use this prompt |
|---|---|
| Start a brand new project | `project_template/project_design_brief_template.md` |
| Set up a session from scratch | `03_config_prompt.md` |
| Build terrain and site | `04_site_prep_prompt.md` |
| Create the building volumes | `05_massing_prompt.md` |
| Add windows, doors, railings | `06_detailing_prompt.md` |
| Add plants and ground | `07_landscaping_prompt.md` |
| Add furniture and context | `08_entourage_prompt.md` |
| Set materials | `09_materials_prompt.md` |
| Place the camera | `10_camera_prompt.md` |
| Set up HDRI lighting | `11_lighting_prompt.md` |
| Animate the camera | `12_animation_prompt.md` |
| Test-render all passes | `13_test_render_prompt.md` |
| Full render + ComfyUI submit | `14_final_render_prompt.md` |
| Change the AI image style | `comfyui/generation_prompts.yaml` |
| Restart after a crash | `15_agent_quick_start.md` |
| Look up a code pattern | `16_agent_workflow_reference.md` |
| Diagnose an error | `17_agent_failure_index.md` |
| Find a Blender/Rhino API call | `aec_skills.md` |

---

## Category 4 � Agent Skills

Skills are code files and reference documents Claude reads **on demand**. INDEX.md is the entry point read at the start of every session. **Skills override all other instructions if there is a conflict.** All files live in skills/.

| File | Type | When Claude reads it | What it does |
|------|------|----------------------|-------------|
| skills/INDEX.md | Reference | First thing, every session | Master entry point � lists all skills, trigger conditions, pipeline flow, points to session_state.md |
| skills/session_state.md | Reference | Immediately after INDEX.md | Live project state � last phase completed, decisions made, what's next |
| skills/architectural_pipeline.md | Reference | Starting any new task | End-to-end pipeline reference � metadata conventions, layer/object naming, material tag system |
| skills/rhino_modeling_skill.md | Reference | Before/during any Rhino construction | Modeling discipline � derive-don't-redraw principle, anti-patterns, layer structure |
| skills/rhino_prep_skill.md | Reference | Before exporting Rhino ? Blender | Pre-export gate checklist � solid Breps, metadata, layer structure |
| skills/depth_and_segmentation.md | Reference | Before rendering depth or seg passes | Pass setup � EEVEE+Raw for seg, camera-distance shader for depth, verification checks |
| skills/audit_active_document.py | Python (Rhino) | During modeling; after geometry changes | Scans Rhino for coplanar faces, duplicates, missing metadata, non-solid Breps |
| skills/pre_export_validate.py | Python (Rhino) | Immediately before Rhino export | Final export gate � units, scale, origin, full geometry audit |
| skills/import_with_metadata.py | Python (Blender) | Phase 4 � first step of Blender import | Imports .3dm, maps material tags, sets custom properties on every mesh |
| skills/validate_blender_scene.py | Python (Blender) | After import; before rendering | Post-import gate � materials assigned, custom props set, camera exists, no z-fighting |
| skills/coplanar_detector.py | Python (Blender) | After import; before render; after edits | Finds z-fighting coplanar faces � identifies affected objects for precise fixing |
| skills/derive_geometry.py | Python (Blender) | When modifying Blender geometry | Helper functions � bounding boxes, face normals, vertex snapping, clean mesh rebuild |

### Skills quick-reference additions to the lookup table

| I want to... | Use this |
|---|---|
| Read skills index | skills/INDEX.md |
| Track project state | skills/session_state.md |
| Recall pipeline conventions | skills/architectural_pipeline.md |
| Audit Rhino geometry | skills/audit_active_document.py |
| Gate before Rhino export | skills/pre_export_validate.py + skills/rhino_prep_skill.md |
| Import Rhino ? Blender | skills/import_with_metadata.py |
| Validate Blender scene | skills/validate_blender_scene.py |
| Find z-fighting faces | skills/coplanar_detector.py |
| Modify Blender geometry | skills/derive_geometry.py |
| Set up depth or seg pass | skills/depth_and_segmentation.md |
| Rhino modeling discipline | skills/rhino_modeling_skill.md |

---

## Category 5 — System Prompts

System prompts govern how Claude initiates and manages sessions. They are always
active, loaded before any phase prompt. All files live in prompts/system_prompts/.

### prompts/system_prompts/00_session_startup.md
Read by: Claude at the very start of every session.
Defines the two session scenarios (New Project and Resume Project). New project:
interviews user, fills in design brief, initiates Phase 0. Resume: reads
session_state.md, confirms current phase, continues. Also covers crash recovery.

### prompts/system_prompts/00b_rhino_scene_protocol.md
Read by: Claude whenever working in Rhino.
Rules for Rhino MCP interaction: when to read vs write, snapshot protocol before
destructive operations, layer naming contract, what Claude is not allowed to delete.

### prompts/system_prompts/00c_references_protocol.md
Read by: Claude when interpreting reference images or adding new references.
How to extract design intent from images, how to tag and file references, when
references override the design brief vs when brief takes precedence.

---

## Category 6 — Rhino-Specific Claude Skills

Installed separately from main skills. These are Rhino-workflow-specific.
Location in package: skills/rhino/
Original system location: C:\Users\{username}\Documents\claude_rhino_skills\

### skills/rhino/INDEX.md
Entry point for Rhino skills. Lists all available skills, when each applies,
operating rules for Rhino-specific work. Read at start of any Rhino session.

### skills/rhino/slope_curve_network.md
Technique for constructing sloped terrain from a curve network in Rhino.
Defines the u-curve/v-curve approach: u-curves = slope profiles (3, N-S),
v-curves = cross sections (2, E-W). Covers loft method, edge handling near
the building pad, and surface validation. Authoritative method for all terrain.

### skills/rhino/patio_retaining_wall.md
Technique for constructing the patio retaining wall as a smooth lofted solid.
Defines wall profile (top always at least 0.5m above patio), construction
sequence, validation checks (solid, no self-intersections, continuous top edge).
Also covers stair integration: step heights and connection to pad and patio.

---

## Lookup Table Additions

| I want to... | Use this |
|---|---|
| Start or resume a session | prompts/system_prompts/00_session_startup.md |
| Understand Rhino scene rules | prompts/system_prompts/00b_rhino_scene_protocol.md |
| Handle reference images | prompts/system_prompts/00c_references_protocol.md |
| Build terrain in Rhino | skills/rhino/slope_curve_network.md |
| Build retaining walls or patio stairs | skills/rhino/patio_retaining_wall.md |
