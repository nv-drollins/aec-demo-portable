"""Rhino-vs-Artist Toggle Runtime
Embedded text block inside cliff_house_act2_textured_v3.blend.
Auto-registers on file load (Text use_module=True + Auto Run Python Scripts).

Hotkeys (3D View, Object Mode):
  Alt + 0   master toggle: all areas flip textured <-> Rhino-basic
  Alt + 1   cycle wall material: Wood Cladding -> Travertine -> Zinc -> ...
  Alt + 2   recall Shot A camera   (frame a view, then Register from N-panel)
  Alt + 3   recall Shot B camera   (frame a view, then Register from N-panel)
  Alt + 4   wall -> Travertine      (light natural stone)
  Alt + 5   wall -> Zinc Panel      (cool metal cladding)
  Alt + 6   aspect toggle: scene render resolution cycles 1024x1024 <-> 1280x720.
            Affects camera frame in viewport AND the resolution that ComfyUI
            receives via the AEC submit pipeline (submit_comfyui.py reads
            scene.render.resolution_x/y dynamically).
  Alt + 7   world toggle: scene world cycles between Studio_Gray (classic
            architectural neutral, default) and ArchWorld (artist's HDRI).
  Alt + 8   recall the Main shot camera (Camera_day) and frame it; restores
            its saved matrix_world if one was registered.
  Alt + 9   SNAP everything to artist textured. Not a toggle - always
            forces every slot to its textured material regardless of current
            state. Useful when the per-area keys (Alt+1..5) have left things
            in a mixed state and you want a clean reveal of the full scene.

N-panel button row: 3D View > Sidebar (N) > Painter tab.
"""
import bpy
import json
from bpy.types import Operator, Panel

SNAPSHOT_KEY = "_act2_snapshot"
BASIC_SUFFIX = "_RhinoBasic"
AREAS = ["walls", "floors", "roof", "windows", "frames"]


def _snapshot():
    raw = bpy.context.scene.get(SNAPSHOT_KEY, "")
    if not raw: return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _entries_for(area):
    snap = _snapshot()
    if area is None or area == "":
        return snap
    return [e for e in snap if e.get("area") == area]


def _area_state(area):
    n_tex = n_bas = 0
    for e in _entries_for(area):
        obj = bpy.data.objects.get(e["obj"])
        if not obj or e["slot"] >= len(obj.material_slots): continue
        mat = obj.material_slots[e["slot"]].material
        if not mat: continue
        if mat.name == e["textured_mat"]: n_tex += 1
        elif mat.name == e["basic_mat"]: n_bas += 1
    return n_tex, n_bas


def _apply(area, target_state):
    changed = 0
    for e in _entries_for(area):
        obj = bpy.data.objects.get(e["obj"])
        if not obj or e["slot"] >= len(obj.material_slots): continue
        target_name = e["basic_mat"] if target_state == "basic" else e["textured_mat"]
        target_mat = bpy.data.materials.get(target_name)
        if target_mat is None: continue
        slot = obj.material_slots[e["slot"]]
        if slot.material is not target_mat:
            slot.material = target_mat
            changed += 1
    # Force every viewport to refresh in case shading mode doesn't auto-update
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type == "VIEW_3D":
                a.tag_redraw()
    return changed


def _toggle(area):
    n_tex, n_bas = _area_state(area)
    target = "basic" if n_tex > n_bas else "textured"
    n = _apply(area, target)
    return n, target


class RT_OT_toggle(Operator):
    bl_idname = "rt.toggle"
    bl_label = "Toggle Rhino / Artist Textured"
    bl_options = {"REGISTER", "UNDO"}
    # SKIP_SAVE so Blender does not persist last-used value into next invocation
    area: bpy.props.StringProperty(default="", options={"SKIP_SAVE"})

    def execute(self, context):
        area = self.area if self.area else None
        n, target = _toggle(area)
        label = area if area else "ALL"
        self.report({"INFO"}, f"RhinoToggle: {label} -> {target}  ({n} slots changed)")
        return {"FINISHED"}


class RT_OT_force_textured(Operator):
    """Snap every material slot to the artist textured material (no toggle)."""
    bl_idname = "rt.force_textured"
    bl_label = "Force ALL Textured"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = _apply(None, "textured")
        self.report({"INFO"}, f"ForceTextured: {n} slot(s) changed")
        return {"FINISHED"}


# (label, width, height) - cycled in order on each Alt+6 press.
ASPECT_PRESETS = [
    ("Square 1024", 1024, 1024),
    ("16:9 720p",   1280, 720),
]


class RT_OT_aspect(Operator):
    bl_idname = "rt.aspect_toggle"
    bl_label = "Toggle Render Aspect Ratio"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        cur_w = sc.render.resolution_x
        cur_h = sc.render.resolution_y
        cur_idx = -1
        for i, (lbl, w, h) in enumerate(ASPECT_PRESETS):
            if w == cur_w and h == cur_h:
                cur_idx = i
                break
        nxt = (cur_idx + 1) % len(ASPECT_PRESETS)
        lbl, w, h = ASPECT_PRESETS[nxt]
        sc.render.resolution_x = w
        sc.render.resolution_y = h
        for area in context.screen.areas:
            if area.type in ("VIEW_3D", "IMAGE_EDITOR", "PROPERTIES"):
                area.tag_redraw()
        self.report({"INFO"}, f"AspectToggle: {lbl} ({w}x{h})")
        return {"FINISHED"}


