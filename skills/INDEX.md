# Skills INDEX — aec_demo_master

**This is the entry point.** Claude reads this file at the start of any
session on this project before doing other work. The index points to
the right skill based on the task at hand.

The project is the aec_demo_master demo — an architectural visualization
pipeline from brief + reference images + base Rhino through Blender
render and optional ComfyUI post-processing. The deliverable is a demo
that runs end-to-end with minimal human intervention, suitable to show
stakeholders.

---

## Operating rules

1. **Read this INDEX first.** Before any task on this project.
2. **MCP health check before any work.** At session start, ping every
   required MCP server (Rhino, Blender, OBS, ComfyUI). Report what's
   up/down. If any required server is down, notify Sean to restart it —
   do not work around or fail silently.
3. **Then view the specific skill(s)** relevant to the task — don't try
   to remember them.
4. **Skills are the source of truth.** If memory, the procedural doc,
   or a phase prompt disagrees with a skill file, the skill file wins.
5. **Update this INDEX whenever a skill is added or refined.** No
   orphan skills.

---

## After reading this INDEX, read `session_state.md`

Captures the current state of the project: what's been decided, what's
pending, and the conversation arc. After session_state.md you'll know
exactly where to pick up.

---

## Pipeline overview (the demo's end-to-end flow)

See `docs/procedural_doc.md` for the full specification. Short form:

```
[0] Session start: MCP health + read user_prompt
    |
    v
[1] Reference interpretation: brief + reference images → design intent
    |
    v
[2] Site prep (Phase 1)  →  base_model.3dm  →  Rhino MCP construction
    |
    v
[3] Massing (Phase 2) + Detailing (Phase 3): Rhino MCP construction
    |
    v
[4] Iterative changes if any (Phase 0 iterative-changes rules)
    |
    v
[5] Export to Blender (Phase 4): pre-validate → snapshot → import → validate
    |
    v
[6] 3D Render (Phase 5 §1): camera, passes, PNG seq, ffmpeg → MP4
    |
    v
[7] (Optional, deferred) ComfyUI enhancement (Phase 5 §2)
```

---

## Skills catalog — EXISTING

### Reference & philosophy

| Skill                    | When to read                                                                | File                          |
|--------------------------|-----------------------------------------------------------------------------|-------------------------------|
| Architectural pipeline   | Starting any new task on this project; recall the full workflow             | `architectural_pipeline.md`   |
| Rhino modeling discipline| Advise on or audit Rhino construction; recognize anti-patterns              | `rhino_modeling_skill.md`     |
| Rhino pre-export checklist | Final-gate items before .3dm handoff to Blender                           | `rhino_prep_skill.md`         |

### Rhino-side tools (Python scripts run INSIDE Rhino)

| Skill                  | When to invoke                                                       | File                         |
|------------------------|----------------------------------------------------------------------|------------------------------|
| Active-document audit  | During modeling; reports coplanar/duplicates/missing metadata        | `audit_active_document.py`   |
| Pre-export validation  | Immediately before File > Export to Blender (Phase 4 gate)           | `pre_export_validate.py`     |

### Blender-side tools (run by Claude in Blender)

| Skill                       | When to invoke                                              | File                         |
|-----------------------------|-------------------------------------------------------------|------------------------------|
| Coplanar detector           | After .3dm import; before render; after geometry edits      | `coplanar_detector.py`       |
| Import .3dm with metadata   | First step of Phase 4 inside Blender                        | `import_with_metadata.py`    |
| Validate scene              | Phase 4 post-import gate; refuses to proceed on critical    | `validate_blender_scene.py`  |
| Derive-geometry helpers     | Modifying geometry in Blender — extract refs, build clean   | `derive_geometry.py`         |

---

## Skills catalog — PENDING (to be built before the demo)

These are the new skills the demo requires. Each will be built and
listed above once complete.

