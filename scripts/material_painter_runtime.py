"""Material Painter Runtime
Embedded as a Text block inside cliff_house_materials_v18.blend.
Auto-registers on file load (text.use_module = True + Auto Run Python Scripts).

Hotkeys (3D View, Object Mode):
  Alt + 1  Walls -> Travertine          (MP_Travertine)
  Alt + 2  Walls -> Polished Concrete   (MP_Polished_Concrete_Wall)
  Alt + 3  Walls -> Wood Cladding       (MP_Wood_Cladding)
  Alt + 4  Interior Floors -> Oak       (MP_Oak_Floor)
  Alt + 5  Outdoor Floors -> Concrete   (MP_Polished_Concrete_Floor)
  Alt + 6  Roof -> Zinc                 (MP_Zinc_Roof)
  Alt + 7  Wood Trim -> Walnut          (MP_Walnut_Accent)
  Alt + 8  Frames -> Dark Anodized      (MP_Dark_Anodized)
  Alt + 9  APPLY ALL upgrades (coastal preset)
  Alt + 0  RESET to artist's materials

Pie menu:
  Alt + M  Opens radial picker with same options.

N-Panel:
  3D View > Sidebar (N) > Painter tab.
"""

import bpy
import json
from bpy.types import Operator, Menu, Panel

bl_info = {
    "name": "Material Painter (Cliff House v18)",
    "blender": (5, 0, 0),
    "category": "Material",
}

# Material categories: a single hotkey may freely swap any material in its
# category to the chosen target (so Alt+1 then Alt+2 then Alt+3 keep cycling
# the wall finish instead of one-shot).
WALL_MATS  = ["White_Travertine", "MP_Travertine", "MP_Polished_Concrete_Wall", "MP_Wood_Cladding"]
FLOOR_INT  = ["Timber_Engineered_Oak", "MP_Oak_Floor"]
FLOOR_EXT  = ["Concrete_Light_3", "Concrete_Light_Patio", "polished_concrete", "MP_Polished_Concrete_Floor"]
ROOF_MATS  = ["Grey_Slate", "MP_Zinc_Roof"]
TRIM_MATS  = ["Timber_Oiled_Dark", "MP_Walnut_Accent"]
FRAME_MATS = ["Aluminum_Anodized_Dark", "MP_Dark_Anodized"]

UPGRADES = {
    "travertine":      {"label": "Walls: Travertine",        "from": WALL_MATS,  "to": "MP_Travertine"},
    "concrete_wall":   {"label": "Walls: Polished Concrete", "from": WALL_MATS,  "to": "MP_Polished_Concrete_Wall"},
    "wood_cladding":   {"label": "Walls: Wood Cladding",     "from": WALL_MATS,  "to": "MP_Wood_Cladding"},
    "oak_floor":       {"label": "Floors: European Oak",     "from": FLOOR_INT,  "to": "MP_Oak_Floor"},
    "concrete_floor":  {"label": "Floors: Polished Concrete","from": FLOOR_EXT,  "to": "MP_Polished_Concrete_Floor"},
    "zinc_roof":       {"label": "Roof: Zinc Standing Seam", "from": ROOF_MATS,  "to": "MP_Zinc_Roof"},
    "walnut_accent":   {"label": "Trim: Walnut",             "from": TRIM_MATS,  "to": "MP_Walnut_Accent"},
    "dark_anodized":   {"label": "Frames: Dark Anodized",    "from": FRAME_MATS, "to": "MP_Dark_Anodized"},
}

# Order matters for the "all" preset.
COASTAL_PRESET = ["travertine", "oak_floor", "concrete_floor", "zinc_roof", "walnut_accent", "dark_anodized"]

SNAPSHOT_KEY = "_mp_artist_snapshot"


