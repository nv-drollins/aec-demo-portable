"""Pass C: remove orphan/temp images, pack real textures, verify the toggle
system, save. Background-safe."""
import bpy, json, os
from collections import Counter

DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v4.blend"

# 1. Remove orphan/temp images that broke pack_all
removed = 0
for img in list(bpy.data.images):
    if img.packed_file:
        continue
    fp = bpy.path.abspath(img.filepath) if img.filepath else ""
    nm = img.name
    is_temp = ("ComfyUI_temp" in nm or "SDNode" in img.filepath or nm.startswith("viewport.png")
               or (fp and not os.path.exists(fp)))
    if is_temp:
        try:
            bpy.data.images.remove(img, do_unlink=True); removed += 1
        except Exception:
            pass
# also drop any movie-clip / sound referencing the missing mp4
for mc in list(bpy.data.movieclips):
    try: bpy.data.movieclips.remove(mc)
    except Exception: pass
print(f"[passC] removed {removed} orphan/temp images")

# 2. Pack real textures now
try:
    bpy.ops.file.pack_all()
    print("[passC] pack_all OK")
except Exception as e:
    print(f"[passC] pack_all warn: {e}")
packed = sum(1 for i in bpy.data.images if i.packed_file)
print(f"[passC] packed images: {packed}")

# 3. Verify snapshot + materials
snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
print(f"[passC] snapshot slots: {len(snap)}")
missing_tex = sum(1 for e in snap if not bpy.data.materials.get(e["textured_mat"]))
missing_bas = sum(1 for e in snap if not bpy.data.materials.get(e["basic_mat"]))
print(f"[passC] snapshot integrity: missing_textured={missing_tex} missing_basic={missing_bas}")

# 4. Exec runtime + simulate toggles
txt = bpy.data.texts["rhino_toggle.py"]
ns = {}
exec(compile(txt.as_string(), txt.name, "exec"), ns)
ns["register"]()

def state():
    c = Counter()
    for e in snap:
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["textured_mat"]: c["textured"] += 1
        elif m and m.name == e["basic_mat"]: c["basic"] += 1
        else: c["other"] += 1
    return dict(c)

print(f"[passC] initial state: {state()}")
bpy.ops.rt.toggle(area="")           # all -> basic (or textured)
print(f"[passC] after Alt+0:   {state()}")
bpy.ops.rt.toggle(area="")           # back
print(f"[passC] after Alt+0:   {state()}")
bpy.ops.rt.force_textured()
print(f"[passC] after Alt+9:   {state()}")

# wall swatches
def wall_state():
    c = Counter()
    for e in snap:
        if e["area"] != "walls": continue
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        c[m.name if m else None] += 1
    return dict(c)
bpy.ops.rt.wall_travertine()
print(f"[passC] walls after Alt+4: {wall_state()}")
bpy.ops.rt.force_textured()

# 5. Camera + worlds
sc = bpy.context.scene
print(f"[passC] camera: {sc.camera.name if sc.camera else None}  bookmark={'_bookmark_matrix' in (sc.camera or {})}")
print(f"[passC] world: {sc.world.name}; worlds={[w.name for w in bpy.data.worlds]}")
print(f"[passC] render: {sc.render.resolution_x}x{sc.render.resolution_y} engine={sc.render.engine}")

# keymap count
km = bpy.context.window_manager.keyconfigs.user.keymaps.get("Window")
n = sum(1 for kmi in km.keymap_items if kmi.idname.startswith("rt.")) if km else 0
print(f"[passC] user/Window rt.* bindings: {n}")

bpy.ops.wm.save_mainfile()
print(f"[passC] SAVED ({os.path.getsize(DST)/1024/1024:.1f} MB)")
print("[passC] DONE")
