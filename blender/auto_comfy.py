import bpy, os, glob, sys
from bpy.app.handlers import persistent

COMFY_INPUT  = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\input"
COMFY_OUTPUT = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\output"

# Tracks whether the heavy (5000-class) ComfyUI node-type registration has
# already succeeded this Blender session. Running it again is what crashed
# Blender on file load. We only ever do it once per process.
_NODE_TYPES_DONE_THIS_SESSION = False


def _patch_traceback_suggestions():
    """Disable Python 3.13's 'did you mean' attribute suggestions.

    Why: Blender 5.1 ships Python 3.13. When the ComfyUI-BlenderAI-node addon's
    update_tick() raises AttributeError on a partially-loaded node, its except
    block calls traceback.print_exc(). Python 3.13's traceback machinery then
    calls _compute_suggestion_error -> dir(node), and dir() on an RNA struct
    with a stale property name dereferences a dangling string in strcmp,
    causing a hard EXCEPTION_ACCESS_VIOLATION crash.

    Returning None from _compute_suggestion_error makes traceback skip
    suggestion computation entirely, sidestepping the dir() crash.
    """
    try:
        import traceback as _tb
        if not hasattr(_tb, '_compute_suggestion_error_original'):
            _tb._compute_suggestion_error_original = _tb._compute_suggestion_error
            _tb._compute_suggestion_error = lambda *a, **kw: None
            print('[AutoComfy] Python 3.13 traceback._compute_suggestion_error neutered (prevents RNA-iteration crashes)')
    except Exception as _e:
        print(f'[AutoComfy] could not patch traceback suggestions: {_e}')


_patch_traceback_suggestions()


def _patch_update_tree_handler():
    """Replace the addon's per-tick CFNodeTree.update_tree_handler with a
    no-op to permanently prevent the EXCEPTION_ACCESS_VIOLATION crash.

    Why: the original handler called update_tick() -> compute_execution_order()
    every second, which iterated `node.inputs[k].links`. After a CFNodeTree
    had any stale RNA pointer in its link table (very easy to reach: node
    deletions, addon reregistration, save+reload of a tree with foreign
    custom-nodes, etc.), the C iterator NodeTree_links_next dereferenced a
    dangling pointer and crashed Blender. Python try/except cannot catch
    C-level access violations.

    Workflow submission still works because tree.serialize() / get_task()
    call compute_execution_order() explicitly on user action.
    """
    try:
        tree_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.tree')
        if not tree_m:
            return 2.0  # retry later when addon is loaded
        CFNodeTree = tree_m.CFNodeTree
        # Re-define as a no-op (return 1 = re-fire in 1s, but does nothing)
        def _noop_handler():
            return 1
        if getattr(CFNodeTree.update_tree_handler, '__name__', '') == '_noop_handler':
            return None  # already patched
        # Unregister live timer (if any), then swap the static method
        try:
            if bpy.app.timers.is_registered(CFNodeTree.update_tree_handler):
                bpy.app.timers.unregister(CFNodeTree.update_tree_handler)
        except Exception:
            pass
        _noop_handler.__name__ = '_noop_handler'
        CFNodeTree.update_tree_handler = staticmethod(_noop_handler)
        try:
            if not bpy.app.timers.is_registered(CFNodeTree.update_tree_handler):
                bpy.app.timers.register(CFNodeTree.update_tree_handler, persistent=True)
        except Exception:
            pass
        print('[AutoComfy] CFNodeTree.update_tree_handler replaced with no-op (prevents idle-tick crashes)')
    except Exception as e:
        print(f'[AutoComfy] could not patch update_tree_handler: {e}')
    return None


bpy.app.timers.register(_patch_update_tree_handler, first_interval=2.0)


