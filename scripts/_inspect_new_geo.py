"""Inspect the new artist delivery cliff_house_26.blend:
meshes, materials, name patterns, cameras, collections, scale, animation.
Writes a report to disk for analysis.
"""
import bpy, os
from collections import defaultdict, Counter

OUT = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_new_geo_inventory.txt"

# Same area classifier we use elsewhere, for a first-pass mapping.
KEYWORD_TO_AREA = [
    ("roof",        ["roof", "_slab", "roof_garage"]),
    ("windows",     ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight"]),
    ("stairs",      ["stair", "step", "tread", "riser"]),
    ("floors",      ["floor", "_flr", "patio", "deck", "balcony_floor", "balccony"]),
    ("frames",      ["rail", "mullion", "frame", "track", "door", "barn"]),
    ("walls",       ["wall", "_col", "column", "header", "sill", "reveal", "cladding", "panel"]),
    ("water",       ["water", "pool", "fall"]),
    ("foundations", ["channel", "foundation"]),
    ("terrain",     ["terrain", "ground", "earth", "grass"]),
]


def area_for(name):
    low = name.lower()
    for label, kws in KEYWORD_TO_AREA:
        for kw in kws:
            if kw in low:
                return label
    return "other"


R = []
R.append(f"FILE: {bpy.data.filepath}")
R.append(f"OBJECTS: {len(bpy.data.objects)}  MESHES: {len(bpy.data.meshes)}  MATERIALS: {len(bpy.data.materials)}  IMAGES: {len(bpy.data.images)}")
R.append("")

R.append("== SCENES / CAMERAS ==")
for s in bpy.data.scenes:
    R.append(f"  scene '{s.name}'  res={s.render.resolution_x}x{s.render.resolution_y}  cam={s.camera.name if s.camera else None}  frames={s.frame_start}-{s.frame_end}")
for c in bpy.data.cameras:
    users = [o.name for o in bpy.data.objects if o.data == c]
    R.append(f"  camera-data '{c.name}' used_by={users}")
R.append("")

R.append("== MATERIALS (usage on meshes) ==")
mat_use = Counter()
mat_to_meshes = defaultdict(list)
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for sl in o.material_slots:
        if sl.material:
            mat_use[sl.material.name] += 1
            mat_to_meshes[sl.material.name].append(o.name)
for m, n in mat_use.most_common():
    has_tex = False
    mat = bpy.data.materials.get(m)
    if mat and mat.use_nodes and mat.node_tree:
        has_tex = any(nd.type == "TEX_IMAGE" and nd.image for nd in mat.node_tree.nodes)
    R.append(f"  {n:>4}x  {m}   (textured={has_tex})")
R.append("")

R.append("== AREA CLASSIFICATION (first-pass by mesh name) ==")
area_counts = Counter()
area_examples = defaultdict(list)
for o in bpy.data.objects:
    if o.type != "MESH": continue
    a = area_for(o.name)
    area_counts[a] += 1
    if len(area_examples[a]) < 6:
        area_examples[a].append(o.name)
for a, n in area_counts.most_common():
    R.append(f"  [{a}]  {n} meshes   e.g. {area_examples[a]}")
R.append("")

R.append("== EXISTING 'material' TAGS (segmentation) ==")
tag_counts = Counter()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    tag_counts[o.get("material", "") or "<untagged>"] += 1
for t, n in tag_counts.most_common():
    R.append(f"  {n:>4}  '{t}'")
R.append("")

R.append("== COLLECTIONS ==")
for c in bpy.data.collections:
    R.append(f"  '{c.name}': {len(c.objects)} objects")
R.append("")

R.append("== ALL MESH OBJECTS (name | dims | slot mats | tag) ==")
for o in sorted([x for x in bpy.data.objects if x.type == "MESH"], key=lambda x: x.name):
    dims = tuple(round(d, 2) for d in o.dimensions)
    mats = [sl.material.name if sl.material else "<none>" for sl in o.material_slots]
    tag = o.get("material", "")
    R.append(f"  {o.name}  | dims={dims} | mats={mats} | tag={tag}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(R))
print("WROTE", OUT)
print(f"OBJECTS={len(bpy.data.objects)} MESHES={len(bpy.data.meshes)} MATERIALS={len(bpy.data.materials)}")
