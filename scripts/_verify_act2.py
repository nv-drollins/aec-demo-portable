"""Verify cliff_house_act2_textured.blend is fully wired."""
import bpy, os
print("[verify] file:", bpy.data.filepath)
print("[verify] file size MB:", round(os.path.getsize(bpy.data.filepath)/1024/1024, 1))

clay = bpy.data.materials.get("Clay_Override")
print(f"[verify] Clay_Override material: {'OK' if clay else 'MISSING'}  fake_user={clay.use_fake_user if clay else None}")

txt = bpy.data.texts.get("clay_toggle.py")
if txt is None:
    print("[verify] FAIL: no clay_toggle.py text block")
else:
    print(f"[verify] OK   text 'clay_toggle.py'  use_module={txt.use_module}  lines={len(txt.lines)}")

packed = sum(1 for i in bpy.data.images if i.packed_file)
unpacked_missing = sum(1 for i in bpy.data.images if not i.packed_file and i.filepath and not os.path.exists(bpy.path.abspath(i.filepath)))
print(f"[verify] images packed={packed}  unpacked-and-missing={unpacked_missing}")

print("[verify] materials in use (top 12):")
from collections import Counter
mu = Counter()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material: mu[s.material.name] += 1
for m, n in mu.most_common(12):
    print(f"    {n:>4}x  {m}")

print("[verify] scene/camera:")
sc = bpy.context.scene
print(f"    scene='{sc.name}'  res={sc.render.resolution_x}x{sc.render.resolution_y}  cam={sc.camera.name if sc.camera else '(none)'}  frames={sc.frame_start}-{sc.frame_end}")

print("[verify] exec embedded runtime + smoke test toggle:")
ns = {}
exec(compile(txt.as_string(), txt.name, "exec"), ns)
ns["register"]()
print("    register() OK")
vl = bpy.context.view_layer
print(f"    pre-toggle  override={vl.material_override}")
bpy.ops.ct.toggle_clay()
print(f"    post-toggle override={vl.material_override.name if vl.material_override else None}")
bpy.ops.ct.toggle_clay()
print(f"    re-toggle   override={vl.material_override.name if vl.material_override else None}")

km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("3D View")
n_kmi = sum(1 for kmi in km.keymap_items if kmi.idname == "ct.toggle_clay") if km else 0
print(f"[verify] keymap items for ct.toggle_clay in 3D View: {n_kmi}  (expected 1)")