CAMERA_BOOKMARK_KEY = "_bookmark_matrix"


# --- Wall material swatches (real PBR, box-projected) ----------------------
# Alt+3/4/5 jump to a specific wall material; Alt+1 cycles through them.
# These replace the old brightness-shifted wood shades with three genuinely
# distinct architectural finishes that all suit a modern coastal cliff house.
# They target the "walls" area from the snapshot (the actual wall surfaces),
# leaving the wood door slats (frames area) untouched.
WALL_SWATCHES = ["Wall_WoodCladding", "Wall_Travertine", "Wall_ZincPanel"]

# 2K PBR maps live here (albedo + nor_gl + rough per slug).
WALL_TEX_DIR = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\assets\textures"

# (mat_name, slug, scale_x, scale_y, tint_rgba_or_None, rough_bias, metallic)
WALL_RECIPES = [
    ("Wall_WoodCladding", "weathered_planks",   1.4, 3.0, None,                    0.00, 0.0),
    ("Wall_Travertine",   "beige_wall_001",     1.2, 1.2, None,                    0.00, 0.0),
    ("Wall_ZincPanel",    "corrugated_iron_03", 2.2, 2.2, (0.56, 0.60, 0.66, 1.0), -0.15, 0.7),
]


def _wall_img(slug, suffix):
    import os
    fname = f"{slug}_{suffix}_2k.png"
    img = bpy.data.images.get(fname)
    if img is not None:
        return img
    path = os.path.join(WALL_TEX_DIR, fname)
    if os.path.exists(path):
        return bpy.data.images.load(path, check_existing=True)
    return None