def _register_comfyui_node_types():
    """Workaround for ComfyUI-BlenderAI-node not auto-registering its types on Blender 5.1.

    Bugs the addon has on this Blender/Python version:
      1) bundled lupa lacks Python 3.13 binaries -> animatedimageplayer import fails
         (separately fixed by edit to animatedimageplayer.py)
      2) auto_comfy's connect path connects RemoteServer but never calls nodes_m.reg(),
         so SDNConfig/MLTRec/etc. (foundation PropertyGroups) stay unregistered.
         Every node has CollectionProperty(type=SDNConfig) etc, so every register_class
         then cascades to failure with a misleading "long socket" error message.
      3) /object_info fetch timeout (2s) too short for large ComfyUI installs.
      4) Two custom-node socket bl_idnames exceed Blender's 64-char limit (FILE_3D
         multi-type sockets); the stock register loop is non-tolerant.

    This function:
      a) registers the 14 foundation classes (clss list) one-by-one tolerantly
      b) re-fetches /object_info with a 30s timeout
      c) registers all socket+node classes one-by-one tolerantly
      d) calls clear_nodes()+load_json_ex(data) if the saved tree is missing nodes
    Result: full graph view, all node types resolved.
    """
    import time, traceback, types, json, requests
    from pathlib import Path
    global _NODE_TYPES_DONE_THIS_SESSION
    if _NODE_TYPES_DONE_THIS_SESSION:
        print('[AutoComfy] node fixer: already done this session, skipping (safe)')
        return None
    nodes_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.nodes')
    if not nodes_m:
        print('[AutoComfy] node fixer: addon not loaded yet, will retry')
        return 5.0
    nt = bpy.data.node_groups.get('ComfyUI Node')
    mgr_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.manager')
    push_patched = bool(mgr_m and hasattr(mgr_m.TaskManager, '_original_push_task'))
    alias_done = '预览' in nodes_m.NodeRegister.CLSS_MAP
    if (nt and len(nt.nodes) > 50
        and sum(1 for n in nt.nodes if n.bl_idname == 'NodeUndefined') == 0
        and len(nodes_m.NodeRegister.CLSS_MAP) > 100
        and push_patched and alias_done):
        print('[AutoComfy] node fixer: already fully registered + patched, skipping')
        return None

    # Apply patches that do NOT depend on ComfyUI being reachable FIRST.
    # The Ollama-model + ResizeImageMaskNode push_task patch is critical for
    # the Execute button to ever submit a valid prompt. The 预览 alias only
    # needs PreviewImage to be in CLSS_MAP. Neither requires a live ComfyUI
    # connection, so we shouldn't gate them on the network probe below.
    # IMPORTANT: do NOT register `预览` / `Preview` as aliases of `PreviewImage`.
    # Doing so makes Blender adopt saved nodes-whose-class-was-stale (the .blend
    # records their `bl_idname` as `Preview`/`预览`) — but those nodes have a
    # dangling RNA-backed CollectionProperty (`prev`) from being saved before
    # the class existed. The addon's update_tick -> set_width then does
    # `bool(self.prev)` and dereferences the dangling pointer -> hard
    # EXCEPTION_ACCESS_VIOLATION at the C level (uncatchable in Python).
    # Leaving the aliases unregistered means those nodes load as NodeUndefined
    # and the addon skips them via `node.is_registered_node_type()`. Cost:
    # 7 red NodeUndefined nodes show in the tree; user can delete + re-add
    # as PreviewImage if they want them back. Safety > convenience.
    try:
        NR = nodes_m.NodeRegister
        # Clean up any old aliases that may have been registered in earlier
        # sessions and survived to the next file load.
        for _alias in ('预览', 'Preview'):
            if _alias in NR.CLSS_MAP and _alias != 'PreviewImage':
                _cls = NR.CLSS_MAP.pop(_alias, None)
                if _cls is not None:
                    try: bpy.utils.unregister_class(_cls)
                    except Exception: pass
                print(f'[AutoComfy] removed unsafe alias {_alias!r} (prevents crash on saved Preview nodes)')
        if mgr_m and not hasattr(mgr_m.TaskManager, '_original_push_task'):
            mgr_m.TaskManager._original_push_task = mgr_m.TaskManager.push_task
            def _patched_push_task(task, tree=None, *args, **kwargs):
                # NOTE: do NOT call bpy.ops.render.render() from here.
                # push_task is invoked from the Execute operator; nesting a sync
                # render inside crashes Blender. Use the AEC > Render + Submit
                # button (or call submit() from the Python console) when you
                # want fresh Beauty/Seg from the current camera.
                try:
                    import random as _rnd, time as _tm
                    _batch = _tm.strftime('Comfy_%Y%m%d_%H%M%S')
                    _tagged = False
                    for nid, ndata in list(task.get('prompt', {}).items()):
                        inner = ndata[0] if isinstance(ndata, tuple) else ndata
                        ct = inner.get('class_type', '')
                        inputs = inner.setdefault('inputs', {})
                        if ct == 'OllamaConnectivityV2':
                            if not inputs.get('model'):
                                inputs['model'] = 'qwen3-vl:latest'
                                print(f'[push_task] inject Ollama model qwen3-vl:latest into {nid}')
                        if ct == 'ResizeImageMaskNode':
                            rt = inputs.get('resize_type')
                            if isinstance(rt, list):
                                inputs['resize_type.match'] = rt
                                inputs['resize_type'] = 'match size'
                                inputs.setdefault('resize_type.crop', 'center')
                            elif rt is None:
                                inputs['resize_type'] = 'scale dimensions'
                                inputs['resize_type.width'] = 512
                                inputs['resize_type.height'] = 512
                                inputs.setdefault('resize_type.crop', 'center')
                        if ct == 'RandomNoise' and 'noise_seed' in inputs:
                            inputs['noise_seed'] = _rnd.randint(0, 2**32 - 1)
                        elif ct in ('KSampler', 'KSamplerAdvanced') and 'seed' in inputs:
                            inputs['seed'] = _rnd.randint(0, 2**32 - 1)
                        if ct == 'SaveImage':
                            base = str(inputs.get('filename_prefix', ''))
                            if not base.startswith('Comfy_'):
                                inputs['filename_prefix'] = f'{_batch}_{base}'
                                _tagged = True
                    if _tagged:
                        print(f'[push_task] seeds randomized & outputs tagged {_batch}_')
                except Exception as _e:
                    print(f'[push_task] patch error: {_e}')
                return mgr_m.TaskManager._original_push_task(task, tree=tree, *args, **kwargs)
            mgr_m.TaskManager.push_task = _patched_push_task
            print('[AutoComfy] push_task patched (auto-render + Ollama + Resize + seeds + batch prefix)')
    except Exception as _e:
        print(f'[AutoComfy] critical-patch step error: {_e}')
        traceback.print_exc()

    # Now check ComfyUI reachability for the heavier node-type registration.
    # If it's busy (>5s response), defer; otherwise proceed.
    try:
        requests.get('http://127.0.0.1:8188/object_info',
                     proxies={'http': None, 'https': None}, timeout=5)
    except Exception:
        print('[AutoComfy] node fixer: ComfyUI slow/unreachable - critical patches still applied, retry node-type sync later')
        return 10.0
    try:
        # (a) foundation classes
        foundation_ok = 0
        for c in nodes_m.clss:
            try: bpy.utils.unregister_class(c)
            except Exception: pass
            try:
                bpy.utils.register_class(c)
                foundation_ok += 1
            except Exception as e:
                print(f'[AutoComfy] foundation {c.__name__}: {e}')
        print(f'[AutoComfy] foundation classes registered: {foundation_ok}/{len(nodes_m.clss)}')

        # (b)+(c) parse and register all ComfyUI node types
        parser = nodes_m.NodeParser()
        def _fetch_long(self):
            try:
                req = requests.get('http://127.0.0.1:8188/object_info',
                                   proxies={'http':None,'https':None}, timeout=30)
                if req.status_code == 200:
                    cur = req.json()
                    self.ori_object_info.update(cur)
                    self.ori_object_info = cur
            except Exception:
                traceback.print_exc()
        parser._fetch_object_from_server = types.MethodType(_fetch_long, parser)
        t0 = time.time()
        _, node_clss, socket_clss = parser.parse()
        ok_s = ok_n = 0
        for c in socket_clss:
            try: bpy.utils.register_class(c); ok_s += 1
            except Exception: pass
        for c in node_clss:
            try:
                bpy.utils.register_class(c)
                nodes_m.NodeRegister.CLSS_MAP[c.bl_label] = c
                ok_n += 1
            except Exception: pass
        print(f'[AutoComfy] node types registered: {ok_s} sockets, {ok_n} nodes in {time.time()-t0:.1f}s')

        # (d) auto-reload AEC workflow if tree looks truncated
        nt = bpy.data.node_groups.get('ComfyUI Node')
        workflow = Path(r'C:/Users/NVIDIA/ComfyUI/ComfyUI_windows_portable/ComfyUI/user_prompt/AEC_Transform_Pipeline.json')
        if nt and workflow.exists():
            with open(workflow, encoding='utf-8') as f:
                data = json.load(f)
            expected = len(data.get('nodes', []))
            current  = len(nt.nodes)
            if current < expected:
                print(f'[AutoComfy] tree has {current} nodes, workflow JSON has {expected}; reloading')
                nt.clear_nodes()
                nt.load_json_ex(data)
                print(f'[AutoComfy] tree now: {len(nt.nodes)} nodes')

        # (e) register the 预览 (Chinese: "Preview") alias for PreviewImage.
        # The addon's load_json_wrapper renames PreviewImage->预览 on load, but later
        # unregisters 预览 as "unused" because ComfyUI's /object_info only ships
        # PreviewImage. That orphans every Preview node in the tree -> save_json
        # raises "Invalid Node Type: Preview". Re-register as an alias.
        try:
            PreviewCls = nodes_m.NodeRegister.CLSS_MAP.get('PreviewImage')
            if PreviewCls and '预览' not in nodes_m.NodeRegister.CLSS_MAP:
                AliasCls = type('预览', (PreviewCls,), {'bl_label': '预览', 'class_type': 'PreviewImage'})
                bpy.utils.register_class(AliasCls)
                nodes_m.NodeRegister.CLSS_MAP['预览'] = AliasCls
                print('[AutoComfy] registered 预览 alias for PreviewImage')
        except Exception as e:
            print(f'[AutoComfy] 预览 alias registration failed: {e}')

        # (f) monkey-patch TaskManager.push_task to inject a valid Ollama model
        # string into the submitted prompt. The addon stores model as an enum, and
        # the enum is empty because comfyui-ollama returned no models from /object_info
        # (Ollama wasn't running when ComfyUI started). Without this injection,
        # ComfyUI rejects the prompt with "model: String should have at least 1 char".
        try:
            mgr_m = sys.modules.get('ComfyUI-BlenderAI-node.SDNode.manager')
            if mgr_m and not hasattr(mgr_m.TaskManager, '_original_push_task'):
                mgr_m.TaskManager._original_push_task = mgr_m.TaskManager.push_task
                def _patched_push_task(task, tree=None, *args, **kwargs):
                    try:
                        for nid, ndata in list(task.get('prompt', {}).items()):
                            inner = ndata[0] if isinstance(ndata, tuple) else ndata
                            if inner.get('class_type') == 'OllamaConnectivityV2':
                                inputs = inner.setdefault('inputs', {})
                                if not inputs.get('model'):
                                    # Smaller model so it fits alongside Flux2 Klein on
                                    # 16-24GB VRAM cards (qwen3-vl:32b would VRAM-thrash)
                                    inputs['model'] = 'qwen3-vl:latest'
                                    print(f'[AutoComfy] injected Ollama model qwen3-vl:latest into prompt[{nid}]')
                    except Exception as _e:
                        print(f'[AutoComfy] Ollama model injection skipped: {_e}')
                    return mgr_m.TaskManager._original_push_task(task, tree=tree, *args, **kwargs)
                mgr_m.TaskManager.push_task = _patched_push_task
                print('[AutoComfy] push_task patched to inject Ollama model')
        except Exception as e:
            print(f'[AutoComfy] push_task patch failed: {e}')
        _NODE_TYPES_DONE_THIS_SESSION = True
        print('[AutoComfy] node fixer: session-flagged done; will not re-run on file load')
    except Exception as e:
        print(f'[AutoComfy] node fixer error: {e}')
        traceback.print_exc()
    return None
