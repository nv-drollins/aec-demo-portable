# ComfyUI Model Manifest
## Required for AEC Demo Portable

All models go inside your ComfyUI installation at:
`<comfyui_install_path>/ComfyUI/models/`

> ⚠️ **This section was corrected against the actual bundled workflow graph**
> (`comfyui/workflows/AEC_last_submitted_workflow.json`) — the previous
> version of this manifest listed the wrong model sizes. If your team already
> has a working Flux.2 Klein setup, check the exact filenames below match
> what you have before assuming everything needs re-downloading.

---

## ★ REQUIRED — AEC Pipeline Models

### 1. Flux.2 Klein 9B (Diffusion Model)
| Field | Value |
|-------|-------|
| File | `models/diffusion_models/klein/flux-2-klein-9b.safetensors` |
| Source | https://huggingface.co/ostris/flux-2-klein (verify exact repo/filename for the 9B variant) |
| Notes | The core image generation model actually referenced by both `UNETLoader` nodes in the bundled workflow (`999`, `933`). The 4B variant previously listed here is NOT what this workflow loads — create the `klein/` subfolder. |

---

### 2. Qwen 3 8B Text Encoder (fp8, mixed precision) — REQUIRED
| Field | Value |
|-------|-------|
| File | `models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors` |
| Source | https://huggingface.co/Qwen/Qwen3-8B (verify exact fp8-mixed export used) |
| Notes | This is the text encoder actually wired into the working graph (`CLIPLoader` nodes `998`, `932`) — used for every text prompt in the cascade. |

### 2b. Qwen 3 4B Text Encoder — present but unused in the current graph
| Field | Value |
|-------|-------|
| File | `models/text_encoders/klein/qwen_3_4b.safetensors` |
| Source | https://huggingface.co/Qwen/Qwen3-4B |
| Notes | Referenced by one `CLIPLoader` node (`1054`) that isn't wired to anything downstream in the bundled workflow — looks like a leftover from an earlier iteration. ComfyUI may still validate that this file exists even though it's not on the execution path, so keep it around unless you trim the orphan node from the graph. |

**Download commands:**
```bash
huggingface-cli download ostris/flux-2-klein --local-dir ./ComfyUI/models/diffusion_models/klein
huggingface-cli download Qwen/Qwen3-8B --local-dir ./ComfyUI/models/text_encoders/klein
# optional, only needed to satisfy the orphaned node above:
huggingface-cli download Qwen/Qwen3-4B --local-dir ./ComfyUI/models/text_encoders/klein
```

---

### 3. Depth Anything (ViT-L) — REQUIRED
| Field | Value |
|-------|-------|
| File | `models/checkpoints/depth_anything_vitl14.pth` (or wherever your ControlNet-aux preprocessor pack expects it — check its own model-download helper) |
| Source | comfyui_controlnet_aux ships a downloader for this; see custom node section below |
| Notes | Used by the `DepthAnythingPreprocessor` node (`1165`) for the structural depth reference. Missing entirely from the previous version of this manifest. |

---

### 4. FLUX.2 VAE
| Field | Value |
|-------|-------|
| File | `models/vae/flux2-vae.safetensors` |
| Size | ~310 MB |
| Source | https://huggingface.co/black-forest-labs/FLUX.1-dev |
| Notes | Also copy to `models/vae/flux/flux2-vae.safetensors` |

**Direct link:** https://huggingface.co/black-forest-labs/FLUX.1-dev/blob/main/vae/diffusion_pytorch_model.safetensors
(rename to `flux2-vae.safetensors`)

---

## OPTIONAL — Extended Pipeline Models

### 5. SDXL Base 1.0 (backup model)
| Field | Value |
|-------|-------|
| File | `models/checkpoints/sd_xl_base_1.0.safetensors` |
| Size | 6.46 GB |
| Source | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 |

### 6. FLUX.1 Depth ControlNet
| Field | Value |
|-------|-------|
| File | `models/diffusion_models/flux1-depth-dev-nvfp4.safetensors` |
| Size | 8.25 GB |
| Source | https://huggingface.co/black-forest-labs/FLUX.1-Depth-dev |
| Notes | Optional — enables depth-guided generation |

### 7. CLIP-L Text Encoder
| Field | Value |
|-------|-------|
| File | `models/text_encoders/clip_l.safetensors` |
| Size | 230 MB |
| Source | https://huggingface.co/openai/clip-vit-large-patch14 |

