"""Measure dimensions of shared exterior meshes + scene unit scale, to detect a
scale mismatch between v3 and cliff_house_26. Run on each file."""
import bpy

REF = ["H2_roof_slab", "H2_floor_L1_garage", "H2_L3_S_col", "H2_glass_balc_south",
       "H2_roof_garage", "H2__L2_balcony_floor"]

print(f"=== {bpy.data.filepath} ===")
print(f"unit_system={bpy.context.scene.unit_settings.system}  scale_length={bpy.context.scene.unit_settings.scale_length}")
for name in REF:
    o = bpy.data.objects.get(name)
    if o is None or o.type != "MESH":
        print(f"  {name}: <missing>")
        continue
    d = o.dimensions
    s = o.scale
    print(f"  {name}: dims=({d.x:.3f}, {d.y:.3f}, {d.z:.3f})  scale=({s.x:.3f},{s.y:.3f},{s.z:.3f})")