RGB_FILE     = "ocean_view_rgb.png"
DEPTH_FILE   = "ocean_view_depth.png"

def get_image_editor():
    # Return the LARGEST image editor, wherever it sits on screen. The old
    # version only matched areas at x>1900 (assumed a right-side layout); when
    # the image editor is on the left, that returned None and the viewer could
    # never replace the black placeholder with the finished render.
    best = None
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "IMAGE_EDITOR":
                if best is None or (area.width * area.height) > (best.width * best.height):
                    best = area
    return best

def get_latest_output_path():
    """Find the most recently modified PNG in ComfyUI/output/ that matches
    any of our known naming conventions (ComfyUI default, AEC variation
    names, or the Comfy_<batch>_ batched naming).
    """
    # Use os.scandir instead of glob.glob: scandir returns a single snapshot
    # of the directory in one syscall, so we can't crash mid-iteration on a
    # generator the way glob does (which was crashing Blender with
    # EXCEPTION_ACCESS_VIOLATION in PyTuple_Pack during PyGen_yf).
    prefixes = ("ComfyUI_", "Comfy_", "Make_Real_", "Change_", "CHange_", "Time_Of_Day_")
    best_path = None
    best_mtime = -1.0
    try:
        with os.scandir(COMFY_OUTPUT) as it:
            for entry in it:
                try:
                    name = entry.name
                    if not name.lower().endswith(".png"):
                        continue
                    if not any(name.startswith(p) for p in prefixes):
                        continue
                    m = entry.stat().st_mtime
                    if m > best_mtime:
                        best_mtime = m
                        best_path = entry.path
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, FileNotFoundError):
        return None
    return best_path


