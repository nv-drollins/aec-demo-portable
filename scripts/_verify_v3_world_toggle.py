"""Quick check: both worlds present, Alt+7 toggle cycles cleanly."""
import bpy
sc = bpy.context.scene

w_studio = bpy.data.worlds.get("Studio_Gray")
w_arch   = bpy.data.worlds.get("ArchWorld")
print(f"[verify] Studio_Gray present: {w_studio is not None}  fake_user={getattr(w_studio,'use_fake_user',None)}")
print(f"[verify] ArchWorld    present: {w_arch   is not None}  fake_user={getattr(w_arch  ,'use_fake_user',None)}")
print(f"[verify] active world on load: {sc.world.name if sc.world else '(none)'}")

txt = bpy.data.texts.get("rhino_toggle.py")
ns = {}; exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()
print("[verify] register() OK")

# Smoke-test cycling
for i in range(3):
    bpy.ops.rt.world_toggle()
    print(f"[verify] after toggle #{i+1}: world = {sc.world.name}")

# Hotkey count - should be 8 now (Alt+0..7)
km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("3D View")
n = 0
if km:
    for kmi in km.keymap_items:
        if kmi.idname in ("rt.toggle","rt.aspect_toggle","rt.world_toggle"): n += 1
print(f"[verify] runtime keymap items: {n}  (expected 8: Alt+0..7)")
