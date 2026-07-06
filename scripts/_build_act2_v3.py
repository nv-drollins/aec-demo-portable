"""Build cliff_house_act2_textured_v3.blend.

This time the 'basic' state is the ACTUAL v17 Rhino materials (appended into
Act 2 with a _v17 suffix), assigned per-mesh by mesh-name match against v17.
146 of 150 Act 2 meshes match v17 directly; the 4 leftovers fall back to
a small lookup by artist-material name.

Steps:
 1. Append all v17 materials with '_v17' suffix
 2. Build snapshot per Act 2 mesh slot:
    - mesh name in v17 -> use that exact v17 slot material
    - else fallback by artist material name
 3. Drop any leftover *_RhinoBasic materials from v2
 4. Re-embed rhino_toggle.py (runtime unchanged - operates on snapshot)
 5. Save as cliff_house_act2_textured_v3.blend
"""
import bpy
import json
import os
from collections import defaultdict

V17_BLEND   = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_v17.blend"
V17_JSON    = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v17_assignments.json"
RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST_DIR     = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets"
DST         = os.path.join(DST_DIR, "cliff_house_act2_textured_v3.blend")
SNAPSHOT_KEY = "_act2_snapshot"
V17_SUFFIX = "_v17"

# Fallback for artist materials whose mesh name does not match anything in v17.
NAME_FALLBACK = {
    "Material":            "White_Travertine" + V17_SUFFIX,
    "Material.004":        "Concrete_Black"   + V17_SUFFIX,
    "Concrete_Black.001":  "Concrete_Black"   + V17_SUFFIX,
    "Water_Pool":          "Water_Pool"       + V17_SUFFIX,
    "HoneyOakWood":        "White_Travertine" + V17_SUFFIX,  # safe default
    "CompositePanel":      "Grey_Slate"       + V17_SUFFIX,
}

KEYWORD_TO_AREA = [
    ("roof",        ["roof", "_slab", "roof_garage"]),
    ("windows",     ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight"]),
    ("floors",      ["floor", "_flr", "patio", "deck", "stair", "step", "balcony_floor", "balccony"]),
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
            if kw in low: return label
    return "other"


def main():
    print(f"[v3 build] source: {bpy.data.filepath}")

    # 0. Clean up any _RhinoBasic twins left over from v2
    purged = 0
    for m in list(bpy.data.materials):
        if m.name.endswith("_RhinoBasic"):
            bpy.data.materials.remove(m)
            purged += 1
    if purged: print(f"[v3 build] purged {purged} stale _RhinoBasic twins")

    # 1. Load v17 mesh-slot assignment JSON
    with open(V17_JSON, "r", encoding="utf-8") as f:
        v17 = json.load(f)
    v17_objs = v17["objects"]
    v17_mats = v17["materials"]
    print(f"[v3 build] v17 reference: {len(v17_objs)} objects, {len(v17_mats)} materials")

    # 2. Append all v17 materials into this file
    before = set(m.name for m in bpy.data.materials)
    with bpy.data.libraries.load(V17_BLEND, link=False) as (data_from, data_to):
        data_to.materials = [n for n in data_from.materials if n in v17_mats]
    after = set(m.name for m in bpy.data.materials)
    appended = after - before
    print(f"[v3 build] appended {len(appended)} materials from v17")

    # 3. Rename appended materials with _v17 suffix.
    # Resolve collisions: if 'White_Travertine' was already in Act 2, Blender
    # gave the appended one a .001 (or .002) suffix; map back to the original.
    rename_map = {}
    for orig_name in v17_mats:
        target = orig_name + V17_SUFFIX
        # Find which appended name corresponds to this orig
        # Blender suffixes with .001, .002, etc. on collision.
        candidates = [orig_name] + [f"{orig_name}.{i:03d}" for i in range(1, 10)]
        for c in candidates:
            if c in appended:
                mat = bpy.data.materials.get(c)
                if mat is None: continue
                mat.name = target
                mat.use_fake_user = True
                rename_map[orig_name] = target
                break
    print(f"[v3 build] renamed to _v17 suffix: {len(rename_map)} materials")

    # 4. Build snapshot
    snap = []
    area_counts = defaultdict(int)
    inheritance_dist = defaultdict(int)
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        a = area_for(o.name)
        area_counts[a] += 1
        v17_slots = v17_objs.get(o.name)
        for i, s in enumerate(o.material_slots):
            if s.material is None: continue
            tex_name = s.material.name
            # never include leftover basic materials in snapshot
            if tex_name.endswith(V17_SUFFIX) or tex_name.endswith("_RhinoBasic"):
                continue
            # Determine basic_mat:
            basic_name = None
            if v17_slots and i < len(v17_slots):
                vm = v17_slots[i]
                if vm and (vm + V17_SUFFIX) in bpy.data.materials:
                    basic_name = vm + V17_SUFFIX
            if basic_name is None:
                basic_name = NAME_FALLBACK.get(tex_name)
            if basic_name is None:
                # last-resort: try same name in v17
                candidate = tex_name + V17_SUFFIX
                if candidate in bpy.data.materials:
                    basic_name = candidate
                else:
                    # truly orphan; map to a neutral
                    basic_name = "White_Travertine" + V17_SUFFIX
            inheritance_dist[(tex_name, basic_name)] += 1
            snap.append({
                "obj": o.name, "slot": i,
                "textured_mat": tex_name, "basic_mat": basic_name,
                "area": a,
            })
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[v3 build] snapshot: {len(snap)} slot records")
    print(f"[v3 build] meshes by area: {dict(area_counts)}")
    print("[v3 build] inheritance (artist -> v17, top 12):")
    for (a, b), n in sorted(inheritance_dist.items(), key=lambda kv: -kv[1])[:12]:
        print(f"    {a:<28} -> {b:<28}  {n}")

    # 5. Re-embed runtime (same as v2 - runtime is snapshot-driven)
    for old in ("clay_toggle.py",):
        if old in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[old])
    name = "rhino_toggle.py"
    txt = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear(); txt.write(body)
    txt.use_module = True
    print(f"[v3 build] embedded '{name}'  use_module={txt.use_module}")

    # 6. Pack and save
    try: bpy.ops.file.pack_all()
    except Exception as e: print(f"[v3 build] pack_all warning: {e}")
    os.makedirs(DST_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    print(f"[v3 build] SAVED {DST}  ({os.path.getsize(DST)/1024/1024:.1f} MB)")
    print("[v3 build] DONE")


main()
