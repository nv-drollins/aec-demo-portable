import struct, os, time

folder = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\input"
for f in ["beauty_input.png", "seg_input.png"]:
    p = os.path.join(folder, f)
    if not os.path.exists(p):
        print(f"{f}: MISSING")
        continue
    with open(p, "rb") as fh:
        fh.read(16)
        w, h = struct.unpack(">II", fh.read(8))
    mt = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p)))
    print(f"{f}: {w}x{h}  modified {mt}  ({os.path.getsize(p)//1024} KB)")
