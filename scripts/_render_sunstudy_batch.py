"""Background batch render: summer + winter sun study at 1280x720.

Apply each season's sun keyframes, set the render filepath, render the
animation, then move on to the next season. Runs as a single Blender
background process (no UI), so the user's interactive Blender session is
free during the renders.
"""
import bpy
import os

OUT_DIR  = r"C:\Users\NVIDIA\Documents\Computex\Blender_Render\SunStudy"
RENDER_W = 1280
RENDER_H = 720

SEASONS = [
    ("summer", {
        "x_keys":   [(1, 1.4), (45, 0.8), (90, 0.18), (135, 0.8), (180, 1.4)],
        "z_keys":   [(1, 1.178), (180, -0.785)],
        "filename": "cliff_house_act3_sunstudy_summer",
        "action_name": "Sun_Summer_SoCal",
    }),
    ("winter", {
        "x_keys":   [(1, 1.4), (45, 1.2), (90, 1.0), (135, 1.2), (180, 1.4)],
        "z_keys":   [(1, 1.178), (180, -0.785)],
        "filename": "cliff_house_act3_sunstudy_winter",
        "action_name": "Sun_Winter_SoCal",
    }),
]


def apply_season(season_id, spec):
    sun = next((o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sun is None:
        print(f"[batch] FAIL: no Sun light")
        return False
    sun.animation_data_clear()
    for f, v in spec["x_keys"]:
        sun.rotation_euler[0] = v
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=0)
    for f in (1, 180):
        sun.rotation_euler[1] = 0.0
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=1)
    for f, v in spec["z_keys"]:
        sun.rotation_euler[2] = v
        sun.keyframe_insert(data_path="rotation_euler", frame=f, index=2)
    if sun.animation_data and sun.animation_data.action:
        sun.animation_data.action.name = spec["action_name"]
        sun.animation_data.action.use_fake_user = True

    sc = bpy.context.scene
    sc.render.resolution_x = RENDER_W
    sc.render.resolution_y = RENDER_H
    sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(OUT_DIR, spec["filename"])
    sc.render.use_compositing = False
    sc.render.use_sequencer = False

    # Architectural sun studies use a flat neutral background, not an HDRI.
    # Force the active world to Studio_Gray (or build a tuned one if missing)
    # so the renders read as a clean studio plate.
    studio = bpy.data.worlds.get("Studio_Gray")
    if studio is None:
        studio = bpy.data.worlds.new("Studio_Gray")
        studio.use_fake_user = True
    studio.use_nodes = True
    nt = studio.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (300, 0)
    bg  = nt.nodes.new("ShaderNodeBackground"); bg.location = (0, 0)
    # Lighter gray (0.45) at lower strength (0.6) - reads as classic studio
    # backdrop, doesn't wash out the sun shadows with ambient bounce.
    bg.inputs["Color"].default_value = (0.45, 0.45, 0.45, 1.0)
    bg.inputs["Strength"].default_value = 0.6
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sc.world = studio

    print(f"[batch] {season_id}: filepath={sc.render.filepath}  res={RENDER_W}x{RENDER_H}  world={sc.world.name}")
    return True


def main():
    sc = bpy.context.scene
    print(f"[batch] file: {bpy.data.filepath}")
    print(f"[batch] frames {sc.frame_start}-{sc.frame_end}  fps={sc.render.fps}")
    print(f"[batch] engine={sc.render.engine}  samples={sc.cycles.samples}  device={sc.cycles.device}")

    os.makedirs(OUT_DIR, exist_ok=True)
    for season_id, spec in SEASONS:
        print(f"[batch] ===== {season_id.upper()} =====")
        if not apply_season(season_id, spec):
            continue
        bpy.ops.render.render(animation=True, write_still=False)
        out_mp4 = os.path.join(OUT_DIR, spec["filename"] + ".mp4")
        if os.path.exists(out_mp4):
            sz = os.path.getsize(out_mp4) / 1024 / 1024
            print(f"[batch] {season_id} OK -> {out_mp4} ({sz:.1f} MB)")
        else:
            print(f"[batch] {season_id} render finished but output not found at {out_mp4}")
    print("[batch] ALL DONE")


main()
