# DGX Spark Demo Runbook

This is the concise operating path for the delivered cliff-house bundle on
DGX Spark. It uses FreeCAD instead of Rhino, isolated Blender 5.1 on ARM64,
and isolated ComfyUI with the exact Flux.2 Klein graph.

## One-time installation

For a fresh Git clone, first download, verify, and extract the non-Git payload
using the Google Drive or SCP instructions in
[DGX_SPARK_PORT.md](DGX_SPARK_PORT.md#google-drive-download).

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
The launcher explicitly enables Python auto-execution for the trusted delivered
scene so embedded scripts and drivers do not trigger an interactive warning.
Do not use this launcher for untrusted `.blend` files.

After a reboot, `restart-portable-demo.sh` is sufficient to restore the whole
stack. The mode launchers below also start any missing service idempotently, so
running `restart` first is recommended for a clean presentation but is not
required twice.

If a power loss left FreeCAD crash-recovery state, the stack launcher moves it
to `runtime/freecad-recovery-archive/` before starting FreeCAD. This prevents a
modal Document Recovery window from blocking MCP; nothing is deleted.

## Choose the demo mode

### Human-gated Hermes walkthrough

Use this when presenting the reasoning and reviewing every phase:

```bash
./scripts/start-portable-manual-demo.sh
```

This is an explicit alias for `start-hermes-demo.sh`. It opens Hermes and
retains the one-human-approval-per-phase policy in `AGENTS.md`. Nothing is
approved automatically.

### Unattended continuous playback

Use this for a kiosk or an all-day looping display:

```bash
./scripts/start-portable-auto-demo.sh
```

To launch playback in a separate large terminal and continuously watch its
phase markers:

```bash
./scripts/start-portable-auto-terminal.sh
```

The monitor terminal shows the deterministic checked-adapter output. It is not
a Hermes chat and does not imply agent-generated approval. Use the manual mode
when the audience should see Hermes reason, prepare a phase, and wait for a
human approval.

This mode does not launch Hermes and does not manufacture approvals. The
operator's launch directly runs the same checked Phase 2-12 adapters, resetting
Blender to the delivered source before each cycle. By default it pauses five
seconds after each phase, keeps the final images visible for 60 seconds, and
retains the latest twelve timestamped three-image sets.

Stop the loop with `Ctrl+C`; Blender, FreeCAD, and ComfyUI stay available.
`./scripts/stop-portable-demo.sh` stops Blender and ComfyUI; FreeCAD is shared and can be closed from its GUI.

Useful one-time rehearsal and timing overrides:

```bash
python3 scripts/run-portable-demo-loop.py --cycles 1 --phase-delay 0
AEC_AUTO_PHASE_DELAY=10 AEC_AUTO_CYCLE_DELAY=120 \
  ./scripts/start-portable-auto-demo.sh
```

The loop retries after transient service failures, refuses to run two copies at
once, and emits `AUTOPLAY_PHASE_*` and `AUTOPLAY_CYCLE_*` markers in its
terminal.

## Manual mode: open Hermes and enter the prompt

Hermes runs as an interactive chat in a terminal. From the repository root,
run:

```bash
./scripts/start-portable-manual-demo.sh
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
Hermes preserves the delivered camera composition and builds a checked wider
three-quarter hero plus named utility cameras:

```text
PORTABLE_CAMERA_INPUT_OK
PORTABLE_CAMERA_BUILD_OK
PORTABLE_CAMERA_FRAMING_OK
PORTABLE_CAMERA_PREVIEW_OK
PORTABLE_CAMERA_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=8 name=camera_placement
```

The camera gate validates and preserves the delivered 20.5mm `Camera_day`.
It creates a slightly elevated 28mm southwest exterior three-quarter
`ocean_view`, plus `compass_cam` and `patio_sweep_cam`; confirms four framing
anchors; and saves a viewport review image. The exterior-side rule rejects
north-side courtyard or interior compositions.

After inspecting and approving Phase 8, one new approval authorizes Phase 9.
Hermes builds a clean bundled-HDRI world and four compass previews:

```text
PORTABLE_LIGHTING_INPUT_OK
PORTABLE_LIGHTING_WORLD_OK
PORTABLE_LIGHTING_LIGHTS_OK
PORTABLE_LIGHTING_PREVIEWS_OK
PORTABLE_LIGHTING_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=9 name=lighting
```

The lighting gate requires `qwantani_puresky_2k.hdr`, gamma 4.0, strength 1.2,
a permanently hidden delivered Sun, one warm 700-energy FireLight, four valid
compass screenshots, and a restored `ocean_view` active camera.

After inspecting Phase 9, one new approval records the intentional Phase 10 skip:

```text
PORTABLE_ANIMATION_INPUT_OK
PORTABLE_ANIMATION_SKIP_OK
PORTABLE_ANIMATION_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=10 name=optional_animation_skipped
```

The skip gate requires `ocean_view`, `patio_sweep_cam`, the Phase 9 world, hidden
Sun, FireLight, and zero animation-camera keyframes. It saves a separate transition
checkpoint for the still-image demo.

After inspecting Phase 10, one new approval authorizes Phase 11 test renders:

```text
PORTABLE_TEST_RENDER_INPUT_OK
PORTABLE_TEST_RENDER_BEAUTY_OK
PORTABLE_TEST_RENDER_DEPTH_OK
PORTABLE_TEST_RENDER_SEGMENTATION_OK
PORTABLE_TEST_RENDER_RESTORE_OK
PORTABLE_TEST_RENDER_PREPARATION_OK
PHASE_REVIEW_REQUIRED phase=11 name=test_renders
```

The still-image gate renders aligned 512x512 beauty, camera-distance depth, and
segmentation passes, validates image variation and dimensions, restores every
material and render setting, and saves a separate checkpoint. Proceed to Phase 12 only through the checked adapter described below.

After inspecting Phase 11, one new approval authorizes the final transformation:

```text
PORTABLE_FINAL_INPUT_OK
PORTABLE_FINAL_SUBMISSION_OK
PORTABLE_FINAL_IMAGES_OK
PORTABLE_FINAL_PREPARATION_OK
FINAL_REVIEW_REQUIRED phase=12 name=final_blender_comfyui
```

The final gate renders fresh Blender beauty and segmentation inputs, submits the
verified ComfyUI API graph, waits for exactly three 1280x720 outputs (Make Real,
Change Environment, and Time of Day), validates them, and saves the final Blender
checkpoint. Sample inputs are not used.

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
