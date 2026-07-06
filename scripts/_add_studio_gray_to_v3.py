"""Add Studio_Gray world to v3, make it active, re-embed updated runtime.

Studio_Gray: flat 0.5 gray Background shader at strength 1.0. Classic
architectural neutral lighting - reads materials cleanly without HDRI bias.

ArchWorld (artist's HDRI) is preserved as a datablock and reachable via the
Alt+7 toggle.
"""
import bpy
import os

RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"


def make_studio_gray():
    name = "Studio_Gray"
    w = bpy.data.worlds.get(name)
    if w is None:
        w = bpy.data.worlds.new(name)
    w.use_fake_user = True
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (300, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (0, 0)
    bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    print(f"[v3 update] Studio_Gray world ready (fake_user=True)")
    return w


def main():
    print(f"[v3 update] file: {bpy.data.filepath}")

    studio = make_studio_gray()

    # Preserve ArchWorld with fake_user so it survives even when not active
    arch = bpy.data.worlds.get("ArchWorld")
    if arch is not None:
        arch.use_fake_user = True
        print(f"[v3 update] ArchWorld preserved (fake_user=True)")

    sc = bpy.context.scene
    sc.world = studio
    print(f"[v3 update] active world = {sc.world.name}")

    # Re-embed the updated runtime
    txt = bpy.data.texts.get("rhino_toggle.py") or bpy.data.texts.new("rhino_toggle.py")
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear(); txt.write(body)
    txt.use_module = True
    print(f"[v3 update] runtime text refreshed  lines={len(txt.lines)}")

    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    sz = os.path.getsize(DST) / 1024 / 1024
    print(f"[v3 update] SAVED {DST}  ({sz:.1f} MB)")


main()
