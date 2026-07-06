# Demo Capture Prompt — AI-Assisted Architectural Modelling
### Screen Capture & Recording Protocol for Video Production
*Companion to: `01_user_prompt.md` and phase prompts `03_config_prompt.md` through `14_final_render_prompt.md`*
*Version 1.2 — May 2026*
*Modifications: Session source verification on startup; ComfyUI browser source added;
gate checkpoint saves; aa_demo_versions per-project file structure*

---

## Purpose of This Document

This prompt governs the **screen capture and recording workflow** for a demonstration
video showing Claude (AI agent) building a complete architectural scene from scratch
using Rhino 3D, Blender, and associated MCP tools.

The goal is to produce a well-organised library of 4K screen capture footage that
a video editing team can navigate quickly, cut efficiently, and combine into a
compelling demonstration of AI-assisted architectural design.

This document is read by Claude. Every OBS instruction in this file is an **action
Claude must perform** — not a suggestion. When you see `→ OBS ACTION`, Claude calls
the appropriate OBS MCP tool immediately, without waiting to be asked.

---

## What This Footage Captures

The demo shows four parallel stories happening simultaneously:

1. **The conversation** — The Claude Desktop window, showing the user's natural
   language prompts and Claude's responses in real time. This is the human-AI
   dialogue layer.

2. **The geometry** — Rhino 3D, showing 3D modelling commands executing live:
   curves being drawn, surfaces being lofted, solids being built and trimmed.

3. **The rendering** — Blender, showing scene assembly, material assignment,
   lighting, camera animation, and Cycles renders progressing frame by frame.

4. **The post-processing** — ComfyUI running in a browser, showing AI image
   processing workflows applied to the rendered output during the final phase.

The video team needs all four. They need to know exactly which phase and which
application every clip belongs to, without watching any footage to find out.

---

## OBS Pre-Configuration (One-Time Setup)

Before any recording session begins, configure OBS as follows. This only needs to
be done once per machine. Save the OBS profile as `aec_demo_master`.

### Scenes
Create exactly **four scenes** in OBS. Name them precisely as written — Claude
references these names by string when switching:

| Scene Name | Captures | Window / Source |
|---|---|---|
| `CLAUDE` | Claude Desktop application | Window Capture → Claude |
| `RHINO` | Rhinoceros 3D application | Window Capture → Rhino 3D |
| `BLENDER` | Blender application | Window Capture → Blender |
| `COMFYUI` | ComfyUI in Google Chrome | Window Capture → Google Chrome |

### ComfyUI Browser Selection — Google Chrome (Required)
ComfyUI must be run in **Google Chrome** specifically, not Edge, Firefox, or any
other browser. Reasons:

- Claude has direct programmatic control of Chrome via the **Claude in Chrome MCP
  extension**. This means Claude can navigate to ComfyUI URLs, trigger workflows,
  read node output, and monitor progress — all without the user touching the mouse.
  No other browser has this integration.
- OBS Window Capture works reliably with Chrome's window title, which is predictable
  and stable across sessions (`ComfyUI — Google Chrome`).
- The Claude in Chrome extension can inject JavaScript and read the DOM, allowing
  Claude to confirm that a ComfyUI workflow has completed without relying solely on
  visual cues captured by OBS.

**Important:** Only one Chrome window should be open when ComfyUI is running.
Multiple Chrome windows create ambiguity in the OBS Window Capture source.
If other browser work is needed during the session, use Edge or Firefox for it and
keep Chrome reserved exclusively for ComfyUI.

### Video Settings
- **Base (Canvas) Resolution:** 3840 × 2160 (4K UHD)
- **Output (Scaled) Resolution:** 3840 × 2160 (no downscale)
- **Frame Rate:** 30 fps
- **Colour Format:** NV12 or I444 (whichever your hardware supports at 4K)

### Output Settings
- **Recording Format:** MKV (safer for long recordings — recoverable if crash)
- **Encoder:** Hardware (NVENC H.264 or NVENC HEVC if available; otherwise x264)
- **Rate Control:** CQP / CRF 18 (high quality)
- **Audio Track:** **All tracks disabled** — no audio capture

