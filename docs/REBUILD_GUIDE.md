# AutoComfy Pipeline — Rebuild Guide
# aec_demo_master / hillside_house ocean_view
# Last updated: May 2026

> **ARCHIVED — describes an older, different pipeline on a different machine.**
> This guide documents the `swags` workstation (`C:\Users\swags\...`, `D:\tools\...`,
> `D:\projects\...`), the ComfyUI-BlenderAI-node "Execute" button, and an
> InstructPix2Pix workflow for the `hillside_house` scene.
>
> The **current** pipeline on this package (`cliff_house_act2_textured_v3.blend`
> + Flux.2 Klein) is a later, separate evolution: it submits directly to
> ComfyUI's `/prompt` endpoint via `scripts/submit_comfyui.py`, bypassing the
> addon's Execute button entirely, so none of the AttributeError/polling-thread
> workarounds below apply to it. See `submit_comfyui.py` and
> [Quick Start](../QUICK_START_GUIDE.md) for the current, working instructions.
>
> Kept here for historical reference only — do not follow these steps for the
> current demo.

## OVERVIEW

This pipeline connects Blender 5.1 → ComfyUI (InstructPix2Pix workflow) for
AI-enhanced architectural visualization renders. The key problem solved: the
ComfyUI-BlenderAI-node addon's "Connect to Comfy" and "Execute" buttons break
silently after every Blender reboot. This system fixes that automatically.

---

## SYSTEM ARCHITECTURE

  Blender 5.1 (Cycles render)
      |
      | ocean_view_rgb.png  →  D:\tools\comfy_for_blender\ComfyUI_ForDemo\ComfyUI\input\
      |
  ComfyUI (http://127.0.0.1:8188)
      |
      | Node graph: ComfyUI Node (in base_model_checkpoint_comfy_01.blend)
      |   Blender RGB Render (LoadImage)
      |     → InstructPixToPixConditioning
      |     → KSampler (FLUX model, UNETLoader)
      |     → VAEDecode → SaveImage
      |   DepthAnythingV2Preprocessor (extracts depth from RGB — no separate depth pass needed)
      |
  Output → D:\tools\comfy_for_blender\ComfyUI_ForDemo\ComfyUI\output\ComfyUI_####.png

---

## FILE LOCATIONS

  Startup script (LIVE):
    C:\Users\swags\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\startup\auto_comfy.py

  Startup script (BACKUP / source of truth):
    C:\Users\swags\Documents\aec_demo_master\claude_config\auto_comfy.py

  Claude Desktop config:
    C:\Users\swags\AppData\Roaming\Claude\claude_desktop_config.json
    Backup: C:\Users\swags\Documents\aec_demo_master\claude_config\claude_desktop_config.json

  Blender file:
    D:\projects\aec_demo_master\hillside_house\base_model_checkpoint_comfy_01.blend
    (or wherever the active .blend lives — check recent files)

  ComfyUI install:
    D:\tools\comfy_for_blender\ComfyUI_ForDemo\ComfyUI\

---

## WHY THE CONNECT BUTTON BREAKS (ROOT CAUSE)

The ComfyUI-BlenderAI-node addon initializes with a FakeServer object.
The Connect button does:

    TaskManager.connect_existing = not TaskManager.connect_existing

But `connect_existing` is never set as a class attribute at init time.
After a reboot, `not TaskManager.connect_existing` raises AttributeError,
which Blender swallows silently. The button appears to do nothing.

Additionally, even if connect_existing were set, the polling threads
(poll_task, poll_res, proc_res, proc_timer) track a `uid` captured at
thread start time. Swapping the server changes the uid, killing those threads.
New threads must be started AFTER the RemoteServer swap.

---

## WHAT auto_comfy.py DOES

1. _auto_connect_comfy() [timer, fires 2s after startup, retries every 10s]:
   - Checks if ComfyUI-BlenderAI-node addon is loaded (sys.modules)
   - If TaskManager.server is FakeServer: creates a RemoteServer, calls wait_connect()
   - On success: swaps server, sets connect_existing=True, sets launch_ip/port/url,
     calls start_polling() to restart threads, calls refresh_current_tree()
   - Then calls _patch_submit() to intercept the Execute button
   - Retries up to 18x (3 minutes) if ComfyUI is not yet running

2. _patch_submit():
   - Replaces Ops.submit with patched_submit
   - patched_submit sets _pending["active"]=True and registers _deferred_render_and_submit timer
   - Stores original as Ops._original_submit (idempotent — only stores once)

3. _deferred_render_and_submit() [timer, 0.1s after Execute click]:
   - Verifies connection, auto-reconnects if dropped
   - Switches scene to Cycles, 64 samples, GPU
   - Calls bpy.ops.render.render(write_still=True) — writes ocean_view_rgb.png
   - Saves Viewer Node depth image if present (optional — DepthAnythingV2 handles it otherwise)
   - Updates "Blender RGB Render" LoadImage node filename
   - Calls TaskManager.push_task(cfu_tree.get_task(), tree=cfu_tree) directly
     (does NOT call bpy.ops.sdn.ops(action="submit") — that recurses into patched_submit)

4. update_comfy_viewer() [timer, every 2s]:
   - Watches ComfyUI output folder for new ComfyUI_####.png files
   - Auto-loads newest into Image Editor (area.x > 1900 — assumes dual-monitor, editor on right)

5. on_load_post handler:
   - Resets _connect_state and re-runs _register() on every .blend file open

---

## RENDER SETTINGS

  Engine:  CYCLES (NOT EEVEE — EEVEE crashes Blender 5.1 when render.render()
           is called from inside an operator/timer context)
  Device:  GPU
  Samples: 64 (good balance for ComfyUI input — not too noisy, fast enough)
  Output:  D:\tools\comfy_for_blender\ComfyUI_ForDemo\ComfyUI\input\ocean_view_rgb.png
  Format:  PNG, RGB

---

## MCP SERVERS (claude_desktop_config.json)

  rhinoceros3d  →  npx mcp-remote http://localhost:3001/mcp
                   (Rhino MCP server, must be running in Rhino)

  obs           →  npx -y obs-mcp@latest
                   (OBS WebSocket, password: REPLACE_WITH_YOUR_OBS_PASSWORD)

  blender       →  npx mcp-remote http://localhost:9876/mcp
                   (BlenderMCP — must run bpy.ops.blendermcp.start_server() in
                    Blender Scripting tab after each launch)

  davinci-resolve → python D:\tools\Davinci\davinci-resolve-mcp\src\server.py
                    (DaVinci Resolve MCP — wired but not yet tested end-to-end)

---

## REBUILD STEPS (fresh machine or after reinstall)

### 1. Install ComfyUI-BlenderAI-node addon
   - Source: https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node
   - Install into Blender 5.1 via Edit > Preferences > Add-ons > Install from disk
   - Install path: C:\Users\swags\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\

### 2. Configure addon preferences
   - In Blender: Edit > Preferences > Add-ons > ComfyUI BlenderAI Node
   - Server Type: Remote
   - Server IP: 127.0.0.1
   - Port: 8188

### 3. Deploy startup script
   - Copy auto_comfy.py from this folder to:
     C:\Users\swags\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\startup\
   - Verify path constants at top of file match current install

### 4. Deploy Claude Desktop config
   - Copy claude_desktop_config.json from this folder to:
     C:\Users\swags\AppData\Roaming\Claude\claude_desktop_config.json
   - Restart Claude Desktop

### 5. Start BlenderMCP each session
   - Open Blender > Scripting tab > run:
       bpy.ops.blendermcp.start_server()
   - Confirm port 9876 is listening (check Task Manager or netstat)

### 6. ComfyUI model requirements
   The node graph uses:
   - FLUX UNET model (UNETLoader)
   - Dual CLIP (DualCLIPLoader)
   - VAE (VAELoader)
   - DepthAnythingV2 preprocessor
   - InstructPixToPixConditioning node

   If models are missing, ComfyUI will error on queue. Check ComfyUI console.

---

## TROUBLESHOOTING

### "Connect to Comfy" does nothing
  Root cause: connect_existing AttributeError (see above).
  Fix: auto_comfy.py handles this automatically on startup.
  Manual fix if needed — run in Blender Scripting tab:

    import sys
    manager_m = sys.modules['ComfyUI-BlenderAI-node.SDNode.manager']
    TaskManager = manager_m.TaskManager
    remote = manager_m.RemoteServer()
    if remote.wait_connect():
        TaskManager.server = remote
        TaskManager.connect_existing = True
        TaskManager.launch_ip = manager_m.get_ip()
        TaskManager.launch_port = manager_m.get_port()
        TaskManager.launch_url = manager_m.get_url()
        TaskManager.start_polling()
        print("Connected:", TaskManager.is_launched())

### Execute button does nothing after reboot
  Cause: _patch_submit() hasn't run yet (auto-connect timer hasn't fired).
  Wait 2-3 seconds after Blender opens, or check Blender System Console
  for "[AutoComfy] RemoteServer connected" message.

