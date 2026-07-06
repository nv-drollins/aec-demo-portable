"""Add ComfyUI segmentation tags (custom 'material' property) to every mesh
in cliff_house_act2_textured_v3.blend so the AEC Render+Submit pipeline can
build a clean seg pass from it. Saves back over v3 in place.

Tag taxonomy must match SEG_COLORS in submit_comfyui.py:
  Walls chain (red):    wall, travertine_*, concrete_*
  Windows chain (cyan): window, aluminum_dark, glass_*, water_blue
  Roof chain (blue):    roof
  Foundations (tan):    wood_walnut
  Untagged (no mask):   floors, terrain, water-spec, anything else
"""
import bpy
import os
from collections import Counter

DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"

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

AREA_TO_TAG = {
    "walls":       "wall",
    "roof":        "roof",
    "windows":     "window",
    "foundations": "wood_walnut",  # routes through Foundations (tan) chain
    # leave floors/terrain/water/other untagged - they don't get inpainted
}


def area_for(name):
    low = name.lower()
    for label, kws in KEYWORD_TO_AREA:
        for kw in kws:
            if kw in low: return label
    return "other"


def smart_frames_tag(obj):
    """Per-mesh logic for frames area: look at the first slot's material name.
    Glass material -> glass_railing.  Aluminum -> aluminum_dark.  Wood -> wall.
    """
    if not obj.material_slots: return None
    m = obj.material_slots[0].material
    if m is None: return None
    n = m.name.lower()
    if "glass" in n or "low_e" in n:    return "glass_railing"
    if "aluminum" in n or "metal" in n: return "aluminum_dark"
    if "timber" in n or "wood" in n:    return "wall"
    return None


def main():
    print(f"[tag] file: {bpy.data.filepath}")
    counts = Counter()
    skipped_no_tag = Counter()
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        area = area_for(o.name)
        tag = AREA_TO_TAG.get(area)
        if tag is None and area == "frames":
            tag = smart_frames_tag(o)
        if tag is None:
            skipped_no_tag[area] += 1
            # ensure no stale tag from a prior run
            if "material" in o:
                del o["material"]
            continue
        o["material"] = tag
        counts[tag] += 1
    print(f"[tag] tagged meshes:")
    for tag, n in counts.most_common():
        print(f"    {tag:<15}  {n} mesh(es)")
    print(f"[tag] intentionally untagged:")
    for area, n in skipped_no_tag.most_common():
        print(f"    {area:<15}  {n} mesh(es)")

    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    sz = os.path.getsize(DST) / 1024 / 1024
    print(f"[tag] SAVED {DST}  ({sz:.1f} MB)")


main()