### Output Folder
Set OBS recording output path to:
```
C:\Users\swags\Documents\aec_demo_master\captures\
```
OBS will save files here. Claude will instruct the renaming of each file immediately
after stopping a recording, using the naming convention below.

### Filename Template
In OBS Advanced Output settings, set filename formatting to:
```
%CCYY%MM%DD_%hh%mm%ss
```
This gives a date-time stamp Claude can match to the correct file for renaming.

---

## Session Startup Source Verification (Every Session)

**This check is mandatory at the start of every recording session — not just the
first time. After a system restart, application update, or OBS crash, OBS can lose
the window handle assigned to a Window Capture source and silently capture the wrong
window, a black frame, or nothing at all. Never assume sources are correct. Always verify.**

### Verification Procedure

At the start of each session, before any recording begins, Claude performs the
following steps in order:

**Step 1 — Query source list**

→ **OBS ACTION:** Call `obs-get-input-list` to confirm all four expected sources
exist: `CLAUDE`, `RHINO`, `BLENDER`, `COMFYUI`. If any are missing, stop and ask
the user to add the missing source in OBS before proceeding.

**Step 2 — Screenshot each source**

For each of the four scenes, switch to that scene and take a screenshot:

→ **OBS ACTION (repeat for each scene):**
1. Call `obs-set-current-scene("CLAUDE")` — then call `obs-get-source-screenshot`
   with the source name for the Claude window capture.
2. Call `obs-set-current-scene("RHINO")` — screenshot the Rhino source.
3. Call `obs-set-current-scene("BLENDER")` — screenshot the Blender source.
4. Call `obs-set-current-scene("COMFYUI")` — screenshot the Chrome/ComfyUI source.

`obs-get-source-screenshot` returns a Base64-encoded image. Claude decodes and
evaluates each screenshot to confirm it shows the correct application.

**Step 3 — Evaluate each screenshot**

For each source screenshot, Claude checks:

| Source | What a correct screenshot shows |
|---|---|
| `CLAUDE` | The Claude Desktop chat interface — message bubbles, text input bar |
| `RHINO` | Rhinoceros 3D viewport — the Rhino UI with 3D viewport panes visible |
| `BLENDER` | Blender interface — viewport, outliner, properties panels |
| `COMFYUI` | Google Chrome showing the ComfyUI node graph interface |

**Step 4 — Report and resolve**

Claude reports the result of each source check to the user:
- ✓ If a source shows the correct application: "CLAUDE source verified ✓"
- ✗ If a source shows the wrong window, a black frame, or is missing:
  "RHINO source appears incorrect — showing [description]. Please reassign
  the Window Capture source in OBS to the Rhinoceros 3D window and confirm."

Do not begin any phase recording until all active sources are verified correct.
If an application is not yet open (e.g. ComfyUI is not running at the start of
Phase 1), note it as "not yet needed" and mark it for re-verification before
its first use.

**Step 5 — Re-verify before first use of each application**

Even if a source was verified at session start, re-verify it immediately before
the first recording that uses it. Applications may be restarted or minimised
during the session. A quick screenshot check costs two seconds and prevents
entire phase recordings being captured on the wrong window.

---

## File Naming Convention

Every capture file is renamed immediately after the recording stops, using this format:

```
{phase_number}-{phase_topic}-{app}.mkv
```

Examples:
```
01-site_prep-claude.mkv
01-site_prep-rhino.mkv
02-massing-claude.mkv
02-massing-rhino.mkv
03-detailing-claude.mkv
03-detailing-rhino.mkv
04-landscaping-claude.mkv
04-landscaping-blender.mkv
05-entourage-claude.mkv
05-entourage-blender.mkv
06-materials-claude.mkv
06-materials-blender.mkv
07-camera-claude.mkv
07-camera-blender.mkv
08-lighting-claude.mkv
08-lighting-blender.mkv
09-animation-claude.mkv
09-animation-blender.mkv
10-test_render-claude.mkv
10-test_render-blender.mkv
11-final_render-claude.mkv
11-final_render-blender.mkv
11-final_render-comfyui.mkv
```

