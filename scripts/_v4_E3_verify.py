"""E3 verify: does v4 now match v3? Check default state, per-area material
distribution, HDRI, camera, toggles, and list unmatched exterior meshes."""
import bpy, json
from collections import Counter

snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
with open(r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json") as f:
    v3 = json.load(f)
v3_keys = {(e["obj"], e["slot"]) for e in v3["snapshot"]}

print(f"[E3] slots={len(snap)}")
mt = sum(1 for e in snap if not bpy.data.materials.get(e["textured_mat"]))
mb = sum(1 for e in snap if not bpy.data.materials.get(e["basic_mat"]))
print(f"[E3] integrity missing_textured={mt} missing_basic={mb}")

# per-area textured distribution (should mirror v3: walls->HoneyOakWood etc.)
for a in ("walls", "floors", "roof", "windows", "frames", "stairs"):
    tx = Counter(e["textured_mat"] for e in snap if e["area"] == a)
    print(f"[E3] [{a}] textured: {dict(tx)}")

# current displayed state
def state():
    c = Counter()
    for e in snap:
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["textured_mat"]: c["textured"] += 1
        elif m and m.name == e["basic_mat"]: c["basic"] += 1
        else: c["other"] += 1
    return dict(c)
print(f"[E3] DEFAULT displayed: {state()}")

# world / camera
sc = bpy.context.scene
aw = bpy.data.worlds.get("ArchWorld")
hdri = None
if aw and aw.use_nodes:
    for n in aw.node_tree.nodes:
        if n.type == "TEX_ENVIRONMENT" and n.image: hdri = n.image.name
print(f"[E3] active_world={sc.world.name}  ArchWorld_hdri={hdri}")
print(f"[E3] camera={sc.camera.name if sc.camera else None}  bookmark={'_bookmark_matrix' in (sc.camera or {})}")
print(f"[E3] render={sc.render.resolution_x}x{sc.render.resolution_y}")

# toggles
txt = bpy.data.texts["rhino_toggle.py"]; ns = {}
exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()
bpy.ops.rt.toggle(area="")
print(f"[E3] after Alt+0: {state()}")
bpy.ops.rt.toggle(area="")
print(f"[E3] after Alt+0: {state()}")
bpy.ops.rt.force_textured()
print(f"[E3] after Alt+9: {state()}")

# unmatched exterior meshes (walls/windows/roof/floors) - quality gauge
unmatched_ext = []
for e in snap:
    if e["area"] in ("walls", "windows", "roof", "floors") and (e["obj"], e["slot"]) not in v3_keys:
        unmatched_ext.append(e["obj"])
print(f"[E3] unmatched EXTERIOR meshes (got fallback, not v3-exact): {len(unmatched_ext)}")
for n in unmatched_ext[:25]:
    print(f"      {n}")
