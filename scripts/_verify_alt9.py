"""Smoke test Alt+9 (force textured) and confirm keymap has 9 items."""
import bpy, json

txt = bpy.data.texts["rhino_toggle.py"]
ns = {}; exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()

# Force a mixed state: flip walls + roof to basic, leave others textured
bpy.ops.rt.toggle(area="walls")
bpy.ops.rt.toggle(area="roof")

def count_basic_total():
    snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
    n = 0
    for e in snap:
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["basic_mat"]: n += 1
    return n

print(f"[verify] basic slots after mixing (walls+roof flipped): {count_basic_total()}")

# Now press Alt+9 equivalent
bpy.ops.rt.toggle(area="", force="textured")
print(f"[verify] basic slots after Alt+9 (force textured): {count_basic_total()}")

# Press it again to confirm idempotence
bpy.ops.rt.toggle(area="", force="textured")
print(f"[verify] basic slots after another Alt+9 (idempotent): {count_basic_total()}")

km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("3D View")
n = 0
if km:
    for kmi in km.keymap_items:
        if kmi.idname in ("rt.toggle","rt.aspect_toggle","rt.world_toggle"): n += 1
print(f"[verify] runtime keymap items: {n}  (expected 9: Alt+0..7 + Alt+9)")