Rules:
- Phase numbers are always two digits with leading zero.
- Topic names use underscores, no spaces, all lowercase.
- App names are always one of: `claude`, `rhino`, `blender`, `comfyui`.
- If a phase involves multiple separate sessions in the same app (for example,
  multiple rounds of feedback and revision in Blender), append a letter suffix:
  `06-materials-blender-a.mkv`, `06-materials-blender-b.mkv`.
- Do not capture an application if nothing is happening in it during that phase.

---

## Recording State Machine

At any moment during the project, OBS is in one of five states. Claude manages
all transitions:

```
IDLE (not recording)
   ↓  [phase begins — user sends first prompt]
RECORDING-CLAUDE  ←─────────────────────────────────────────────┐
   ↓  [Claude about to send commands to Rhino]                   │
RECORDING-RHINO                                                   │
   ↓  [Rhino work complete, returning to Claude]                │
RECORDING-CLAUDE ─────────────────── [user feedback loop] ──────┘
   ↓  [Claude about to send commands to Blender]
RECORDING-BLENDER
   ↓  [Blender work complete]
RECORDING-CLAUDE
   ↓  [Claude about to drive ComfyUI workflow]
RECORDING-COMFYUI
   ↓  [ComfyUI workflow complete]
RECORDING-CLAUDE
   ↓  [review gate cleared by user]
IDLE → [rename files] → IDLE
```

**Transitions Claude must manage:**

| Trigger | OBS Action |
|---|---|
| User sends first message of a new phase | Switch to CLAUDE scene, start recording |
| Claude about to call Rhino MCP tools | Switch to RHINO (keep recording) |
| Rhino MCP calls complete | Switch to CLAUDE (keep recording) |
| Claude about to call Blender MCP tools | Switch to BLENDER (keep recording) |
| Blender MCP calls complete | Switch to CLAUDE (keep recording) |
| Claude about to drive ComfyUI via Chrome MCP | Switch to COMFYUI (keep recording) |
| ComfyUI workflow complete | Switch to CLAUDE (keep recording) |
| User approves review gate | Stop recording, rename files, confirm to user |

**Critical rules (unchanged from v1.0):**
- Switch scene *before* sending any command to the target application.
- Never stop recording during a feedback/revision loop.
- Each application gets one continuous clip per phase unless genuinely separated
  by IDLE time, in which case use letter suffixes (a, b, c).

---

## Phase-by-Phase Recording Instructions

---

### Phase 0 — Project Setup

**Apps involved:** Claude only.
**Captures:** `00-project_setup-claude.mkv`

→ **OBS ACTION — SESSION START:** Before responding to any prompt, run the full
Session Startup Source Verification procedure described above. Report each source
status to the user. Proceed only when all needed sources are verified.

→ **OBS ACTION:** After verification is complete, call `obs-set-current-scene("CLAUDE")`,
then `obs-start-record`. Confirm: "OBS recording started — `00-project_setup-claude`."

Work through project setup: file structure, coordinate origin, units confirmation.

→ **OBS ACTION:** Phase complete. `obs-stop-record`.
Rename to `00-project_setup-claude.mkv`. Confirm.

---

### Phase 1 — Site Preparation

**Apps involved:** Claude + Rhino 3D.
**Captures:** `01-site_prep-claude.mkv`, `01-site_prep-rhino.mkv`

→ **OBS ACTION:** Verify RHINO source before use (screenshot check).
Then `obs-set-current-scene("CLAUDE")` → `obs-start-record`.
Confirm: "Recording started — `01-site_prep-claude`."

Claude processes the brief, plans terrain approach, explains what it is about to do.

→ **OBS ACTION:** Before first Rhino MCP command, `obs-set-current-scene("RHINO")`.
Confirm: "Switching to Rhino capture."

Rhino work: U/V curves, NURBS surface, lot lines, building pad, curtain wall, trimming.

