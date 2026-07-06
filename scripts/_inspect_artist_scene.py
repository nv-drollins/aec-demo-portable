"""Inventory of the artist's Screen_Capture_unpacked scene.

Reports:
 - scenes, cameras, render settings, world setup
 - materials (and how many meshes they cover)
 - images: paths, missing-on-disk count, packed status
 - mesh tag custom property 'material' (for segmentation compatibility check)
"""
import bpy, os
from collections import defaultdict

print("=" * 70)
print("FILE:", bpy.data.filepath)
print(f"OBJECTS: {len(bpy.data.objects)}   MESHES: {len(bpy.data.meshes)}   MATERIALS: {len(bpy.data.materials)}   IMAGES: {len(bpy.data.images)}")

print()
print("=== SCENES ===")
for s in bpy.data.scenes:
    cam = s.camera.name if s.camera else "(none)"
    print(f"  '{s.name}'  render={s.render.resolution_x}x{s.render.resolution_y}  active_cam={cam}")

print()
print("=== CAMERAS ===")
for c in bpy.data.cameras:
    users = [o.name for o in bpy.data.objects if o.data == c]
    print(f"  '{c.name}'  obj={users}")

print()
print("=== WORLD / HDRI ===")
for w in bpy.data.worlds:
    print(f"  world '{w.name}'  use_nodes={w.use_nodes}")
    if w.use_nodes and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == "TEX_ENVIRONMENT":
                img = n.image.name if n.image else "(none)"
                print(f"    env-tex '{n.name}': image={img}")

print()
print("=== IMAGES (missing-from-disk?) ===")
missing = []
packed = 0
on_disk = 0
for img in bpy.data.images:
    if img.packed_file:
        packed += 1
        print(f"  [PACKED] '{img.name}'  size={img.size[0]}x{img.size[1]}")
        continue
    fp = bpy.path.abspath(img.filepath) if img.filepath else ""
    has_disk = bool(fp and os.path.exists(fp))
    if has_disk:
        on_disk += 1
    else:
        missing.append((img.name, img.filepath, fp))
    state = "OK" if has_disk else "MISSING"
    print(f"  [{state}] '{img.name}'  raw='{img.filepath}'  -> '{fp}'")

print()
print(f"summary: {packed} packed, {on_disk} on disk, {len(missing)} MISSING")

print()
print("=== MATERIALS (usage on meshes) ===")
mat_use = defaultdict(int)
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if s.material:
            mat_use[s.material.name] += 1
for m, n in sorted(mat_use.items(), key=lambda kv: -kv[1]):
    print(f"  {n:>4}x  {m}")

print()
print("=== MESH 'material' TAG COVERAGE (for ComfyUI segmentation) ===")
tag_counts = defaultdict(int)
total_meshes = 0
for o in bpy.data.objects:
    if o.type != "MESH": continue
    total_meshes += 1
    tag = o.get("material", "")
    tag_counts[tag if tag else "<untagged>"] += 1
for t, n in sorted(tag_counts.items(), key=lambda kv: -kv[1]):
    print(f"  {n:>4}  '{t}'")
print(f"total meshes: {total_meshes}")

print()
print("=== ANIMATION ===")
sc = bpy.context.scene
print(f"  frame_range: {sc.frame_start} to {sc.frame_end}  current: {sc.frame_current}")
for obj in bpy.data.objects:
    if obj.animation_data and obj.animation_data.action:
        n_fc = len(obj.animation_data.action.fcurves)
        print(f"  animated obj: '{obj.name}'  fcurves={n_fc}")