def get_latest_batch_files(batch_prefix=None):
    """Return a list of every file in the latest Comfy_<batch>_ batch.
    Useful to bulk-load all 6 variations after a script-path submission.
    """
    try:
        if batch_prefix is None:
            # find newest Comfy_*.png in the folder
            latest_name = None; latest_mtime = -1.0
            with os.scandir(COMFY_OUTPUT) as it:
                for entry in it:
                    try:
                        if not entry.name.startswith("Comfy_"): continue
                        if not entry.name.lower().endswith(".png"): continue
                        m = entry.stat().st_mtime
                        if m > latest_mtime:
                            latest_mtime = m
                            latest_name = entry.name
                    except (OSError, FileNotFoundError):
                        continue
            if not latest_name:
                return []
            parts = latest_name.split("_", 3)
            if len(parts) < 4 or parts[0] != "Comfy":
                return []
            batch_prefix = f"Comfy_{parts[1]}_{parts[2]}"

        # collect every file starting with batch_prefix
        files = []
        with os.scandir(COMFY_OUTPUT) as it:
            for entry in it:
                try:
                    if entry.name.startswith(batch_prefix) and entry.name.lower().endswith(".png"):
                        files.append(entry.path)
                except (OSError, FileNotFoundError):
                    continue
        return sorted(files)
    except (OSError, FileNotFoundError):
        return []

