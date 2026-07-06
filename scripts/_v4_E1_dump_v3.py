"""E1: open v3, dump its exact snapshot + world/camera/material inventory to JSON
so we can replicate v3 precisely on the new geometry."""
import bpy, json

OUT = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\scripts\_v3_setup.json"

snap = json.loads(bpy.context.scene.get("_act2_snapshot", "[]"))

# worlds + which has an environment-texture image (HDRI)
worlds = {}
for w in bpy.data.worlds:
    hdri = None
    if w.use_nodes and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == "TEX_ENVIRONMENT" and n.image:
                hdri = n.image.name
    worlds[w.name] = hdri

cams = {}
for o in bpy.data.objects:
    if o.type == "CAMERA":
        cams[o.name] = {
            "lens": o.data.lens,
            "has_bookmark": "_bookmark_matrix" in o,
            "matrix": [list(r) for r in o.matrix_world],
        }

# all materials referenced by the snapshot
ref_mats = sorted({e["textured_mat"] for e in snap} | {e["basic_mat"] for e in snap})
present = {m.name for m in bpy.data.materials}
missing = [m for m in ref_mats if m not in present]

data = {
    "snapshot": snap,
    "worlds": worlds,
    "active_world": bpy.context.scene.world.name if bpy.context.scene.world else None,
    "cameras": cams,
    "active_camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
    "snapshot_materials": ref_mats,
    "snapshot_materials_missing_in_v3": missing,
    "render": {
        "x": bpy.context.scene.render.resolution_x,
        "y": bpy.context.scene.render.resolution_y,
    },
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1)

print(f"[E1] snapshot slots: {len(snap)}")
print(f"[E1] worlds: {worlds}  active={data['active_world']}")
print(f"[E1] cameras: {list(cams.keys())}  active={data['active_camera']}")
print(f"[E1] snapshot materials: {len(ref_mats)}  missing_in_v3={missing}")
print(f"[E1] wrote {OUT}")
