"""Inspect lights + animation + render setup."""
import bpy

print(f"== FILE: {bpy.data.filepath}")
sc = bpy.context.scene
print(f"== SCENE ==  '{sc.name}'  frames={sc.frame_start}-{sc.frame_end}  active_cam={sc.camera.name if sc.camera else '(none)'}")
print(f"   resolution={sc.render.resolution_x}x{sc.render.resolution_y}  fps={sc.render.fps}/{sc.render.fps_base}")
print(f"   engine={sc.render.engine}")
if sc.render.engine == 'CYCLES':
    print(f"   cycles samples={sc.cycles.samples}  adaptive={sc.cycles.use_adaptive_sampling}")

print()
print("== LIGHTS ==")
for o in bpy.data.objects:
    if o.type != "LIGHT": continue
    print(f"   '{o.name}'  type={o.data.type}  energy={o.data.energy}  rot=({o.rotation_euler.x:.2f},{o.rotation_euler.y:.2f},{o.rotation_euler.z:.2f})")
    if o.animation_data and o.animation_data.action:
        try:
            n_fc = len(o.animation_data.action.fcurves)
        except Exception:
            n_fc = "?"
        print(f"      ANIMATED: action='{o.animation_data.action.name}'  fcurves~={n_fc}")

print()
print("== ANIMATED OBJECTS (any kind) ==")
for o in bpy.data.objects:
    if not o.animation_data or not o.animation_data.action: continue
    try:
        n_fc = len(o.animation_data.action.fcurves)
    except Exception:
        n_fc = "?"
    print(f"   '{o.name}'  type={o.type}  action='{o.animation_data.action.name}'  fcurves~={n_fc}")

print()
print("== WORLD ANIMATION ==")
for w in bpy.data.worlds:
    if w.animation_data and w.animation_data.action:
        print(f"   world '{w.name}' has animation action='{w.animation_data.action.name}'")
    if w.use_nodes and w.node_tree:
        if w.node_tree.animation_data and w.node_tree.animation_data.action:
            print(f"   world '{w.name}' NODE TREE has animation: '{w.node_tree.animation_data.action.name}'")

print()
print("== CAMERAS ==")
for c in bpy.data.cameras:
    users = [o.name for o in bpy.data.objects if o.data == c]
    print(f"   camera-data '{c.name}'  used by {users}")