_last_viewer = {"mtime": 0.0, "path": "", "batch": ""}

def update_comfy_viewer():
    """Outer wrapper: catch ANY exception so the timer can never crash
    Blender. The previous version called glob.glob() which returned a
    generator; iterating that generator while files were being added/removed
    by ComfyUI could trip a C-level access violation in PyGen_yf.
    """
    try:
        return _update_comfy_viewer_impl()
    except Exception as e:
        print(f"[AutoComfy] viewer update error (recovered): {type(e).__name__}: {e}")
        return 2.0


def _update_comfy_viewer_impl():
    """Polled every 2s. When a new output appears:
      1. Bulk-load every file from the latest Comfy_<batch>_ set into
         bpy.data.images so the user can switch between them in the
         Image Editor dropdown.
      2. Set the first available Image Editor area to display the newest
         output (or the Make_Real of the latest batch if available).

    Honors a "minimum black-hold" so the recording always shows the
    black placeholder for at least N seconds after Render+Submit, even
    if the Blender render finishes fast and the user has an old batch
    on disk with a recent mtime.
    """
    import time as _t
    MIN_BLACK_HOLD_S = 5.0  # always show black for at least this long after a click
    black_started = _last_viewer.get("black_started")
    if black_started and (_t.time() - black_started) < MIN_BLACK_HOLD_S:
        return 1.0  # keep showing black; check again sooner than 2s

    latest = get_latest_output_path()
    if not latest:
        return 2.0
    try:
        mtime = os.path.getmtime(latest)
    except (OSError, FileNotFoundError):
        return 2.0
    if latest == _last_viewer["path"] and mtime == _last_viewer["mtime"]:
        return 2.0
    # Once a real file replaces the black, clear the black-hold flag.
    _last_viewer.pop("black_started", None)

    # If the new file is part of a Comfy_<batch>_ batch we haven't loaded
    # yet, bulk-load all files from that batch first.
    basename = os.path.basename(latest)
    if basename.startswith("Comfy_"):
        parts = basename.split("_", 3)
        if len(parts) >= 4:
            batch_prefix = f"Comfy_{parts[1]}_{parts[2]}"
            if batch_prefix != _last_viewer.get("batch"):
                batch_files = get_latest_batch_files(batch_prefix)
                preferred = None
                for p in batch_files:
                    name = os.path.basename(p)
                    # Re-load each so the user sees the new variation set
                    if name in bpy.data.images:
                        try: bpy.data.images.remove(bpy.data.images[name])
                        except Exception: pass
                    img = bpy.data.images.load(p, check_existing=False)
                    img.name = name
                    img.use_fake_user = True
                    if "Make_Real" in name and preferred is None:
                        preferred = img
                if preferred:
                    latest = preferred.filepath
                _last_viewer["batch"] = batch_prefix
                print(f"[AutoComfy] Bulk-loaded {len(batch_files)} files from {batch_prefix}_*")

    area = get_image_editor()
    if not area:
        # Still updated bpy.data.images even if no Image Editor pane exists
        _last_viewer["path"]  = latest
        _last_viewer["mtime"] = mtime
        return 2.0
    img = bpy.data.images.load(latest, check_existing=True)
    img.reload()
    area.spaces[0].image = img
    _last_viewer["path"]  = latest
    _last_viewer["mtime"] = mtime
    print(f"[AutoComfy] Viewer updated -> {os.path.basename(latest)}")
    return 2.0

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
    cam   = scene.camera

    # Mute camera animation so manually positioned viewport camera is used,
    # not the animated position at frame_current
    cam_anim      = cam.animation_data if cam else None
    cam_action    = cam_anim.action if cam_anim else None
    cam_influence = cam_anim.action_influence if cam_anim else 1.0
    if cam_anim and cam_action:
        cam_anim.action_influence = 0.0
        bpy.context.view_layer.update()
        print(f"[AutoComfy] Camera anim muted — rendering viewport position {cam.location[:]}")

    scene.render.engine                     = "CYCLES"
    orig_samples                            = scene.cycles.samples
    scene.cycles.samples                    = 64
    scene.render.filepath                   = os.path.join(COMFY_INPUT, RGB_FILE)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode  = "RGB"

    print("[AutoComfy] Rendering (Cycles 64 samples GPU)...")
    bpy.ops.render.render(write_still=True)
    print(f"[AutoComfy] RGB saved -> {scene.render.filepath}")
    scene.cycles.samples = orig_samples

    # Restore camera animation
    if cam_anim and cam_action:
        cam_anim.action_influence = cam_influence
        bpy.context.view_layer.update()
        print("[AutoComfy] Camera animation restored")

    depth_img = bpy.data.images.get("Viewer Node")
    if depth_img and depth_img.size[0] > 0:
        depth_img.filepath_raw = os.path.join(COMFY_INPUT, DEPTH_FILE)
        depth_img.file_format  = "PNG"
        depth_img.save()
        print("[AutoComfy] Depth saved")
    else:
        print("[AutoComfy] No Viewer Node — DepthAnythingV2 extracts depth from RGB")

    cfu_tree = bpy.data.node_groups.get("ComfyUI Node")
    if not cfu_tree:
        print("[AutoComfy] ERROR: ComfyUI Node tree not found")
        return None
    try:
        n = cfu_tree.nodes.get("Beauty") or cfu_tree.nodes.get("Blender RGB Render")
        if n:
            n.image = RGB_FILE
            print(f"[AutoComfy] LoadImage '{n.name}' set to {RGB_FILE}")
        else:
            print("[AutoComfy] WARN: no LoadImage node named 'Beauty' or 'Blender RGB Render'")
    except Exception as e:
        print(f"[AutoComfy] LoadImage error: {e}")
    try:
        TaskManager.push_task(cfu_tree.get_task(), tree=cfu_tree)
        print("[AutoComfy] Task submitted to ComfyUI")
    except Exception as e:
        print(f"[AutoComfy] push_task error: {e}")
    return None

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
        print("[AutoComfy] Execute — queuing deferred Cycles render (viewport camera)...")
        _pending["active"] = True
        bpy.app.timers.register(_deferred_render_and_submit, first_interval=0.1)
    Ops.submit = patched_submit
    print("[AutoComfy] Ops.submit patched")

