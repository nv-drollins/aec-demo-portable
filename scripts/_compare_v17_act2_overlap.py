"""Compare v17 mesh names against Act 2 mesh names to estimate how many
Act 2 meshes can be matched 1:1 to a v17 material assignment."""
import bpy, json, os
from collections import Counter

V17_JSON = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v17_assignments.json"

with open(V17_JSON, "r", encoding="utf-8") as f:
    v17 = json.load(f)
v17_objs = v17["objects"]

matched = 0
unmatched = []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    if o.name in v17_objs:
        matched += 1
    else:
        unmatched.append(o.name)

print(f"Act 2 meshes total: {sum(1 for o in bpy.data.objects if o.type=='MESH')}")
print(f"Match v17 by name : {matched}")
print(f"No v17 match      : {len(unmatched)}")

# Map Act 2 materials -> distribution of v17 materials they'd inherit
mat_inherit = Counter()
mat_orphan  = Counter()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    art_slots = [s.material.name if s.material else None for s in o.material_slots]
    if o.name in v17_objs:
        v17_slots = v17_objs[o.name]
        for i, m in enumerate(art_slots):
            if m is None: continue
            v17_mat = v17_slots[i] if i < len(v17_slots) else None
            if v17_mat: mat_inherit[(m, v17_mat)] += 1
            else: mat_orphan[m] += 1
    else:
        for m in art_slots:
            if m: mat_orphan[m] += 1

print()
print("== inheritance map (Act 2 mat -> v17 mat, count) ==")
seen_art = set()
for (art, rhino), n in sorted(mat_inherit.items(), key=lambda kv: -kv[1]):
    print(f"  {art:<30} -> {rhino:<30}  {n}")
    seen_art.add(art)

print()
print("== Act 2 materials with NO v17 counterpart found via mesh-name match ==")
for art, n in sorted(mat_orphan.items(), key=lambda kv: -kv[1]):
    if art in seen_art: continue
    print(f"  {art:<30}  {n} slots need a fallback")

print()
print("== unmatched Act 2 mesh names (first 20) ==")
for n in sorted(unmatched)[:20]:
    print(f"  - {n}")
