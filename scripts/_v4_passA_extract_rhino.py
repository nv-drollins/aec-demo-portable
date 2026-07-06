"""Pass A: import the .3dm, capture per-mesh Rhino material, suffix the
materials with _RH (+ fake_user), save a temp .blend we can append from,
and dump the mesh->rhino-material mapping to JSON.
Run with --factory-startup so the engon addon noise stays out.
"""
import bpy, addon_utils, json

DM = r"C:\Users\NVIDIA\Downloads\Updated Geo\aec_demo_rhino_26.3dm"
TMP_BLEND = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_rhino_26_basic.blend"
MAP_JSON  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_rhino_26_map.json"

addon_utils.enable("bl_ext.user_default.import_3dm", default_set=True, persistent=False)

# clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.import_3dm.some_data(filepath=DM)

# mesh name -> material name (slot 0)
mesh_to_mat = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    mat = o.material_slots[0].material if o.material_slots and o.material_slots[0].material else None
    mesh_to_mat[o.name] = mat.name if mat else None

# Suffix every material with _RH and keep it (fake_user) so it survives append.
rename = {}
for m in list(bpy.data.materials):
    new = m.name + "_RH"
    rename[m.name] = new
    m.name = new
    m.use_fake_user = True

# remap the mapping to suffixed names
mesh_to_mat_rh = {k: (rename[v] if v in rename else None) for k, v in mesh_to_mat.items()}

with open(MAP_JSON, "w", encoding="utf-8") as f:
    json.dump(mesh_to_mat_rh, f, indent=1)

# Save a temp blend that holds the _RH materials for appending in Pass B.
bpy.ops.wm.save_as_mainfile(filepath=TMP_BLEND, compress=True)

n_mats = len([m for m in bpy.data.materials if m.name.endswith("_RH")])
n_mapped = sum(1 for v in mesh_to_mat_rh.values() if v)
print(f"[passA] meshes mapped: {len(mesh_to_mat_rh)}  with-material: {n_mapped}")
print(f"[passA] _RH materials: {n_mats}")
print(f"[passA] saved temp blend: {TMP_BLEND}")
print(f"[passA] saved map: {MAP_JSON}")
print("[passA] DONE")
