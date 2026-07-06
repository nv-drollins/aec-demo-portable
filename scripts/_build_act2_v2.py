"""Build cliff_house_act2_textured_v2.blend from the textured Act 2.

Adds:
 - One "_RhinoBasic" twin per currently-used artist material
   (flat Principled BSDF; base color is the average of the diffuse texture, or
    the BSDF base color when no diffuse texture exists; glass keeps mild alpha).
 - Snapshot of per-mesh-slot {obj, slot, textured_mat, basic_mat, area} into
   scene["_act2_snapshot"], where 'area' is one of
   walls / floors / roof / windows / frames / other / water / foundations.
 - rhino_toggle_runtime.py embedded as Text 'rhino_toggle.py' (use_module=True),
   replacing the previous clay_toggle.py.

Save target: cliff_house_act2_textured_v2.blend (sibling of the input).
"""
import bpy
import json
import os
from collections import defaultdict

RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST_DIR     = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets"
DST         = os.path.join(DST_DIR, "cliff_house_act2_textured_v2.blend")
SNAPSHOT_KEY = "_act2_snapshot"
BASIC_SUFFIX = "_RhinoBasic"

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
            if kw in low:
                return label
    return "other"


def find_image_by_name(mat_name):
    """Primary lookup: match conventional artist filenames like
    T_<MaterialName>_Albedo.png. Don't filter on has_data because packed
    images report False until first pixel access."""
    candidates = [
        f"T_{mat_name}_Albedo.png", f"{mat_name}_Albedo.png",
        f"T_{mat_name}_BaseColor.png", f"{mat_name}_BaseColor.png",
        f"T_{mat_name}_Diffuse.png", f"{mat_name}_Diffuse.png",
        f"T_{mat_name}_diff.png", f"{mat_name}_diff.png",
    ]
    for c in candidates:
        img = bpy.data.images.get(c)
        if img is not None: return img
    low = mat_name.lower()
    for img in bpy.data.images:
        n = img.name.lower()
        if low in n and any(k in n for k in ("albedo", "basecolor", "diffuse", "_diff")):
            return img
    return None


def find_image_for_basecolor(mat):
    """Fallback: walk all nodes in the material tree for any TEX_IMAGE that
    looks like a diffuse map by image name. Skips normal/rough/AO maps.
    """
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.type != "TEX_IMAGE" or n.image is None: continue
        nm = n.image.name.lower()
        if any(k in nm for k in ("normal", "_nor", "_rough", "_ao", "_metal", "_disp")):
            continue
        if any(k in nm for k in ("albedo", "basecolor", "diffuse", "_diff", "_col")):
            return n.image
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image is not None and n.image.has_data:
            nm = n.image.name.lower()
            if not any(k in nm for k in ("normal", "_nor", "_rough", "_ao", "_metal", "_disp")):
                return n.image
    return None