@persistent
def on_load_post(filepath):
    _connect_state["done"]     = False
    _connect_state["attempts"] = 0
    _register()
    print("[AutoComfy] Re-registered after file load")

def _register():
    if not bpy.app.timers.is_registered(update_comfy_viewer):
        bpy.app.timers.register(update_comfy_viewer, first_interval=2.0, persistent=True)
    if not bpy.app.timers.is_registered(_auto_connect_comfy):
        bpy.app.timers.register(_auto_connect_comfy, first_interval=2.0, persistent=True)
    # Only schedule the heavy node-type registration on initial Blender startup
    # (i.e., when the flag is still False). On subsequent file loads, classes
    # are already registered and re-running this crashes Blender.
    if (not _NODE_TYPES_DONE_THIS_SESSION
            and not bpy.app.timers.is_registered(_register_comfyui_node_types)):
        bpy.app.timers.register(_register_comfyui_node_types, first_interval=5.0, persistent=True)
    bpy.app.handlers.load_post[:] = [
        h for h in bpy.app.handlers.load_post if getattr(h, '__name__', '') != 'on_load_post'
    ]
    bpy.app.handlers.load_post.append(on_load_post)
    latest = get_latest_output_path()
    area   = get_image_editor()
    if latest and area:
        img = bpy.data.images.load(latest, check_existing=True)
        area.spaces[0].image = img
        _last_viewer["path"]  = latest
        _last_viewer["mtime"] = os.path.getmtime(latest)

