
import re

guide = r"C:\Users\swags\Documents\AEC_Demo_Portable\docs\INSTALL_GUIDE.md"
with open(guide, encoding="utf-8") as f:
    content = f.read()

old = "### 4.6 Start ComfyUI\n```batch\ncd D:\\tools\\comfy_for_blender\\ComfyUI_ForDemo\nset PYTHONIOENCODING=utf-8\npython_embeded\\python.exe -X utf8 -s ComfyUI\\main.py --windows-standalone-build\n```\nAccess at: http://127.0.0.1:8188"

new = """### 4.6 Start ComfyUI

> ⚠️ **CRITICAL — Windows encoding flags required.** ComfyUI will crash immediately
> without these. This is not optional.

```batch
cd D:\\tools\\comfy_for_blender\\ComfyUI_ForDemo
set PYTHONIOENCODING=utf-8
python_embeded\\python.exe -X utf8 -s ComfyUI\\main.py --windows-standalone-build
```

Wait for: `To see the GUI go to: http://127.0.0.1:8188`
Then open: http://127.0.0.1:8188

### 4.6b Install packages in ComfyUI's embedded Python

```batch
cd D:\\tools\\comfy_for_blender\\ComfyUI_ForDemo
python_embeded\\python.exe -m pip install requests pyyaml Pillow numpy
```

These are required by the AEC demo scripts."""

content = content.replace(old, new)
with open(guide, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
