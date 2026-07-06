# Demo replication readiness

## Bottom line

The delivered bundle contains enough source material to reproduce the polished
Blender-to-ComfyUI demonstration once the compatible runtime is installed and
the remaining path/add-on integration is completed. It does not contain the
finished architectural model as Rhino construction history; the bundled Rhino
file is the 11-curve starting template. The finished model is authoritative in
the delivered Blender scenes.

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

## Runtime work still required

### Blender

- Install a compatible Blender 5.1+ ARM64 build separately from the working
  Ubuntu Blender 4.0 installation.
- Install and validate the bundled Blender MCP and ComfyUI-BlenderAI add-ons in
  that Blender version.
- Replace hard-coded Windows paths in the delivered Blender startup/submission
  integration with `config/runtime.env` values.
- Open a copy of the 106 MB v17 scene first; then validate the 1.55 GB canonical
  scene.

### ComfyUI models

Strict preflight checks the execution graph's required files:

- `models/diffusion_models/klein/flux-2-klein-9b.safetensors`
- `models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors`
- `models/vae/flux2-vae.safetensors`
- `models/vae/flux/flux2-vae.safetensors` (may be a symlink to the same VAE)
- `models/checkpoints/depth_anything_vitl14.pth`

The graph also contains an orphan Qwen 3 4B loader. It is not on the execution
path but may be removed or supplied if the UI requires its dropdown value.

### ComfyUI nodes

The current shared ComfyUI already provides `ResizeImageMaskNode`,
`BatchImagesNode`, `GetImageSize`, and `ImageScaleToTotalPixels`. The first two
are now core nodes from `comfy_extras.nodes_post_processing`, not unknown
third-party packs.

The current shared runtime is missing eight classes needed by the submitted
graph:

| Missing class | Source |
|---|---|
| `ColorCode` | Bundled `comfyui/custom_nodes/aec_utility_nodes` |
| `SimpleInpaintCrop` | Bundled `aec_utility_nodes` |
| `SimpleInpaintStitch` | Bundled `aec_utility_nodes` |
| `AnyLineArtPreprocessor_aux` | `comfyui_controlnet_aux` |
| `DepthAnythingPreprocessor` | `comfyui_controlnet_aux` |
| `MaskFromColor+` | `ComfyUI_essentials` |
| `Image Comparer (rgthree)` | `rgthree-comfy` |
| `Text Multiline` | `was-node-suite-comfyui` |

## Agent/CAD parity

The original package assumes Claude Desktop and Rhino MCP. On this Spark,
Hermes plus FreeCAD MCP is the replacement track. The previous
`/home/nvidia/aec-demo` project supplies proven local Hermes, FreeCAD,
Blender-MCP, startup, and reset patterns. Porting the original phase prompts to
FreeCAD remains integration work; it is not required to demonstrate the
already-finished Blender scene and ComfyUI transformation pipeline.

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