| Pending skill                          | Stage  | What it needs to do                                                                                                                            |
|----------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------|
| MCP health check + restart-notify      | [all]  | At session start, ping Rhino/Blender/OBS/(ComfyUI) MCPs. Report status. If down mid-session, notify Sean — don't work around.                  |
| Reference interpretation               | [1]    | Read image library + brief → architectural intent (style, materials, proportions, mood). Outputs a structured `docs/design_intent.md`.         |
| Rhino construction via MCP             | [2]    | Given design intent + base Rhino → built model with metadata. Applies derive-don't-redraw discipline from `rhino_modeling_skill.md`.           |
| Iterative change loop via Rhino MCP    | [4]    | User says "wider patio" → agent locates patio, derives new geometry from existing snaps, updates Rhino model via MCP, re-audits. Loop logged.  |
| OBS recording orchestration            | [all]  | Control OBS via MCP. Start/stop recording per segment per `demo_rules.md`. Handle segment boundaries cleanly.                                  |
| Materials library (metadata → Blender) | [6]    | For each metadata `material` value, produce the right Blender material setup: shader nodes, textures, scale, finish. Single library lookup.    |
| Render pass configuration              | [6]    | Beyond beauty + depth — normal, AO, mist, ID maps for compositing flexibility (full version; v1 demo uses beauty + depth only).                |
| ComfyUI integration                    | [7]    | Submit rendered frames + depth maps to ComfyUI HTTP API via MCP; retrieve enhanced output; integrate into final deliverable. Deferred.         |

---

## Open questions

- **Q2: ComfyUI endpoint and workflow.** URL, workflow JSON path, model checkpoints loaded, the stylization strength. Deferred until the ComfyUI MCP is connected.
- **Q5: Scripted change for the iteration phase.** What does Sean ask the agent to change? Suggested default: "widen the patio 1 m on the west" since it exercises derive-don't-redraw. Decide at Stage 6 dry-run.
- **Q6: Reference-interpretation skill technique.** Vision pass, structured tag extraction, or hand-curated tag files? Design when that skill is written.
- **Q7: Render quality tier for the demo.** Cycles 256 samples (~10 min total) vs 1024 samples (slow). Decide once Phases 1–4 are timed end-to-end.

---

## Triggers — when each skill activates

- **"audit" / "z-fight" / "coplanar"** → `coplanar_detector.py` (Blender) or `audit_active_document.py` (Rhino)
- **"export" / "Rhino → Blender" / "Phase 4"** → `pre_export_validate.py` → snapshot → `import_with_metadata.py` → `validate_blender_scene.py`
- **"new geometry" / "modify object"** → `derive_geometry.py`
- **"material" / "texture" / "looks wrong"** → check `architectural_pipeline.md` metadata conventions; read object custom_props; (eventually) materials-library skill
- **"render" / "encode" / "MP4"** → `Prompts/phase_5_render.txt` §1
- **"Rhino discipline" / "modeling correctly"** → `rhino_modeling_skill.md`
- **"interpret brief" / "what does this image mean for design"** → (reference-interpretation skill, to be built)
- **"user wants a change"** → (change-loop skill, to be built; orchestration in `phase_0_config.txt` Iterative changes section)
- **"send to ComfyUI"** → (ComfyUI integration skill, to be built; spec in `phase_5_render.txt` §2)

---

*Last updated: 2026-05-12. Architecture: MCP-controlled (Rhino, Blender,
OBS, eventually ComfyUI). 9 existing skills, 8 pending. Project rooted at
`{AEC_DEMO_ROOT}`.*

- **"send to ComfyUI" / "AI render" / "Execute"** → `Prompts/phase_8_blender_comfyui.txt`
- **"ControlNet" / "SDXL" / "canny"** → `Prompts/phase_8_blender_comfyui.txt`

---

## Phase 8 — Blender-to-ComfyUI Live Rendering (COMPLETE)

Phase 8 is fully built and operational. See `Prompts/phase_8_blender_comfyui.txt`
for the complete specification. Key facts:

- **Local ComfyUI** at 127.0.0.1:8188 (not DGX Spark)
- **SDXL base 1.0** + **ControlNet Canny SDXL** — preserves building geometry
- **auto_comfy.py** startup script handles all connection and render automation
- **Execute button** in Blender fires Cycles render → ComfyUI → Image Editor
- **Fidelity slider**: ControlNet strength (0.85–0.95) + KSampler denoise (0.45–0.65)
- Active scene: `blender/base_model_comfy_master_04.blend`
- Current look: polished white travertine, dark reflective glass, desert sunset,
  warm interior glow, citrus_orchard_road HDR at 0.08 strength

---

*Last updated: 2026-05-16. Architecture: MCP-controlled (Rhino, Blender,
OBS, ComfyUI local). Phases 0-8 complete. Project rooted at
`{AEC_DEMO_ROOT}`.*


