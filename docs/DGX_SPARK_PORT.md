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

| Component | Delivered expectation | Current Spark state | Status |
|---|---|---|---|
| Agent | Claude Desktop | Hermes + local Qwen available | Port required |
| CAD | Rhino 8, optional in this drop | FreeCAD 1.1.1 + FreeCAD MCP | Replacement track available |
| Blender | 5.1 | Ubuntu Blender 4.0.2 | Blocked pending compatible Blender |
| ComfyUI | 0.16+ with Flux.2 Klein | Existing local SD 1.5 runtime | Blocked pending models/nodes |
| Blender MCP | Add-on on port 9876 | Existing 4.0 add-on works | Must reinstall/verify for Blender 5.1 |

## Repository boundary

Ordinary Git tracks the source scripts, prompts, skills, workflow JSON,
custom-node source, documentation, setup checks, and sanitized examples. It
does not track sample scenes, textures, model weights, bundled add-on archives,
renders, local credentials, logs, or PID files. If large assets eventually
need remote versioning, choose an artifact store or Git LFS deliberately.

## Commands

```bash
cp config/runtime.env.example config/runtime.env
./scripts/status-portable-demo.sh
./scripts/preflight-portable-demo.sh
./scripts/start-portable-demo.sh
./scripts/restart-portable-demo.sh
./scripts/stop-portable-demo.sh
```

`start` and `restart` are strict: they stop before launching anything if the
configured Blender is too old or required Flux.2 models are absent. Set
`AEC_PORTABLE_REQUIRE_MODELS=0` only for infrastructure testing, never for a
claimed end-to-end demonstration.

## Next porting steps

1. Install or provide a DGX Spark-compatible Blender 5.1 executable.
2. Install the portable Blender MCP and ComfyUI-BlenderAI add-ons for that
   Blender version, without replacing the working Blender 4.0 setup.
3. Install the Flux.2 Klein model set and required custom nodes into an
   isolated ComfyUI environment.
4. Open a copy of Scene B first, validate materials/cameras/render passes, then
   test the 1.55 GB canonical Scene A.
5. Adapt the Claude/Rhino phase prompts to Hermes/FreeCAD while preserving the
   original files for comparison.
