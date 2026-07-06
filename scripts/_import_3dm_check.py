"""Enable import_3dm extension, import the .3dm into an empty scene,
count objects/materials, compare to the .blend. Background-safe."""
import bpy, addon_utils
from collections import Counter

EXT = "bl_ext.user_default.import_3dm"
PATH = r"C:\Users\NVIDIA\Downloads\Updated Geo\aec_demo_rhino_26.3dm"

ok = False
try:
    addon_utils.enable(EXT, default_set=True, persistent=False)
    ok = True
    print(f"[chk] enabled {EXT}")
except Exception as e:
    print(f"[chk] enable failed: {e}")

# wipe default scene objects
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

imported = False
try:
    bpy.ops.import_3dm.some_data(filepath=PATH, import_hidden=False)
    imported = True
    print("[chk] imported via bpy.ops.import_3dm.some_data")
except Exception as e:
    print(f"[chk] some_data with kwargs failed: {e}")
    try:
        bpy.ops.import_3dm.some_data(filepath=PATH)
        imported = True
        print("[chk] imported via bpy.ops.import_3dm.some_data (filepath only)")
    except Exception as e2:
        print(f"[chk] some_data failed: {e2}")

n_obj = len([o for o in bpy.data.objects if o.type == "MESH"])
print(f"[chk] imported MESH objects: {n_obj}")
print(f"[chk] total objects: {len(bpy.data.objects)}")
print(f"[chk] materials: {len(bpy.data.materials)}")
mat_use = Counter()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material: mat_use[s.material.name] += 1
print("[chk] material usage (top 20):")
for m, n in mat_use.most_common(20):
    print(f"    {n:>4}  {m}")
print("[chk] sample mesh names:")
for o in sorted([x.name for x in bpy.data.objects if x.type=='MESH'])[:25]:
    print(f"    {o}")
