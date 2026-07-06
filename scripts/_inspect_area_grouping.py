"""Inspect mesh names + materials to figure out the area grouping
(walls, floors, roof, windows, frames) for cliff_house_act2_textured.blend.

Strategy:
 - For each mesh, classify by name keyword first.
 - Print a per-material breakdown: how many meshes share that material,
   broken down by inferred area.
"""
import bpy
import re
from collections import defaultdict, Counter

# Order matters - first match wins. Keywords are matched as substrings
# (case-insensitive) so they will match across underscores and dots.
KEYWORD_TO_AREA = [
    ("roof", ["roof", "slab", "roof_garage"]),
    ("windows", ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight"]),
    ("floors", ["floor", "_flr", "patio", "deck", "stair", "step", "balcony_floor", "balccony"]),
    ("frames", ["rail", "mullion", "frame", "track", "door", "barn"]),
    ("walls", ["wall", "_col", "column", "header", "sill", "reveal", "cladding", "panel"]),
    ("water", ["water", "pool", "fall"]),
    ("terrain", ["terrain", "ground", "earth", "grass"]),
    ("foundations", ["channel", "foundation"]),
]


def area_for(name):
    low = name.lower()
    for label, kws in KEYWORD_TO_AREA:
        for kw in kws:
            if kw in low:
                return label
    return "other"


per_mat = defaultdict(lambda: Counter())
sample_objs = defaultdict(lambda: defaultdict(list))

for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material is None: continue
        m = s.material.name
        a = area_for(o.name)
        per_mat[m][a] += 1
        if len(sample_objs[m][a]) < 3:
            sample_objs[m][a].append(o.name)

print("=" * 80)
print("MATERIAL -> AREA BREAKDOWN")
print("=" * 80)
for m in sorted(per_mat.keys(), key=lambda k: -sum(per_mat[k].values())):
    total = sum(per_mat[m].values())
    parts = ", ".join(f"{a}={n}" for a, n in per_mat[m].most_common())
    print(f"\n[{m}]  total={total}  {parts}")
    for a, names in sample_objs[m].items():
        print(f"    {a}: {names}")

print()
print("=" * 80)
print("PROPOSED AREA -> MATERIALS")
print("=" * 80)
area_to_mats = defaultdict(Counter)
for m, areas in per_mat.items():
    for a, n in areas.items():
        area_to_mats[a][m] += n
for a in sorted(area_to_mats.keys()):
    print(f"\n[{a}]:")
    for m, n in area_to_mats[a].most_common():
        print(f"    {n:>4}x  {m}")