def _build_pbr_wall(name, slug, sx, sy, tint, rough_bias, metallic):
    """Create (or repair) a box-projected PBR wall material from disk textures.
    Returns the material, or None if the albedo texture is unavailable.
    Box projection + Generated coords means no UV unwrap is required."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bsdf = None
        if mat.use_nodes and mat.node_tree:
            bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf and bsdf.inputs.get("Base Color") and bsdf.inputs["Base Color"].is_linked:
            return mat  # healthy, keep it
        bpy.data.materials.remove(mat)  # broken, rebuild

    diff = _wall_img(slug, "diff")
    if diff is None:
        return None
    nor = _wall_img(slug, "nor_gl")
    rough = _wall_img(slug, "rough")

    mat = bpy.data.materials.new(name)
    mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (560, 0)
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic

    texcoord = nt.nodes.new("ShaderNodeTexCoord"); texcoord.location = (-720, 0)
    mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-520, 0)
    mapping.inputs["Scale"].default_value = (sx, sy, 1.0)
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])

    img_d = nt.nodes.new("ShaderNodeTexImage"); img_d.location = (-220, 240)
    img_d.image = diff; img_d.projection = "BOX"; img_d.projection_blend = 0.2
    nt.links.new(mapping.outputs["Vector"], img_d.inputs["Vector"])

    base_out = img_d.outputs["Color"]
    if tint is not None:
        mix = nt.nodes.new("ShaderNodeMixRGB"); mix.location = (140, 300)
        mix.blend_type = "MULTIPLY"; mix.inputs["Fac"].default_value = 0.85
        mix.inputs["Color2"].default_value = tint
        nt.links.new(base_out, mix.inputs["Color1"])
        base_out = mix.outputs["Color"]
    nt.links.new(base_out, bsdf.inputs["Base Color"])

    if nor is not None:
        nor.colorspace_settings.name = "Non-Color"
        img_n = nt.nodes.new("ShaderNodeTexImage"); img_n.location = (-220, -40)
        img_n.image = nor; img_n.projection = "BOX"; img_n.projection_blend = 0.2
        nt.links.new(mapping.outputs["Vector"], img_n.inputs["Vector"])
        nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (180, -40)
        nmap.inputs["Strength"].default_value = 0.8
        nt.links.new(img_n.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if rough is not None:
        rough.colorspace_settings.name = "Non-Color"
        img_r = nt.nodes.new("ShaderNodeTexImage"); img_r.location = (-220, -340)
        img_r.image = rough; img_r.projection = "BOX"; img_r.projection_blend = 0.2
        nt.links.new(mapping.outputs["Vector"], img_r.inputs["Vector"])
        rmap = nt.nodes.new("ShaderNodeMapRange"); rmap.location = (180, -340)
        rmap.inputs["To Min"].default_value = max(0.0, 0.2 + rough_bias)
        rmap.inputs["To Max"].default_value = min(1.0, 0.95 + rough_bias)
        nt.links.new(img_r.outputs["Color"], rmap.inputs["Value"])
        nt.links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = max(0.0, 0.5 + rough_bias)

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _ensure_wall_palette():
    """Build all wall swatch materials if missing/broken (idempotent)."""
    for name, slug, sx, sy, tint, rb, met in WALL_RECIPES:
        _build_pbr_wall(name, slug, sx, sy, tint, rb, met)


def _set_walls(mat_name):
    """Set every wall-area slot (from the snapshot) to mat_name."""
    target = bpy.data.materials.get(mat_name)
    if target is None:
        return 0
    changed = 0
    for e in _entries_for("walls"):
        obj = bpy.data.objects.get(e["obj"])
        if not obj or e["slot"] >= len(obj.material_slots):
            continue
        slot = obj.material_slots[e["slot"]]
        if slot.material is not target:
            slot.material = target
            changed += 1
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type == "VIEW_3D":
                a.tag_redraw()
    return changed


def _current_wall_swatch_idx():
    """Index in WALL_SWATCHES of the swatch most wall slots use, else -1."""
    from collections import Counter
    c = Counter()
    for e in _entries_for("walls"):
        obj = bpy.data.objects.get(e["obj"])
        if not obj or e["slot"] >= len(obj.material_slots):
            continue
        m = obj.material_slots[e["slot"]].material
        if m and m.name in WALL_SWATCHES:
            c[m.name] += 1
    if not c:
        return -1
    return WALL_SWATCHES.index(c.most_common(1)[0][0])


class RT_OT_cycle_wall(Operator):
    """Cycle the walls through Wood Cladding -> Travertine -> Zinc -> ..."""
    bl_idname = "rt.cycle_wall"
    bl_label = "Cycle Wall Material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        _ensure_wall_palette()
        idx = _current_wall_swatch_idx()
        nxt = (idx + 1) % len(WALL_SWATCHES)
        target = WALL_SWATCHES[nxt]
        n = _set_walls(target)
        self.report({"INFO"}, f"WallCycle: {target}  ({n} slot(s))")
        return {"FINISHED"}


class RT_OT_wall_wood(Operator):
    bl_idname = "rt.wall_wood"
    bl_label = "Wall: Wood Cladding"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        _ensure_wall_palette()
        n = _set_walls("Wall_WoodCladding")
        self.report({"INFO"}, f"Wall Wood Cladding: {n} slot(s)")
        return {"FINISHED"}


class RT_OT_wall_travertine(Operator):
    bl_idname = "rt.wall_travertine"
    bl_label = "Wall: Travertine"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        _ensure_wall_palette()
        n = _set_walls("Wall_Travertine")
        self.report({"INFO"}, f"Wall Travertine: {n} slot(s)")
        return {"FINISHED"}


class RT_OT_wall_zinc(Operator):
    bl_idname = "rt.wall_zinc"
    bl_label = "Wall: Zinc Panel"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        _ensure_wall_palette()
        n = _set_walls("Wall_ZincPanel")
        self.report({"INFO"}, f"Wall Zinc Panel: {n} slot(s)")
        return {"FINISHED"}


class RT_OT_recall_bookmark(Operator):
    bl_idname = "rt.recall_bookmark"
    bl_label = "Recall Camera Bookmark"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cam = context.scene.camera
        if cam is None:
            self.report({"WARNING"}, "no active camera in scene")
            return {"CANCELLED"}
        bm = cam.get(CAMERA_BOOKMARK_KEY)
        if not bm:
            self.report({"WARNING"}, f"no bookmark on '{cam.name}'")
            return {"CANCELLED"}
        from mathutils import Matrix
        cam.matrix_world = Matrix([list(r) for r in bm])
        for win in bpy.context.window_manager.windows:
            for a in win.screen.areas:
                if a.type == "VIEW_3D": a.tag_redraw()
        self.report({"INFO"}, f"Recalled bookmark on '{cam.name}'")
        return {"FINISHED"}


class RT_OT_save_bookmark(Operator):
    bl_idname = "rt.save_bookmark"
    bl_label = "Save Current Camera Position as Bookmark"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cam = context.scene.camera
        if cam is None:
            self.report({"WARNING"}, "no active camera in scene")
            return {"CANCELLED"}
        cam[CAMERA_BOOKMARK_KEY] = [list(r) for r in cam.matrix_world]
        self.report({"INFO"}, f"Saved current position as bookmark on '{cam.name}'")
        return {"FINISHED"}


# --- Shot cameras: three recallable framings bound to Alt+2 / Alt+3 / Alt+8 ---
# Frame a view in the viewport, Register it, then the hotkey jumps back to it:
# it becomes the scene camera, every viewport snaps into its camera view, and
# the black passepartout turns on. Alt+8 stays on the original Camera_day.
SHOT_CAMS = {"A": "Cam_Shot_A", "B": "Cam_Shot_B", "8": "Camera_day"}


def _all_views_to_camera():
    """Put every 3D viewport into camera view so the active scene camera frames
    the shot the user just recalled."""
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type == "VIEW_3D":
                try:
                    a.spaces.active.region_3d.view_perspective = "CAMERA"
                except Exception:
                    pass
                a.tag_redraw()


class RT_OT_recall_shot(Operator):
    """Jump to a saved shot camera and frame it (Alt+2 -> Shot A,
    Alt+3 -> Shot B, Alt+8 -> Main). Restores the exact saved position even if
    the camera was nudged. Warns if the slot was never registered."""
    bl_idname = "rt.recall_shot"
    bl_label = "Recall Shot Camera"
    bl_options = {"REGISTER", "UNDO"}
    shot: bpy.props.StringProperty(default="A", options={"SKIP_SAVE"})

    def execute(self, context):
        name = SHOT_CAMS.get(self.shot)
        cam = bpy.data.objects.get(name) if name else None
        if cam is None or cam.type != "CAMERA":
            self.report({"WARNING"},
                        f"Shot {self.shot} not set yet - frame a view and Register it")
            return {"CANCELLED"}
        context.scene.camera = cam
        bm = cam.get(CAMERA_BOOKMARK_KEY)
        if bm:
            from mathutils import Matrix
            cam.matrix_world = Matrix([list(r) for r in bm])
        cam.data.show_passepartout = True
        cam.data.passepartout_alpha = 1.0
        _all_views_to_camera()
        self.report({"INFO"}, f"Shot {self.shot}: {cam.name}")
        return {"FINISHED"}


class RT_OT_register_shot(Operator):
    """Capture the CURRENT viewport view into a shot camera and bind it
    (Alt+2 -> Shot A, Alt+3 -> Shot B, Alt+8 -> Main). Frame the view you want,
    then run this once for that slot."""
    bl_idname = "rt.register_shot"
    bl_label = "Register Shot Camera (from current view)"
    bl_options = {"REGISTER", "UNDO"}
    shot: bpy.props.StringProperty(default="A", options={"SKIP_SAVE"})

    def execute(self, context):
        name = SHOT_CAMS.get(self.shot)
        if not name:
            self.report({"WARNING"}, f"unknown shot '{self.shot}'")
            return {"CANCELLED"}
        cam = _snap_shot_cam_to_view(context, name)
        if cam is None:
            self.report({"WARNING"}, "no 3D viewport found to capture")
            return {"CANCELLED"}
        context.scene.camera = cam
        self.report({"INFO"}, f"Registered Shot {self.shot} -> {cam.name}")
        return {"FINISHED"}


# Worlds cycled in order on each Alt+7 press.
WORLD_PRESETS = ["Studio_Gray", "ArchWorld"]


# Sun-study seasonal presets. Keys are (frame, value) pairs for rotation_euler.
# X is altitude-from-vertical; Y stays 0; Z sweeps east -> west across the day.
# Values are tuned for Santa Barbara latitude (~34 N): summer noon ~79 deg
# altitude (X = pi/2 - 79deg = 0.183 rad), winter noon ~33 deg altitude
# (X = pi/2 - 33deg = 1.0 rad). At dawn / dusk the sun is near horizon
# (X close to pi/2 = 1.57).
SEASONS = {
    "summer": {
        "label":    "Summer (SoCal, ~79deg noon)",
        "x_keys":   [(1, 1.4), (45, 0.8), (90, 0.18), (135, 0.8), (180, 1.4)],
        "z_keys":   [(1, 1.178), (180, -0.785)],
        "filename": "cliff_house_act3_sunstudy_summer",
        "action_name": "Sun_Summer_SoCal",
    },
    "winter": {
        "label":    "Winter (SoCal, ~33deg noon)",
        "x_keys":   [(1, 1.4), (45, 1.2), (90, 1.0), (135, 1.2), (180, 1.4)],
        "z_keys":   [(1, 1.178), (180, -0.785)],
        "filename": "cliff_house_act3_sunstudy_winter",
        "action_name": "Sun_Winter_SoCal",
    },
}


def _apply_season(season_id):
    """Rebuild the Sun light's keyframes for the given season and update the
    render output filepath so the resulting MP4 has the season suffix.
    """
    spec = SEASONS.get(season_id)
    if spec is None: return False, f"unknown season '{season_id}'"
    sun = next((o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sun is None: return False, "no Sun light in scene"

    sun.animation_data_clear()
    for f, v in spec["x_keys"]:
        sun.rotation_euler[0] = v
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=0)
    for f in (1, 180):
        sun.rotation_euler[1] = 0.0
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=1)
    for f, v in spec["z_keys"]:
        sun.rotation_euler[2] = v
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=2)
    if sun.animation_data and sun.animation_data.action:
        sun.animation_data.action.name = spec["action_name"]
        sun.animation_data.action.use_fake_user = True

    sc = bpy.context.scene
    out_dir = r"C:\Users\NVIDIA\Documents\Computex\Blender_Render\SunStudy"
    import os
    sc.render.filepath = os.path.join(out_dir, spec["filename"])

    while sc.timeline_markers:
        sc.timeline_markers.remove(sc.timeline_markers[0])
    for f, n in [(1, "Dawn"), (45, "Morning"), (90, "Noon"), (135, "Afternoon"), (180, "Dusk")]:
        sc.timeline_markers.new(n, frame=f)

    return True, f"{spec['label']} -> {spec['filename']}.mp4"


class RT_OT_season_summer(Operator):
    """Set the Sun light to summer arc + name the next render <name>_summer.mp4."""
    bl_idname = "rt.season_summer"
    bl_label = "Sun Study: Summer"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ok, msg = _apply_season("summer")
        self.report({"INFO"} if ok else {"WARNING"}, f"Season: {msg}")
        return {"FINISHED"} if ok else {"CANCELLED"}


class RT_OT_season_winter(Operator):
    """Set the Sun light to winter arc + name the next render <name>_winter.mp4."""
    bl_idname = "rt.season_winter"
    bl_label = "Sun Study: Winter"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ok, msg = _apply_season("winter")
        self.report({"INFO"} if ok else {"WARNING"}, f"Season: {msg}")
        return {"FINISHED"} if ok else {"CANCELLED"}


class RT_OT_world_toggle(Operator):
    bl_idname = "rt.world_toggle"
    bl_label = "Toggle World (Studio Gray / HDRI)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        cur_name = sc.world.name if sc.world else None
        cur_idx = WORLD_PRESETS.index(cur_name) if cur_name in WORLD_PRESETS else -1
        nxt = (cur_idx + 1) % len(WORLD_PRESETS)
        target = bpy.data.worlds.get(WORLD_PRESETS[nxt])
        if target is None:
            self.report({"WARNING"}, f"world '{WORLD_PRESETS[nxt]}' not found")
            return {"CANCELLED"}
        sc.world = target
        for area in context.screen.areas:
            if area.type in ("VIEW_3D", "PROPERTIES"):
                area.tag_redraw()
        self.report({"INFO"}, f"WorldToggle: {target.name}")
        return {"FINISHED"}


# Warm-daylight lighting toggle: flips between the scene's current lighting and
# a brighter, warmer "artist daylight" grade matching the warm interior
# reference. Reversible - stores the neutral values and restores them on toggle
# off. Tune these three numbers to taste.
# "Bright Daylight" toggle. The scene's warm HDRI (ArchWorld) dominates and
# tints everything orange, so this REPLACES the world with a neutral bright
# white world (the real lever for "more white, less warm"), neutralizes the
# sun, and lifts exposure. Fully reversible - the previous world/sun/exposure
# are stored and restored. Tune the numbers below to taste.
BRIGHT_DAYLIGHT = {
    "world_color":     (1.0, 1.0, 1.0),    # neutral white fill - kills the warm HDRI tint
    "world_strength":  1.8,                # bright, airy ambient
    "exposure_add":    0.25,               # a little extra lift
    "sun_color":       (1.0, 0.98, 0.96),  # near-white, barely warm
    "sun_energy_mult": 1.25,
}


def _scene_sun():
    return next((o for o in bpy.data.objects
                 if o.type == "LIGHT" and o.data.type == "SUN"), None)


def _ensure_bright_world():
    """A plain neutral-white world used by the Bright Daylight toggle."""
    w = bpy.data.worlds.get("Bright_Daylight")
    if w is None:
        w = bpy.data.worlds.new("Bright_Daylight")
    w.use_nodes = True
    nt = w.node_tree
    bg = next((n for n in nt.nodes if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = nt.nodes.new("ShaderNodeBackground")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_WORLD"), None)
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputWorld")
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Color"].default_value = (*BRIGHT_DAYLIGHT["world_color"], 1.0)
    bg.inputs["Strength"].default_value = BRIGHT_DAYLIGHT["world_strength"]
    w.use_fake_user = True
    return w


class RT_OT_warm_daylight(Operator):
    """Toggle a neutral, BRIGHT daylight: swaps the warm HDRI for a white world,
    neutralizes the sun, and lifts exposure so the interior reads white and airy
    instead of orange. Toggling off restores the exact previous world/sun/exposure."""
    bl_idname = "rt.warm_daylight"
    bl_label = "Bright Daylight (toggle)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        sun = _scene_sun()
        if not sc.get("_warm_daylight_on", 0):
            save = {"exposure": sc.view_settings.exposure,
                    "world": sc.world.name if sc.world else ""}
            if sun:
                save["sun_color"] = list(sun.data.color)
                save["sun_energy"] = sun.data.energy
            sc["_warm_daylight_saved"] = json.dumps(save)
            sc.world = _ensure_bright_world()
            sc.view_settings.exposure += BRIGHT_DAYLIGHT["exposure_add"]
            if sun:
                sun.data.color = BRIGHT_DAYLIGHT["sun_color"]
                sun.data.energy = sun.data.energy * BRIGHT_DAYLIGHT["sun_energy_mult"]
            sc["_warm_daylight_on"] = 1
            msg = "Bright Daylight: ON (neutral white world)"
        else:
            saved = json.loads(sc.get("_warm_daylight_saved", "{}"))
            if "exposure" in saved:
                sc.view_settings.exposure = saved["exposure"]
            w = bpy.data.worlds.get(saved.get("world", ""))
            if w:
                sc.world = w
            if sun and "sun_color" in saved:
                sun.data.color = saved["sun_color"]
            if sun and "sun_energy" in saved:
                sun.data.energy = saved["sun_energy"]
            sc["_warm_daylight_on"] = 0
            msg = "Bright Daylight: OFF (restored)"
        for a in [ar for w in bpy.context.window_manager.windows
                  for ar in w.screen.areas if ar.type == "VIEW_3D"]:
            a.tag_redraw()
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class RT_PT_panel(Panel):
    bl_label = "Rhino/Artist Toggle"
    bl_idname = "RT_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Painter"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        n_tex, n_bas = _area_state("")
        col.label(text=f"Global: tex={n_tex}  basic={n_bas}", icon="MATERIAL")
        col.operator("rt.toggle", text="0 - Toggle ALL", icon="WORLD").area = ""
        col.separator()
        col.label(text="Wall Material  (Alt+1 cycles)", icon="MATSHADERBALL")
        col.operator("rt.cycle_wall", text="1 - Cycle Wall Material", icon="LOOP_FORWARDS")
        row = col.row(align=True)
        row.operator("rt.wall_wood",       text="Wood Clad")
        row.operator("rt.wall_travertine", text="4 - Travertine")
        row.operator("rt.wall_zinc",       text="5 - Zinc")
        col.separator()
        col.label(text="Per-area toggles (no hotkey)", icon="MOD_ARRAY")
        labels = [("Walls", "walls"), ("Floors", "floors"),
                  ("Roof", "roof"), ("Windows", "windows"),
                  ("Frames", "frames")]
        for label, area in labels:
            n_tex_a, n_bas_a = _area_state(area)
            row = col.row(align=True)
            row.operator("rt.toggle", text=label).area = area
            sub = row.row(); sub.alignment = "RIGHT"
            sub.label(text=f"{n_tex_a}T/{n_bas_a}B")
        col.separator()
        sc = context.scene
        col.label(text=f"Aspect: {sc.render.resolution_x}x{sc.render.resolution_y}", icon="OUTLINER_OB_CAMERA")
        col.operator("rt.aspect_toggle", text="6 - Toggle Aspect", icon="FILE_REFRESH")
        col.separator()
        world_name = sc.world.name if sc.world else "(none)"
        col.label(text=f"World: {world_name}", icon="WORLD")
        col.operator("rt.world_toggle", text="7 - Toggle World", icon="LIGHT_SUN")
        wd_on = bool(sc.get("_warm_daylight_on", 0))
        col.operator("rt.warm_daylight",
                     text=("Bright Daylight: ON" if wd_on else "Bright Daylight: OFF"),
                     icon="LIGHT_SUN", depress=wd_on)
        col.separator()
        cam = sc.camera
        col.label(text=f"Shot cameras  (active: {cam.name if cam else '-'})", icon="CAMERA_DATA")
        col.label(text="frame a view, press REC to set it", icon="INFO")
        for slot, lbl in (("A", "2 - Shot A"), ("B", "3 - Shot B"), ("8", "8 - Main")):
            exists = bpy.data.objects.get(SHOT_CAMS[slot]) is not None
            row = col.row(align=True)
            o1 = row.operator("rt.recall_shot", text=lbl,
                              icon="RESTRICT_VIEW_OFF" if exists else "RESTRICT_VIEW_ON")
            o1.shot = slot
            o2 = row.operator("rt.register_shot", text="REC", icon="RADIOBUT_ON")
            o2.shot = slot
        col.separator()
        op = col.operator("rt.force_textured", text="9 - Force ALL Textured", icon="SHADERFX")
        col.separator()
        col.label(text="ComfyUI shots (match current view)", icon="SCENE")
        col.operator("rt.submit_exterior", text="O - Submit Exterior", icon="RENDER_STILL")
        col.operator("rt.submit_interior", text="I - Submit Interior (out to cliff)", icon="RENDER_STILL")
        col.operator("rt.capture_interior_cam", text="Save Interior Cam (current view)", icon="OUTLINER_OB_CAMERA")
        # Sun study season presets - only useful in Act 3 but harmless elsewhere
        sun_present = any(o.type == "LIGHT" and o.data.type == "SUN" for o in bpy.data.objects)
        if sun_present:
            col.separator()
            col.label(text="Sun Study Season", icon="LIGHT_SUN")
            row = col.row(align=True)
            row.operator("rt.season_summer", text="Summer")
            row.operator("rt.season_winter", text="Winter")
        box = layout.box()
        box.label(text="Hotkeys: Alt + 0..9, Alt+I, Alt+O", icon="EVENT_ALT")


# ---- Interior ComfyUI shot (inside looking out at the cliff) --------------
_SUBMIT_PATH = r"C:/Users/NVIDIA/Downloads/AEC_Demo_Portable/AEC_Demo_Portable/scripts/submit_comfyui.py"
_COMFY_INPUT = r"C:/Users/NVIDIA/ComfyUI/ComfyUI_windows_portable/ComfyUI/input"
_COMFY_URL   = "http://127.0.0.1:8188"
INTERIOR_CAM = "InteriorCam"


def _run_aec_submit(interior):
    """Load submit_comfyui.py fresh and run submit() with the chosen prompt set.
    Mirrors auto_comfy's invocation but lets us flip INTERIOR_MODE."""
    import importlib.util as _ilu
    from pathlib import Path as _P
    spec = _ilu.spec_from_file_location("aec_submit_rt", _SUBMIT_PATH)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.COMFY_INPUT = _P(_COMFY_INPUT)
    mod.COMFY_URL = _COMFY_URL
    mod.INTERIOR_MODE = bool(interior)
    return mod.submit(render=True)