def _get_snapshot():
    raw = bpy.context.scene.get(SNAPSHOT_KEY, "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _apply_upgrade(upgrade_id):
    spec = UPGRADES.get(upgrade_id)
    if not spec:
        return 0, "unknown upgrade " + str(upgrade_id)
    new_mat = bpy.data.materials.get(spec["to"])
    if new_mat is None:
        return 0, "missing material '" + spec["to"] + "' (rebuild required)"
    targets = set(spec["from"])
    changed = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            if slot.material and slot.material.name in targets:
                if slot.material is new_mat:
                    continue
                slot.material = new_mat
                changed += 1
    return changed, "swapped " + str(changed) + " slot(s) -> " + spec["to"]


def _reset_all():
    snap = _get_snapshot()
    if not snap:
        return 0, "no snapshot found; cannot reset"
    changed = 0
    missing_objs = 0
    missing_mats = 0
    for entry in snap:
        obj_name = entry.get("obj")
        slot_idx = entry.get("slot")
        mat_name = entry.get("mat")
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            missing_objs += 1
            continue
        if slot_idx >= len(obj.material_slots):
            continue
        mat = bpy.data.materials.get(mat_name) if mat_name else None
        if mat_name and mat is None:
            missing_mats += 1
            continue
        if obj.material_slots[slot_idx].material is not mat:
            obj.material_slots[slot_idx].material = mat
            changed += 1
    msg = "restored " + str(changed) + " slot(s)"
    if missing_objs or missing_mats:
        msg += " (skipped: " + str(missing_objs) + " obj, " + str(missing_mats) + " mat)"
    return changed, msg


# ---------------- operators ----------------

class MP_OT_apply(Operator):
    bl_idname = "mp.apply"
    bl_label = "Apply Material Upgrade"
    bl_options = {"REGISTER", "UNDO"}
    upgrade_id: bpy.props.StringProperty()

    def execute(self, context):
        n, msg = _apply_upgrade(self.upgrade_id)
        self.report({"INFO"} if n else {"WARNING"}, "MP: " + msg)
        return {"FINISHED"}


class MP_OT_apply_all(Operator):
    bl_idname = "mp.apply_all"
    bl_label = "Apply Coastal Preset (All Upgrades)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        total = 0
        for uid in COASTAL_PRESET:
            n, _ = _apply_upgrade(uid)
            total += n
        self.report({"INFO"}, "MP: applied coastal preset (" + str(total) + " slot swaps)")
        return {"FINISHED"}


class MP_OT_reset(Operator):
    bl_idname = "mp.reset"
    bl_label = "Reset to Artist Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n, msg = _reset_all()
        self.report({"INFO"} if n else {"WARNING"}, "MP: " + msg)
        return {"FINISHED"}


# ---------------- pie menu ----------------

class MP_MT_pie(Menu):
    bl_label = "Material Painter"
    bl_idname = "MP_MT_pie"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 8 slices around + center labels; counterclockwise from W
        pie.operator("mp.apply", text=UPGRADES["travertine"]["label"]).upgrade_id = "travertine"           # W
        pie.operator("mp.apply", text=UPGRADES["wood_cladding"]["label"]).upgrade_id = "wood_cladding"   # E
        pie.operator("mp.apply", text=UPGRADES["oak_floor"]["label"]).upgrade_id = "oak_floor"           # S
        pie.operator("mp.apply", text=UPGRADES["zinc_roof"]["label"]).upgrade_id = "zinc_roof"           # N
        pie.operator("mp.apply", text=UPGRADES["concrete_wall"]["label"]).upgrade_id = "concrete_wall"   # NW
        pie.operator("mp.apply", text=UPGRADES["walnut_accent"]["label"]).upgrade_id = "walnut_accent"   # NE
        pie.operator("mp.apply", text=UPGRADES["concrete_floor"]["label"]).upgrade_id = "concrete_floor" # SW
        pie.operator("mp.apply", text=UPGRADES["dark_anodized"]["label"]).upgrade_id = "dark_anodized"   # SE


# ---------------- N-panel ----------------

class MP_PT_panel(Panel):
    bl_label = "Material Painter"
    bl_idname = "MP_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Painter"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Walls", icon="MATERIAL")
        col.operator("mp.apply", text="1 - Travertine").upgrade_id = "travertine"
        col.operator("mp.apply", text="2 - Polished Concrete").upgrade_id = "concrete_wall"
        col.operator("mp.apply", text="3 - Wood Cladding").upgrade_id = "wood_cladding"
        col.separator()
        col.label(text="Floors", icon="MESH_PLANE")
        col.operator("mp.apply", text="4 - European Oak").upgrade_id = "oak_floor"
        col.operator("mp.apply", text="5 - Polished Concrete").upgrade_id = "concrete_floor"
        col.separator()
        col.label(text="Roof & Trim", icon="HOME")
        col.operator("mp.apply", text="6 - Zinc Roof").upgrade_id = "zinc_roof"
        col.operator("mp.apply", text="7 - Walnut Trim").upgrade_id = "walnut_accent"
        col.operator("mp.apply", text="8 - Dark Anodized Frames").upgrade_id = "dark_anodized"
        col.separator()
        col.operator("mp.apply_all", text="9 - Apply All (Coastal)", icon="BRUSH_DATA")
        col.operator("mp.reset", text="0 - Reset to Artist", icon="LOOP_BACK")
        col.separator()
        box = layout.box()
        box.label(text="Hotkeys: Alt+0..9", icon="EVENT_ALT")
        box.label(text="Pie: Alt+M", icon="EVENT_M")


# ---------------- registration / keymap ----------------

CLASSES = (MP_OT_apply, MP_OT_apply_all, MP_OT_reset, MP_MT_pie, MP_PT_panel)
_KEYMAPS = []

ALT_HOTKEYS = [
    ("ONE",   "travertine"),
    ("TWO",   "concrete_wall"),
    ("THREE", "wood_cladding"),
    ("FOUR",  "oak_floor"),
    ("FIVE",  "concrete_floor"),
    ("SIX",   "zinc_roof"),
    ("SEVEN", "walnut_accent"),
    ("EIGHT", "dark_anodized"),
]


def register():
    for c in CLASSES:
        try:
            bpy.utils.register_class(c)
        except ValueError:
            bpy.utils.unregister_class(c)
            bpy.utils.register_class(c)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    for key, uid in ALT_HOTKEYS:
        kmi = km.keymap_items.new("mp.apply", type=key, value="PRESS", alt=True)
        kmi.properties.upgrade_id = uid
        _KEYMAPS.append((km, kmi))
    kmi = km.keymap_items.new("mp.apply_all", type="NINE", value="PRESS", alt=True)
    _KEYMAPS.append((km, kmi))
    kmi = km.keymap_items.new("mp.reset", type="ZERO", value="PRESS", alt=True)
    _KEYMAPS.append((km, kmi))
    kmi = km.keymap_items.new("wm.call_menu_pie", type="M", value="PRESS", alt=True)
    kmi.properties.name = "MP_MT_pie"
    _KEYMAPS.append((km, kmi))


def unregister():
    for km, kmi in _KEYMAPS:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    _KEYMAPS.clear()
    for c in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("[MaterialPainter] registered: 10 hotkeys (Alt+0..9), pie (Alt+M), N-panel 'Painter'")