_register()


# ── AEC N-panel: "Render + Submit" button ────────────────────────────────
# Calls submit_comfyui.py's submit(render=True) from an operator context,
# which IS safe to nest bpy.ops.render.render() in (unlike calling it from
# inside the addon's push_task hook, which crashed Blender).

def _show_black_in_image_editor():
    """Flash a solid-black 1024×1024 image into every Image Editor area.
    Used at the start of Render+Submit so the recording shows a clean
    black frame until ComfyUI's first NEW output replaces it.

    Important: we seed _last_viewer to the *current* newest file on disk
    (not 0!), so the live-watcher only loads files that are TRULY newer
    than what existed before this click. Otherwise the previous batch's
    last image would immediately replace the black after one watcher tick.
    """
    name = '__aec_black_placeholder'
    img = bpy.data.images.get(name)
    if not img:
        img = bpy.data.images.new(name, width=1024, height=1024, alpha=False)
    if img.size[0] != 1024 or img.size[1] != 1024:
        img.scale(1024, 1024)
    try:
        import numpy as _np
        px = _np.zeros(1024 * 1024 * 4, dtype=_np.float32)
        px[3::4] = 1.0
        img.pixels.foreach_set(px)
    except Exception:
        img.pixels = [0.0, 0.0, 0.0, 1.0] * (1024 * 1024)
    img.update()
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces[0].image = img
                area.tag_redraw()
    # Seed the live-watcher with the current newest file so it only loads
    # something STRICTLY newer than what existed when the user clicked.
    try:
        import time as _t
        latest = get_latest_output_path()
        if latest:
            _last_viewer["path"]  = latest
            _last_viewer["mtime"] = os.path.getmtime(latest)
        else:
            _last_viewer["path"]  = '<black>'
            _last_viewer["mtime"] = _t.time()
        # Also remember when the black started so we can enforce a minimum hold.
        _last_viewer["black_started"] = _t.time()
    except Exception:
        pass


