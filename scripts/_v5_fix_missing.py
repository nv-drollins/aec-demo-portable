"""Fix v5: remap the 8 snapshot entries whose textured_mat was purged from v3,
set Studio_Gray as the default world (HDRI stays on Alt+7), apply clean
textured default, save."""
import bpy, json, os

V5 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v5.blend"
SNAPSHOT_KEY = "_act2_snapshot"

REMAP = {
    "Concrete_Black": "Concrete_Black_v17",
    "Concrete_Black.001": "Concrete_Black_v17",
    "Material": "White_Travertine",
    "Material.004": "Concrete_Black_v17",
    "Water_Pool": "Water_Pool_v17",
}

bpy.ops.wm.open_mainfile(filepath=V5)
snap = json.loads(bpy.context.scene.get(SNAPSHOT_KEY, "[]"))

fixed = 0
for e in snap:
    for key in ("textured_mat", "basic_mat"):
        if not bpy.data.materials.get(e[key]):
            r = REMAP.get(e[key])
            if r and bpy.data.materials.get(r):
                e[key] = r; fixed += 1
            elif "_v17" in e["basic_mat"] and bpy.data.materials.get(e["basic_mat"]):
                e[key] = e["basic_mat"]; fixed += 1
            else:
                e[key] = "White_Travertine" if key == "textured_mat" else "White_Travertine_v17"; fixed += 1
bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
print(f"[fix] remapped {fixed} missing material refs")

# apply clean textured default
for e in snap:
    o = bpy.data.objects.get(e["obj"])
    if not o or e["slot"] >= len(o.material_slots): continue
    tm = bpy.data.materials.get(e["textured_mat"])
    if tm:
        o.material_slots[e["slot"]].material = tm
        tm.use_fake_user = True
    bm = bpy.data.materials.get(e["basic_mat"])
    if bm: bm.use_fake_user = True

# default world = Studio_Gray (preferred recording look); HDRI on Alt+7
studio = bpy.data.worlds.get("Studio_Gray")
if studio:
    bpy.context.scene.world = studio

# integrity re-check
mt = sum(1 for e in snap if not bpy.data.materials.get(e["textured_mat"]))
mb = sum(1 for e in snap if not bpy.data.materials.get(e["basic_mat"]))
print(f"[fix] integrity now: missing_textured={mt} missing_basic={mb}")
print(f"[fix] active world: {bpy.context.scene.world.name}")

try: bpy.ops.file.pack_all()
except Exception as e: print(f"[fix] pack warn: {e}")
bpy.ops.wm.save_as_mainfile(filepath=V5, compress=True)
print(f"[fix] SAVED ({os.path.getsize(V5)/1024/1024:.1f} MB)")
print("[fix] DONE")