→ **OBS ACTION:** Rhino work complete. `obs-set-current-scene("CLAUDE")`.

Claude presents screenshots and awaits feedback. User reviews and approves.

**▶ REVIEW GATE 1 — Site**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`.
Rename to `01-site_prep-claude.mkv` and `01-site_prep-rhino.mkv`. Confirm both.

---

### Phase 2 — Massing

**Apps involved:** Claude + Rhino 3D.
**Captures:** `02-massing-claude.mkv`, `02-massing-rhino.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

Claude plans massing: lower floor, upper floor overhang, shed roof, slabs, garage.

→ **OBS ACTION:** Before first Rhino command, `obs-set-current-scene("RHINO")`.

Rhino work: all building volume geometry.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 2 — Massing**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 3 — Detailing

**Apps involved:** Claude + Rhino 3D.
**Captures:** `03-detailing-claude.mkv`, `03-detailing-rhino.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Rhino, `obs-set-current-scene("RHINO")`.

Rhino work: mullions, balcony, posts, entry canopy, steps, garage doors, driveway.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 3 — Detailing**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 4 — Landscaping

**Apps involved:** Claude + Blender.
**Captures:** `04-landscaping-claude.mkv`, `04-landscaping-blender.mkv`

→ **OBS ACTION:** Verify BLENDER source (screenshot check) before first use.
Then `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender, `obs-set-current-scene("BLENDER")`.

Blender work: terrain, pad, driveway material assignment.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 4 — Landscaping**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 5 — Entourage

**Apps involved:** Claude + Blender.
**Captures:** `05-entourage-claude.mkv`, `05-entourage-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

Claude plans patio layout, chair count, fire pit, Hyper3D prompts.

→ **OBS ACTION:** Before Blender/Hyper3D, `obs-set-current-scene("BLENDER")`.

Blender work: patio disc, Hyper3D chair generation and import, fire pit table,
chair scaling and rotation debugging, fire geometry, PATIO_GROUP parenting.

Stay on BLENDER throughout all Blender work including all revision rounds.
The chair rotation debugging loop is important footage — do not switch away.

→ **OBS ACTION:** Entourage complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 5 — Entourage**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 6 — Material Assignment

**Apps involved:** Claude + Blender.
**Captures:** `06-materials-claude.mkv`, `06-materials-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender, `obs-set-current-scene("BLENDER")`.

Blender work: all Principled BSDF materials, test renders after each category.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 6 — Materials**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 7 — Camera Placement

**Apps involved:** Claude + Blender.
**Captures:** `07-camera-claude.mkv`, `07-camera-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender, `obs-set-current-scene("BLENDER")`.

Blender work: camera objects, focal length, hero and test camera positions,
single hero-camera still render for review.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 7 — Camera**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 8 — Lighting

**Apps involved:** Claude + Blender.
**Captures:** `08-lighting-claude.mkv`, `08-lighting-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before Blender, `obs-set-current-scene("BLENDER")`.

Blender work: HDRI node setup, rotation, gamma correction, strength, fire light,
compass test renders after each lighting adjustment.

→ **OBS ACTION:** Complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 8 — Lighting**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 9 — Animation

