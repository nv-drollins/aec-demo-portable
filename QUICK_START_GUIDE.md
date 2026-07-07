# AEC Demo Portable — Quick Start

Use this guide after completing [docs/INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md).
It is the supported DGX Spark quick start for Hermes, FreeCAD, Blender, and
ComfyUI.

## 1. Start the stack

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
```

Continue only when the terminal reports:

```text
FREECAD_MCP=healthy
BLENDER_MCP=healthy
COMFYUI=healthy
FLUX_MODELS_MISSING=0
WORKFLOW_NODES_MISSING=0
PORTABLE_STACK_OK
```

FreeCAD and Blender should be visible on the desktop. ComfyUI is available at
`http://127.0.0.1:8188`.

## 2. Pick one demo mode

### Recommended presentation: automatic Hermes cycle

```bash
./scripts/start-portable-auto-hermes-demo.sh
```

Hermes visibly introduces and supervises one authorized Phase 2–12 cycle. This
is the easiest end-to-end demonstration because it highlights Hermes without
requiring an approval after every phase.

### Manual approval walkthrough

```bash
./scripts/start-portable-manual-demo.sh
```

A Hermes chat opens in the terminal. Paste this exact opening instruction:

```text
Load the delivered_cliff_house_demo prompt profile and obey AGENTS.md. Perform
read-only source validation, preflight, and status checks. Summarize the
accepted design intent in five bullets, identify the next phase, and explain
what that phase will visibly do. Do not begin or execute the phase, do not
launch Rhino or OBS, and do not generate an approval on my behalf. Stop with
the WAITING_FOR_HUMAN_APPROVAL marker. Do not restart the design interview.
```

Hermes should stop at:

```text
WAITING_FOR_HUMAN_APPROVAL phase=2 name=site_preparation
```

After reviewing each proposal or completed phase, type:

```text
Approved — proceed to the next phase.
```

Each approval advances one phase only. Do not paste multiple approvals at once.
The sequence finishes with Phase 12 and three final ComfyUI images.

### Unattended looping display

```bash
./scripts/start-portable-auto-terminal.sh
```

This opens a separate terminal that repeatedly runs the checked deterministic
workflow. It is suitable for a kiosk or an unattended booth. It is not a
Hermes chat; use the automatic Hermes mode when the audience should see Hermes.

## 3. What you should see

The workflow progresses through:

| Phase | Visible result |
|---:|---|
| 1 | Source, profile, and service validation |
| 2 | FreeCAD site reconstruction |
| 3 | FreeCAD building massing |
| 4 | FreeCAD architectural detailing |
| 5 | Blender landscaping and site context |
| 6 | Blender entourage and outdoor living |
| 7 | Materials and segmentation tags |
| 8 | Original 28 mm southwest hero camera |
| 9 | HDRI lighting and compass previews |
| 10 | Intentional animation skip for the still-image demo |
| 11 | Beauty, depth, and segmentation test renders |
| 12 | Three final ComfyUI transformations |

The final images are:

- Make Real
- Change Environment
- Time of Day

They are saved under:

```text
/home/nvidia/AEC_Demo_Portable/projects/recorded_demo/final_outputs/
```

The final Blender file is:

```text
/home/nvidia/AEC_Demo_Portable/projects/recorded_demo/blender/portable_cliff_house_FINAL.blend
```

## 4. Stop or restart

Stop an automatic loop with `Ctrl+C`.

Stop Blender and ComfyUI services:

```bash
./scripts/stop-portable-demo.sh
```

For a clean rehearsal, restart the services and launch the chosen mode again.
The checked adapters overwrite their own generated checkpoints; do not delete
the delivered payload manually.

```bash
./scripts/restart-portable-demo.sh
```

## 5. After a reboot

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
```

No reinstall is required.

## 6. Common checks

Run strict preflight:

```bash
./scripts/preflight-portable-demo.sh
```

Run one fast unattended rehearsal without phase delays:

```bash
python3 scripts/run-portable-demo-loop.py --cycles 1 --phase-delay 0
```

For complete phase markers, approval behavior, and troubleshooting, see
[docs/SPARK_RUNBOOK.md](docs/SPARK_RUNBOOK.md).
