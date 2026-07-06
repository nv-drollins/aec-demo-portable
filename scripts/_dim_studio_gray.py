"""Dim the Studio_Gray world to match the reference image (darker neutral)."""
import bpy, os
DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"

w = bpy.data.worlds.get("Studio_Gray")
if w is None:
    print("[dim] FAIL: Studio_Gray not found"); raise SystemExit(1)

bg = w.node_tree.nodes.get("Background")
if bg is None:
    # try first Background-type node
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg is None:
    print("[dim] FAIL: no Background node in Studio_Gray"); raise SystemExit(1)

old_col = tuple(bg.inputs["Color"].default_value)
old_str = bg.inputs["Strength"].default_value
bg.inputs["Color"].default_value = (0.15, 0.15, 0.15, 1.0)
bg.inputs["Strength"].default_value = 1.0
print(f"[dim] Studio_Gray:  color {old_col} -> {tuple(bg.inputs['Color'].default_value)}")
print(f"[dim] Studio_Gray:  strength {old_str} -> {bg.inputs['Strength'].default_value}")

bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
print(f"[dim] SAVED {DST}  ({os.path.getsize(DST)/1024/1024:.1f} MB)")