### 8. T5-XXL Text Encoder (FP8)
| Field | Value |
|-------|-------|
| File | `models/text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors` |
| Size | 4.8 GB |
| Source | https://huggingface.co/mcmonkey4eva/t5-v1_1-xxl-encoder-bf16 |

---

## Required Custom Nodes

Verified directly against a live ComfyUI install's `custom_nodes/` source
(`C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable`) on 2026-07-06 — not
guessed from naming conventions.

### ✅ Already covered (confirmed present on that install)

| class_type used by workflow | Confirmed source |
|---|---|
| `SimpleInpaintCrop`, `SimpleInpaintStitch`, `ColorCode` | `aec_utility_nodes` (bundled in this package) |
| `MaskFromColor+` | `ComfyUI_essentials/mask.py` |
| `AnyLineArtPreprocessor_aux` | `comfyui_controlnet_aux/node_wrappers/anyline.py` |
| `DepthAnythingPreprocessor` | `comfyui_controlnet_aux/node_wrappers/depth_anything.py` |
| `Text Multiline` | `was-node-suite-comfyui/WAS_Node_Suite.py` (exact registration, line 14582) |
| `GetImageSize`, `ImageScaleToTotalPixels` | covered redundantly by `ComfyUI-KJNodes`, `ComfyUI_LayerStyle`, `ComfyUI_essentials`, `masquerade-nodes-comfyui` |

Install: `comfyui_controlnet_aux` (https://github.com/Fannovel16/comfyui_controlnet_aux),
`was-node-suite-comfyui` (https://github.com/WASasquatch/was-node-suite-comfyui),
`ComfyUI_essentials` (https://github.com/cubiq/ComfyUI_essentials) if not already present.

### Current compatibility notes for formerly unresolved node classes

| class_type used by workflow | What was checked | Status |
|---|---|---|
| `ResizeImageMaskNode` | Live DGX Spark registry (`python_module=comfy_extras.nodes_post_processing`) | **Core in current ComfyUI**; require a recent ComfyUI version. |
| `Image Comparer (rgthree)` | Checked for `rgthree-comfy` pack | **Not installed at all.** A different pack (`skbundle/comparerplus.py`) registers a similarly-purposed `"ImageComparer"` node, but it's a different class name from a different pack and will NOT satisfy this workflow. Install `rgthree-comfy`: https://github.com/rgthree/rgthree-comfy |
| `BatchImagesNode` | Live DGX Spark registry (`python_module=comfy_extras.nodes_post_processing`) | **Core in current ComfyUI**; require a recent ComfyUI version. |

> `Image Comparer (rgthree)` still requires `rgthree-comfy`. The two other classes are now provided by current ComfyUI core; older ComfyUI builds may still report them as unknown.

### Previously-listed packs — not used by this specific workflow

`ComfyUI-Impact-Pack`, `ComfyUI-Custom-Scripts`, and `ComfyUI-Easy-Use` don't
match any class_type this graph actually calls (kept installed is harmless,
just not required). `ComfyUI-Inpaint-CropAndStitch` is also not used — this
workflow's crop/stitch nodes come from `aec_utility_nodes` instead.
`comfyui-ollama` is only needed if you re-enable the auto-prompt-generation
branch (`submit_comfyui.py` currently strips the Ollama nodes before
submitting).

---

## Folder Structure After Setup

```
ComfyUI/
└── models/
    ├── diffusion_models/
    │   └── klein/
    │       └── flux-2-klein-9b.safetensors            ← REQUIRED
    ├── text_encoders/
    │   └── klein/
    │       ├── qwen_3_8b_fp8mixed.safetensors         ← REQUIRED (actually wired in)
    │       └── qwen_3_4b.safetensors                  ← present but orphaned node (see above)
    ├── vae/
    │   ├── flux2-vae.safetensors                      ← REQUIRED
    │   └── flux/
    │       └── flux2-vae.safetensors                  ← REQUIRED (duplicate)
    └── checkpoints/
        └── depth_anything_vitl14.pth                  ← REQUIRED (path depends on your
                                                            controlnet_aux install — verify)
```

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU VRAM | 16 GB | 24+ GB |
| System RAM | 32 GB | 64+ GB |
| Storage | 60 GB free | 100+ GB SSD |
| GPU | RTX 3090 | RTX 4090 / H100 |

> The Flux.2 Klein 4B pipeline uses ~16 GB VRAM at 1024×1024.
