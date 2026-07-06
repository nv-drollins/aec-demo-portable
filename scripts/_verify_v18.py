"""Verify cliff_house_materials_v18.blend has everything wired."""
import bpy, json, os

print("[verify] file:", bpy.data.filepath, flush=True)

# 1. Materials
expected_mats = [
    "MP_Travertine", "MP_Polished_Concrete_Wall", "MP_Wood_Cladding",
    "MP_Oak_Floor", "MP_Polished_Concrete_Floor", "MP_Zinc_Roof",
    "MP_Walnut_Accent", "MP_Dark_Anodized",
]
for m in expected_mats:
    mat = bpy.data.materials.get(m)
    if mat is None:
        print(f"[verify] FAIL: material missing: {m}", flush=True)
    else:
        ntexes = sum(1 for n in (mat.node_tree.nodes if mat.use_nodes else []) if n.type == 'TEX_IMAGE')
        print(f"[verify] OK   {m}  (texture nodes: {ntexes})", flush=True)

# 2. Snapshot
snap_raw = bpy.context.scene.get("_mp_artist_snapshot", "")
snap = json.loads(snap_raw) if snap_raw else []
print(f"[verify] snapshot records: {len(snap)}", flush=True)

# 3. Text block
txt = bpy.data.texts.get("material_painter.py")
if txt is None:
    print("[verify] FAIL: no material_painter.py text block", flush=True)
else:
    print(f"[verify] OK   text block 'material_painter.py'  use_module={txt.use_module}  lines={len(txt.lines)}", flush=True)

# 4. Are images packed?
unpacked = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and i.filepath]
packed   = sum(1 for i in bpy.data.images if i.packed_file)
print(f"[verify] images packed={packed}  unpacked-on-disk-still-referenced={len(unpacked)}", flush=True)

# 5. Simulate the runtime: exec the embedded text and check ops appear
if txt is not None:
    try:
        ns = {}
        exec(compile(txt.as_string(), txt.name, 'exec'), ns)
        if 'register' in ns:
            ns['register']()
            print("[verify] runtime register() OK", flush=True)
        else:
            print("[verify] FAIL: runtime has no register()", flush=True)
    except Exception as e:
        print(f"[verify] FAIL exec runtime: {e}", flush=True)

# 6. Operator presence
for op in ("mp.apply", "mp.apply_all", "mp.reset"):
    mod, name = op.split(".")
    if hasattr(getattr(bpy.ops, mod, None), name):
        print(f"[verify] OK   operator bpy.ops.{op}", flush=True)
    else:
        print(f"[verify] FAIL operator bpy.ops.{op}", flush=True)

# 7. Smoke test: apply travertine, then reset
def count_slots_with(mat_name):
    n = 0
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        for s in o.material_slots:
            if s.material and s.material.name == mat_name:
                n += 1
    return n

before_white = count_slots_with("White_Travertine")
before_mp = count_slots_with("MP_Travertine")
print(f"[verify] pre-apply  White_Travertine slots={before_white}  MP_Travertine slots={before_mp}", flush=True)

try:
    bpy.ops.mp.apply(upgrade_id="travertine")
except Exception as e:
    print(f"[verify] FAIL apply: {e}", flush=True)

after_white = count_slots_with("White_Travertine")
after_mp = count_slots_with("MP_Travertine")
print(f"[verify] post-apply White_Travertine slots={after_white}  MP_Travertine slots={after_mp}", flush=True)

try:
    bpy.ops.mp.reset()
except Exception as e:
    print(f"[verify] FAIL reset: {e}", flush=True)

reset_white = count_slots_with("White_Travertine")
reset_mp = count_slots_with("MP_Travertine")
print(f"[verify] post-reset White_Travertine slots={reset_white}  MP_Travertine slots={reset_mp}", flush=True)

ok = (before_white > 0 and after_mp == before_white and reset_white == before_white)
print(f"[verify] CYCLE_OK={ok}", flush=True)
