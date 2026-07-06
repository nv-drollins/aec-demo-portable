"""Verify v4: default=basic gray, Alt+9 reveals v3 artist, toggles + swatches work."""
import bpy, json
from collections import Counter

snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
print(f"[v] snapshot slots: {len(snap)}")

# integrity
mt = sum(1 for e in snap if not bpy.data.materials.get(e["textured_mat"]))
mb = sum(1 for e in snap if not bpy.data.materials.get(e["basic_mat"]))
print(f"[v] integrity: missing_textured={mt} missing_basic={mb}")

def sample(area):
    tx = Counter(); bs = Counter()
    for e in snap:
        if e["area"] != area: continue
        tx[e["textured_mat"]] += 1; bs[e["basic_mat"]] += 1
    return dict(tx), dict(bs)

for a in ("walls","floors","roof","windows","frames","stairs"):
    tx, bs = sample(a)
    print(f"[v] [{a}] textured={tx}  basic={bs}")

def cur_state():
    c = Counter()
    for e in snap:
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["textured_mat"]: c["textured"]+=1
        elif m and m.name == e["basic_mat"]: c["basic"]+=1
        else: c["other"]+=1
    return dict(c)

print(f"[v] DEFAULT on open: {cur_state()}")

txt = bpy.data.texts["rhino_toggle.py"]
ns = {}; exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()
bpy.ops.rt.force_textured()
print(f"[v] after Alt+9 (force artist): {cur_state()}")
bpy.ops.rt.toggle(area="")
print(f"[v] after Alt+0: {cur_state()}")
bpy.ops.rt.toggle(area="")
print(f"[v] after Alt+0: {cur_state()}")

# wall swatch still works
def walls_now():
    c = Counter()
    for e in snap:
        if e["area"] != "walls": continue
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        c[m.name if m else None]+=1
    return dict(c)
bpy.ops.rt.wall_travertine()
print(f"[v] walls after Alt+4 swatch: {walls_now()}")
bpy.ops.rt.force_textured()

# reset to default basic for shipping
for e in snap:
    o = bpy.data.objects.get(e["obj"])
    if not o or e["slot"] >= len(o.material_slots): continue
    bm = bpy.data.materials.get(e["basic_mat"])
    if bm: o.material_slots[e["slot"]].material = bm

sc = bpy.context.scene
print(f"[v] camera={sc.camera.name if sc.camera else None} world={sc.world.name} res={sc.render.resolution_x}x{sc.render.resolution_y}")
tags = Counter(o.get('material','') for o in bpy.data.objects if o.type=='MESH' and o.get('material'))
print(f"[v] seg tags: {dict(tags)}")
print(f"[v] artist mats present: HoneyOakWood={bpy.data.materials.get('HoneyOakWood') is not None} White_Travertine={bpy.data.materials.get('White_Travertine') is not None}")
print(f"[v] v17 mats present: White_Travertine_v17={bpy.data.materials.get('White_Travertine_v17') is not None} Grey_Slate_v17={bpy.data.materials.get('Grey_Slate_v17') is not None}")

bpy.ops.wm.save_mainfile()
print("[v] saved (default=basic). DONE")
