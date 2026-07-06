# Phase 10 — Test Rendering
### Test Render Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 10, skills/depth_and_segmentation.md*
*Version 1.0 — May 2026*

---

## Purpose

Validate the full scene at half resolution before final rendering. Produce beauty
renders, depth maps, and segmentation masks. The client approves this output before
any full-resolution render is launched.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 9
- `[project]/skills/depth_and_segmentation.md` — or master version if no override

## Outputs

- `[project]/test_renders/half_res/` — beauty PNG sequence + MP4
- `[project]/test_renders/depth/` — 16-bit greyscale depth maps
- `[project]/test_renders/segmentation/` — 8-bit RGB segmentation masks

---

## Pre-Phase Audit Checklist

- [ ] Phase 9 gate approved
- [ ] Animation verified — all 193 keyframes present and confirmed different
- [ ] `patio_sweep_cam` set as active camera
- [ ] Depth and segmentation skill file has been read this session

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.

→ **OBS ACTION:** Before any render launch, `obs-set-current-scene("BLENDER")`.
Stay on BLENDER for the full duration of every render — do not switch away
during active rendering. The Cycles tiles and denoising passes are key footage.

→ **OBS ACTION:** All renders complete, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. Beauty render — half resolution
- Engine: Cycles GPU, 128 samples, OPTIX denoiser.
- Resolution: 960×540 (half of 1920×1080).
- Frames: 0–192. Output: `[project]/test_renders/half_res/png/frame_####.png`.
- Encode to MP4: `[project]/test_renders/half_res/patio_sweep_halfres.mp4`.

### 2. Depth maps
Follow the procedure in `depth_and_segmentation.md` exactly. Summary:

**Step A — Render raw depth EXRs:**
- Assign `_DepthRaw` emission material (CameraData View Distance → Emission)
  to ALL objects. Set `rotation_mode = 'XYZ'` on all. Zero all bounces.
  Kill world (strength=0). Set `film_transparent=True`.
- Render 1 sample per frame, OPEN_EXR, uncompressed.
- Output: `[project]/test_renders/depth_raw_temp/raw_####.exr`.

**Step B — Normalise via subprocess:**
- Run `normalise_depth.py` (in `[project]/scripts/` or master scripts/).
- Per-frame auto-normalise from actual min/max pixel values.
- Do NOT apply `flipud` — OpenEXR Python already returns top-down.
- Save 16-bit greyscale PNG to `[project]/test_renders/depth/depth_####.png`.

### 3. Segmentation masks
Follow `depth_and_segmentation.md`. Summary:
- Assign flat emission materials by object name category (zero bounces, black world,
  transparent background). Set `rotation_mode = 'XYZ'` on all.
- Use the standard palette from Appendix C of `01_user_prompt.md`.
- 1 sample per frame, PNG RGB 8-bit.
- Output: `[project]/test_renders/segmentation/seg_####.png`.

### 4. Restore beauty materials
After depth and segmentation passes, restore all original materials and render
settings. Confirm the scene looks correct with a single Cycles test still.

---

## Post-Phase Cleanup Checklist

- [ ] Beauty MP4 plays smoothly, fire glows in pit, materials correct
- [ ] Depth maps: near objects white, far/sky black, smooth gradation — no shadows,
      no AO, no flat areas with no differentiation
- [ ] Segmentation masks: flat solid colours, no gradients, no shadows
- [ ] `depth_raw_temp/` folder can be deleted after depth PNG extraction confirmed
- [ ] Beauty materials fully restored after passes

---

## ▶ REVIEW GATE 10 — Test Renders

Present:
1. Half-resolution beauty MP4
2. Four sample depth frames (frames 0, 48, 96, 144)
3. Four sample segmentation frames (frames 0, 48, 96, 144)

Confirm: motion, materials, depth differentiation, mask colours.
Wait for written approval before launching full-resolution render.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `10-test_render-claude.mkv`, `10-test_render-blender.mkv`. Confirm.

Proceed to `14_final_render_prompt.md`.
