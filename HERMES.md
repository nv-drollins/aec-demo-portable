# Hermes workspace instructions

This repository is the independent control layer for the complete
`AEC_Demo_Portable` bundle. Keep it separate from `/home/nvidia/aec-demo`.
The extracted heavyweight assets remain local source material and are ignored
by ordinary Git.

## Authoritative bundle assets

- Default Blender scene:
  `sample_project/blender_assets/cliff_house_act2_textured_v3.blend`
- Alternative lightweight scene:
  `sample_project/blender_assets/cliff_house_v17.blend`
- ComfyUI UI graph: `comfyui/workflows/AEC_Transform_Pipeline.json`
- Verified API graph: `comfyui/workflows/AEC_last_submitted_workflow.json`
- Render/submit entrypoint: `scripts/submit_comfyui.py`
- Original phase prompts: `prompts/master_workflow/`

Do not edit, overwrite, relocate, or recommit the large Blender scenes, model
weights, textures, or render outputs without explicit user approval. Work on
copies when testing Blender compatibility.

## Spark runtime

Use `scripts/portable_stack.py` or its shell wrappers. Never improvise broad
`pkill` commands. The controller records only processes it starts and stops
only those recorded processes. The earlier `/home/nvidia/aec-demo` runtime may
be reused through `config/runtime.env`, but its Git repository remains
independent.

Run `scripts/status-portable-demo.sh` before mutations. Run strict preflight
before `start` or `restart`. Do not claim the full bundle is ready unless:

- Blender meets the bundle's required major version (5.1 is documented);
- Blender MCP answers on `127.0.0.1:9876`;
- the Flux.2 Klein model set exists in the configured ComfyUI runtime;
- ComfyUI answers on `127.0.0.1:8188`; and
- the canonical scene and workflow files are present.

FreeCAD on `127.0.0.1:9875` is the approved open-source replacement track for
Rhino on this Spark. Preserve the original Rhino prompts and skills as source
evidence; do not describe FreeCAD reconstruction as recovered Rhino history.

## Security

Never commit `config/user_config.yaml`, `config/runtime.env`, OBS passwords,
API keys, tokens, or locally generated Claude/Hermes configurations. Commit
only sanitized `.example` files. Services must remain bound to localhost.
