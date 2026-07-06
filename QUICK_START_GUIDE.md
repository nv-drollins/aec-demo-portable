# AEC Demo — Quick Start Guide

> This is the original Windows/Claude/Rhino quick start. DGX Spark users should first read `docs/DGX_SPARK_PORT.md` and run `scripts/status-portable-demo.sh`.
### From zero to rendered AI architectural visualization in 30 minutes

---

## What This Demo Does

You will:
1. Open a 3D architectural model in Blender
2. Let Claude (via MCP) render beauty, depth, and segmentation passes
3. Send those passes to ComfyUI running Flux.2 Klein
4. Get three AI-transformed views: photorealistic, environment change, and time-of-day

No manual node-wiring. No command-line work. Claude handles it.

---

## Before You Begin

✅ You have completed the installation (see `docs/INSTALL_GUIDE.md`)
✅ `python setup/system_check.py` passes with no failures
✅ Your `config/user_config.yaml` is filled in

---

## Step 1 — Start All Services (5 minutes)

Open three windows and start each service:

**Terminal 1 — ComfyUI**
```batch
cd D:\tools\comfy_for_blender\ComfyUI_ForDemo
set PYTHONIOENCODING=utf-8
python_embeded\python.exe -X utf8 -s ComfyUI\main.py --windows-standalone-build
```
Wait until you see: `To see the GUI go to: http://127.0.0.1:8188`

**Terminal 2 — Blender**
Open Blender and load: `sample_project/blender_assets/cliff_house_act2_textured_v3.blend`

*(Alternative: `cliff_house_v17.blend` — the earlier, simpler version of the same
house, from before it was customized for the live video demo. Same steps below
work with either file — see README.md "Two Sample Scenes" for the difference.)*

Then in Blender's N panel (press N) → MCP tab → click **Start Server**

**Terminal 3 — Rhino** *(optional, for modeling)*
This drop does not include a bundled `.3dm` — Rhino is only needed if you're
modeling from scratch rather than starting from the Blender sample scene.

**OBS** *(optional, for recording)*
Open OBS Studio. It will connect automatically.

---

## Step 2 — First ComfyUI Run (3 minutes)

This step is required once to create a valid entry in ComfyUI history.

1. Open your browser: http://127.0.0.1:8188
2. Click **Load** (top right)
3. Navigate to `comfyui/workflows/AEC_Transform_Pipeline.json`
4. The workflow loads — do NOT change anything yet
5. Click **Queue** (top right)
6. Wait for it to finish (~20 seconds)

You will see output images appear in: `<comfyui_path>/ComfyUI/output/`

✅ This creates the history entry the scripts need.

---

## Step 3 — Open Claude Desktop (1 minute)

1. Open Claude Desktop
2. Start a new conversation
3. Type: `List my connected MCP tools`

You should see **blender** and **rhinoceros3d** listed. If not, see Troubleshooting in `docs/INSTALL_GUIDE.md`.

---

## Step 4 — Render Your First Pass Set (5 minutes)

In Claude Desktop, type:

> **"Render a new pass"**

Claude will:
- Render a beauty pass (Cycles, 128 samples) from RenderCam
- Render a depth pass (normalised camera depth)
- Render a segmentation pass (material ID colours, EEVEE, transparent background)
- Number the outputs automatically (e.g., `beauty_0001.png`)

Files land in:
```
sample_project/renders/beauty/
sample_project/renders/depth/
sample_project/renders/seg/
```

---

## Step 5 — Submit to ComfyUI (1 minute)

In Blender's Python console (Scripting tab → Python Console):

```python
exec(open(r"C:/AEC_Demo_Portable/scripts/submit_comfyui.py").read())
submit()
```

Or ask Claude:
> **"Submit the current render to ComfyUI"**

Watch the ComfyUI terminal — you'll see the model load and generate.

Output images (~20 seconds):
```
<comfyui_path>/ComfyUI/output/Make_Real_XXXXX_.png
<comfyui_path>/ComfyUI/output/Change_Environment_XXXXX_.png
<comfyui_path>/ComfyUI/output/Time_Of_Day_XXXXX_.png
```

---

## Step 6 — View Results

In Blender, ask Claude:
> **"Load the latest ComfyUI outputs into the Image Editor"**

Or open the output folder directly in Windows Explorer.

---

## Demo Flow at a Glance

```
Rhino 8          →  3D modeling via Claude MCP
    ↓
Blender 5.1      →  Materials, lighting, camera setup
    ↓
render_passes.py →  Beauty + Depth + Seg PNG files
    ↓
ComfyUI          →  Flux.2 Klein AI transformation
    ↓
Output           →  3× photorealistic variations
```

---

## Customising the Prompts

Edit `scripts/submit_comfyui.py` — find the `PROMPTS` dict:

```python
PROMPTS = {
    "1124": "Your Make Real prompt here...",
    "1128": "Your Environment prompt here...",
    "1129": "Your Time of Day prompt here...",
}
```

Then call `submit(render=False)` to reuse the last renders with new prompts.

---

## Useful Claude Commands

Once Claude is connected via MCP, these work directly in the chat:

| Say this... | Claude does... |
|------------|----------------|
| "Render a new pass" | Renders beauty + depth + seg with auto-numbering |
| "Make the glass more reflective" | Updates glass material in Blender |
| "Change the background to medium gray" | Updates world shader, keeps HDRI lighting |
| "Save a snapshot of the scene" | Saves timestamped .blend to snapshots folder |
| "Submit the current render to ComfyUI" | Renders and queues to Flux.2 |
| "Start recording" | Starts OBS capture |
| "Stop recording" | Stops OBS and saves MP4 |

---

## File Structure Reference

```
AEC_Demo_Portable/
├── README.md                    ← You are here
├── QUICK_START_GUIDE.md         ← This file
├── config/
│   └── user_config.yaml         ← Your settings (edit this)
├── setup/
│   ├── system_check.py          ← Run first
│   └── setup_windows.bat        ← Run once as Admin
├── scripts/
│   ├── config_loader.py         ← Shared config utility
│   ├── render_passes.py         ← Render beauty/depth/seg
│   └── submit_comfyui.py        ← Submit to ComfyUI
├── blender/
│   └── auto_comfy.py            ← Blender startup script
├── comfyui/
│   ├── workflows/               ← ComfyUI workflow JSON
│   ├── custom_nodes/            ← aec_utility_nodes
│   └── models/
│       └── MODEL_MANIFEST.md    ← Download links
├── claude/
│   └── claude_desktop_config_template.json
├── assets/
│   └── hdri/                    ← HDRI lighting files
├── sample_project/
│   ├── blender_assets/          ← .blend sample file
│   ├── rhino_assets/            ← .3dm sample file
│   └── renders/                 ← Output renders
└── docs/
    ├── INSTALL_GUIDE.md         ← Full installation
    └── MODEL_MANIFEST.md        ← Model downloads
```

---

## Getting Help

- Installation issues → `docs/INSTALL_GUIDE.md`
- Model downloads → `comfyui/models/MODEL_MANIFEST.md`
- System check → `python setup/system_check.py`
- ComfyUI docs → https://github.com/comfyanonymous/ComfyUI/wiki
- Blender MCP → https://github.com/ahujasid/blender-mcp
- Anthropic Console → https://console.anthropic.com
