"""E2: make v4 truly match v3.

- Append v3's snapshot-referenced materials + ArchWorld (HDRI) + Camera_day.
- Apply v3's EXACT per-mesh (obj,slot) material assignment to matching meshes.
- New interior meshes (stairs / added walls not in v3) -> area-based fallback.
- Keep v4's runtime, wall swatches, seg tags, Studio_Gray.
- Default: artist textured, Studio_Gray active, ArchWorld available via Alt+7.
"""
import bpy, json, os
from collections import Counter

V4 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v4.blend"
V3 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"
SETUP = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json"
SNAPSHOT_KEY = "_act2_snapshot"

# Snapshot materials missing as datablocks in v3 -> remap to surviving equivalents.
MISSING_REMAP = {
    "Concrete_Black": "Concrete_Black_v17",
    "Concrete_Black.001": "Concrete_Black_v17",
    "Water_Pool": "Water_Pool_v17",
    "Material": "White_Travertine",
    "Material.004": "Concrete_Black_v17",
}

KEYWORD_TO_AREA = [
    ("roof", ["roof", "_slab", "roof_garage", "combined_pad"]),
    ("windows", ["glass", "window", "w_glass", "frost", "low_e", "glaz", "skylight", "curtain_wall"]),
    ("stairs", ["stair", "tread", "riser", "_step"]),
    ("floors", ["floor", "_flr", "patio", "deck", "balcony_floor", "balccony"]),
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


def fallback_assign(area, cur):
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


def mat(name):
    return bpy.data.materials.get(name)


def resolve(name):
    """Return a present material name, remapping missing ones."""
    if mat(name):
        return name
    r = MISSING_REMAP.get(name)
    if r and mat(r):
        return r
    return None


def main():
    with open(SETUP, "r", encoding="utf-8") as f:
        v3 = json.load(f)
    v3_snap = v3["snapshot"]
    # (obj, slot) -> entry
    v3_lookup = {(e["obj"], e["slot"]): e for e in v3_snap}
    want_mats = set(v3["snapshot_materials"])

    print(f"[E2] opening {V4}")
    bpy.ops.wm.open_mainfile(filepath=V4)

    # remove v4 placeholder ArchWorld so we can bring v3's real one
    pl = bpy.data.worlds.get("ArchWorld")
    if pl is not None:
        bpy.data.worlds.remove(pl)

    # append materials + ArchWorld + Camera_day from v3
    before_m = {m.name for m in bpy.data.materials}
    with bpy.data.libraries.load(V3, link=False) as (src, dst):
        dst.materials = [m for m in src.materials if m in want_mats and m not in before_m]
        dst.worlds = [w for w in src.worlds if w == "ArchWorld"]
        dst.objects = [o for o in src.objects if o == "Camera_day"]
    appended = {m.name for m in bpy.data.materials} - before_m
    for n in appended:
        bpy.data.materials[n].use_fake_user = True
    print(f"[E2] appended materials: {len(appended)}; ArchWorld={'ArchWorld' in bpy.data.worlds}; Camera_day={'Camera_day' in bpy.data.objects}")

    # link Camera_day to scene + activate
    cam = bpy.data.objects.get("Camera_day")
    if cam is not None:
        if cam.name not in bpy.context.scene.collection.all_objects:
            try: bpy.context.scene.collection.objects.link(cam)
            except Exception: pass
        bpy.context.scene.camera = cam
        if "_bookmark_matrix" not in cam:
            cam["_bookmark_matrix"] = [list(r) for r in cam.matrix_world]

    # apply assignment per slot
    snap = []
    matched = 0
    newmesh = 0
    area_counts = Counter()
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for i, sl in enumerate(o.material_slots):
            if sl.material is None:
                continue
            key = (o.name, i)
            if key in v3_lookup:
                e = v3_lookup[key]
                area = e["area"]
                tex = resolve(e["textured_mat"]) or "White_Travertine"
                bas = resolve(e["basic_mat"]) or "White_Travertine_v17"
                matched += 1
            else:
                area = area_for(o.name)
                t, b = fallback_assign(area, sl.material.name)
                tex = resolve(t) or "White_Travertine"
                bas = resolve(b) or "White_Travertine_v17"
                newmesh += 1
            area_counts[area] += 1
            tm = mat(tex); 
            if tm:
                sl.material = tm  # default = artist textured (match v3)
            snap.append({"obj": o.name, "slot": i, "textured_mat": tex, "basic_mat": bas, "area": area})
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    # lock all referenced materials
    for e in snap:
        for k in ("textured_mat", "basic_mat"):
            m = mat(e[k])
            if m: m.use_fake_user = True
    print(f"[E2] slots: {len(snap)}  matched-to-v3={matched}  new-mesh-fallback={newmesh}")
    print(f"[E2] areas: {dict(area_counts)}")

    # worlds: keep Studio_Gray active (v4 look), ArchWorld available for Alt+7
    studio = bpy.data.worlds.get("Studio_Gray")
    if studio:
        bpy.context.scene.world = studio
    print(f"[E2] worlds: {[w.name for w in bpy.data.worlds]}  active={bpy.context.scene.world.name}")

    # render res to match v3
    bpy.context.scene.render.resolution_x = v3["render"]["x"]
    bpy.context.scene.render.resolution_y = v3["render"]["y"]

    # pack + save
    try: bpy.ops.file.pack_all()
    except Exception as e: print(f"[E2] pack warn: {e}")
    bpy.ops.wm.save_as_mainfile(filepath=V4, compress=True)
    print(f"[E2] SAVED {V4} ({os.path.getsize(V4)/1024/1024:.1f} MB)")
    print("[E2] DONE")


main()
