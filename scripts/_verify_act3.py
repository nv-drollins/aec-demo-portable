"""Verify cliff_house_act3_sunstudy.blend is fully wired."""
import bpy, os
print("[verify] file:", bpy.data.filepath)
print("[verify] size MB:", round(os.path.getsize(bpy.data.filepath)/1024/1024, 1))

sc = bpy.context.scene
vl = bpy.context.view_layer

# Camera
print(f"[verify] active camera: {sc.camera.name if sc.camera else '(none)'}")

# Clay override
print(f"[verify] view-layer material_override: {vl.material_override.name if vl.material_override else 'NONE'}")

# Sun animation: sample rotation at a few frames
sun = next((o for o in bpy.data.objects if o.type=='LIGHT' and o.data.type=='SUN'), None)
if sun is None:
    print("[verify] FAIL: no Sun light")
else:
    print(f"[verify] Sun light '{sun.name}'  has anim={bool(sun.animation_data and sun.animation_data.action)}")
    for f in (1, 45, 90, 135, 180):
        sc.frame_set(f)
        rot = sun.rotation_euler
        print(f"   frame {f:>3}: sun rotation = ({rot.x:+.3f}, {rot.y:+.3f}, {rot.z:+.3f})")

# Window hiding
from collections import Counter
hidden = Counter()
visible = Counter()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    t = o.get("material", "")
    bucket = hidden if (o.hide_render or o.hide_viewport) else visible
    bucket[t or "(untagged)"] += 1
print(f"[verify] hidden meshes by tag: {dict(hidden)}")
print(f"[verify] visible meshes by tag (top 5): {dict(list(visible.most_common(5)))}")

# Render config
r = sc.render
print(f"[verify] render: {r.resolution_x}x{r.resolution_y}@{r.fps}fps  frames {sc.frame_start}-{sc.frame_end}")
print(f"[verify] engine={r.engine}  samples={sc.cycles.samples}  device={sc.cycles.device}  adaptive={sc.cycles.use_adaptive_sampling}")
print(f"[verify] file_format={r.image_settings.file_format}  ffmpeg.format={r.ffmpeg.format}  codec={r.ffmpeg.codec}")
print(f"[verify] filepath: {r.filepath}")
print(f"[verify] use_compositing={r.use_compositing}  use_sequencer={r.use_sequencer}  use_persistent_data={r.use_persistent_data}")

# Sanity: total visible meshes after window-hide
total_meshes = sum(1 for o in bpy.data.objects if o.type=='MESH')
visible_meshes = sum(1 for o in bpy.data.objects if o.type=='MESH' and not (o.hide_render or o.hide_viewport))
print(f"[verify] meshes total={total_meshes}  visible={visible_meshes}  hidden={total_meshes - visible_meshes}")
