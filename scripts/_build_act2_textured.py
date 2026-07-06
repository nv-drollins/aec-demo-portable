"""Build cliff_house_act2_textured.blend from the artist's
base_scene_swag_Screen_Capture_unpacked.blend.

Steps:
 1. Drop 8 orphan ComfyUI/SDNode temp-image references (not used by any node)
 2. Pack all valid texture images so the .blend is portable
 3. Create Clay_Override material (mid-grey Principled BSDF, fake-user kept)
 4. Embed clay_toggle_runtime.py as Text 'clay_toggle.py' with use_module=True
 5. Save as cliff_house_act2_textured.blend in sample_project/blender_assets
"""
import bpy
import os

RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\clay_toggle_runtime.py"
DST_DIR     = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets"
DST         = os.path.join(DST_DIR, "cliff_house_act2_textured.blend")

CLAY_MAT_NAME = "Clay_Override"


def step1_drop_orphan_images():
    """Remove images whose filepath is a missing temp file and that have zero users."""
    removed = []
    for img in list(bpy.data.images):
        if img.packed_file: continue
        fp = bpy.path.abspath(img.filepath) if img.filepath else ""
        if fp and os.path.exists(fp): continue
        users = img.users
        if users == 0:
            removed.append(img.name)
            bpy.data.images.remove(img)
            continue
        # Some have 1 'fake' user from the .blend load. Inspect raw name for temp pattern.
        nm = img.name
        if ("ComfyUI_temp" in nm) or ("SDNode_" in img.filepath) or nm.startswith("viewport.png"):
            removed.append(nm)
            bpy.data.images.remove(img, do_unlink=True)
    print(f"[act2 build] dropped {len(removed)} orphan/temp image(s)")
    for n in removed: print(f"    - {n}")


def step2_pack_images():
    n_before = sum(1 for i in bpy.data.images if i.packed_file)
    try:
        bpy.ops.file.pack_all()
    except Exception as e:
        print(f"[act2 build] pack_all warning: {e}")
    n_after = sum(1 for i in bpy.data.images if i.packed_file)
    print(f"[act2 build] packed images: {n_before} -> {n_after}")


def step3_make_clay_material():
    mat = bpy.data.materials.get(CLAY_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(CLAY_MAT_NAME)
    mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.60, 0.58, 0.55, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    print(f"[act2 build] {CLAY_MAT_NAME} ready (fake_user=True)")


def step4_embed_runtime():
    name = "clay_toggle.py"
    txt = bpy.data.texts.get(name)
    if txt is None:
        txt = bpy.data.texts.new(name)
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear()
    txt.write(body)
    txt.use_module = True
    print(f"[act2 build] embedded '{name}'  use_module={txt.use_module}  lines={len(txt.lines)}")


def step5_save():
    os.makedirs(DST_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    sz = os.path.getsize(DST) / 1024 / 1024
    print(f"[act2 build] SAVED {DST}  ({sz:.1f} MB)")


def main():
    print(f"[act2 build] source: {bpy.data.filepath}")
    step1_drop_orphan_images()
    step2_pack_images()
    step3_make_clay_material()
    step4_embed_runtime()
    step5_save()
    print("[act2 build] DONE")


main()
