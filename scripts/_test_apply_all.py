"""Smoke-test Apply All + verify hotkey count."""
import bpy

txt = bpy.data.texts["material_painter.py"]
ns = {}
exec(compile(txt.as_string(), txt.name, "exec"), ns)
ns["register"]()

def slots_with(name):
    n = 0
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        for s in o.material_slots:
            if s.material and s.material.name == name: n += 1
    return n

watch = ["White_Travertine", "Timber_Engineered_Oak", "Concrete_Light_3", "Concrete_Light_Patio",
         "polished_concrete", "Grey_Slate", "Timber_Oiled_Dark", "Aluminum_Anodized_Dark",
         "MP_Travertine", "MP_Oak_Floor", "MP_Polished_Concrete_Floor", "MP_Zinc_Roof",
         "MP_Walnut_Accent", "MP_Dark_Anodized"]

print("[apply-all] BEFORE")
for m in watch: print(f"  {m:36s} {slots_with(m)}")

bpy.ops.mp.apply_all()

print("[apply-all] AFTER")
for m in watch: print(f"  {m:36s} {slots_with(m)}")

bpy.ops.mp.reset()

print("[apply-all] AFTER RESET")
for m in watch: print(f"  {m:36s} {slots_with(m)}")

km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("3D View")
if km:
    n = sum(1 for kmi in km.keymap_items if kmi.idname.startswith("mp.") or (kmi.idname == "wm.call_menu_pie" and getattr(kmi.properties, "name", "") == "MP_MT_pie"))
    print(f"[hotkeys] 3D View keymap items for mp.*/pie: {n}  (expected 11)")