**Apps involved:** Claude + Blender.
**Captures:** `09-animation-claude.mkv`, `09-animation-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

Claude explains 100° arc, 8-second duration, smoothstep easing, per-frame keyframes.

→ **OBS ACTION:** Before Blender, `obs-set-current-scene("BLENDER")`.

Blender work: camera sweep object, 193 keyframes, Workbench preview render,
Cycles test frames at every 10th frame, MP4 encoding.

→ **OBS ACTION:** Preview complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 9 — Animation Preview**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 10 — Test Rendering

**Apps involved:** Claude + Blender.
**Captures:** `10-test_render-claude.mkv`, `10-test_render-blender.mkv`

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before rendering, `obs-set-current-scene("BLENDER")`.

Blender work: half-resolution Cycles stills, full animation at half resolution,
depth map pass, segmentation mask pass, MP4 encoding.
Stay on BLENDER for the full duration of every active render.

→ **OBS ACTION:** All test renders complete. `obs-set-current-scene("CLAUDE")`.

**▶ REVIEW GATE 10 — Test Renders**

→ **OBS ACTION:** Gate cleared. `obs-stop-record`. Rename. Confirm.

---

### Phase 11 — Final Rendering

**Apps involved:** Claude (setup) + Blender (render) + ComfyUI in Chrome (post).
**Captures:**
- `11-final_render-claude.mkv` — Claude setting up and describing the render
- `11-final_render-blender.mkv` — Blender executing the full Cycles render
- `11-final_render-comfyui.mkv` — ComfyUI post-processing workflow in Chrome

#### Step A — Render Setup (Claude)

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.
Confirm: "Recording started — `11-final_render-claude`."

Claude describes the full-resolution render settings, passes, and output structure.

→ **OBS ACTION:** Before launching the render, `obs-stop-record`.
Rename to `11-final_render-claude.mkv`. Confirm.

#### Step B — Full Cycles Render (Blender)

Note: During an extended GPU render, the Claude window is idle. Only Blender
needs to be captured.

→ **OBS ACTION:** Verify BLENDER source (screenshot check) immediately before
launching the render. Then `obs-set-current-scene("BLENDER")` → `obs-start-record`.
Confirm: "Recording started — `11-final_render-blender`."

Blender work: full 1920×1080 Cycles animation, depth maps, segmentation masks,
MP4 encoding. Stay on BLENDER for the full duration of every render.

→ **OBS ACTION:** All Blender renders complete. `obs-stop-record`.
Rename to `11-final_render-blender.mkv`. Confirm.

#### Step C — ComfyUI Post-Processing (Chrome)

→ **OBS ACTION:** Before opening Chrome/ComfyUI, verify the COMFYUI source
(screenshot check). If ComfyUI is not yet running, confirm the source shows
an empty or loading Chrome tab, then proceed to launch ComfyUI. Once the
ComfyUI node graph is visible in the browser, take a second verification
screenshot to confirm the source is now correct.

Then `obs-set-current-scene("COMFYUI")` → `obs-start-record`.
Confirm: "Recording started — `11-final_render-comfyui`."

ComfyUI workflow in Chrome (controlled via Claude in Chrome MCP):
- Load the post-processing workflow (upscaling, style transfer, or compositing)
- Connect the Blender output frames as input
- Run the workflow — nodes executing progressively in the graph are visible
- Monitor completion via Chrome MCP DOM inspection
- Export processed frames

The node graph updating, progress indicators filling, and preview images
appearing in the ComfyUI interface are the key footage in this clip.

→ **OBS ACTION:** ComfyUI workflow complete. `obs-stop-record`.
Rename to `11-final_render-comfyui.mkv`. Confirm.

**▶ FINAL REVIEW — Delivery**

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

Claude presents the final MP4, processed output, and delivery summary.

→ **OBS ACTION:** User confirms delivery is complete. `obs-stop-record`.
This final clip can be named `11-delivery-claude.mkv` if worth preserving.

---

## Checkpoint Saves — Gate Protocol

At the approval of **every review gate**, immediately save timestamped checkpoints
for every scene file that was modified during that phase. Do not wait until the end
of the project — save at every gate without exception.

### What to save at each gate

| Modified in phase | Save as |
|---|---|
| Rhino scene | `base_model_checkpoint_YYYYMMDD_HHMM.3dm` in `rhino/snapshots/` |
| Blender scene | `base_model_checkpoint_YYYYMMDD_HHMM.blend` in project root |
| Both | Save both — always save both if either was touched |

### Save command sequence (gate approval)

1. User says the gate is cleared.
2. → **OBS ACTION:** Stop recording and rename capture files (as described per phase).
3. Save Blender checkpoint:
   ```python
   import bpy, datetime
   stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
   bpy.ops.wm.save_as_mainfile(
       filepath=f"[PROJECT_ROOT]/base_model_checkpoint_{stamp}.blend", copy=True)
   bpy.ops.wm.save_as_mainfile(filepath="[PROJECT_ROOT]/base_model.blend")
   ```
4. Save Rhino checkpoint (via RhinoMCP):
   ```csharp
   string stamp = DateTime.Now.ToString("yyyyMMdd_HHmm");
   doc.WriteFile($@"[PROJECT_ROOT]\rhino\snapshots\base_model_checkpoint_{stamp}.3dm",
       new Rhino.FileIO.FileWriteOptions());
   ```
5. Confirm both filenames to the user before moving to the next phase.

The checkpoint files are the recovery mechanism if anything goes wrong. They are
also the source material for pickup shots — the video team can reload any phase
checkpoint and render additional angles not captured during the original session.

---

## Project Versioning & File Structure

Each new house or iteration of the demo gets its own dedicated folder under
`aa_demo_versions`. The master project assets at `aec_demo_master/` — skills,
prompts, HDRI library, scripts — are the **source of truth and shared reference**.
The iteration folder is where **everything created for that specific scene** lives.

### Root paths
```
Root:    C:\Users\swags\Documents\aec_demo_master\
Subroot: C:\Users\swags\Documents\aec_demo_master\aa_demo_versions\
Project: C:\Users\swags\Documents\aec_demo_master\aa_demo_versions\[project_name]\
```

`[project_name]` is a short, lowercase, underscore-separated identifier with a
version suffix. Examples: `hillside_house_01`, `beach_cottage_02`, `urban_townhouse_01`.
Never use spaces or special characters.

### Per-project folder structure

```
aa_demo_versions/
  [project_name]/
    blender_assets/        ← Blender scene files and checkpoints for this project
    rhino_assets/          ← Rhino scene files and checkpoints for this project
    renders/               ← Full-quality Cycles render sequences (PNG, EXR)
    test_renders/          ← Half/quarter-res test renders and compass stills
    hdr/                   ← HDRI files used by this project
    comfy_source/          ← ComfyUI workflow files (.json) for this project
    comfy_output/          ← Processed frames output from ComfyUI
    demo_captures/         ← OBS 4K screen recordings (all .mkv files)
    video_source/          ← Source video clips assembled for editing
    video_edits/           ← Video editing project files (DaVinci, Premiere, etc.)
    scripts/               ← Python scripts written or modified for this project
    skills/                ← Project-specific skill files (additions or overrides)
    prompts/               ← Project-specific prompt modifications (see below)
