"""Diagnostic: which cliff_house_26 objects are NOT in v3, and what type are they?"""
import bpy, json
from collections import Counter

with open(r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json") as f:
    v3 = json.load(f)
v3_names = {e["obj"] for e in v3["snapshot"]}
print(f"[diag] v3 snapshot mesh names: {len(v3_names)}")

# also need ALL v3 mesh names (some may have no material). Open v5 (=v3) quickly? 
# Instead: treat snapshot names as the v3 set (good enough for overlap).

types = Counter()
new_by_type = Counter()
new_mesh_examples = []
new_other_examples = []
for o in bpy.data.objects:
    types[o.type] += 1
    if o.name not in v3_names:
        new_by_type[o.type] += 1
        if o.type == "MESH" and len(new_mesh_examples) < 20:
            new_mesh_examples.append(o.name)
        elif o.type != "MESH" and len(new_other_examples) < 20:
            inst = ""
            if o.type == "EMPTY" and o.instance_collection:
                inst = f" -> instances '{o.instance_collection.name}'"
            new_other_examples.append(f"{o.name} [{o.type}]{inst}")

print(f"[diag] cliff26 total objects by type: {dict(types)}")
print(f"[diag] NEW (not in v3) by type: {dict(new_by_type)}")
print(f"[diag] sample NEW meshes: {new_mesh_examples}")
print(f"[diag] sample NEW non-mesh: {new_other_examples}")