### Render produces black image
  Cause: EEVEE was active. auto_comfy.py forces Cycles before every render.
  Also check: camera is not inside geometry, scene has a light source.

### ComfyUI errors on queue (invalid node / model missing)
  Check ComfyUI web UI at http://127.0.0.1:8188 for error details.
  Common causes: missing model file, wrong node connection, VRAM overflow.

### BlenderMCP drops after idle
  Known issue. Re-run bpy.ops.blendermcp.start_server() in Scripting tab.
  This does NOT affect the ComfyUI pipeline — they use different ports.

### Polling threads die after server swap
  Cause: poll_task thread exits when server uid changes.
  Fix: call TaskManager.start_polling() again after swapping server.
  auto_comfy.py handles this correctly in _auto_connect_comfy().

---

## NODE GRAPH STRUCTURE (ComfyUI Node group in .blend)

  Key nodes:
    "Blender RGB Render"  (bl_idname: LoadImage) — input from Blender render
    "Input Image"         (bl_idname: 输入图像)   — alternate input node
    "DepthAnythingV2Preprocessor"               — generates depth map from RGB
    "InstructPixToPixConditioning"              — main conditioning node
    "KSampler"                                  — diffusion sampler
    "UNETLoader"                                — FLUX model
    "DualCLIPLoader"                            — text encoder
    "VAELoader" / "VAEEncode" / "VAEDecode"     — latent space
    "Save" / "SaveImage" / "Save.001"           — output nodes
    "Preview" / "PreviewImage"                  — preview nodes

  The graph does NOT need a separate Blender depth pass.
  DepthAnythingV2 infers depth from the RGB render automatically.

---

## SESSION STARTUP CHECKLIST

  [ ] Start ComfyUI:
        cd D:\tools\comfy_for_blender\ComfyUI_ForDemo\ComfyUI
        python main.py --listen
  [ ] Start Blender 5.1
  [ ] Open base_model_checkpoint_comfy_01.blend
  [ ] Open Scripting tab → run: bpy.ops.blendermcp.start_server()
  [ ] Wait ~3s for "[AutoComfy] RemoteServer connected" in System Console
  [ ] Switch to ComfyUI node editor area
  [ ] Click Execute — render fires automatically, result appears in Image Editor

---
