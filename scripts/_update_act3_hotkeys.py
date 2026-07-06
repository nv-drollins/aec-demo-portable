"""Bring cliff_house_act3_sunstudy.blend up to feature parity with v3:
 - Replace embedded rhino_toggle.py with the latest runtime (Alt+0..9 + bookmark)
 - Add Studio_Gray world (so Alt+7 has something to toggle to)
 - Camera animation kept intact (user picked the animated artist camera for sun study)

Snapshot, v17 materials, and clay override are already inherited from v3.
"""
import bpy
import os

RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act3_sunstudy.blend"


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
    bg.inputs["Color"].default_value = (0.15, 0.15, 0.15, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def main():
    print(f"[act3 update] file: {bpy.data.filepath}")

    # 1. Embed latest runtime
    txt = bpy.data.texts.get("rhino_toggle.py") or bpy.data.texts.new("rhino_toggle.py")
    with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
        body = f.read()
    txt.clear(); txt.write(body)
    txt.use_module = True
    print(f"[act3 update] embedded runtime  lines={len(txt.lines)}  use_module={txt.use_module}")

    # 2. Snapshot present?
    raw = bpy.context.scene.get("_act2_snapshot", "")
    print(f"[act3 update] snapshot bytes={len(raw)}  records={(len(raw.split('}, {')) if raw else 0)}")

    # 3. v17 materials present?
    n_v17 = sum(1 for m in bpy.data.materials if m.name.endswith("_v17"))
    print(f"[act3 update] _v17 materials present: {n_v17}")

    # 4. Studio_Gray world (don't make it active - clay override masks the world anyway)
    make_studio_gray()
    studio = bpy.data.worlds.get("Studio_Gray")
    print(f"[act3 update] Studio_Gray world ready (active world stays {bpy.context.scene.world.name})")

    # 5. ArchWorld preserved for the toggle?
    arch = bpy.data.worlds.get("ArchWorld")
    if arch is not None:
        arch.use_fake_user = True
    print(f"[act3 update] ArchWorld present: {arch is not None}")

    # 6. Clay override still set?
    vl = bpy.context.view_layer
    print(f"[act3 update] view-layer override: {vl.material_override.name if vl.material_override else 'None'}")

    # 7. Save
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    sz = os.path.getsize(DST) / 1024 / 1024
    print(f"[act3 update] SAVED {DST}  ({sz:.1f} MB)")


main()
