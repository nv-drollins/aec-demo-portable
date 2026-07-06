import bpy, os, glob, sys
from bpy.app.handlers import persistent

COMFY_INPUT       = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\input"
COMFY_OUTPUT      = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\output"
RGB_FILE          = "beach_house_rgb.png"
DEPTH_FILE        = "beach_house_depth.png"
FIXED_OUTPUT      = os.path.join(COMFY_OUTPUT, "beach_house_latest.png")
VIEWER_IMAGE_NAME = "beach_house_latest"

# ── Image Editor viewer ───────────────────────────────────────────────
def get_image_editor():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "IMAGE_EDITOR":
                return area
    return None

_last_viewer = {"mtime": 0.0}

def update_comfy_viewer():
    if not os.path.exists(FIXED_OUTPUT):
        return 2.0
    mtime = os.path.getmtime(FIXED_OUTPUT)
    if mtime == _last_viewer["mtime"]:
        return 2.0
    area = get_image_editor()
    if not area:
        return 2.0
    img = bpy.data.images.get(VIEWER_IMAGE_NAME)
    if img is None:
        img = bpy.data.images.load(FIXED_OUTPUT, check_existing=False)
        img.name = VIEWER_IMAGE_NAME
    else:
        img.reload()
    area.spaces[0].image = img
    _last_viewer["mtime"] = mtime
    print(f"[AutoComfy] Viewer reloaded -> {VIEWER_IMAGE_NAME}")
    return 2.0

# ── Auto-connect RemoteServer ─────────────────────────────────────────
_connect_state = {"attempts": 0, "done": False}

def _auto_connect_comfy():
    if _connect_state["done"]:
        return None
    manager_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.manager')
    if not manager_m:
        _connect_state["attempts"] += 1
        if _connect_state["attempts"] < 18:
            return 10.0
        print("[AutoComfy] Addon never loaded — giving up")
        _connect_state["done"] = True
        return None
    TaskManager  = manager_m.TaskManager
    RemoteServer = manager_m.RemoteServer
    if TaskManager.is_launched():
        print("[AutoComfy] RemoteServer already connected")
        _connect_state["done"] = True
        _patch_submit()
        return None
    print(f"[AutoComfy] Connecting to ComfyUI ({manager_m.get_url()}) ...")
    try:
        remote    = RemoteServer()
        connected = remote.wait_connect()
    except Exception as e:
        print(f"[AutoComfy] Connection error: {e}")
        connected = False
    if connected:
        TaskManager.server           = remote
        TaskManager.connect_existing = True
        TaskManager.launch_ip        = manager_m.get_ip()
        TaskManager.launch_port      = manager_m.get_port()
        TaskManager.launch_url       = manager_m.get_url()
        TaskManager.start_polling()
        ops_m = sys.modules.get('ComfyUI-BlenderAI-node.ops')
        if ops_m:
            try:
                ops_m.CFNodeTree.refresh_current_tree()
            except Exception:
                pass
        _patch_submit()
        _connect_state["done"] = True
        print(f"[AutoComfy] RemoteServer connected  url={TaskManager.launch_url}")
        return None
    _connect_state["attempts"] += 1
    if _connect_state["attempts"] < 18:
        print(f"[AutoComfy] Not ready (attempt {_connect_state['attempts']}) — retrying in 10s")
        return 10.0
    print("[AutoComfy] Could not connect — giving up")
    _connect_state["done"] = True
    return None

# ── Deferred Render + Submit ──────────────────────────────────────────
_pending = {"active": False}