```

### Prompt inheritance model

The master prompts at `aec_demo_master/master_prompts/` define the general workflow
and are never modified for a specific project. Instead:

- The `[project_name]/prompts/` folder holds **delta documents** — additions,
  overrides, and design-specific notes that apply only to this iteration.
- These might include: a specific material palette, a different site orientation,
  revised entourage instructions, custom camera paths, or ComfyUI workflow notes.
- When Claude reads the prompt at the start of a session, it reads the master prompt
  first, then reads any documents in `[project_name]/prompts/` and applies them as
  modifications on top. The project-level prompts win over the master where they conflict.
- This means a new design can be started by writing a short delta prompt (one or two
  pages describing what is different) rather than rewriting the entire master brief.

Example delta prompt filename: `[project_name]/prompts/01_site_and_massing_notes.md`

### What lives at master level vs. project level

| Asset type | Master (`aec_demo_master/`) | Project (`aa_demo_versions/[project_name]/`) |
|---|---|---|
| Prompt documents | `master_prompts/` — canonical, never edited per-project | `prompts/` — delta modifications only |
| Skills | `skills/` — reusable across all projects | `skills/` — project-specific additions or overrides |
| HDRI library | `assets/` or `hdr/` — shared library | `hdr/` — HDRIs actually used in this project |
| Python scripts | `scripts/` — shared utility scripts | `scripts/` — scripts written or modified for this project |
| Blender files | `base_model.blend` — current working file | `blender_assets/` — all .blend files for this project |
| Rhino files | `rhino/` — current working files | `rhino_assets/` — all .3dm files for this project |
| Renders | `renders/` — current project renders | `renders/` + `test_renders/` — all render output for this project |
| OBS captures | — | `demo_captures/` — all capture files for this project |
| ComfyUI | — | `comfy_source/` + `comfy_output/` |
| Video | — | `video_source/` + `video_edits/` |

### Project setup procedure

At the start of every new project, before any modelling begins:

1. Confirm the project name with the user (e.g. `hillside_house_01`).
2. Create the full folder tree above under `aa_demo_versions/[project_name]/`.
3. Ask the user if there are any design differences from the master prompt that
   should be captured in a delta document. If yes, create
   `[project_name]/prompts/01_delta_notes.md` and document them before proceeding.
4. Copy any HDRI files needed for this project into `[project_name]/hdr/`.
5. Set Blender render output paths to `[project_name]/renders/` and
   `[project_name]/test_renders/`.
6. Set OBS output path to `[project_name]/demo_captures/`.
7. Confirm the folder structure to the user before starting Phase 0.

---

## Capture Folder Structure

All OBS recordings for a project go in `[project_name]/demo_captures/`:

```
demo_captures/
  00-project_setup-claude.mkv
  01-site_prep-claude.mkv
  01-site_prep-rhino.mkv
  02-massing-claude.mkv
  02-massing-rhino.mkv
  03-detailing-claude.mkv
  03-detailing-rhino.mkv
  04-landscaping-claude.mkv
  04-landscaping-blender.mkv
  05-entourage-claude.mkv
  05-entourage-blender.mkv
  06-materials-claude.mkv
  06-materials-blender.mkv
  07-camera-claude.mkv
  07-camera-blender.mkv
  08-lighting-claude.mkv
  08-lighting-blender.mkv
  09-animation-claude.mkv
  09-animation-blender.mkv
  10-test_render-claude.mkv
  10-test_render-blender.mkv
  11-final_render-claude.mkv
  11-final_render-blender.mkv
  11-final_render-comfyui.mkv
  11-delivery-claude.mkv         ← optional
