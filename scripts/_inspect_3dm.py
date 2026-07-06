"""Read aec_demo_rhino_26.3dm via the rhino3dm wheel bundled with import_3dm.
Reports object count, layer names, and render materials so we can compare
against cliff_house_26.blend for mismatches.
Run with Blender's python (3.13) in background.
"""
import sys, os, glob

WHEEL_DIR = r"C:\Users\NVIDIA\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default\import_3dm\wheels"
# Prefer the cp313 wheel (matches Blender 5.1 python)
for whl in glob.glob(os.path.join(WHEEL_DIR, "rhino3dm*cp313*.whl")):
    if whl not in sys.path:
        sys.path.insert(0, whl)

try:
    import rhino3dm as r3
except Exception as e:
    print(f"[3dm] could not import rhino3dm: {e}")
    raise SystemExit(0)

PATH = r"C:\Users\NVIDIA\Downloads\Updated Geo\aec_demo_rhino_26.3dm"
f = r3.File3dm.Read(PATH)
if f is None:
    print("[3dm] failed to read file")
    raise SystemExit(0)

objs = f.Objects
print(f"[3dm] objects: {len(objs)}")

# Layers
layers = f.Layers
print(f"[3dm] layers: {len(layers)}")
from collections import Counter
layer_names = {}
for i in range(len(layers)):
    lay = layers[i]
    layer_names[lay.Index] = lay.Name

# Materials
mats = f.Materials
print(f"[3dm] materials: {len(mats)}")
mat_names = []
for i in range(len(mats)):
    try:
        mat_names.append(mats[i].Name)
    except Exception:
        pass
print(f"[3dm] material names: {mat_names}")

# Object -> layer distribution + sample names
by_layer = Counter()
obj_names = []
for i in range(len(objs)):
    obj = objs[i]
    attr = obj.Attributes
    li = attr.LayerIndex
    by_layer[layer_names.get(li, f'layer{li}')] += 1
    nm = attr.Name
    if nm:
        obj_names.append(nm)

print(f"[3dm] objects-with-names: {len(obj_names)}")
print("[3dm] === objects per layer (top 40) ===")
for lay, n in by_layer.most_common(40):
    print(f"    {n:>4}  {lay}")

print("[3dm] === sample object names (first 40) ===")
for n in obj_names[:40]:
    print(f"    {n}")
