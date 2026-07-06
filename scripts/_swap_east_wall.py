"""Swap the reshaped east wall + door into the CURRENTLY OPEN file (v5).

- Reads the object names from blender_east_wall.blend.
- Deletes the old same-named meshes in v5 (+ their snapshot entries).
- Appends the new meshes, scales them 0.001 about origin (meter -> v5 mm scale).
- Reassigns each new mesh the SAME material/area/seg-tag the old one had
  (so the Alt+0/9 toggle + ComfyUI segmentation keep working identically);
  genuinely new names fall back to area-based assignment.
- Saves.
"""
import bpy, json
from mathutils import Matrix, Vector

EAST = r"C:\Users\NVIDIA\Downloads\Updated Geo\blender_east_wall.blend"
SNAPSHOT_KEY = "_act2_snapshot"
FACTOR = 0.001

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
            if kw in low: return label
    return "other"

def assign(area, cur):
    cur = (cur or "").lower()
    if area == "windows":
        if "frost" in cur: return ("Glass_Frosted", "Glass_Frosted_v17")
        if "balc" in cur or "pale" in cur or "tint" in cur: return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        return ("Glass_Clear_Low_E", "Glass_Clear_Low_E_v17")
    if area == "roof": return ("CompositePanel", "Grey_Slate_v17")
    if area == "floors": return ("Timber_Engineered_Oak", "Timber_Engineered_Oak_v17")
    if area == "stairs": return ("Timber_Engineered_Oak", "Timber_Engineered_Oak_v17")
    if area == "foundations": return ("Concrete_Black_v17", "Concrete_Black_v17")
    if area == "frames":
        if "glass" in cur or "rail" in cur or "cable" in cur: return ("Glass_Pale_Blue", "Glass_Pale_Blue_v17")
        if "wood" in cur or "door" in cur or "timber" in cur: return ("HoneyOakWood", "Timber_Oiled_Dark_v17")
        return ("Aluminum_Anodized_Dark", "Aluminum_Anodized_Dark_v17")
    if area == "walls": return ("HoneyOakWood", "White_Travertine_v17")
    return ("White_Travertine", "White_Travertine_v17")

AREA_TO_TAG = {"walls": "wall", "stairs": "wall", "roof": "roof", "windows": "window", "foundations": "wood_walnut"}
def seg_tag(obj, area):
    tag = AREA_TO_TAG.get(area)
    if tag is None and area == "frames":
        m0 = obj.material_slots[0].material.name.lower() if (obj.material_slots and obj.material_slots[0].material) else ""
        tag = "glass_railing" if ("glass" in m0 or "rail" in m0) else (
              "wall" if ("wood" in m0 or "door" in m0 or "timber" in m0) else "aluminum_dark")
    return tag

def mat(n): return bpy.data.materials.get(n)


def main():
    snap = json.loads(bpy.context.scene.get(SNAPSHOT_KEY, "[]"))
    old_map = {}
    for e in snap:
        old_map.setdefault(e["obj"], (e["textured_mat"], e["basic_mat"], e["area"]))

    # 1. read the object names in the east wall file (names only, no append yet)
    with bpy.data.libraries.load(EAST, link=False) as (data_from, data_to):
        east_names = list(data_from.objects)
    print(f"[swap] east wall file objects: {len(east_names)}")

    # 2. delete old same-named objects in v5 + drop their snapshot entries
    deleted = 0
    for name in east_names:
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
            deleted += 1
    east_set = set(east_names)
    snap = [e for e in snap if e["obj"] not in east_set]
    print(f"[swap] deleted {deleted} old meshes from v5")

    # 3. append the new objects (now no name collision)
    coll = bpy.data.collections.get("East_Wall_Swap") or bpy.data.collections.new("East_Wall_Swap")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    with bpy.data.libraries.load(EAST, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    appended = [o for o in data_to.objects if o is not None]
    app_names = {o.name for o in appended}
    for o in appended:
        if o.name not in coll.objects:
            try: coll.objects.link(o)
            except Exception: pass
    print(f"[swap] appended {len(appended)} objects")

    # 4. scale roots by 0.001 about world origin (meter -> mm)
    S = Matrix.Diagonal((FACTOR, FACTOR, FACTOR, 1.0))
    roots = [o for o in appended if (o.parent is None) or (o.parent.name not in app_names)]
    for o in roots:
        o.matrix_world = S @ o.matrix_world
    bpy.context.view_layer.update()
    print(f"[swap] scaled {len(roots)} roots by {FACTOR}")

    # 5. reassign materials + snapshot + tags for the new meshes
    reused = newasg = 0
    for o in appended:
        if o.type != "MESH": continue
        if o.name in old_map:
            tex_n, bas_n, area = old_map[o.name]; reused += 1
        else:
            area = area_for(o.name)
            tex_n, bas_n = assign(area, o.material_slots[0].material.name if (o.material_slots and o.material_slots[0].material) else "")
            newasg += 1
        tag = seg_tag(o, area)
        if tag: o["material"] = tag
        elif "material" in o: del o["material"]
        if len(o.material_slots) == 0:
            tm = mat(tex_n) or mat("White_Travertine")
            if tm: o.data.materials.append(tm)
        for i, sl in enumerate(o.material_slots):
            tm = mat(tex_n) or mat("White_Travertine")
            bm = mat(bas_n) or mat("White_Travertine_v17")
            if tm: sl.material = tm; tm.use_fake_user = True
            if bm: bm.use_fake_user = True
            snap.append({"obj": o.name, "slot": i,
                         "textured_mat": tm.name if tm else tex_n,
                         "basic_mat": bm.name if bm else bas_n, "area": area})
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[swap] reassigned: reused-old={reused}  new-fallback={newasg}  snapshot slots now={len(snap)}")

    # 6. report position sanity: new east wall bbox vs whole building (H2_) bbox
    def bbox(pred):
        mn = Vector((1e18,)*3); mx = Vector((-1e18,)*3); n=0
        for o in bpy.data.objects:
            if o.type!="MESH" or not pred(o): continue
            n+=1
            for c in o.bound_box:
                w=o.matrix_world@Vector(c)
                for i in range(3):
                    mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
        return mn,mx,n
    nmn,nmx,nn = bbox(lambda o: o.name in app_names)
    hmn,hmx,hn = bbox(lambda o: o.name.startswith("H2_") and o.name not in app_names)
    print(f"[swap] new east-wall bbox: min={tuple(round(x,3) for x in nmn)} max={tuple(round(x,3) for x in nmx)}")
    print(f"[swap] existing H2_ bldg bbox: min={tuple(round(x,3) for x in hmn)} max={tuple(round(x,3) for x in hmx)}")

    bpy.ops.wm.save_mainfile()
    print("[swap] SAVED. DONE")

main()
