# Demo replication readiness

## Bottom line

The delivered bundle and this port now reproduce the complete checked
Hermes-to-FreeCAD-to-Blender-to-ComfyUI demonstration on DGX Spark. It does not
contain the finished architectural model as Rhino construction history; the
bundled Rhino file is the 11-curve starting template. The delivered Blender
scene and reconstructed FreeCAD checkpoints are the authoritative targets for
this demonstration.

## Present in the bundle

- Canonical finished Blender scene:
  `sample_project/blender_assets/cliff_house_act2_textured_v3.blend`
  (approximately 1.55 GB).
- Alternative finished scene:
  `sample_project/blender_assets/cliff_house_v17.blend`
  (approximately 106 MB).
- Sun-study scene:
  `sample_project/blender_assets/cliff_house_act3_sunstudy.blend`
  (approximately 1.43 GB).
- Rhino starting template: `sample_project/rhino_assets/beach_house_02.3dm`;
  Rhino 8 archive, metres, 10 layers, 11 curve objects, no finished solids.
- Beauty, depth, and segmentation reference renders under
  `sample_project/renders/`.
- Full Blender render/segmentation/submission scripts.
- Blender MCP and ComfyUI-BlenderAI add-on payloads.
- ComfyUI UI graph (83 nodes) and submitted API graph (136 nodes).
- Bundled `aec_utility_nodes`, original prompts, skills, and project template.

## Validated Spark runtime

### Blender

- Isolated ARM64 Blender 5.1.0 is installed under `runtime/blender`.
- Both the 106 MB v17 scene and 1.55 GB canonical textured scene open.
- Blender MCP auto-starts on port 9876 and reports the intended 5.1 runtime.
- The controller rejects an older Blender instance occupying the same port.

### ComfyUI

The isolated CUDA 13 runtime is installed under `runtime/comfyui`. Strict
preflight checks the execution graph's three static model files:

- `models/diffusion_models/flux/flux-2-klein-9b.safetensors`
- `models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors`
- `models/vae/flux/flux2-vae.safetensors`

All 12 required workflow classes are registered. Depth Anything downloads its
own cache under `comfyui_controlnet_aux` on first use. The orphaned 4B loader
is not on a retained output path and needs no model.

The submitted API graph now normalizes Windows separators for Linux, supplies
the crop-node defaults required by the bundled utility node, removes
browser-only debug outputs, and retains exactly three SaveImage branches.

## Agent/CAD parity

The original package assumes Claude Desktop and Rhino MCP. On this Spark,
Hermes plus FreeCAD MCP is the replacement track. The portable installer now
downloads the pinned FreeCAD 1.1.1 ARM64 AppImage and FreeCAD MCP source,
installs the auto-start RPC links, and registers that MCP source with Hermes.
The portable controller no longer depends on a separate `/home/nvidia/aec-demo`
checkout.

## Readiness gates

The replication is demo-ready only after all of these pass:

1. `scripts/preflight-portable-demo.sh` returns `PORTABLE_PREFLIGHT_OK`.
2. Blender 5.1+ opens the copied v17 and canonical scenes without conversion
   loss.
3. Blender MCP reports the intended scene and render camera.
4. ComfyUI `/object_info` contains every required workflow class.
5. The bundled API graph queues without unknown nodes or missing models.
6. Beauty, depth, and segmentation passes are nonblank and aligned.
7. All three final branches produce valid images.

The 2026-07-07 validation completed all seven gates and produced three 1280 x
720 outputs using camera-v3, exact rendered depth at strength 0.98, and three
required visible building levels.
