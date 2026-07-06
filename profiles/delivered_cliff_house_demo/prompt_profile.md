# Prompt Profile — Delivered Cliff House Demo

profile_format: aec-demo-prompt-profile-v1
profile_id: delivered_cliff_house_demo
status: approved_for_demo
approval_policy: supplied defaults are approved; do not repeat the interview

## 1. Purpose

Reproduce the delivered contemporary coastal cliff-house demonstration using
the complete bundle. The live agent should explain each phase briefly, operate
through checked tools/scripts, show the result at review gates, and avoid a
long design interview during the recorded run.

## 2. Authoritative instructions

Read these files in order:

1. `HERMES.md` — local safety, runtime, and integrity rules.
2. `prompts/master_workflow/01_user_prompt.md` — complete architectural brief.
3. `prompts/system_prompts/00_session_startup.md` — session protocol.
4. `prompts/system_prompts/00b_rhino_scene_protocol.md` — original CAD-scene rules.
5. `prompts/system_prompts/00c_references_protocol.md` — reference policy.
6. The matching phase prompt under `prompts/master_workflow/` before each phase.

The `[adjustable]` annotations in `01_user_prompt.md` describe customization
points. They are not unanswered fields. For this preset, use the stated value
immediately preceding each annotation as the approved answer.

## 3. Project identity

- Project: contemporary hillside residence, ocean-view/outdoor-living edition.
- Demonstration profile: delivered_cliff_house_demo.
- Setting: remote Southern California coastal cliff near Santa Barbara.
- Primary view: west toward the ocean and rugged coastline.
- Architectural language: strong horizontal modernism, broad cantilevers,
  extensive view-facing glass, dark metal frames, warm wood, pale stone or
  concrete terraces, and an infinity pool.
- Presentation goal: photoreal architectural visualization with consistent
  geometry across beauty, depth, segmentation, and AI-transformed outputs.

## 4. Authoritative assets

- Starting CAD template:
  `sample_project/rhino_assets/beach_house_02.3dm`
  (Rhino 8, metres, 10 layers, 11 source curves, no finished solids).
- Canonical finished visual target:
  `sample_project/blender_assets/cliff_house_act2_textured_v3.blend`.
- Lightweight validation target:
  `sample_project/blender_assets/cliff_house_v17.blend`.
- Sun-study scene:
  `sample_project/blender_assets/cliff_house_act3_sunstudy.blend`.
- Reference passes: `sample_project/renders/beauty`, `depth`, and `seg`.
- ComfyUI execution graph:
  `comfyui/workflows/AEC_last_submitted_workflow.json`.
- ComfyUI editable graph:
  `comfyui/workflows/AEC_Transform_Pipeline.json`.

The Blender scene is the authoritative finished appearance. The Rhino file is
only the original curve template; do not claim it contains finished
construction history.

## 5. Spark tool mapping

- Agent: Hermes with the local tool-capable model, replacing Claude Desktop.
- CAD: FreeCAD + FreeCAD MCP on localhost:9875, replacing Rhino for the Spark
  reconstruction track.
- Visualization: isolated Blender 5.1+ + Blender MCP on localhost:9876.
- Generation: isolated ComfyUI + Flux.2 Klein on localhost:8188.
- Recording: OBS is optional and never blocks geometry/render validation.

Preserve original Rhino instructions as design evidence. Translate operations
to checked FreeCAD builders; never execute RhinoCommon code inside FreeCAD.

## 6. Approved phase sequence

1. Configuration and source audit.
2. Site preparation from the supplied curve template.
3. Building massing.
4. Architectural detailing and glazing.
5. Landscaping/site context.
6. Entourage and outdoor-living elements.
7. Materials.
8. Camera placement.
9. Lighting.
10. Optional animation/sun study.
11. Test beauty/depth/segmentation renders.
12. Final Blender-to-ComfyUI transformation.

Use a fresh Hermes session at major application boundaries when helpful, but
preserve this profile and the checked project state. A user response of
`Approved — proceed to the next phase` authorizes exactly one next phase.

## 7. Rendering and ComfyUI defaults

- Render resolution: 1024 × 1024 for the AI pipeline unless the phase prompt
  requests a lower-cost test.
- Beauty: Cycles GPU with denoising.
- Depth: aligned structural depth, validated as nonblank.
- Segmentation: exact palette and material tags defined by the supplied scripts.
- Make Real: preserve camera, building position, walls, slabs, windows, deck,
  pool, and terrace edges.
- Environment: isolated Southern California cliff, coastline and ocean; no
  neighboring buildings, roads, people, or invented architecture.
- Time of Day: early dusk with restrained warm interior light; change lighting
  and sky only.

ComfyUI may alter appearance, atmosphere, planting, and lighting. It must not
be used as evidence that CAD geometry is correct.

## 8. Review and success gates

- Preflight: `scripts/preflight-portable-demo.sh` returns
  `PORTABLE_PREFLIGHT_OK`.
- Blender: compatible 5.1+ runtime opens the copied lightweight scene first,
  then the canonical scene; Blender MCP confirms the active file and camera.
- ComfyUI: every required class is registered and every required model path
  exists before graph submission.
- Render passes: beauty, depth, and segmentation have matching dimensions,
  are nonblank, and preserve framing.
- Final generation: all three expected branches produce valid images.
- CAD parity: any FreeCAD reconstruction is clearly labeled as reconstruction,
  not recovered Rhino construction history.

## 9. Recorded-demo opening instruction

Use this exact instruction to begin without an interview:

```text
Load the delivered_cliff_house_demo prompt profile. Validate its sources and
runtime gates, summarize the approved design intent in five bullets, and begin
the next uncompleted phase using the checked workflow. Stop at the phase review
gate and report the success markers. Do not restart the design interview.
```