class RT_OT_capture_interior_cam(Operator):
    """Save the current camera view as 'InteriorCam' for repeatable interior shots."""
    bl_idname = "rt.capture_interior_cam"
    bl_label = "Capture Interior Camera (current view)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        src = context.scene.camera
        cam = bpy.data.objects.get(INTERIOR_CAM)
        if cam is None or cam.type != "CAMERA":
            cd = bpy.data.cameras.new(INTERIOR_CAM)
            cam = bpy.data.objects.new(INTERIOR_CAM, cd)
            context.scene.collection.objects.link(cam)
        if src is not None and src.type == "CAMERA":
            cam.matrix_world = src.matrix_world.copy()
            cam.data.lens = src.data.lens
            self.report({"INFO"}, f"InteriorCam captured from '{src.name}'")
        else:
            self.report({"WARNING"}, "no active camera to capture; positioned at origin")
        cam.data.show_passepartout = True
        cam.data.passepartout_alpha = 1.0
        cam["_bookmark_matrix"] = [list(r) for r in cam.matrix_world]
        return {"FINISHED"}


def _viewport_rv3d(context):
    """Return (space, region_3d) of the 3D viewport the user is looking at -
    preferring the area the hotkey was invoked over, else the first VIEW_3D."""
    area = getattr(context, "area", None)
    if area and area.type == "VIEW_3D":
        sp = area.spaces.active
        return sp, sp.region_3d
    for w in context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == "VIEW_3D":
                sp = a.spaces.active
                return sp, sp.region_3d
    return None, None


