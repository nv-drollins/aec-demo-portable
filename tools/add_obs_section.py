
import os

guide = r"C:\Users\swags\Documents\AEC_Demo_Portable\docs\INSTALL_GUIDE.md"
with open(guide, encoding="utf-8") as f:
    content = f.read()

obs_section = """
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

"""

# Insert before Part 8 (Verify)
content = content.replace("---\n\n## Part 8 — Verify", obs_section + "---\n\n## Part 8 — Verify")
with open(guide, "w", encoding="utf-8") as f:
    f.write(content)
print("OBS section added")
print(f"Guide length: {len(content.splitlines())} lines")
