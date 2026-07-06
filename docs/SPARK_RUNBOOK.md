# DGX Spark Demo Runbook

This is the concise operating path for the delivered cliff-house bundle on
DGX Spark. It uses FreeCAD instead of Rhino, isolated Blender 5.1 on ARM64,
and isolated ComfyUI with the exact Flux.2 Klein graph.

## One-time installation

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/install-portable-runtime.sh
```

The installers are idempotent. Heavy runtimes and model files stay under
`runtime/` and remain outside Git. The Comfy installer pins ComfyUI and all
required custom-node commits, excludes only the unavailable optional ARM64
`onnxruntime-gpu` wheel, and verifies all three production model checksums.

## Prompt profile

There was no upstream file literally named `prompt_profile.md`. The complete,
populated design brief is `prompts/master_workflow/01_user_prompt.md`.
This port wraps it in the approved no-interview preset:

`profiles/delivered_cliff_house_demo/prompt_profile.md`

The delivered profile is already fully populated. For this standard demo, do
not create a project copy and do not run the profile-generation commands.
The launcher validates the supplied profile automatically.

For diagnostics only, its validation command is:

```bash
python3 scripts/prompt_profile.py validate \
  profiles/delivered_cliff_house_demo/prompt_profile.md
```

Begin a Hermes session with the exact opening instruction stored in section 9
of the approved profile. Hermes should not repeat the design interview for the
delivered preset.

## Start and verify

Close any older Blender or ComfyUI instance using ports 9876 or 8188, then run:

```bash
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
```

The required healthy state is:

```text
FREECAD_MCP=healthy
BLENDER_MCP=healthy ... version=5.1.0
COMFYUI=healthy
FLUX_MODELS_MISSING=0
WORKFLOW_NODES_MISSING=0
PORTABLE_STACK_OK
```

The controller rejects an old Blender 4.x server already occupying port 9876.
Blender MCP starts automatically; no sidebar click is required.

## Open Hermes and enter the prompt

Hermes runs as an interactive chat in a terminal. From the repository root,
run:

```bash
./scripts/start-hermes-demo.sh
```

This safely starts any missing demo services and then opens the Hermes chat.
The terminal displaying the Hermes prompt is where you type or paste all demo
instructions. Keep it open throughout the demonstration. The launcher defaults
to the local `qwen3.6:latest` model, a 30-iteration safety limit, and preloads
the checked portable Phase 2 and Phase 3 skills.

At the Hermes prompt, paste this exact opening instruction:

```text
Load the delivered_cliff_house_demo prompt profile and obey AGENTS.md. Perform
read-only source validation, preflight, and status checks. Summarize the
accepted design intent in five bullets, identify the next phase, and explain
what that phase will visibly do. Do not begin or execute the phase, do not
launch Rhino or OBS, and do not generate an approval on my behalf. Stop with
the WAITING_FOR_HUMAN_APPROVAL marker. Do not restart the design interview.
```

Hermes must now stop without changing FreeCAD, Blender, ComfyUI, or project
files. The read-only audit is canonical Phase 1, so confirm that its final line
is:

```text
WAITING_FOR_HUMAN_APPROVAL phase=2 name=site_preparation
```

Only after it displays that marker and its proposed phase is correct, return
to the same Hermes terminal and type:

```text
Approved — proceed to the next phase.
```

Do not paste several approvals at once. Each approval advances exactly one
phase and is consumed immediately. Hermes must never print or supply this
approval for you. After completing the phase, it must stop at the next review
gate before another approval.

For Phase 2, Hermes must run the checked portable adapter rather than writing
FreeCAD code. Its terminal output must contain all four markers:

```text
PORTABLE_RHINO_EXTRACT_OK
PORTABLE_FREECAD_REFERENCE_OK
PORTABLE_SITE_BUILD_OK
PORTABLE_SITE_PREPARATION_OK
```

The active FreeCAD document should show a source-derived green terrain, yellow
lot boundary, and four site pads. Hermes must then stop with:

```text
PHASE_REVIEW_REQUIRED phase=2 name=site_preparation
```

After inspecting and approving the Phase 2 site, one new approval authorizes
Phase 3. Hermes must use the checked target-massing adapter and report:

```text
PORTABLE_MASSING_TARGET_OK
PORTABLE_MASSING_BUILD_OK
PORTABLE_MASSING_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=3 name=building_massing
```

The Phase 3 FreeCAD view contains 11 massing solids plus six read-only links to
the approved site context.

After inspecting and approving Phase 3, one new approval authorizes Phase 4.
Hermes must use the checked target-detailing adapter and report:

```text
PORTABLE_DETAILING_TARGET_OK
PORTABLE_DETAILING_OVERLAP_OK
PORTABLE_DETAILING_BUILD_OK
PORTABLE_DETAILING_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=4 name=architectural_detailing
```

The result contains 109 target-derived FreeCAD detail objects covering slabs,
walls, glazing, mullions, frames, doors, and railings.

After inspecting and approving Phase 4, one new approval authorizes Phase 5.
Hermes validates the saved FreeCAD reconstruction and creates a separate
Blender landscaping checkpoint without overwriting the delivered target:

```text
PORTABLE_LANDSCAPING_FREECAD_OK
PORTABLE_LANDSCAPING_TARGET_OK
PORTABLE_LANDSCAPING_BUILD_OK
PORTABLE_LANDSCAPING_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=5 name=landscaping_site_context
```

The checkpoint organizes and verifies 15 delivered site elements across
drainage, site edges, dark hardscape, patio/pool deck, pool basin, and pool
water.

After inspecting and approving Phase 5, one new approval authorizes Phase 6.
Hermes creates a separate deterministic outdoor-living checkpoint:

```text
PORTABLE_ENTOURAGE_INPUT_OK
PORTABLE_ENTOURAGE_BUILD_OK
PORTABLE_ENTOURAGE_LAYOUT_OK
PORTABLE_ENTOURAGE_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=6 name=entourage_outdoor_living
```

The checkpoint contains ten procedural objects: two pool loungers, one side
table, one firepit, one dining table, two dining chairs, two entry planters,
and one driveway vehicle. The layout gate requires all ten items to be inside
the established camera, with no item-to-item or pool-volume overlaps.

After inspecting and approving Phase 6, one new approval authorizes Phase 7.
Hermes preserves the delivered shaders, finalizes entourage materials, and
completes segmentation metadata in a separate checkpoint:

```text
PORTABLE_MATERIALS_INPUT_OK
PORTABLE_MATERIALS_ASSIGNMENT_OK
PORTABLE_MATERIALS_SHADER_OK
PORTABLE_MATERIALS_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=7 name=materials
```

The materials gate requires 160 materialized and tagged meshes, 150 preserved
source meshes, ten finalized entourage meshes, and valid delivered clear,
frosted, and pale-blue glass shaders. It does not replace the authoritative
building/site palette from prose.

After inspecting and approving Phase 7, one new approval authorizes Phase 8.
Hermes preserves the delivered camera composition and adds named utility cameras:

```text
PORTABLE_CAMERA_INPUT_OK
PORTABLE_CAMERA_BUILD_OK
PORTABLE_CAMERA_FRAMING_OK
PORTABLE_CAMERA_PREVIEW_OK
PORTABLE_CAMERA_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=8 name=camera_placement
```

The camera gate validates the delivered 20.5mm `Camera_day` composition, creates
`ocean_view`, `compass_cam`, and `patio_sweep_cam`, confirms four framing anchors,
and saves a viewport review image. The delivered framing overrides the prompt's
adjustable 28mm starting value.

Do not approve Phase 9 until its checked portable adapter has been added;
Hermes must report `BLOCKED_MISSING_CHECKED_ADAPTER` instead of guessing.

## Fast recorded integration proof

This command stages the supplied 1024 x 1024 beauty and segmentation passes,
asks Blender through Blender MCP to submit the workflow, waits for ComfyUI,
and fails unless exactly three images are produced:

```bash
./scripts/run-comfy-demo.py --sample-inputs
```

Expected outputs are:

- `Make_Real`
- `Change_Environment`
- `Time_Of_Day`

For a live render from the open Blender scene before submission:

```bash
./scripts/run-comfy-demo.py --render
```

That path is slower because Blender renders fresh segmentation and beauty
passes first. Generated images are written to `runtime/comfyui/output/`.

## Stop

```bash
./scripts/stop-portable-demo.sh
```

The controller stops only Blender and ComfyUI processes that it started.
FreeCAD remains a shared service and is intentionally left running.

## Validated baseline

On 2026-07-06 the Spark opened both delivered Blender scenes, served the full
textured scene through Blender MCP, registered all 12 workflow node classes,
loaded the checksum-verified 9B KV-FP8 model, and produced all three 1024 x
1024 outputs. The community Spark build reports Blender 5.1.0; the supplied
scenes report a newer 5.1 patch-level writer warning but opened successfully.
