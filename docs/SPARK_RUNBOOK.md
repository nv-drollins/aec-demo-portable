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

Validate or create a project copy:

```bash
python3 scripts/prompt_profile.py list
python3 scripts/prompt_profile.py validate \
  profiles/delivered_cliff_house_demo/prompt_profile.md
python3 scripts/prompt_profile.py materialize \
  --preset delivered_cliff_house_demo \
  --output projects/recorded_demo/prompt_profile.md
```

For a different project that should use the original interview questions:

```bash
python3 scripts/prompt_profile.py new \
  --output projects/my_project/prompt_profile.md
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
instructions. Keep it open throughout the demonstration.

At the Hermes prompt, paste this exact opening instruction:

```text
Load the delivered_cliff_house_demo prompt profile. Validate its sources and
runtime gates, summarize the approved design intent in five bullets, and begin
the next uncompleted phase using the checked workflow. Stop at the phase review
gate and report the success markers. Do not restart the design interview.
```

When Hermes reaches a review gate, inspect the visible result in FreeCAD or
Blender. To authorize one additional phase, return to the same Hermes terminal
and type:

```text
Approved — proceed to the next phase.
```

Do not paste several approvals at once. Each approval advances exactly one
phase so the live model remains synchronized with the review state.

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