def _snap_shot_cam_to_view(context, cam_name):
    """Move <cam_name> to match the CURRENT viewport view so the render is
    exactly what the user sees. Returns the camera (or None if no viewport)."""
    sp, rv3d = _viewport_rv3d(context)
    if rv3d is None:
        return None
    cam = bpy.data.objects.get(cam_name)
    if cam is None or cam.type != "CAMERA":
        cd = bpy.data.cameras.new(cam_name)
        cam = bpy.data.objects.new(cam_name, cd)
        context.scene.collection.objects.link(cam)
    # world transform = inverse of the view matrix
    cam.matrix_world = rv3d.view_matrix.inverted()
    # match focal length: camera-view uses the active cam's lens, free-nav uses
    # the viewport lens so the field of view tracks what's on screen
    if rv3d.view_perspective == "CAMERA" and context.scene.camera and context.scene.camera.type == "CAMERA":
        cam.data.lens = context.scene.camera.data.lens
        cam.data.sensor_fit = context.scene.camera.data.sensor_fit
    else:
        cam.data.lens = sp.lens
        cam.data.sensor_fit = "AUTO"
    # See very close geometry without near-clipping (scene is mm-scaled).
    cam.data.clip_start = 0.0001
    if cam.data.clip_end < 1000.0:
        cam.data.clip_end = 1000.0
    # Black passepartout: everything outside the camera frame goes solid black
    # so the viewer focuses only on what's in shot.
    cam.data.show_passepartout = True
    cam.data.passepartout_alpha = 1.0
    cam["_bookmark_matrix"] = [list(r) for r in cam.matrix_world]
    return cam


