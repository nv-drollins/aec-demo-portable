# AEC Demo Portable

AEC Demo Portable is the NVIDIA DGX Spark version of the delivered cliff-house
AEC demonstration. Hermes coordinates a checked, phase-gated workflow across
FreeCAD, Blender, and ComfyUI using local models and local MCP services.

The supported demonstration platform is:

- NVIDIA DGX Spark / GB10
- Ubuntu 24.04 ARM64
- Hermes Agent with local Ollama `qwen3.6:latest`
- FreeCAD 1.1.1 with FreeCAD MCP
- Blender 5.1 ARM64 with Blender MCP
- ComfyUI with Flux.2 Klein

Rhino, Claude Desktop, OBS, Windows, and Docker are not required for this port.
The original Windows/Rhino material remains in selected reference documents for
comparison with the delivered upstream workflow; it is not the installation
path for this repository.

## Start here

For a new Spark, follow [docs/INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md).

For an already installed Spark, use [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md).

For the detailed phase-by-phase operator procedure, use
[docs/SPARK_RUNBOOK.md](docs/SPARK_RUNBOOK.md).

For a self-contained USB deployment with no event internet, use
[docs/OFFLINE_EVENT_DEPLOYMENT.md](docs/OFFLINE_EVENT_DEPLOYMENT.md).

## Repository and payload

Git contains the control layer: scripts, skills, prompts, workflow JSON,
documentation, checks, and sanitized configuration examples. Large scenes,
textures, model weights, generated renders, and local runtime files are
intentionally excluded.

A fresh machine therefore needs both:

1. This public Git repository.
2. The separately distributed payload archive described in
   [docs/INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md#3-download-and-extract-the-demo-payload).

## Installed quick start

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
```

A healthy stack reports:

```text
FREECAD_MCP=healthy
BLENDER_MCP=healthy
COMFYUI=healthy
FLUX_MODELS_MISSING=0
WORKFLOW_NODES_MISSING=0
PORTABLE_STACK_OK
```

Then choose one mode:

| Mode | Command | Purpose |
|---|---|---|
| Manual Hermes | `./scripts/start-portable-manual-demo.sh` | Hermes pauses for human approval at every phase |
| Automatic Hermes | `./scripts/start-portable-auto-hermes-demo.sh` | Hermes visibly supervises one authorized Phase 2–12 cycle |
| Unattended loop | `./scripts/start-portable-auto-demo.sh` | Repeats the deterministic demo for kiosk playback |
| Loop in a new terminal | `./scripts/start-portable-auto-terminal.sh` | Opens the unattended loop in a visible monitor terminal |

The automatic Hermes mode is the best default when the presentation should
highlight Hermes while completing the whole workflow without repeated typing.

## Demonstrated workflow

1. Hermes validates the delivered profile and source evidence.
2. FreeCAD reconstructs site, massing, and architectural detailing in separate
   checked documents.
3. Blender builds landscaping, entourage, materials, camera, and lighting
   checkpoints.
4. Blender produces aligned beauty, depth, and segmentation passes.
5. ComfyUI generates three final images: Make Real, Change Environment, and
   Time of Day.

The current Phase 12 contract uses the restored 28 mm southwest camera-v3,
exact Blender camera-depth conditioning at 98%, and an explicit requirement to
preserve all three visible building levels.

## Outputs

Generated checkpoints and images are written below `projects/recorded_demo/`:

```text
projects/recorded_demo/freecad/
projects/recorded_demo/blender/
projects/recorded_demo/test_renders/
projects/recorded_demo/final_outputs/
```

The final Blender checkpoint is:

```text
projects/recorded_demo/blender/portable_cliff_house_FINAL.blend
```

## After a reboot

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
```

The controller restores FreeCAD, Blender MCP, and ComfyUI. It also archives
stale FreeCAD crash-recovery state so a recovery dialog cannot block the demo.

## Updating

```bash
cd /home/nvidia/AEC_Demo_Portable
git pull --ff-only origin main
./scripts/install-portable-runtime.sh
```

The installer is idempotent and re-runs preflight after updating dependencies
or configuration.

## Security

All MCP and ComfyUI endpoints bind to `127.0.0.1`. Do not expose ports 9875,
9876, or 8188 to an untrusted network. Blender Python auto-execution is enabled
only by the trusted demo launcher; do not use that launcher for untrusted
`.blend` files.

## Historical upstream material

The following documents describe or inventory parts of the delivered
Windows/Claude/Rhino workflow and are retained as source evidence:

- `docs/CLAUDE_ASSISTANT_GUIDE.md`
- `docs/REBUILD_GUIDE.md`
- `docs/PROMPT_INVENTORY.md`
- original prompts and Rhino skills under `prompts/` and `skills/rhino/`

They do not supersede the Spark installation guide or Spark runbook.

## License

Sample project files and third-party runtimes remain subject to their original
licenses. Flux.2 Klein and its associated models are subject to their respective
model licenses.