def _deferred_render_and_submit():
    if not _pending["active"]:
        return None
    _pending["active"] = False
    manager_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.manager')
    ops_m     = sys.modules.get('ComfyUI-BlenderAI-node.ops')
    if not manager_m or not ops_m:
        print("[AutoComfy] ERROR: addon modules missing")
        return None
    TaskManager = manager_m.TaskManager
    if not TaskManager.is_launched():
        print("[AutoComfy] Not connected — auto-reconnecting before submit")
        _connect_state["done"] = False
        bpy.app.timers.register(_auto_connect_comfy, first_interval=0.5)
        _pending["active"] = True
        bpy.app.timers.register(_deferred_render_and_submit, first_interval=5.0)
        return None

    scene = bpy.context.scene

    # Render — camera position controlled entirely by keyframes
    orig_samples                            = scene.cycles.samples
    scene.render.engine                     = "CYCLES"
    scene.cycles.samples                    = 128
    scene.cycles.use_denoising             = True
    scene.render.filepath                   = os.path.join(COMFY_INPUT, RGB_FILE)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode  = "RGB"

    print("[AutoComfy] Rendering (Cycles 128 samples)...")
    bpy.ops.render.render(write_still=True)
    print(f"[AutoComfy] RGB saved -> {scene.render.filepath}")
    scene.cycles.samples = orig_samples

    # Update LoadImage node
    cfu_tree = bpy.data.node_groups.get("ComfyUI Node")
    if not cfu_tree:
        print("[AutoComfy] ERROR: ComfyUI Node tree not found")
        return None
    try:
        # Try both node names (Beauty = AEC pipeline, Blender RGB Render = legacy)
        n = cfu_tree.nodes.get("Beauty") or cfu_tree.nodes.get("Blender RGB Render")
        if n:
            n.image = RGB_FILE
            print(f"[AutoComfy] LoadImage node '{n.name}' set to {RGB_FILE}")
    except Exception as e:
        print(f"[AutoComfy] LoadImage error: {e}")

    # Submit to ComfyUI
    try:
        TaskManager.push_task(cfu_tree.get_task(), tree=cfu_tree)
        print("[AutoComfy] Task submitted to ComfyUI ✓")
    except Exception as e:
        print(f"[AutoComfy] push_task error: {e}")
    return None

# ── Patch Ops.submit ──────────────────────────────────────────────────
def _patch_submit():
    ops_m = sys.modules.get('ComfyUI-BlenderAI-node.ops')
    if not ops_m:
        return
    Ops = getattr(ops_m, 'Ops', None)
    if not Ops:
        return
    if not hasattr(Ops, '_original_submit'):
        Ops._original_submit = Ops.submit
    def patched_submit(self):
        print("[AutoComfy] Execute — queuing Cycles render...")
        _pending["active"] = True
        bpy.app.timers.register(_deferred_render_and_submit, first_interval=0.1)
    Ops.submit = patched_submit
    print("[AutoComfy] Ops.submit patched")

# ── Handlers ─────────────────────────────────────────────────────────
@persistent
def on_load_post(filepath):
    _connect_state["done"]     = False
    _connect_state["attempts"] = 0
    _register()
    print("[AutoComfy] Re-registered after file load")

# ── Register ──────────────────────────────────────────────────────────
def _register():
    if not bpy.app.timers.is_registered(update_comfy_viewer):
        bpy.app.timers.register(update_comfy_viewer, first_interval=2.0, persistent=True)
    if not bpy.app.timers.is_registered(_auto_connect_comfy):
        bpy.app.timers.register(_auto_connect_comfy, first_interval=2.0, persistent=True)
    bpy.app.handlers.load_post[:] = [
        h for h in bpy.app.handlers.load_post if getattr(h, '__name__', '') != 'on_load_post'
    ]
    bpy.app.handlers.load_post.append(on_load_post)
    if os.path.exists(FIXED_OUTPUT):
        area = get_image_editor()
        if area:
            img = bpy.data.images.get(VIEWER_IMAGE_NAME)
            if img is None:
                img = bpy.data.images.load(FIXED_OUTPUT, check_existing=False)
                img.name = VIEWER_IMAGE_NAME
            area.spaces[0].image = img
            _last_viewer["mtime"] = os.path.getmtime(FIXED_OUTPUT)

_register()
print("[AutoComfy] Startup loaded — camera controlled by keyframes, no overrides")