# Process-wide flag to debounce duplicate Render+Submit clicks. The button
# disables itself while a submission is in flight, but a fast double-click
# in the same operator-poll window could still re-enter. This guard makes
# even hand-spammed clicks safe.
_AEC_SUBMIT_IN_FLIGHT = {"v": False}


class AEC_OT_render_submit(bpy.types.Operator):
    bl_idname = "aec.render_submit"
    bl_label = "Render + Submit"
    bl_description = ("Render Beauty + Seg from current Blender camera, "
                      "then submit the ComfyUI workflow with that fresh image")

    @classmethod
    def poll(cls, context):
        # Grey out the button while a submission is in flight
        return not _AEC_SUBMIT_IN_FLIGHT["v"]

    def execute(self, context):
        if _AEC_SUBMIT_IN_FLIGHT["v"]:
            self.report({'WARNING'}, 'AEC: submission already in progress — wait for it to finish')
            return {'CANCELLED'}
        _AEC_SUBMIT_IN_FLIGHT["v"] = True
        try:
            return self._do_submit(context)
        finally:
            _AEC_SUBMIT_IN_FLIGHT["v"] = False

    def _do_submit(self, context):
        # Flash black first — the recording sees a clean black frame while
        # Blender renders Beauty/Seg and ComfyUI builds the variations.
        try:
            _show_black_in_image_editor()
        except Exception as _e:
            print(f'AEC: black-placeholder skipped: {_e}')

        try:
            import importlib.util as _ilu
            from pathlib import Path as _P
            sm_path = r'C:/Users/NVIDIA/Downloads/AEC_Demo_Portable/AEC_Demo_Portable/scripts/submit_comfyui.py'
            spec = _ilu.spec_from_file_location('aec_submit', sm_path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.COMFY_INPUT = _P(r'C:/Users/NVIDIA/ComfyUI/ComfyUI_windows_portable/ComfyUI/input')
            mod.COMFY_URL = 'http://127.0.0.1:8188'
            self.report({'INFO'}, 'AEC: rendering Beauty + Seg from camera and submitting...')
            ok = mod.submit(render=True)
            if ok:
                self.report({'INFO'}, 'AEC: submitted to ComfyUI; watch output folder for new batch')
            else:
                self.report({'WARNING'}, 'AEC: submit() returned False — check ComfyUI history')
        except Exception as e:
            import traceback; traceback.print_exc()
            self.report({'ERROR'}, f'AEC: {e}')
            return {'CANCELLED'}
        return {'FINISHED'}


class AEC_PT_panel(bpy.types.Panel):
    bl_label = "AEC"
    bl_idname = "AEC_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AEC"

    def draw(self, context):
        self.layout.operator("aec.render_submit", icon="RENDER_STILL")


def _register_aec_panel():
    try:
        bpy.utils.register_class(AEC_OT_render_submit)
        bpy.utils.register_class(AEC_PT_panel)
        print('[AutoComfy] AEC N-panel registered  ->  View3D > N > AEC > Render + Submit')
    except Exception as e:
        # Already registered if we reload — that's fine
        print(f'[AutoComfy] AEC panel register skipped: {e}')


_register_aec_panel()
print("[AutoComfy] Startup script loaded — auto-connect + viewport camera render ready")
