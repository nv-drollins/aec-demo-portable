"""Dump v17.blend mesh-slot -> material assignments to a JSON file
that the Act 2 builder can consume.
"""
import bpy, json

OUT = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v17_assignments.json"

dump = {
    "objects": {},      # obj_name -> [mat_name | None per slot]
    "materials": [],    # list of material names available in v17
}

for o in bpy.data.objects:
    if o.type != "MESH": continue
    slots = []
    for s in o.material_slots:
        slots.append(s.material.name if s.material else None)
    dump["objects"][o.name] = slots

dump["materials"] = sorted([m.name for m in bpy.data.materials])

# also note whether each material has any image textures, to give us a
# sense of how "Rhino-flat" they look
mat_info = {}
for m in bpy.data.materials:
    has_tex = False
    if m.use_nodes and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image is not None:
                has_tex = True
                break
    bc = None
    if m.use_nodes:
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf and "Base Color" in bsdf.inputs:
            bc = list(bsdf.inputs["Base Color"].default_value)
    mat_info[m.name] = {"has_tex": has_tex, "base_color": bc}

dump["material_info"] = mat_info

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(dump, f, indent=1)

n_obj = len(dump["objects"])
n_mat = len(dump["materials"])
print(f"[v17 dump] wrote {OUT}: {n_obj} objects, {n_mat} materials")
print(f"[v17 dump] materials with image textures: {sum(1 for v in mat_info.values() if v['has_tex'])}")
print(f"[v17 dump] materials flat-colored (no textures): {sum(1 for v in mat_info.values() if not v['has_tex'])}")
