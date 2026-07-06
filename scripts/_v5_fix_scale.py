"""Fix the 1000x scale mismatch: scale the imported interior (New_Interior
collection) by 0.001 about the world origin so it matches v3's mm-scale
building. Scaling about origin corrects size AND position together."""
import bpy, json, os
from mathutils import Matrix, Vector

V5 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v5.blend"
FACTOR = 0.001

bpy.ops.wm.open_mainfile(filepath=V5)

coll = bpy.data.collections.get("New_Interior")
if coll is None:
    print("[scale] FAIL: New_Interior collection not found")
    raise SystemExit(0)

imported = list(coll.all_objects)
imported_names = {o.name for o in imported}
print(f"[scale] imported objects: {len(imported)}")

# sample BEFORE
def dims(name):
    o = bpy.data.objects.get(name)
    return tuple(round(x, 4) for x in o.dimensions) if o else None
sample_int = next((o.name for o in imported if o.type == "MESH" and "tread" in o.name.lower()), None) \
             or next((o.name for o in imported if o.type == "MESH"), None)
print(f"[scale] BEFORE interior sample {sample_int}: {dims(sample_int)}")
print(f"[scale] v3 exterior H2_roof_slab: {dims('H2_roof_slab')}")

# Scale each ROOT of the imported hierarchy about world origin.
S = Matrix.Diagonal((FACTOR, FACTOR, FACTOR, 1.0))
roots = [o for o in imported if (o.parent is None) or (o.parent.name not in imported_names)]
print(f"[scale] hierarchy roots to scale: {len(roots)}")
for o in roots:
    o.matrix_world = S @ o.matrix_world

bpy.context.view_layer.update()

# sample AFTER
print(f"[scale] AFTER interior sample {sample_int}: {dims(sample_int)}")

# bbox comparison: imported interior vs v3 building (snapshot objs, robust to outliers)
with open(r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json") as f:
    v3names = {e["obj"] for e in json.load(f)["snapshot"]}

def bbox(objs):
    mn = Vector((1e18,)*3); mx = Vector((-1e18,)*3)
    for o in objs:
        if o.type != "MESH": continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

v3b = [o for o in bpy.data.objects if o.type == "MESH" and o.name in v3names]
imn, imx = bbox(imported)
vmn, vmx = bbox(v3b)
print(f"[scale] interior bbox: min={tuple(round(x,3) for x in imn)} max={tuple(round(x,3) for x in imx)}")
print(f"[scale] v3 bldg  bbox: min={tuple(round(x,3) for x in vmn)} max={tuple(round(x,3) for x in vmx)}")

bpy.ops.wm.save_as_mainfile(filepath=V5, compress=True)
print(f"[scale] SAVED ({os.path.getsize(V5)/1024/1024:.1f} MB)")
print("[scale] DONE")
