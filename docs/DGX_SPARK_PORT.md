# DGX Spark port status

This repository wraps the delivered `AEC_Demo_Portable` bundle without
modifying its 19 GB sample project or other heavyweight assets.

## Verified bundle inventory

- `sample_project/`: approximately 19 GB; 88 files.
- `assets/`: approximately 348 MB; 26 files.
- `setup/`: approximately 141 MB; mostly bundled third-party Blender add-ons.
- Canonical scene A: `cliff_house_act2_textured_v3.blend`, approximately
  1.55 GB.
- Alternative scene B: `cliff_house_v17.blend`, approximately 106 MB.
- The `.blend` files use Zstandard compression.
- The portable ComfyUI package contains workflow/custom-node source and a model
  manifest, not the required Flux.2 model weights.

## Current Spark compatibility

See [REPLICATION_READINESS.md](REPLICATION_READINESS.md) for the complete asset, model, custom-node, and parity checklist.


| Component | Delivered expectation | Current Spark state | Status |
|---|---|---|---|
| Agent | Claude Desktop | Hermes + local Qwen available | Port required |
| CAD | Rhino 8, optional in this drop | FreeCAD 1.1.1 + FreeCAD MCP | Replacement track available |
| Blender | 5.1 | Isolated ARM64 Blender 5.1.0 | Validated with both delivered scenes |
| ComfyUI | Flux.2 Klein 9B | Isolated ComfyUI 0.27.0 + CUDA 13 | Validated, 0 missing nodes/models |
| Blender MCP | Add-on on port 9876 | Auto-started by controller | Validated against full textured scene |

## Repository boundary

Ordinary Git tracks the source scripts, prompts, skills, workflow JSON,
custom-node source, documentation, setup checks, and sanitized examples. It
does not track sample scenes, textures, model weights, bundled add-on archives,
renders, local credentials, logs, or PID files. If large assets eventually
need remote versioning, choose an artifact store or Git LFS deliberately.

## Transfer the non-Git payload

The complete checked demo does not require all 19 GB under `sample_project/`.
The canonical `cliff_house_act2_textured_v3.blend` has packed textures and no
linked Blender libraries. The required minimum is:

- `sample_project/blender_assets/cliff_house_act2_textured_v3.blend`
- `sample_project/rhino_assets/beach_house_02.3dm`
- `assets/hdri/qwantani_puresky_2k.hdr`
- `setup/blender_addons/BlenderMCP_addon.py`

Create the default minimal transfer package:

```bash
./scripts/package-portable-payload.sh
```

To preserve the complete delivered bundle instead:

```bash
./scripts/package-portable-payload.sh --mode full
```

Both modes create a `.tar.gz`, a portable SHA-256 file, and a contents listing
under `transfer/`. On the source Spark:

```bash
scp transfer/aec-demo-portable-payload-demo-*.tar.gz* nvidia@NEW_SPARK:/home/nvidia/
```

On the destination Spark, after cloning this repository:

```bash
cd /home/nvidia
sha256sum -c aec-demo-portable-payload-demo-*.tar.gz.sha256
tar -xzf aec-demo-portable-payload-demo-*.tar.gz \
  -C /home/nvidia/AEC_Demo_Portable
cd /home/nvidia/AEC_Demo_Portable
./scripts/install-portable-runtime.sh
./scripts/preflight-portable-demo.sh
```

`runtime/` is intentionally not transferred. The installer rebuilds Blender,
ComfyUI, custom nodes, and model files for the destination Spark.

## Prompt profile

The delivered demo does not use a file literally named `prompt_profile.md` upstream. Its complete brief is `prompts/master_workflow/01_user_prompt.md`; this port exposes it as a pinned, approved preset at `profiles/delivered_cliff_house_demo/prompt_profile.md`.

```bash
python3 scripts/prompt_profile.py validate profiles/delivered_cliff_house_demo/prompt_profile.md
python3 scripts/prompt_profile.py materialize --preset delivered_cliff_house_demo --output projects/recorded_demo/prompt_profile.md
```

Use `python3 scripts/prompt_profile.py new --output projects/my_project/prompt_profile.md` for a blank interview template.

## Commands

```bash
cp config/runtime.env.example config/runtime.env
./scripts/status-portable-demo.sh
./scripts/preflight-portable-demo.sh
./scripts/start-portable-demo.sh
./scripts/restart-portable-demo.sh
./scripts/stop-portable-demo.sh
./scripts/start-portable-manual-demo.sh
./scripts/start-portable-auto-demo.sh
./scripts/run-comfy-demo.py --sample-inputs
./scripts/run-comfy-demo.py --render
```

`start` and `restart` are strict: they stop before launching anything if the
configured Blender is too old or required Flux.2 models are absent. Set
`AEC_PORTABLE_REQUIRE_MODELS=0` only for infrastructure testing, never for a
claimed end-to-end demonstration.

`start-portable-manual-demo.sh` opens the human-gated Hermes walkthrough.
`start-portable-auto-demo.sh` bypasses Hermes approvals without fabricating
them and continuously runs the same checked phase adapters for kiosk playback.

## Validated result

The Spark opened both supplied Blender scenes, served the full scene through
Blender MCP, registered every required Comfy node, loaded the public 9B
KV-FP8 model and 8B encoder, and produced the three expected 1024 x 1024
outputs: Make Real, Change Environment, and Time of Day. See
[SPARK_RUNBOOK.md](SPARK_RUNBOOK.md) for the concise operating procedure.
