"""Verify cliff_house_act2_textured_v2.blend has the toggle system wired."""
import bpy, json, os

print("[verify] file:", bpy.data.filepath)
print("[verify] size MB:", round(os.path.getsize(bpy.data.filepath)/1024/1024, 1))

# 1. _RhinoBasic twins exist for every used artist material
used = set()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material and not s.material.name.endswith("_RhinoBasic"):
            used.add(s.material.name)

missing_twins = []
for n in sorted(used):
    twin = bpy.data.materials.get(n + "_RhinoBasic")
    if twin is None:
        missing_twins.append(n)
    else:
        bsdf = next((nd for nd in twin.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            c = bsdf.inputs["Base Color"].default_value
            r = bsdf.inputs["Roughness"].default_value
            print(f"  [OK] {n}_RhinoBasic  base=({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})  rough={r:.2f}")
        else:
            print(f"  [OK] {n}_RhinoBasic  (no BSDF info)")
if missing_twins:
    print(f"[verify] FAIL: missing twins for: {missing_twins}")
else:
    print(f"[verify] OK: all {len(used)} artist materials have _RhinoBasic twins")

# 2. Snapshot present and well-formed
snap_raw = bpy.context.scene.get("_act2_snapshot", "")
snap = json.loads(snap_raw) if snap_raw else []
from collections import Counter
area_counts = Counter(e["area"] for e in snap)
print(f"[verify] snapshot records: {len(snap)}")
for a, n in area_counts.most_common():
    print(f"    area '{a}': {n}")

# 3. Text block + register
txt = bpy.data.texts.get("rhino_toggle.py")
print(f"[verify] text 'rhino_toggle.py': {'OK' if txt else 'FAIL'}  use_module={getattr(txt, 'use_module', None)}")
ns = {}
exec(compile(txt.as_string(), txt.name, "exec"), ns)
ns["register"]()
print("[verify] register() OK")

# 4. Operator present
ok = hasattr(bpy.ops.rt, "toggle")
print(f"[verify] bpy.ops.rt.toggle present: {ok}")

# 5. Smoke test: toggle each area, count slots that flipped
def count_basic_in_area(area):
    n = 0
    for e in snap:
        if e["area"] != area: continue
        obj = bpy.data.objects.get(e["obj"])
        if not obj or e["slot"] >= len(obj.material_slots): continue
        m = obj.material_slots[e["slot"]].material
        if m and m.name == e["basic_mat"]: n += 1
    return n

print()
print("[verify] toggle smoke test (3 sample areas):")
for area in ("walls", "roof", "windows"):
    before = count_basic_in_area(area)
    bpy.ops.rt.toggle(area=area)
    after_on = count_basic_in_area(area)
    bpy.ops.rt.toggle(area=area)
    after_off = count_basic_in_area(area)
    print(f"    {area:>8}: before basic={before}  after Alt-press basic={after_on}  after 2nd press basic={after_off}")

# 6. Master toggle
print()
print("[verify] master toggle (Alt+0):")
total_basic_before = sum(1 for e in snap if (lambda obj: obj and e["slot"] < len(obj.material_slots) and obj.material_slots[e["slot"]].material and obj.material_slots[e["slot"]].material.name == e["basic_mat"])(bpy.data.objects.get(e["obj"])))
bpy.ops.rt.toggle(area="")
total_basic_mid = sum(1 for e in snap if (lambda obj: obj and e["slot"] < len(obj.material_slots) and obj.material_slots[e["slot"]].material and obj.material_slots[e["slot"]].material.name == e["basic_mat"])(bpy.data.objects.get(e["obj"])))
bpy.ops.rt.toggle(area="")
total_basic_back = sum(1 for e in snap if (lambda obj: obj and e["slot"] < len(obj.material_slots) and obj.material_slots[e["slot"]].material and obj.material_slots[e["slot"]].material.name == e["basic_mat"])(bpy.data.objects.get(e["obj"])))
print(f"    basic slots: before={total_basic_before}  after first Alt+0={total_basic_mid}  after second Alt+0={total_basic_back}")

# 7. Keymap count
km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("3D View")
n_kmi = sum(1 for kmi in km.keymap_items if kmi.idname == "rt.toggle") if km else 0
print(f"[verify] keymap items for rt.toggle: {n_kmi}  (expected 6: Alt+0..5)")