def find_image_for_input(mat, input_name):
    """Same as base color helper but for arbitrary input."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None: return None
    inp = bsdf.inputs.get(input_name)
    if inp is None or not inp.is_linked: return None
    cur = inp.links[0].from_node
    visited = set(); depth = 0
    while cur and cur.name not in visited and depth < 6:
        visited.add(cur.name)
        if cur.type == "TEX_IMAGE": return cur.image
        for sub in cur.inputs:
            if sub.is_linked: cur = sub.links[0].from_node; depth += 1; break
        else: break
    return None


def avg_color(img, max_pixels=200_000):
    """Average RGB of an image. Triggers a load if needed (packed images may
    report has_data=False until first pixel access)."""
    if img is None: return None
    try:
        import numpy as np
        # Touch .pixels to force load. Slicing the channel-flat array is fast.
        px = np.array(img.pixels[:], dtype=np.float32)
        if px.size == 0: return None
        rgba = px.reshape(-1, 4)
        n = rgba.shape[0]
        stride = max(1, n // max_pixels)
        sub = rgba[::stride]
        avg = sub.mean(axis=0)
        return (float(avg[0]), float(avg[1]), float(avg[2]), 1.0)
    except Exception as e:
        print(f"  [avg_color] {img.name}: {e}")
        return None


def avg_scalar(img, max_pixels=50_000, default=0.6):
    """Average red channel value (for roughness maps)."""
    if img is None: return default
    try:
        import numpy as np
        px = np.array(img.pixels[:], dtype=np.float32)
        if px.size == 0: return default
        rgba = px.reshape(-1, 4)
        stride = max(1, rgba.shape[0] // max_pixels)
        return float(rgba[::stride, 0].mean())
    except Exception:
        return default


def get_bsdf_basecolor(mat):
    if not mat or not mat.use_nodes: return (0.5, 0.5, 0.5, 1.0)
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None: return (0.5, 0.5, 0.5, 1.0)
    bc = bsdf.inputs.get("Base Color")
    if bc is None: return (0.5, 0.5, 0.5, 1.0)
    return tuple(bc.default_value)


# Materials with no diffuse map -> sensible Rhino-import default colors.
NAME_OVERRIDE_COLOR = {
    "Glass_Pale_Blue":     (0.78, 0.88, 0.95, 1.0),
    "Glass_Clear_Low_E":   (0.85, 0.92, 0.97, 1.0),
    "Glass_Frosted":       (0.90, 0.91, 0.93, 1.0),
    "Aluminum_Anodized_Dark": (0.07, 0.07, 0.08, 1.0),
    "Concrete_Black":      (0.10, 0.10, 0.10, 1.0),
    "Concrete_Black.001":  (0.10, 0.10, 0.10, 1.0),
    "Timber_Oiled_Dark":   (0.16, 0.10, 0.06, 1.0),
    "Water_Pool":          (0.18, 0.32, 0.40, 1.0),
}


def is_glass(mat_name):
    l = mat_name.lower()
    return ("glass" in l) or ("water" in l) or ("low_e" in l)


def make_basic_twin(src):
    """Build a flat-color Principled BSDF version of src material."""
    name = src.name + BASIC_SUFFIX
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)

    # Base color priority: (1) hardcoded override, (2) sampled diffuse map,
    # (3) source BSDF default.
    src_img = "<none>"
    if src.name in NAME_OVERRIDE_COLOR:
        base_rgba = NAME_OVERRIDE_COLOR[src.name]
        src_img = "<override>"
    else:
        diffuse_img = find_image_by_name(src.name) or find_image_for_basecolor(src)
        base_rgba = avg_color(diffuse_img) if diffuse_img else None
        if diffuse_img: src_img = diffuse_img.name
        if base_rgba is None:
            base_rgba = get_bsdf_basecolor(src)
            src_img = "<bsdf default>"
    bsdf.inputs["Base Color"].default_value = base_rgba
    mat["_basic_src"] = src_img

    # roughness
    rough_img = find_image_for_input(src, "Roughness")
    if rough_img is not None:
        bsdf.inputs["Roughness"].default_value = avg_scalar(rough_img, default=0.55)
    else:
        src_bsdf = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if src.use_nodes else None
        if src_bsdf and "Roughness" in src_bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = src_bsdf.inputs["Roughness"].default_value
        else:
            bsdf.inputs["Roughness"].default_value = 0.55

    # metallic
    if "Metallic" in bsdf.inputs:
        if src.use_nodes:
            sb = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if sb and "Metallic" in sb.inputs:
                bsdf.inputs["Metallic"].default_value = sb.inputs["Metallic"].default_value

    # glass-ish: mild transparency
    if is_glass(src.name):
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.35
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.85
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.85
        mat.surface_render_method = "DITHERED" if hasattr(mat, "surface_render_method") else mat.surface_render_method
        try: mat.blend_method = "BLEND"
        except Exception: pass

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def main():
    print(f"[v2 build] source: {bpy.data.filepath}")

    # 1. Build _RhinoBasic twin for every artist material that is in use.
    used_mat_names = set()
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        for s in o.material_slots:
            if s.material: used_mat_names.add(s.material.name)
    # Skip ones that are already a basic twin or look like placeholders.
    artist_mats = [n for n in used_mat_names if not n.endswith(BASIC_SUFFIX)]
    print(f"[v2 build] artist materials in use: {len(artist_mats)}")
    built = 0
    for mname in sorted(artist_mats):
        src = bpy.data.materials.get(mname)
        if src is None: continue
        twin = make_basic_twin(src)
        built += 1
        col = twin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
        print(f"  built {twin.name}  basecolor=({col[0]:.2f},{col[1]:.2f},{col[2]:.2f})")
    print(f"[v2 build] built {built} _RhinoBasic twins")

    # 2. Snapshot per-mesh-slot assignments, classifying area by mesh name.
    snap = []
    area_counts = defaultdict(int)
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        a = area_for(o.name)
        area_counts[a] += 1
        for i, s in enumerate(o.material_slots):
            if s.material is None: continue
            tex_name = s.material.name
            if tex_name.endswith(BASIC_SUFFIX):
                tex_name = tex_name[:-len(BASIC_SUFFIX)]
            basic_name = tex_name + BASIC_SUFFIX
            snap.append({
                "obj": o.name, "slot": i,
                "textured_mat": tex_name, "basic_mat": basic_name,
                "area": a,
            })
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    print(f"[v2 build] snapshot: {len(snap)} slot record(s)")
    print(f"[v2 build] meshes by area: {dict(area_counts)}")

    # 3. Replace the old clay_toggle text with rhino_toggle.
    for old in ("clay_toggle.py",):
        if old in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[old])
            print(f"[v2 build] removed old text '{old}'")
    name = "rhino_toggle.py"
    txt = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear(); txt.write(body)
    txt.use_module = True
    print(f"[v2 build] embedded '{name}'  use_module={txt.use_module}  lines={len(txt.lines)}")

    # 4. Re-pack (twin materials don't reference images so this is just a refresh)
    try: bpy.ops.file.pack_all()
    except Exception as e: print(f"[v2 build] pack_all warning: {e}")

    # 5. Save
    os.makedirs(DST_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    print(f"[v2 build] SAVED {DST}  ({os.path.getsize(DST)/1024/1024:.1f} MB)")
    print("[v2 build] DONE")


main()
