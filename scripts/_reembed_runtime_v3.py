"""Hot-swap the embedded rhino_toggle.py text in v3 with the updated runtime
that includes Alt+6 aspect toggle. Saves in place."""
import bpy, os

RUNTIME_SRC = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\rhino_toggle_runtime.py"
DST = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v3.blend"

txt = bpy.data.texts.get("rhino_toggle.py") or bpy.data.texts.new("rhino_toggle.py")
with open(RUNTIME_SRC, "r", encoding="utf-8") as f:
    body = f.read()
txt.clear()
txt.write(body)
txt.use_module = True
print(f"[reembed] text 'rhino_toggle.py' updated, lines={len(txt.lines)}, use_module={txt.use_module}")

bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
print(f"[reembed] SAVED {DST}  ({os.path.getsize(DST)/1024/1024:.1f} MB)")
