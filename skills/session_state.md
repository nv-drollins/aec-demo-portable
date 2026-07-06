# Session state — aec_demo_master

**Read this AFTER INDEX.md when starting a new session.**

*Last saved: 2026-05-12 (end of session). Full pipeline run completed.*

---

## MCP connections required next session

| MCP              | Required for                    | Status                                     |
|------------------|---------------------------------|--------------------------------------------|
| Filesystem       | All                             | Working                                    |
| Rhino            | Phases 1–4                      | Working via Cowork connector (localhost:3001) |
| Blender          | Phases 4–5                      | Working via Cowork connector (uvx blender-mcp, port 9876) |
| OBS              | Recording                       | Config known — needs Cowork connector (obs-mcp, password in env) |
| DaVinci Resolve  | Post-production editing         | Config known — needs Cowork connector       |
| ComfyUI          | Phase 7 (deferred)              | Running at 192.168.50.67:8188              |

### Full MCP config (claude_desktop_config.json + Cowork connector URLs)

```json
{
  "blender":       { "command": "uvx", "args": ["blender-mcp"] },
  "rhinoceros3d":  { "command": "npx", "args": ["mcp-remote", "http://localhost:3001/mcp"] },
  "obs":           { "command": "npx.cmd", "args": ["-y", "obs-mcp@latest"],
                     "env": { "OBS_WEBSOCKET_PASSWORD": "REPLACE_WITH_YOUR_OBS_PASSWORD" } },
  "davinci-resolve": { see D:\\tools\\Davinci\\davinci-resolve-mcp\\src\\server.py }
}
```

**Cowork connector URLs (add these in Cowork to activate each MCP):**
- Blender:  started via `uvx blender-mcp` — Cowork connector already added
- Rhino:    `http://localhost:3001/mcp`
- OBS:      obs-mcp runs on its own port — check obs-mcp docs for URL once started

### DaVinci Resolve MCP — PENDING CONFIG
Sean installed the DaVinci Resolve MCP. It needs to be added to Cowork as a connector.
The AppData folder is NOT in the Filesystem MCP allowed directories.

---

## Current pipeline state — COMPLETE ✅

All phases run from scratch this session with inference + action recordings.

### Phase outputs on disk

| Phase | Status | Key outputs |
|-------|--------|-------------|
| 0 — Source Audit | ✅ PASS | source curves confirmed (11 objects) |
| 1 — Site Prep    | ✅ PASS | terrain (err=0, 10×15, 0.0001/0.0001/1.0), pad, driveway, street, curtain wall |
| 2 — Massing      | ✅ PASS | L2 slab X=3.5→17, L1 slab X=9→17, balconies N/S within footprint, no garage box |
| 3 — Detailing    | ✅ PASS | glass=11, mullions=13, doors=1, garage_doors=3, entry_feature=4 |
| 4 — Export       | ✅ PASS | 62 objects imported to Blender, all materials assigned |
| 5 — Render       | ✅ PASS | 144 PNGs + 144 EXRs + 144 depth maps, ocean_view.mp4 encoded |

### Render details
- Resolution: 1920×1080
- Samples: 128 (Cycles)
- Camera: Z=4.5m, 50m distance, orbit 160→200°, target Z=2.5m (L1 windows visible)
- HDRI: qwantani_puresky_2k.hdr, Z rotation=90° (sun in west), strength=1.2
- Beauty: `renders/ocean_view/png/frame_####.png` (144 × ~2 MB)
- EXR passes: `renders/ocean_view/exr/frame_####.exr` (Depth.V + CryptoObject00 + CryptoMaterial00)
- Depth maps: `renders/ocean_view/depth/depth_####.png` (16-bit, globally normalised, near=white)
- MP4: `renders/ocean_view/ocean_view.mp4`

### OBS recordings saved to `screen_captures/`
- phase_0_inference.mp4, phase_0_action.mp4
- phase_1_inference.mp4, phase_1_action.mp4
- phase_2_inference.mp4, phase_2_action.mp4
- phase_3_inference.mp4, phase_3_action.mp4
- phase_4_inference.mp4, phase_4_action.mp4
- phase_5_inference.mp4, phase_5_action.mp4 (78 min — full render)

### Rhino snapshot
`rhino/snapshots/base_model_phase4_20260512_195022.3dm`

### Blender
`base_model.blend` — complete scene with materials, HDRI, camera, compositor

---

## Video production state

Sean is assembling a demo video in DaVinci Resolve.

### Google Drive project folder
Parent: `1JKV0B8jqo8m_CF-9fO2xSR59anmmHiwG`

| Subfolder              | Contents                                                     |
|------------------------|--------------------------------------------------------------|
| `video_captures_raw/`  | 11 source clips (hillside_house_phase_01 through phase_06 + addendums) |
| `Video_source/`        | `Demo_video_script` Google Doc (updated today with voice-over) |
| `renders/`             | Render outputs                                               |
| `documentation/`       | Project docs                                                 |
| `demo_prompts/`        | Prompt files                                                 |
| `rhino_scenes/`        | Rhino files (Phase_03_v7.3dm etc.)                           |
| `architectural_references/` | Reference images                                        |

### Voice-over script
Written this session (~145 words, ~60 seconds). Saved to:
`Demo_video_script` Google Doc ID: `1I4ZsCruJZJxY0zYLqTk31ChTQ378eKonSmZXa4bMPMQ`

Key beat: "What you're watching was built entirely by an AI agent..."

---

## Scripts on disk

| Script | Purpose |
|--------|---------|
| `scripts/extract_passes.py` | Extract depth + cryptomatte from EXR sequence |
| `scripts/comfyui_phase7.py` | Phase 7 ComfyUI automation (dry-run first) |

---

## Open items for next session

1. **DaVinci Resolve MCP config** — add to claude_desktop_config.json
2. **Phase 7 ComfyUI** — run dry-run first: `python scripts\comfyui_phase7.py --dry-run`
   to check what checkpoints and depth ControlNets are loaded on the DGX.
3. **Demo video assembly** — Sean is editing in Resolve.
   New renders from today's session available at `renders/ocean_view/`.
4. **session_state.md** — update after Resolve MCP is connected.

---

## Architecture decisions confirmed this session

- Terrain tolerance: 0.0001 / 0.0001 / 1.0 (both edge and interior)
- Balconies: within footprint, outside upper floor walls (N:Y=8→10, S:Y=-10→-8)
- Floor slab: ONE object per floor, includes cantilever
- Garage: inside lower floor, no external box
- Render resolution: 1920×1080 (production)
- EXR depth channel name: `Depth.V` (FLOAT)
- HDRI sun orientation: Z rotation = 90° puts sun in west (-X)

---

*If anything in this file disagrees with a specific skill file, the skill file wins.*
