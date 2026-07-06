"""Build v5 = v3 + new interior geometry (robust append).

Appends every object in cliff_house_26 that is NOT already in v3 (114 meshes +
31 parent empties + 5 curves), preserving hierarchy/transforms. Only the new
MESH objects get guesstimation materials, snapshot entries, and seg tags.
Everything inherited from v3 is untouched.
"""
import bpy, json, os
from collections import Counter

V5  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v5.blend"
N26 = r"C:\Users\NVIDIA\Downloads\Updated Geo\cliff_house_26.blend"
SNAPSHOT_KEY = "_act2_snapshot"

KEYWORD_TO_AREA = [
    ("roof", ["roof", "_slab", "roof_garage", "combined_pad"]),
    ("windows", ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight", "curtain_wall"]),
    ("stairs", ["stair", "tread", "riser", "_step", "stringer", "landing", "spine"]),
    ("floors", ["floor", "_flr", "patio", "deck", "balcony_floor", "balccony", "scullery"]),
    ("frames", ["rail", "mullion", "frame", "track", "door", "barn", "reveal"]),
    ("walls", ["wall", "_col", "column", "header", "sill", "cladding", "panel"]),
    ("water", ["water", "pool", "fall", "weir"]),
    ("foundations", ["channel", "foundation", "retaining"]),
    ("terrain", ["terrain", "ground", "earth", "grass", "site", "driveway"]),
]


def area_for(name):
    low = name.lower()
    for label, kws in KEYWORD_TO_AREA:
        for kw in kws:
            if kw in low:
                return label
    return "other"


def assign(area, cur):
    cur = (cur or "").lower()
    if area == "windows":
        if "frost" in cur: return ("Glass_Frosted", "Glass_Frosted_v17")
        if "balc" in cur or "pale" in cur or "tint" in cur or "bronze" in cur: return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        return ("Glass_Clear_Low_E", "Glass_Clear_Low_E_v17")
    if area == "roof": return ("CompositePanel", "Grey_Slate_v17")
    if area == "floors": return ("Timber_Engineered_Oak", "Timber_Engineered_Oak_v17")
    if area == "stairs": return ("Timber_Engineered_Oak", "Timber_Engineered_Oak_v17")
    if area == "foundations": return ("Concrete_Black_v17", "Concrete_Black_v17")
    if area == "water": return ("Water_Pool_v17", "Water_Pool_v17")
    if area == "frames":
        if "glass" in cur or "railing" in cur or "cable" in cur or "low_e" in cur: return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        if "wood" in cur or "door" in cur or "cedar" in cur or "timber" in cur: return ("HoneyOakWood", "Timber_Oiled_Dark_v17")
        return ("Aluminum_Anodized_Dark", "Aluminum_Anodized_Dark_v17")
    if area == "walls": return ("HoneyOakWood", "White_Travertine_v17")
    return ("White_Travertine", "White_Travertine_v17")


def mat(n): return bpy.data.materials.get(n)
AREA_TO_TAG = {"walls": "wall", "stairs": "wall", "roof": "roof",
               "windows": "window", "foundations": "wood_walnut"}


def main():
    print(f"[v5] opening {V5}")
    bpy.ops.wm.open_mainfile(filepath=V5)
    v3_names = {o.name for o in bpy.data.objects}
    snap = json.loads(bpy.context.scene.get(SNAPSHOT_KEY, "[]"))
    print(f"[v5] v3 objects={len(v3_names)}  snapshot slots={len(snap)}")

    coll = bpy.data.collections.get("New_Interior") or bpy.data.collections.new("New_Interior")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)

    # robust append: dst.objects becomes the appended datablocks (no .get())
    with bpy.data.libraries.load(N26, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n not in v3_names]
    appended = [o for o in dst.objects if o is not None]
    print(f"[v5] appended objects: {len(appended)}")

    # link ALL appended objects (keep empties/curves as parents -> transforms intact)
    for o in appended:
        if o.name not in coll.objects:
            try: coll.objects.link(o)
            except Exception: pass

    meshes = [o for o in appended if o.type == "MESH"]
    print(f"[v5] new MESH objects: {len(meshes)}")

    area_counts = Counter(); tag_counts = Counter(); added = 0
    for obj in meshes:
        a = area_for(obj.name)
        area_counts[a] += 1
        tag = AREA_TO_TAG.get(a)
        if tag is None and a == "frames":
            m0 = obj.material_slots[0].material.name.lower() if (obj.material_slots and obj.material_slots[0].material) else ""
            tag = "glass_railing" if ("glass" in m0 or "rail" in m0 or "cable" in m0) else (
                  "aluminum_dark" if ("alum" in m0 or "steel" in m0 or "metal" in m0 or "bronze" in m0) else "wall")
        if tag:
            obj["material"] = tag; tag_counts[tag] += 1
        if len(obj.material_slots) == 0:
            tm = mat("White_Travertine")
            if tm: obj.data.materials.append(tm)
        for i, sl in enumerate(obj.material_slots):
            t, b = assign(a, sl.material.name if sl.material else "")
            tm = mat(t) or mat("White_Travertine")
            bm = mat(b) or mat("White_Travertine_v17")
            if tm:
                sl.material = tm
                tm.use_fake_user = True
            if bm: bm.use_fake_user = True
            snap.append({"obj": obj.name, "slot": i,
                         "textured_mat": tm.name if tm else t,
                         "basic_mat": bm.name if bm else b, "area": a})
            added += 1

    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[v5] new-mesh areas: {dict(area_counts)}")
    print(f"[v5] new-mesh tags: {dict(tag_counts)}")
    print(f"[v5] snapshot slots now: {len(snap)} (+{added})")

    try: bpy.ops.file.pack_all()
    except Exception as e: print(f"[v5] pack warn: {e}")
    bpy.ops.wm.save_as_mainfile(filepath=V5, compress=True)
    print(f"[v5] SAVED ({os.path.getsize(V5)/1024/1024:.1f} MB)")
    print("[v5] DONE")


main()
