"""Clay Toggle Runtime
Embedded text block inside a textured cliff_house scene.

  Alt + 0   toggle the view-layer material override between None (textured)
            and a clay override material (gray architectural shaded look).
            Same idea as a presentation toggle - no slot rewrites, instant.

Optional N-panel button under 3D View > Sidebar (N) > Painter tab.
"""

import bpy
from bpy.types import Operator, Panel

CLAY_MAT_NAME = "Clay_Override"


def _ensure_clay_material():
    mat = bpy.data.materials.get(CLAY_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(CLAY_MAT_NAME)
        mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.60, 0.58, 0.55, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


class CT_OT_toggle(Operator):
    bl_idname = "ct.toggle_clay"
    bl_label = "Toggle Clay Override"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        vl = context.view_layer
        clay = _ensure_clay_material()
        if vl.material_override is clay:
            vl.material_override = None
            self.report({"INFO"}, "Clay OFF -> showing artist textures")
        else:
            vl.material_override = clay
            self.report({"INFO"}, "Clay ON -> hiding artist textures")
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
        return {"FINISHED"}


class CT_PT_panel(Panel):
    bl_label = "Clay Toggle"
    bl_idname = "CT_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Painter"

    def draw(self, context):
        vl = context.view_layer
        clay = bpy.data.materials.get(CLAY_MAT_NAME)
        on = clay is not None and vl.material_override is clay
        layout = self.layout
        col = layout.column(align=True)
        icon = "RESTRICT_RENDER_OFF" if on else "MATERIAL"
        label = "Clay: ON" if on else "Clay: OFF (textured)"
        col.operator("ct.toggle_clay", text=label, icon=icon)
        box = layout.box()
        box.label(text="Hotkey: Alt + 0", icon="EVENT_ALT")


CLASSES = (CT_OT_toggle, CT_PT_panel)
_KM = []


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
    kmi = km.keymap_items.new("ct.toggle_clay", type="ZERO", value="PRESS", alt=True)
    _KM.append((km, kmi))


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
    print("[ClayToggle] registered: Alt+0 toggles clay override; N-panel Painter tab")
