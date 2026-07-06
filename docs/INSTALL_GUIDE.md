# AEC Demo — Full Installation Guide

## Overview

This guide installs everything needed to run the AEC Demo:
1. Operating system prerequisites
2. Python and Node.js
3. Blender 5.1 with addons
4. ComfyUI with models and custom nodes
5. Rhino 8 with MCP plugin
6. Claude Desktop with MCP configuration
7. OBS Studio (for recording)

Estimated time: **2–4 hours** (mostly model download time)

---

## Part 1 — Operating System Setup

### 1.1 Windows Requirements
- Windows 10 or 11 (64-bit)
- NVIDIA GPU with 16+ GB VRAM (RTX 3090 or better)
- Latest NVIDIA drivers: https://www.nvidia.com/en-us/drivers/
- CUDA Toolkit 12.x: https://developer.nvidia.com/cuda-downloads

### 1.2 Enable Hyper-V (required for npx/Docker)
Open PowerShell as Administrator:
```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```
Restart your computer.

### 1.3 Run Environment Setup
```
Right-click setup\setup_windows.bat → Run as Administrator
```
This sets ANTHROPIC_API_KEY, opens firewall ports, and installs Python packages.

### 1.4 Firewall Ports
The following ports must be open on **localhost only** (no external access needed):

| Port | Service |
|------|---------|
| 8188 | ComfyUI |
| 9876 | BlenderMCP |
| 3001 | RhinoMCP |
| 4455 | OBS WebSocket |

---

## Part 2 — Python and Node.js

### 2.1 Python 3.11+
Download: https://www.python.org/downloads/
- ✅ Check "Add Python to PATH" during install
- Verify: `python --version`

Install required packages:
```bash
pip install pyyaml requests Pillow numpy
```

### 2.2 Node.js 18+
Download: https://nodejs.org/en/download
- Use the LTS version
- Verify: `node --version` and `npx --version`

---

## Part 3 — Blender 5.1

### 3.1 Download and Install
https://www.blender.org/download/

Download **Blender 5.1** (or the version specified in user_config.yaml).
Install to: `C:\Program Files\Blender Foundation\Blender 5.1\`

### 3.2 BlenderMCP Addon
1. Download: https://github.com/ahujasid/blender-mcp/releases
2. In Blender: Edit → Preferences → Add-ons → Install
3. Navigate to the downloaded `.zip`
4. Enable the addon
5. In the N panel (press N in viewport) → MCP tab → Start Server
6. Verify port 9876 is shown

### 3.3 ComfyUI Blender Addon
1. Download: https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node
2. Install the same way as above
3. Open the N panel → ComfyUI tab
4. Set ComfyUI server URL to `http://127.0.0.1:8188`

### 3.4 Install Startup Script
Copy `blender/auto_comfy.py` to:
```
%APPDATA%\Blender Foundation\Blender\5.1\scripts\startup\auto_comfy.py
```
This script patches the ComfyUI addon's Execute button to render and submit automatically.

### 3.5 Load the Sample Scene
Open `sample_project/blender_assets/beach_house_02.blend`

---

## Part 4 — ComfyUI

### 4.1 Download ComfyUI
```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
```
Or download the Windows portable package:
https://github.com/comfyanonymous/ComfyUI/releases

### 4.2 Recommended Directory
Install to: `D:\tools\comfy_for_blender\ComfyUI_ForDemo\`
(Or change the path in `config/user_config.yaml`)

### 4.3 Install Custom Nodes
From `ComfyUI/custom_nodes/`, run:
```bash
# Copy bundled AEC nodes
xcopy /E /I "PATH_TO\AEC_Demo_Portable\comfyui\custom_nodes\aec_utility_nodes" ".\aec_utility_nodes"

# Install community nodes via ComfyUI Manager
# First install Manager:
cd custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager
```
Then launch ComfyUI and use Manager → Install Missing Custom Nodes.

See `comfyui/models/MODEL_MANIFEST.md` for the full list.

### 4.4 Download Models
See `comfyui/models/MODEL_MANIFEST.md` for download links and locations.
Total download: ~23 GB for the required models.

### 4.5 Install the Workflow
Copy `comfyui/workflows/AEC_Transform_Pipeline.json` to:
```
<comfyui_path>/ComfyUI/user_prompt/AEC_Transform_Pipeline.json
```

### 4.6 Start ComfyUI

> ⚠️ **CRITICAL — Windows encoding flags required.** ComfyUI will crash immediately
> without these. This is not optional.

```batch
cd D:\tools\comfy_for_blender\ComfyUI_ForDemo
set PYTHONIOENCODING=utf-8
python_embeded\python.exe -X utf8 -s ComfyUI\main.py --windows-standalone-build
```

Wait for: `To see the GUI go to: http://127.0.0.1:8188`
Then open: http://127.0.0.1:8188

