"""Pass D: re-map v4's Alt+0/Alt+9 toggle to the v3 material sets.

TEXTURED = v3 artist materials (HoneyOakWood, White_Travertine, ...)
BASIC    = v3 _v17 rhino flat colors (White_Travertine_v17, Grey_Slate_v17, ...)
Both mapped onto the new geometry by AREA (+ frame sub-type from current mat).

Starts from the existing v4 (keeps runtime, wall swatches, camera, worlds, tags),
appends the v3 material sets, rebuilds the snapshot, sets the default displayed
state to BASIC gray, packs and saves over v4.
"""
import bpy, json, os
from collections import Counter

V4  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v4.blend"
V3  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"
SNAPSHOT_KEY = "_act2_snapshot"
DEFAULT_STATE = "basic"   # what the file shows on open

ARTIST = ["HoneyOakWood", "White_Travertine", "Aluminum_Anodized_Dark",
          "Glass_Clear_Low_E", "Glass_Pale_Blue", "Glass_Frosted",
          "Timber_Engineered_Oak", "Timber_Oiled_Dark", "Concrete_Black",
          "CompositePanel", "Water_Pool"]
V17 = [n + "_v17" for n in ("White_Travertine", "Grey_Slate", "Aluminum_Anodized_Dark",
        "Glass_Clear_Low_E", "Glass_Pale_Blue", "Glass_Frosted",
        "Timber_Engineered_Oak", "Timber_Oiled_Dark", "Concrete_Black",
        "Concrete_Light_3", "Water_Pool")]

KEYWORD_TO_AREA = [
    ("roof",        ["roof", "_slab", "roof_garage", "combined_pad"]),
    ("windows",     ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight", "curtain_wall"]),
    ("stairs",      ["stair", "tread", "riser", "_step"]),
    ("floors",      ["floor", "_flr", "patio", "deck", "balcony_floor", "balccony"]),
    ("frames",      ["rail", "mullion", "frame", "track", "door", "barn", "reveal"]),
    ("walls",       ["wall", "_col", "column", "header", "sill", "cladding", "panel"]),
    ("water",       ["water", "pool", "fall", "weir"]),
    ("foundations", ["channel", "foundation", "retaining"]),
    ("terrain",     ["terrain", "ground", "earth", "grass", "site", "driveway"]),
]


def area_for(name):
    low = name.lower()
    for label, kws in KEYWORD_TO_AREA:
        for kw in kws:
            if kw in low:
                return label
    return "other"


def assign(area, cur_mat_name):
    """Return (artist_textured, v17_basic) material names for this slot."""
    cur = (cur_mat_name or "").lower()
    if area == "windows":
        if "frost" in cur:
            return ("Glass_Frosted", "Glass_Frosted_v17")
        if "balc" in cur or "pale" in cur or "tint" in cur or "bronze" in cur:
            return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        return ("Glass_Clear_Low_E", "Glass_Clear_Low_E_v17")
    if area == "roof":
        return ("CompositePanel", "Grey_Slate_v17")
    if area == "floors":
        return ("Timber_Engineered_Oak", "Timber_Engineered_Oak_v17")
    if area == "stairs":
        return ("White_Travertine", "White_Travertine_v17")
    if area == "foundations":
        # artist Concrete_Black was purged from v3; use the surviving _v17 concrete
        return ("Concrete_Black_v17", "Concrete_Black_v17")
    if area == "water":
        return ("Water_Pool_v17", "Water_Pool_v17")
    if area == "frames":
        if "glass" in cur or "railing" in cur or "cable" in cur or "low_e" in cur:
            return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        if "wood" in cur or "door" in cur or "cedar" in cur or "timber" in cur:
            return ("HoneyOakWood", "Timber_Oiled_Dark_v17")
        return ("Aluminum_Anodized_Dark", "Aluminum_Anodized_Dark_v17")
    if area == "walls":
        return ("HoneyOakWood", "White_Travertine_v17")
    return ("White_Travertine", "White_Travertine_v17")  # other / terrain fallback


def main():
    print(f"[passD] opening {V4}")
    bpy.ops.wm.open_mainfile(filepath=V4)

    # 1. Append the v3 material sets (only the names we need; avoids Wall_* clashes)
    want = set(ARTIST + V17)
    before = {m.name for m in bpy.data.materials}
    with bpy.data.libraries.load(V3, link=False) as (src, dst):
        dst.materials = [n for n in src.materials if n in want]
    appended = {m.name for m in bpy.data.materials} - before
    for n in appended:
        bpy.data.materials[n].use_fake_user = True
    print(f"[passD] appended {len(appended)} v3 materials")
    missing = want - {m.name for m in bpy.data.materials}
    if missing:
        print(f"[passD] WARNING missing from v3: {sorted(missing)}")

    # 2. Rebuild snapshot + reassign slots to the default state
    snap = []
    area_counts = Counter()
    pair_counts = Counter()
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        a = area_for(o.name)
        area_counts[a] += 1
        for i, sl in enumerate(o.material_slots):
            if sl.material is None:
                continue
            tex_name, bas_name = assign(a, sl.material.name)
            tex = bpy.data.materials.get(tex_name)
            bas = bpy.data.materials.get(bas_name)
            if tex is None or bas is None:
                # fallback to travertine pair
                tex = bpy.data.materials.get("White_Travertine") or tex
                bas = bpy.data.materials.get("White_Travertine_v17") or bas
                tex_name = tex.name if tex else tex_name
                bas_name = bas.name if bas else bas_name
            pair_counts[(a, tex_name, bas_name)] += 1
            sl.material = bas if DEFAULT_STATE == "basic" else tex
            snap.append({"obj": o.name, "slot": i,
                         "textured_mat": tex_name, "basic_mat": bas_name, "area": a})
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[passD] snapshot rebuilt: {len(snap)} slots; default state = {DEFAULT_STATE}")
    print(f"[passD] areas: {dict(area_counts)}")
    print("[passD] area -> (artist / v17) distribution:")
    for (a, t, b), n in sorted(pair_counts.items(), key=lambda kv: -kv[1]):
        print(f"    {n:>4}  [{a}] {t}  /  {b}")

    # 3. Drop now-unused M_* and _RH materials so the file is clean
    for m in list(bpy.data.materials):
        if m.name.startswith("M_") or m.name.endswith("_RH") or m.name == "Basic_Grey_RH":
            m.use_fake_user = False
    # (they will be purged on save since nothing references them)

    # 4. Pack + save
    try:
        bpy.ops.file.pack_all()
    except Exception as e:
        print(f"[passD] pack warn: {e}")
    bpy.ops.wm.save_as_mainfile(filepath=V4, compress=True)
    print(f"[passD] SAVED {V4}  ({os.path.getsize(V4)/1024/1024:.1f} MB)")
    print("[passD] DONE")


main()
