from PIL import Image
from collections import Counter
import os

p = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\input\seg_input.png"
im = Image.open(p).convert("RGB")
c = Counter(im.getdata())
print("top colors in seg_input.png (rgb : count : hex):")
for col, n in c.most_common(12):
    print("  %-16s %8d  #%02X%02X%02X" % (str(col), n, col[0], col[1], col[2]))

targets = {"Walls": (200,109,103), "Roof": (95,114,199),
           "Windows": (136,188,194), "Foundations": (197,168,114)}
print("\ntargets the MaskFromColor nodes expect:")
for k,v in targets.items():
    print("  %-12s %-16s #%02X%02X%02X" % (k, str(v), v[0], v[1], v[2]))
