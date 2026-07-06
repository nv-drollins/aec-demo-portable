"""Inspect blender_east_wall.blend: object count, mesh names (esp. east/door),
materials. Determine if it's the whole scene or just wall pieces."""
import bpy
from collections import Counter

print(f"OBJECTS={len(bpy.data.objects)} MESHES={len(bpy.data.meshes)} MATERIALS={len(bpy.data.materials)}")
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print(f"MESH objects: {len(meshes)}")

# East/door related meshes
print("=== east / door / wall-named meshes ===")
for o in sorted(meshes, key=lambda x: x.name):
    nm = o.name.lower()
    if any(k in nm for k in ("east", "_e_", "door", "wall")):
        d = tuple(round(v, 3) for v in o.dimensions)
        mats = [s.material.name if s.material else None for s in o.material_slots]
        print(f"  {o.name}  dims={d}  mats={mats}")

# If few objects, list all
if len(meshes) <= 30:
    print("=== ALL meshes (small file) ===")
    for o in sorted(meshes, key=lambda x: x.name):
        d = tuple(round(v, 3) for v in o.dimensions)
        mats = [s.material.name if s.material else None for s in o.material_slots]
        print(f"  {o.name}  dims={d}  mats={mats}")

print("=== materials in use ===")
mu = Counter()
for o in meshes:
    for s in o.material_slots:
        if s.material: mu[s.material.name] += 1
for m, n in mu.most_common():
    print(f"  {n:>4}  {m}")
