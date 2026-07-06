"""Verify v5: new interior positioned within v3 building, toggle works on all,
v3 systems intact (HDRI, camera, runtime)."""
import bpy, json
from mathutils import Vector
from collections import Counter

with open(r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json") as f:
    v3 = json.load(f)
v3_objnames = {e["obj"] for e in v3["snapshot"]}

snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
print(f"[V] snapshot slots: {len(snap)}")
mt = sum(1 for e in snap if not bpy.data.materials.get(e["textured_mat"]))
mb = sum(1 for e in snap if not bpy.data.materials.get(e["basic_mat"]))
print(f"[V] integrity: missing_textured={mt} missing_basic={mb}")

def bbox(names):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name not in names: continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

v3_meshes = {o.name for o in bpy.data.objects if o.type=="MESH" and o.name in v3_objnames}
new_meshes = {o.name for o in bpy.data.objects if o.type=="MESH" and o.name not in v3_objnames}
print(f"[V] v3 meshes={len(v3_meshes)}  new meshes={len(new_meshes)}")
v3mn, v3mx = bbox(v3_meshes)
nwmn, nwmx = bbox(new_meshes)
print(f"[V] v3 bbox:  min={tuple(round(x,1) for x in v3mn)} max={tuple(round(x,1) for x in v3mx)}")
print(f"[V] new bbox: min={tuple(round(x,1) for x in nwmn)} max={tuple(round(x,1) for x in nwmx)}")
# overlap check: new should sit inside/around v3 building, not off in space
inside = all(nwmn[i] >= v3mn[i]-5 and nwmx[i] <= v3mx[i]+5 for i in range(3))
print(f"[V] new geometry within v3 bounds (+/-5m): {inside}")

# toggle test across all 267
def state():
    c = Counter()
    for e in snap:
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["textured_mat"]: c["textured"]+=1
        elif m and m.name == e["basic_mat"]: c["basic"]+=1
        else: c["other"]+=1
    return dict(c)
print(f"[V] default state: {state()}")
txt = bpy.data.texts["rhino_toggle.py"]; ns={}
exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()
bpy.ops.rt.toggle(area="")
print(f"[V] after Alt+0: {state()}")
bpy.ops.rt.force_textured()
print(f"[V] after Alt+9: {state()}")

sc = bpy.context.scene
aw = bpy.data.worlds.get("ArchWorld"); hdri=None
if aw and aw.use_nodes:
    for n in aw.node_tree.nodes:
        if n.type=="TEX_ENVIRONMENT" and n.image: hdri=n.image.name
print(f"[V] camera={sc.camera.name if sc.camera else None} world={sc.world.name} ArchWorld_hdri={hdri}")
ws = [w.name for w in bpy.data.workspaces]
print(f"[V] workspaces: {ws}")
print("[V] DONE")
