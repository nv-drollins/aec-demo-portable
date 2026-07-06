"""Pass B: build cliff_house_act2_textured_v4.blend from cliff_house_26.blend.

- Append _RH (Rhino basic) materials from the temp blend.
- Build per-slot snapshot: textured = current M_* material, basic = matched _RH.
- Embed rhino_toggle.py runtime; build 3 PBR wall swatches.
- Create Studio_Gray + ArchWorld worlds (Studio_Gray active).
- Segmentation tags by area. Camera from a hero angle (bookmarked).
- Pack + save.
"""
import bpy, json, os
from collections import defaultdict, Counter
from mathutils import Vector

SRC_BLEND = r"C:\Users\NVIDIA\Downloads\Updated Geo\cliff_house_26.blend"
TMP_BLEND = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_rhino_26_basic.blend"
MAP_JSON  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_rhino_26_map.json"
RUNTIME   = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST_DIR   = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets"
DST       = os.path.join(DST_DIR, "cliff_house_act2_textured_v4.blend")
SNAPSHOT_KEY = "_act2_snapshot"

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


# Segmentation tag per area (matches submit_comfyui.py SEG_COLORS taxonomy).
AREA_TO_TAG = {
    "walls": "wall",
    "stairs": "wall",
    "roof": "roof",
    "windows": "window",
    "foundations": "wood_walnut",
}


def smart_frame_tag(obj):
    if not obj.material_slots or obj.material_slots[0].material is None:
        return None
    n = obj.material_slots[0].material.name.lower()
    if "glass" in n or "railing" in n or "cable" in n or "low_e" in n:
        return "glass_railing"
    if "alum" in n or "steel" in n or "metal" in n or "bronze" in n:
        return "aluminum_dark"
    if "wood" in n or "timber" in n or "door" in n or "cedar" in n:
        return "wall"
    return "aluminum_dark"


def make_grey(name, rgba):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (0, 0)
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = 0.6
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def make_world(name, color, strength):
    w = bpy.data.worlds.get(name)
    if w is None:
        w = bpy.data.worlds.new(name)
    w.use_fake_user = True
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (300, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (0, 0)
    bg.inputs["Color"].default_value = color
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def main():
    print(f"[passB] opening {SRC_BLEND}")
    bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)

    # 1. Append _RH materials from temp blend
    before = {m.name for m in bpy.data.materials}
    with bpy.data.libraries.load(TMP_BLEND, link=False) as (src, dst):
        dst.materials = [n for n in src.materials if n.endswith("_RH")]
    appended = {m.name for m in bpy.data.materials} - before
    for n in appended:
        bpy.data.materials[n].use_fake_user = True
    print(f"[passB] appended {len(appended)} _RH materials")

    # fallback basic material for meshes the .3dm didn't cover
    grey = make_grey("Basic_Grey_RH", (0.55, 0.55, 0.55, 1.0))

    # 2. Load mesh->rhino map
    with open(MAP_JSON, "r", encoding="utf-8") as f:
        rhino_map = json.load(f)

    # 3. Build snapshot + tags + fake_user on artist materials
    snap = []
    area_counts = Counter()
    tag_counts = Counter()
    missing_basic = 0
    artist_mats = set()
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        a = area_for(o.name)
        area_counts[a] += 1
        # segmentation tag
        tag = AREA_TO_TAG.get(a)
        if tag is None and a == "frames":
            tag = smart_frame_tag(o)
        if tag:
            o["material"] = tag
            tag_counts[tag] += 1
        elif "material" in o:
            del o["material"]
        # basic material for this mesh (suffixed _RH), else fallback grey
        basic_name = rhino_map.get(o.name)
        if not basic_name or basic_name not in bpy.data.materials:
            basic_name = grey.name
            missing_basic += 1
        for i, sl in enumerate(o.material_slots):
            if sl.material is None:
                continue
            tex_name = sl.material.name
            artist_mats.add(tex_name)
            snap.append({
                "obj": o.name, "slot": i,
                "textured_mat": tex_name, "basic_mat": basic_name,
                "area": a,
            })
    # lock artist materials so zero-user purge can't delete them
    for mn in artist_mats:
        m = bpy.data.materials.get(mn)
        if m:
            m.use_fake_user = True
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[passB] snapshot: {len(snap)} slots  | missing-basic(fallback grey)={missing_basic}")
    print(f"[passB] areas: {dict(area_counts)}")
    print(f"[passB] seg tags: {dict(tag_counts)}")

    # 4. Worlds
    studio = make_world("Studio_Gray", (0.55, 0.55, 0.55, 1.0), 1.5)
    existing = bpy.context.scene.world
    if existing is not None and existing.name not in ("Studio_Gray",):
        existing.name = "ArchWorld"
        existing.use_fake_user = True
    else:
        make_world("ArchWorld", (0.05, 0.06, 0.08, 1.0), 1.0)
    bpy.context.scene.world = studio
    print(f"[passB] worlds ready; active={bpy.context.scene.world.name}")

    # 5. Embed runtime + build wall palette
    txt = bpy.data.texts.get("rhino_toggle.py") or bpy.data.texts.new("rhino_toggle.py")
    with open(RUNTIME, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear(); txt.write(body); txt.use_module = True
    ns = {}
    exec(compile(txt.as_string(), txt.name, "exec"), ns)
    ns["_ensure_wall_palette"]()
    built = [n for n in ("Wall_WoodCladding", "Wall_Travertine", "Wall_ZincPanel") if bpy.data.materials.get(n)]
    print(f"[passB] embedded runtime ({len(txt.lines)} lines); wall swatches built: {built}")

    # 6. Camera from a hero 3/4 angle, bookmarked
    mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            wc = o.matrix_world @ Vector(corner)
            mins.x = min(mins.x, wc.x); mins.y = min(mins.y, wc.y); mins.z = min(mins.z, wc.z)
            maxs.x = max(maxs.x, wc.x); maxs.y = max(maxs.y, wc.y); maxs.z = max(maxs.z, wc.z)
    center = (mins + maxs) * 0.5
    size = (maxs - mins).length
    cam_data = bpy.data.cameras.new("HeroCam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("HeroCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_loc = center + Vector((size * 0.55, -size * 0.55, size * 0.33))
    cam_obj.location = cam_loc
    direction = (center - cam_loc).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam_obj
    cam_obj["_bookmark_matrix"] = [list(r) for r in cam_obj.matrix_world]
    print(f"[passB] HeroCam at {tuple(round(v,1) for v in cam_loc)} -> center {tuple(round(v,1) for v in center)}")

    # 7. Render settings (match v3 defaults; 16:9 since artist set 1280x720)
    sc = bpy.context.scene
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.resolution_percentage = 100
    try:
        sc.render.engine = "CYCLES"
        sc.cycles.device = "GPU"
        sc.cycles.samples = 128
    except Exception as e:
        print(f"[passB] cycles cfg warn: {e}")

    # 8. Pack + save
    try:
        bpy.ops.file.pack_all()
    except Exception as e:
        print(f"[passB] pack warn: {e}")
    os.makedirs(DST_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    print(f"[passB] SAVED {DST}  ({os.path.getsize(DST)/1024/1024:.1f} MB)")
    print("[passB] DONE")


main()
