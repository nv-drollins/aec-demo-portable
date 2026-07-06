import bpy, json, os
from collections import defaultdict
report = []
report.append(f"FILE: {bpy.data.filepath}")
report.append(f"OBJECTS: {len(bpy.data.objects)}, MESHES: {len(bpy.data.meshes)}, MATERIALS: {len(bpy.data.materials)}")
report.append("")
report.append("== MATERIALS (active in scene) ==")
used_mats = set()
mat_to_meshes = defaultdict(list)
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material:
            used_mats.add(s.material.name)
            mat_to_meshes[s.material.name].append(o.name)
for m in sorted(used_mats):
    report.append(f"  [{m}]  on {len(mat_to_meshes[m])} mesh(es)")
    for n in mat_to_meshes[m][:5]:
        report.append(f"      - {n}")
    if len(mat_to_meshes[m]) > 5:
        report.append(f"      ... +{len(mat_to_meshes[m])-5} more")
report.append("")
report.append("== ALL MESH OBJECTS (first 50) ==")
for o in sorted([x.name for x in bpy.data.objects if x.type=="MESH"])[:50]:
    obj = bpy.data.objects[o]
    mats = [s.material.name if s.material else "<none>" for s in obj.material_slots]
    tag = obj.get("material","")
    report.append(f"  {o}  | tag={tag}  | slots={mats}")
report.append("")
report.append("== COLLECTIONS ==")
for c in bpy.data.collections:
    report.append(f"  {c.name}: {len(c.objects)} objects")
report.append("")
report.append("== CAMERAS / SCENE ==")
for c in bpy.data.cameras: report.append(f"  cam: {c.name}")
sc = bpy.context.scene
report.append(f"  scene: {sc.name}  render: {sc.render.resolution_x}x{sc.render.resolution_y}")
out_path = r"C:\\Users\\NVIDIA\\Downloads\\AEC_Demo_Portable\\AEC_Demo_Portable\\scripts\\_v17_inventory.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print("WROTE", out_path)
