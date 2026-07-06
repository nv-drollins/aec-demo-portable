# Hermes workspace instructions

This repository is the independent control layer for the complete
`AEC_Demo_Portable` bundle. Keep it separate from `/home/nvidia/aec-demo`.
The extracted heavyweight assets remain local source material and are ignored
by ordinary Git.

`AGENTS.md` is the automatically loaded execution policy for this workspace.
Its human-only phase gate is absolute. A ready profile or approved design
default does not authorize a phase, and Hermes must never approve itself.

## Prompt profiles

The recorded delivered demo uses
`profiles/delivered_cliff_house_demo/prompt_profile.md`. It is already fully
populated; do not materialize a copy or run the design interview for the
standard demo. Its defaults approve design choices only, never execution.

Canonical Phase 2 uses the `prepare-portable-freecad-site` skill and only the
checked `scripts/run-portable-site-preparation.py` entrypoint. Raw FreeCAD
`execute_code` experimentation is prohibited for that phase.

Canonical Phase 3 uses `build-portable-freecad-massing` and only
`scripts/run-portable-massing.py`. Never create compatibility aliases for old
document or object names. Phases without an explicit `AGENTS.md` adapter are
blocked rather than improvised.

Canonical Phase 4 uses `build-portable-freecad-detailing` and only
`scripts/run-portable-detailing.py`. The runner reconstructs target detail
envelopes and owns all opening/clearance booleans. Do not improvise detailing
through raw FreeCAD code.

Canonical Phase 5 uses `build-portable-blender-landscaping` and only
`scripts/run-portable-landscaping.py`. It validates the approved FreeCAD state,
checks the delivered Blender site target, and saves a separate landscaping
checkpoint. Before approval, use only the read-only
`scripts/check-portable-landscaping-ready.py`; never improvise `python3 -c`
FreeCAD imports. Do not overwrite a delivered scene or add Phase 6 entourage.

Canonical Phase 6 uses `build-portable-blender-entourage` and only
`scripts/run-portable-entourage.py`. It creates a versioned procedural outdoor-
living checkpoint because the delivered target has no named entourage meshes.
Before approval, use only `scripts/check-portable-entourage-ready.py`. Do not
download assets, improvise raw Blender code, or begin Phase 7 materials.

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
Never launch or operate Rhino for this workflow. If an upstream prompt names
Rhino, RhinoCommon, or OBS, apply the FreeCAD mapping in `AGENTS.md`; if a
checked FreeCAD adapter is unavailable, stop and report that gap.

## Security

Never commit `config/user_config.yaml`, `config/runtime.env`, OBS passwords,
API keys, tokens, or locally generated Claude/Hermes configurations. Commit
only sanitized `.example` files. Services must remain bound to localhost.
