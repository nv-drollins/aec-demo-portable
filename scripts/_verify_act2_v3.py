"""Verify cliff_house_act2_textured_v3.blend uses real v17 materials."""
import bpy, json, os
from collections import Counter

print("[verify] file:", bpy.data.filepath)
print("[verify] size MB:", round(os.path.getsize(bpy.data.filepath)/1024/1024, 1))

# Check all 16 v17 materials present with _v17 suffix and fake_user=True
v17_names = ["Aluminum_Anodized_Dark","Concrete_Black","Concrete_Light_3","Concrete_Light_Patio",
             "Glass_Clear_Low_E","Glass_Frosted","Glass_Pale_Blue","Grey_Slate",
             "Timber_Engineered_Oak","Timber_Oiled_Dark","Water_Fall","Water_Pool",
             "White_Travertine","grass_earth","polished_concrete","water_pool"]
missing = []
for n in v17_names:
    m = bpy.data.materials.get(n + "_v17")
    if m is None: missing.append(n)
print(f"[verify] v17 materials present (_v17 suffix): {len(v17_names)-len(missing)}/{len(v17_names)}")
if missing: print(f"   missing: {missing}")

# Snapshot inspection
snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))
print(f"[verify] snapshot records: {len(snap)}")
inh = Counter()
for e in snap:
    inh[(e["textured_mat"], e["basic_mat"])] += 1
print("[verify] inheritance (artist -> v17, all):")
for (a, b), n in sorted(inh.items(), key=lambda kv: -kv[1]):
    print(f"   {a:<28} -> {b:<28}  {n}")

# No more *_RhinoBasic floating around
rb = [m.name for m in bpy.data.materials if m.name.endswith("_RhinoBasic")]
print(f"[verify] leftover _RhinoBasic materials: {len(rb)}  (should be 0)")

# Embedded text
txt = bpy.data.texts.get("rhino_toggle.py")
print(f"[verify] text rhino_toggle.py: {'OK' if txt else 'FAIL'}  use_module={getattr(txt,'use_module',None)}")
ns = {}; exec(compile(txt.as_string(), txt.name, "exec"), ns); ns["register"]()
print("[verify] register() OK")

# Smoke test - toggle each area
def count_basic(area):
    n = 0
    for e in snap:
        if e["area"] != area: continue
        o = bpy.data.objects.get(e["obj"])
        if not o or e["slot"] >= len(o.material_slots): continue
        m = o.material_slots[e["slot"]].material
        if m and m.name == e["basic_mat"]: n += 1
    return n

print()
print("[verify] toggle smoke test:")
for area in ("walls", "floors", "roof", "windows", "frames", ""):
    label = area if area else "ALL"
    before = count_basic(area) if area else sum(1 for a in ("walls","floors","roof","windows","frames","other","water","foundations","terrain") for _ in range(count_basic(a)))
    bpy.ops.rt.toggle(area=area)
    if area:
        after = count_basic(area)
    else:
        after = sum(count_basic(a) for a in ("walls","floors","roof","windows","frames","other","water","foundations","terrain"))
    bpy.ops.rt.toggle(area=area)
    if area:
        back = count_basic(area)
    else:
        back = sum(count_basic(a) for a in ("walls","floors","roof","windows","frames","other","water","foundations","terrain"))
    print(f"   {label:>8}: before={before}  toggled-on={after}  toggled-back={back}")

# Sanity sample: pick a few specific Act2 meshes and confirm what v17 material they now point to in basic state
print()
print("[verify] sample mesh -> v17 inheritance:")
sample_meshes = ["H2_wall_L1_north", "H2_wall_L2_east_new", "H2_roof_garage", "H2_glass_balc_east", "L1_door_centre"]
# Force basic state for all areas
bpy.ops.rt.toggle(area="")  # toggle all once
for name in sample_meshes:
    o = bpy.data.objects.get(name)
    if not o: print(f"   {name:<30} not found"); continue
    mats = [s.material.name if s.material else "(none)" for s in o.material_slots]
    print(f"   {name:<30} -> {mats}")