class RT_OT_submit_interior(Operator):
    """Snap a camera to the CURRENT viewport view, then render + submit to
    ComfyUI with the interior prompt set (looking out at the cliff)."""
    bl_idname = "rt.submit_interior"
    bl_label = "AEC Submit - Interior"
    bl_options = {"REGISTER"}

    def execute(self, context):
        cam = _snap_shot_cam_to_view(context, INTERIOR_CAM)
        if cam is not None:
            context.scene.camera = cam
        elif context.scene.camera is None:
            fallback = bpy.data.objects.get(INTERIOR_CAM)
            if fallback:
                context.scene.camera = fallback
        self.report({"INFO"}, "AEC: submitting INTERIOR shot (matched to current view)...")
        try:
            ok = _run_aec_submit(interior=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            self.report({"ERROR"}, f"AEC interior: {e}")
            return {"CANCELLED"}
        self.report({"INFO"} if ok else {"WARNING"},
                    "AEC interior submitted - watch output for Comfy_*_Interior_*" if ok
                    else "AEC interior submit returned False")
        return {"FINISHED"}


class RT_OT_submit_exterior(Operator):
    """Snap a camera to the CURRENT viewport view, then render + submit to
    ComfyUI with the EXTERIOR prompt set. Frame the building to FILL the view
    (avoid empty space) so the environment pass has no void to invent into."""
    bl_idname = "rt.submit_exterior"
    bl_label = "AEC Submit - Exterior"
    bl_options = {"REGISTER"}

    def execute(self, context):
        cam = _snap_shot_cam_to_view(context, "ExteriorCam")
        if cam is not None:
            context.scene.camera = cam
        self.report({"INFO"}, "AEC: submitting EXTERIOR shot (matched to current view)...")
        try:
            ok = _run_aec_submit(interior=False)
        except Exception as e:
            import traceback; traceback.print_exc()
            self.report({"ERROR"}, f"AEC exterior: {e}")
            return {"CANCELLED"}
        self.report({"INFO"} if ok else {"WARNING"},
                    "AEC exterior submitted - watch output folder" if ok
                    else "AEC exterior submit returned False")
        return {"FINISHED"}


CLASSES = (RT_OT_toggle, RT_OT_force_textured, RT_OT_aspect, RT_OT_world_toggle,
           RT_OT_recall_bookmark, RT_OT_save_bookmark,
           RT_OT_recall_shot, RT_OT_register_shot,
           RT_OT_season_summer, RT_OT_season_winter,
           RT_OT_cycle_wall, RT_OT_wall_wood, RT_OT_wall_travertine,
           RT_OT_wall_zinc, RT_OT_capture_interior_cam, RT_OT_submit_interior,
           RT_OT_submit_exterior, RT_OT_warm_daylight, RT_PT_panel)
_KM = []

# (operator_idname, key, properties_dict)
HOTKEYS = [
    ("rt.toggle",        "ZERO",  {"area": ""}),
    ("rt.cycle_wall",     "ONE",   {}),
    ("rt.recall_shot",    "TWO",   {"shot": "A"}),
    ("rt.recall_shot",    "THREE", {"shot": "B"}),
    ("rt.wall_travertine","FOUR",  {}),
    ("rt.wall_zinc",      "FIVE",  {}),
    ("rt.aspect_toggle",    "SIX",   {}),
    ("rt.world_toggle",     "SEVEN", {}),
    ("rt.recall_shot",      "EIGHT", {"shot": "8"}),
    ("rt.force_textured",   "NINE",  {}),
    ("rt.submit_interior",  "I",     {}),
    ("rt.submit_exterior",  "O",     {}),
]


def _disable_conflicting_keymaps():
    """Blender's default Outliner has Alt+0..9 bound to object.hide_collection,
    and the user keyconfig has higher priority than the addon keyconfig - so
    when the cursor sits over the Outliner, those defaults swallow our Alt+
    hotkeys. Disable them here so the addon bindings can fire.
    """
    NUMS = {"ZERO","ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE"}
    BLOCKERS = {"object.hide_collection", "object.subdivision_set"}
    wm = bpy.context.window_manager
    n = 0
    for kc in (wm.keyconfigs.user, wm.keyconfigs.default):
        if kc is None: continue
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                # Alt+0..9 -> hide_collection / subdivision_set (Outliner/Sculpt)
                num_conflict = (kmi.type in NUMS and kmi.idname in BLOCKERS)
                # Alt+I -> Delete/Clear Keyframes (3D View) collides with interior submit
                i_conflict = (kmi.type == "I" and ("keyframe_delete" in kmi.idname
                                                   or "keyframe_clear" in kmi.idname))
                # Alt+O -> image.open / text.open / etc collide with exterior submit
                o_conflict = (kmi.type == "O" and kmi.idname in (
                    "image.open", "text.open", "sequencer.offset_clear", "graph.smooth"))
                if (kmi.alt and not kmi.ctrl and not kmi.shift and not kmi.oskey
                    and (num_conflict or i_conflict or o_conflict) and kmi.active):
                    try:
                        kmi.active = False
                        n += 1
                    except Exception:
                        pass
    if n:
        print(f"[RhinoToggle] disabled {n} conflicting Alt+0..9 / Alt+I default bindings")


def _add_window_bindings(kc):
    """Add all hotkeys to the global 'Window' keymap of the given keyconfig.
    The Window keymap fires regardless of which editor the cursor hovers over,
    so we don't need per-area keymaps (and avoid the 'View3D' vs '3D View'
    name pitfall entirely)."""
    if kc is None:
        return 0
    km = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    n = 0
    for op_idname, key, props in HOTKEYS:
        kmi = km.keymap_items.new(op_idname, type=key, value="PRESS", alt=True)
        for prop_name, prop_val in props.items():
            setattr(kmi.properties, prop_name, prop_val)
        _KM.append((km, kmi))
        n += 1
    return n


def _fix_all_camera_clipping():
    """Every camera should see very close geometry without near-clipping (the
    scene is mm-scaled, so surfaces sit fractions of a unit from the lens).
    Re-applied on every file load via register()."""
    for cd in bpy.data.cameras:
        try:
            cd.clip_start = 0.0001
            if cd.clip_end < 1000.0:
                cd.clip_end = 1000.0
        except Exception:
            pass


def register():
    for c in CLASSES:
        try: bpy.utils.register_class(c)
        except ValueError:
            bpy.utils.unregister_class(c); bpy.utils.register_class(c)
    _disable_conflicting_keymaps()
    _fix_all_camera_clipping()
    wm = bpy.context.window_manager
    # Bind into BOTH the addon and the active (user) keyconfigs. The user
    # keyconfig is always evaluated; the addon one is the conventional home.
    # Binding the global 'Window' keymap means the hotkeys fire over any editor.
    n_addon = _add_window_bindings(wm.keyconfigs.addon)
    n_user = _add_window_bindings(wm.keyconfigs.user)
    print(f"[RhinoToggle] Window-keymap bindings: addon={n_addon} user={n_user}")


def unregister():
    for km, kmi in _KM:
        try: km.keymap_items.remove(kmi)
        except Exception: pass
    _KM.clear()
    for c in reversed(CLASSES):
        try: bpy.utils.unregister_class(c)
        except Exception: pass


if __name__ == "__main__":
    try: unregister()
    except Exception: pass
    register()
    print("[RhinoToggle] registered: Alt+0..7 + Alt+9 hotkeys, N-panel 'Painter' tab")
