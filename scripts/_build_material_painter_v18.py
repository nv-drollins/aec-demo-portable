"""One-shot build script for cliff_house_materials_v18.blend.

Run as:
  blender --background <v17.blend> --python _build_material_painter_v18.py

Behavior:
 - Imports 7 PBR texture sets from AEC_Demo_Portable/assets/textures.
 - Creates 8 MP_* materials (7 PBR + 1 procedural Dark Anodized).
 - Snapshots every mesh slot's current material into scene["_mp_artist_snapshot"].
 - Embeds material_painter_runtime.py as Text "material_painter.py" with use_module=True.
 - Saves as cliff_house_materials_v18.blend (same dir as input).
 - Packs all images.
"""

import bpy
import json
import os

TEX_DIR = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\assets\textures"
RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\material_painter_runtime.py"

# (mp_mat_name, polyhaven_slug, scale_x, scale_y, base_color_tint_rgba_or_none, roughness_bias)
# Tints multiply with the diffuse so the photographic colour stays believable.
PBR_RECIPES = [
    # warm travertine cream tint over a neutral beige stone wall, big tile so the building reads as one stone
    ("MP_Travertine",                "beige_wall_001",    1.2, 1.2, (0.95, 0.88, 0.74, 1.0),    0.05),
    ("MP_Polished_Concrete_Wall",    "concrete_wall_008", 1.5, 1.5, None,                       -0.05),
    ("MP_Wood_Cladding",             "weathered_planks",  1.2, 3.0, None,                       0.0),
    ("MP_Oak_Floor",                 "wood_floor",        2.0, 2.0, None,                       0.0),
    ("MP_Polished_Concrete_Floor",   "concrete_floor_03", 3.0, 3.0, None,                       -0.15),
    ("MP_Zinc_Roof",                 "corrugated_iron_03",4.0, 4.0, (0.55, 0.58, 0.62, 1.0),    -0.1),
    ("MP_Walnut_Accent",             "wood_table_001",    1.2, 3.5, (0.25, 0.14, 0.08, 1.0),    0.05),
]


def _ensure_image(path):
    name = os.path.basename(path)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(path, check_existing=True)
    return img


def _make_pbr_material(name, slug, sx, sy, color_tint, rough_bias):
    diff_p  = os.path.join(TEX_DIR, slug + "_diff_2k.png")
    nor_p   = os.path.join(TEX_DIR, slug + "_nor_gl_2k.png")
    rough_p = os.path.join(TEX_DIR, slug + "_rough_2k.png")
    for p in (diff_p, nor_p, rough_p):
        if not os.path.exists(p):
            raise FileNotFoundError("missing texture: " + p)

    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_fake_user = True  # zero-user safety so save doesn't purge it
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
    bsdf.inputs["Roughness"].default_value = max(0.0, 0.5 + rough_bias)

    texcoord = nt.nodes.new("ShaderNodeTexCoord"); texcoord.location = (-700, 0)
    mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-500, 0)
    mapping.inputs["Scale"].default_value = (sx, sy, 1.0)

    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])

    img_diff = nt.nodes.new("ShaderNodeTexImage"); img_diff.location = (-200, 200)
    img_diff.image = _ensure_image(diff_p)
    img_diff.projection = "BOX"
    img_diff.projection_blend = 0.2

    img_nor = nt.nodes.new("ShaderNodeTexImage"); img_nor.location = (-200, -100)
    img_nor.image = _ensure_image(nor_p)
    img_nor.image.colorspace_settings.name = "Non-Color"
    img_nor.projection = "BOX"
    img_nor.projection_blend = 0.2

    img_rough = nt.nodes.new("ShaderNodeTexImage"); img_rough.location = (-200, -400)
    img_rough.image = _ensure_image(rough_p)
    img_rough.image.colorspace_settings.name = "Non-Color"
    img_rough.projection = "BOX"
    img_rough.projection_blend = 0.2

    for img_node in (img_diff, img_nor, img_rough):
        nt.links.new(mapping.outputs["Vector"], img_node.inputs["Vector"])

    if color_tint is None:
        nt.links.new(img_diff.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        mix = nt.nodes.new("ShaderNodeMixRGB"); mix.location = (220, 250); mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 0.85
        mix.inputs["Color2"].default_value = color_tint
        nt.links.new(img_diff.outputs["Color"], mix.inputs["Color1"])
        nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    nrm = nt.nodes.new("ShaderNodeNormalMap"); nrm.location = (220, -100)
    nrm.inputs["Strength"].default_value = 0.8
    nt.links.new(img_nor.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])

    rmap = nt.nodes.new("ShaderNodeMapRange"); rmap.location = (220, -400)
    rmap.inputs["From Min"].default_value = 0.0
    rmap.inputs["From Max"].default_value = 1.0
    rmap.inputs["To Min"].default_value = max(0.0, 0.2 + rough_bias)
    rmap.inputs["To Max"].default_value = min(1.0, 0.95 + rough_bias)
    nt.links.new(img_rough.outputs["Color"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def _make_dark_anodized():
    name = "MP_Dark_Anodized"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.045, 0.05, 0.055, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.35
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _snapshot_artist_assignments():
    snap = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for i, slot in enumerate(obj.material_slots):
            snap.append({
                "obj": obj.name,
                "slot": i,
                "mat": slot.material.name if slot.material else None,
            })
    bpy.context.scene[SNAPSHOT_KEY] = json.dumps(snap)
    return len(snap)


def _embed_runtime_text():
    name = "material_painter.py"
    txt = bpy.data.texts.get(name)
    if txt is None:
        txt = bpy.data.texts.new(name)
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear()
    txt.write(body)
    txt.use_module = True
    return txt


SNAPSHOT_KEY = "_mp_artist_snapshot"


def main():
    print("[v18 build] starting", flush=True)

    # 1. Snapshot the artist's assignments BEFORE making any change.
    n_snap = _snapshot_artist_assignments()
    print(f"[v18 build] snapshot: {n_snap} slot record(s)", flush=True)

    # 2. Build 7 PBR materials + 1 procedural.
    for name, slug, sx, sy, tint, rbias in PBR_RECIPES:
        _make_pbr_material(name, slug, sx, sy, tint, rbias)
        print(f"[v18 build] built {name} <- {slug}", flush=True)
    _make_dark_anodized()
    print("[v18 build] built MP_Dark_Anodized (procedural)", flush=True)

    # 3. Embed runtime text.
    txt = _embed_runtime_text()
    print(f"[v18 build] embedded text '{txt.name}', use_module={txt.use_module}", flush=True)

    # 4. Pack images so the .blend is portable.
    try:
        bpy.ops.file.pack_all()
        print("[v18 build] images packed", flush=True)
    except Exception as e:
        print(f"[v18 build] pack_all warning: {e}", flush=True)

    # 5. Save as v18 in the same directory.
    src = bpy.data.filepath
    dst = os.path.join(os.path.dirname(src), "cliff_house_materials_v18.blend")
    bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
    print(f"[v18 build] SAVED {dst}", flush=True)
    print(f"[v18 build] file size: {os.path.getsize(dst)/1024/1024:.1f} MB", flush=True)
    print("[v18 build] DONE", flush=True)


main()