```

Total expected captures: approximately 24 files.

---

## OBS MCP Tool Reference

| Action | OBS MCP Tool | Key Parameters |
|---|---|---|
| Switch active scene | `obs-set-current-scene` | `scene-name`: "CLAUDE" / "RHINO" / "BLENDER" / "COMFYUI" |
| Start recording | `obs-start-record` | none |
| Stop recording | `obs-stop-record` | none |
| Check recording status | `obs-get-record-status` | none |
| Get current scene | `obs-get-current-scene` | none |
| Set output folder | `obs-set-record-directory` | `record-directory`: path |
| List all sources | `obs-get-input-list` | none |
| **Screenshot a source** | **`obs-get-source-screenshot`** | `source-name`, `image-format`: "png", `image-width`, `image-height` |
| Get source properties | `obs-open-input-properties` | `input-name` — opens the OBS properties dialog for a source; useful for confirming which window is assigned |

**Startup verification sequence (every session):**
1. `obs-get-input-list` → confirm all four sources exist
2. For each source: `obs-set-current-scene` then `obs-get-source-screenshot` → evaluate image
3. Report pass/fail for each source before any recording begins
4. Re-verify any source before its first use in each phase

---

## Notes for the Video Team

- Every MKV file = one application, one phase. Filename tells you both without watching.
- **CLAUDE** clips: AI conversation, reasoning, code output. Use as narrator/commentary.
- **RHINO** clips: Live 3D geometry construction from commands. Technical B-roll.
- **BLENDER** clips: Materials, renders in progress, animation. Most cinematic footage.
- **COMFYUI** clips: AI post-processing node graph executing. Shows the full AI pipeline.
- Checkpoint `.blend` files allow re-opening any phase for additional pickup shots.
- All files are 4K / 30fps / no audio. Add narration or music in post.
- The source verification screenshots (taken at session startup) are not recorded
  to MKV — they are evaluated in memory by Claude only.

---

*End of demo capture prompt v1.2.*
*Saved as `02_demo_prompt.md` in `master_prompts/`.*
*This document is read and acted on by Claude — not just stored for human reference.*