### 4.6b Install packages in ComfyUI's embedded Python

```batch
cd D:\tools\comfy_for_blender\ComfyUI_ForDemo
python_embeded\python.exe -m pip install requests pyyaml Pillow numpy
```

These are required by the AEC demo scripts.

### 4.7 First Run — Load Workflow in Browser
1. Open http://127.0.0.1:8188
2. Click "Load" → select `AEC_Transform_Pipeline.json`
3. Set the LoadImage nodes to use your input files
4. Click "Queue" — this creates the first entry in history
5. **This step is required before the scripts can work**

---

## Part 5 — Rhino 8

### 5.1 Download
https://www.rhino3d.com/download/
(Requires a paid license or 90-day trial)

### 5.2 RhinoMCP Plugin
1. Download: https://github.com/SerjoschDuering/rhino-mcp
2. In Rhino: Tools → Options → Plug-ins → Install
3. Or type `_PackageManager` in Rhino and search "mcp"
4. After installing, type `mcp_server_start` in the Rhino command line
5. Verify it starts on port 3001

### 5.3 Load the Sample Model
Open `sample_project/rhino_assets/beach_house_02.3dm`

---

## Part 6 — Claude Desktop

### 6.1 Download
https://claude.ai/download

Install Claude Desktop for Windows.

### 6.2 Configure MCP Servers
1. Copy `claude/claude_desktop_config_template.json` to:
   `%APPDATA%\Claude\claude_desktop_config.json`
2. Edit the file:
   - Replace `REPLACE_WITH_YOUR_OBS_PASSWORD` with your OBS password
   - Remove the `davinci-resolve` block if not using DaVinci
3. Restart Claude Desktop completely (check Task Manager)

### 6.3 Set API Key
Claude Desktop uses your Anthropic account login — no API key needed in the app itself.
However the **scripts** (render_passes.py, submit_comfyui.py) use the API key from:
- `config/user_config.yaml` → `anthropic.api_key`
- OR the `ANTHROPIC_API_KEY` environment variable

Get your API key at: https://console.anthropic.com

### 6.4 Verify MCP Connections
In Claude Desktop, start a new chat. Type:
```
List all my connected MCP tools
```
You should see: blender, rhinoceros3d, obs (and optionally davinci-resolve).

---

## Part 7 — OBS Studio (Recording)

### 7.1 Download
https://obsproject.com/download

### 7.2 Configure WebSocket
1. Tools → WebSocket Server Settings
2. Enable WebSocket server
3. Set port to 4455
4. Set a password (note it in `user_config.yaml`)
5. Click OK → restart OBS


---

## Part 7 — OBS Studio (Recording)

### 7.1 Download
https://obsproject.com/download

### 7.2 Configure WebSocket
1. Tools → WebSocket Server Settings
2. Enable WebSocket server
3. Set port: **4455**
4. Set a password and add it to `config/user_config.yaml` → `obs.websocket_password`
5. Click OK and restart OBS

### 7.3 Required OBS Scenes and Sources
The demo uses these OBS scenes. Create them manually or import the profile:

**Scene: `Claude-rhino_capture`**
| Source Name | Type | Notes |
|---|---|---|
| `claude_window` | Window Capture | Capture Claude Desktop window |
| `Rhino_window` | Window Capture | Capture Rhino 3D window |
| `blender_window` | Window Capture | Capture Blender window |
| `Display Capture` | Display Capture | Full screen fallback |

**Scene: `CLAUDE`** (used during Claude-only phases)
| Source Name | Type | Notes |
|---|---|---|
| `claude_window` | Window Capture | Claude Desktop only |

### 7.4 Output Settings
- Output → Recording → Output Path: set to your project's `demo_captures/` folder
- Format: MP4
- Encoder: NVIDIA NVENC H.264 (or x264 if no GPU)

### 7.5 OBS Tools (in `tools/obs/`)
- `obs_recorder.py` — Python script for programmatic recording control
- `obs_recorder_config.json` — OBS connection settings
- `launch_obs_recorder.bat` — Quick launcher

---

## Part 8 — Verify Installation

Run the system check:
```bash
python setup/system_check.py
```

All items should show [PASS] or at worst [WARN].
Fix any [FAIL] items before proceeding.

---

## Troubleshooting

**BlenderMCP won't start:**
- Check Hyper-V is enabled
- Try port 9876 manually: `netstat -ano | findstr 9876`

**ComfyUI model not found:**
- Check the exact path — `klein/` subfolder is required
- Restart ComfyUI after adding models

**"No successful prompt in history":**
- You must run the workflow in the ComfyUI browser first (Step 4.7)
- The pinned prompt ID in `submit_comfyui.py` must match a real run

**MCP server not connecting in Claude:**
- Check `claude_desktop_config.json` was saved correctly
- Restart Claude Desktop completely (not just the window)
- Verify `npx` works: `npx --version` in a terminal
