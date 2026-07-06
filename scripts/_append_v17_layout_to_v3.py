"""Append v17's 'Layout' workspace (split: IMAGE_EDITOR | VIEW_3D) into v3
in place, so the user can switch to that layout via the top workspace tabs.

Strategy:
  1. Rename v3's existing 'Layout' workspace -> 'Layout_Default'  (preserve as
     backup; artist's default layout)
  2. bpy.data.libraries.load v17.blend with workspaces=['Layout']
  3. Loaded workspace lands as 'Layout' (no collision now) or 'Layout.001'
     (if libraries.load adds a suffix). If suffixed, rename to 'Layout'.
  4. Save v3 in place.
"""
import bpy
import os

V17 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_v17.blend"
V3  = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"


def main():
    print(f"[layout] file: {bpy.data.filepath}")
    existing_layout = bpy.data.workspaces.get("Layout")
    if existing_layout is not None:
        existing_layout.name = "Layout_Default"
        print("[layout] renamed existing 'Layout' -> 'Layout_Default' (preserved)")

    before = {ws.name for ws in bpy.data.workspaces}
    with bpy.data.libraries.load(V17, link=False) as (data_from, data_to):
        if "Layout" not in data_from.workspaces:
            print("[layout] FAIL: v17 has no 'Layout' workspace")
            return
        data_to.workspaces = ["Layout"]
    after = {ws.name for ws in bpy.data.workspaces}
    appended = after - before
    print(f"[layout] appended workspaces: {appended}")

    # Make sure the new one is called exactly 'Layout' (it might be 'Layout.001'
    # if there was any residual collision with screens / data).
    if "Layout" not in after:
        # find the just-appended one
        for nm in appended:
            ws = bpy.data.workspaces.get(nm)
            if ws is None: continue
            ws.name = "Layout"
            print(f"[layout] renamed '{nm}' -> 'Layout'")
            break

    final = bpy.data.workspaces.get("Layout")
    if final is not None:
        ws_screens = [(sc.name, [a.type for a in sc.areas]) for sc in final.screens]
        print(f"[layout] OK: 'Layout' workspace present, screens={ws_screens}")

    # List all workspaces for the user.
    print("[layout] all workspaces now:")
    for ws in bpy.data.workspaces:
        sc_count = len(ws.screens)
        areas = [a.type for sc in ws.screens for a in sc.areas]
        print(f"    '{ws.name}'  screens={sc_count}  area_types={areas}")

    bpy.ops.wm.save_as_mainfile(filepath=V3, compress=True)
    sz = os.path.getsize(V3) / 1024 / 1024
    print(f"[layout] SAVED {V3}  ({sz:.1f} MB)")


main()
