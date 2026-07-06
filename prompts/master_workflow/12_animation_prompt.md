# Phase 9 — Animation
### Animation Execution Prompt
*Part of the aec_demo_master prompt suite*
*Reads: `01_user_prompt.md` § Phase 9, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Set up and keyframe the patio sweep camera animation. Render a Workbench preview
and Cycles test frames for approval before committing to a full-quality render.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 8
- Delta notes — check for: arc width, duration, camera radius, look target

## Outputs

- `[project]/blender_assets/base_model.blend` — `patio_sweep_cam` fully animated
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — Workbench preview MP4 + Cycles stills every 10 frames

---

## Pre-Phase Audit Checklist

- [ ] Phase 8 gate approved
- [ ] `patio_sweep_cam` object exists from Phase 7
- [ ] Patio centre coordinates confirmed: default (−4.0, 0.0)

---

## OBS Recording Protocol

→ **OBS ACTION:** `obs-set-current-scene("CLAUDE")` → `obs-start-record`.
Claude explains smoothstep easing, arc geometry, and keyframe rationale.

→ **OBS ACTION:** Before Blender work, `obs-set-current-scene("BLENDER")`.
Stay on BLENDER through keyframe insertion, Workbench preview render, and
Cycles test stills.

→ **OBS ACTION:** Preview complete, `obs-set-current-scene("CLAUDE")`.

---

## Execution Steps

### 1. Define sweep parameters
Default values — override with delta notes:
- Patio centre: (−4.0, 0.0, 0.0)
- Camera radius: 22m from patio centre
- Camera height: 6.0m
- Look target: (5.0, 0.0, 1.5) — between patio and house west face
- Start azimuth: 220° (SSW)
- End azimuth: 320° (NNW)
- Arc: 100°, passing through due West
- Duration: 192 frames at 24fps (8 seconds)
- Lens: 24mm

### 2. Apply smoothstep easing
```python
def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)
```
For each frame, remap `t_linear = frame / 192` through `smoothstep(t_linear)` to
get `t_smooth`, then compute azimuth as `START + t_smooth × (END − START)`.

### 3. Insert keyframes — CRITICAL RULES
- Set camera location and rotation for each frame, then call
  `keyframe_insert(data_path="location", frame=frame)` with the explicit frame number.
- **Never call `scene.frame_set()` inside the keyframe insertion loop.**
  `frame_set()` evaluates the animation at that frame, overriding the location
  value you just set — causing all frames to bake to the same position.
- Insert a keyframe at **every frame** (193 total). Do not rely on sparse keyframes
  with spline interpolation — imported objects may have Quaternion rotation mode
  that ignores euler interpolation between sparse keyframes.
- After insertion, verify by sampling `positions[0]`, `positions[96]`, `positions[192]`
  and confirming they are all different.

### 4. Set rotation mode
- `cam_obj.rotation_mode = 'XYZ'` before any keyframe insertion.

### 5. Render Workbench preview
- Engine: `BLENDER_WORKBENCH`, material colour mode, studio lighting, shadows on.
- Resolution: 1280×720. All 193 frames.
- Output PNG sequence to `[project]/test_renders/preview/png/frame_####.png`.
- Encode to MP4: `[project]/test_renders/patio_sweep_preview.mp4`.

### 6. Render Cycles stills at every 10th frame
- Engine: Cycles GPU, 128 samples, OPTIX denoiser.
- Resolution: 640×360 (quarter resolution).
- Frames: 0, 10, 20, … 190, 192.
- Save to `[project]/test_renders/anim_test/frame_####.png`.

---

## Post-Phase Cleanup Checklist

- [ ] Camera positions at frame 0, 96, and 192 are all different (animation verified)
- [ ] Ease-in confirmed: speed at frame 5 is much slower than speed at frame 96
- [ ] House west face is visible in frame at every point of the arc
- [ ] Full patio disc fits in frame throughout the arc
- [ ] Preview MP4 plays smoothly at 24fps
- [ ] 10th-frame Cycles stills saved

---

## ▶ REVIEW GATE 9 — Animation Preview

Present:
1. Workbench preview MP4
2. Grid of 10th-frame Cycles stills

Confirm: camera moves, easing feels cinematic, patio + house both in frame throughout.
Wait for written approval.

---

## Checkpoint Save

Save Blender checkpoint to `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`.

→ **OBS ACTION:** `obs-stop-record`.
Rename: `09-animation-claude.mkv`, `09-animation-blender.mkv`. Confirm.

Proceed to `13_test_render_prompt.md`.
