"""Build cliff_house_act3_sunstudy.blend from v3.

Steps:
 1. Create Clay_Override material; assign to scene.view_layer.material_override
 2. Port SunAction from base_scene_swag_04_sunstudy.blend onto v3's existing Sun
 3. Hide window-tagged meshes (tag in {window, glass_railing}) in viewport + render
 4. Render config: 1920x1080, 24fps, Cycles 128 samples adaptive, MP4 H.264
 5. Frame range 1-180
 6. Use Camera_day (already active)
 7. Save as cliff_house_act3_sunstudy.blend (next to v3)
"""
import bpy
import os

OLD_SUNSTUDY = r"C:\Users\NVIDIA\Downloads\base_scene_swag_04_sunstudy.blend"
DST_DIR = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets"
DST = os.path.join(DST_DIR, "cliff_house_act3_sunstudy.blend")
RENDER_OUT_DIR = r"C:\Users\NVIDIA\Documents\Computex\Blender_Render\SunStudy"


def make_clay_material():
    name = "Clay_Override"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_fake_user = True
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.60, 0.58, 0.55, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def port_sun_action():
    sun_obj = next((o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sun_obj is None:
        print("[act3] WARN: no Sun light found; sun will be static")
        return False
    sun_data = sun_obj.data

    before_actions = {a.name for a in bpy.data.actions}
    with bpy.data.libraries.load(OLD_SUNSTUDY, link=False) as (data_from, data_to):
        data_to.actions = [n for n in data_from.actions if "Sun" in n]
    after_actions = {a.name for a in bpy.data.actions}
    new_actions = after_actions - before_actions
    if not new_actions:
        print("[act3] WARN: no SunAction in old sunstudy; sun will stay static")
        return False
    # Pick the SunAction (Blender 5.x style: action with 'Sun' in name)
    action_name = next((n for n in new_actions if "Sun" in n), None)
    if not action_name:
        print(f"[act3] WARN: appended actions {new_actions} have no Sun-prefix; using {list(new_actions)[0]}")
        action_name = list(new_actions)[0]
    action = bpy.data.actions.get(action_name)

    # Attach to the SUN OBJECT's animation_data (rotation lives on the object
    # transform, not on the light data block).
    if sun_obj.animation_data is None:
        sun_obj.animation_data_create()
    sun_obj.animation_data.action = action
    sun_obj.animation_data.action_slot = None
    # Blender 5.x: slotted actions need explicit slot
    try:
        slots = action.slots
        if len(slots) > 0:
            for s in slots:
                if s.target_id_type in ('OBJECT', 'EMPTY'):
                    sun_obj.animation_data.action_slot = s
                    break
            else:
                sun_obj.animation_data.action_slot = slots[0]
    except Exception as e:
        print(f"[act3] action_slot setup skipped: {e}")
    print(f"[act3] ported sun animation: action='{action.name}' onto '{sun_obj.name}'")
    return True


def hide_windows():
    hidden = 0
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        t = o.get("material", "")
        if t in ("window", "glass_railing"):
            o.hide_viewport = True
            o.hide_render = True
            hidden += 1
    print(f"[act3] hid {hidden} window/glass-railing meshes")


def set_clay_override():
    vl = bpy.context.view_layer
    clay = bpy.data.materials.get("Clay_Override")
    vl.material_override = clay
    print(f"[act3] view-layer material override = {clay.name}")


def configure_render():
    sc = bpy.context.scene
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.render.fps_base = 1.0
    sc.frame_start = 1
    sc.frame_end = 180

    sc.render.engine = "CYCLES"
    sc.cycles.samples = 128
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    try:
        sc.cycles.device = "GPU"
    except Exception:
        pass

    # MP4 H.264 output. In Blender 5.x, media_type=VIDEO must come before
    # file_format=FFMPEG becomes available.
    img = sc.render.image_settings
    try:
        img.media_type = "VIDEO"
    except Exception as e:
        print(f"[act3] media_type set skipped: {e}")
    try:
        img.file_format = "FFMPEG"
    except Exception as e:
        print(f"[act3] file_format FFMPEG failed: {e}")
    try:
        sc.render.ffmpeg.format = "MPEG4"
        sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
        sc.render.ffmpeg.audio_codec = "NONE"
    except Exception as e:
        print(f"[act3] ffmpeg config warning: {e}")

    os.makedirs(RENDER_OUT_DIR, exist_ok=True)
    sc.render.filepath = os.path.join(RENDER_OUT_DIR, "cliff_house_act3_sunstudy")
    # Be safe: re-enable persistent data for speed, disable compositor/VSE to avoid
    # render pipeline producing black output.
    sc.render.use_persistent_data = True
    sc.render.use_compositing = False
    sc.render.use_sequencer = False
    sc.use_nodes = False

    print(f"[act3] render: {sc.render.resolution_x}x{sc.render.resolution_y}@{sc.render.fps}fps  frames {sc.frame_start}-{sc.frame_end}")
    print(f"[act3] cycles samples={sc.cycles.samples}  adaptive={sc.cycles.use_adaptive_sampling}  GPU={sc.cycles.device}")
    print(f"[act3] output: {sc.render.filepath}.mp4")


def main():
    print(f"[act3] source: {bpy.data.filepath}")
    sc = bpy.context.scene
    if sc.camera is None or sc.camera.name != "Camera_day":
        cd = bpy.data.objects.get("Camera_day")
        if cd: sc.camera = cd
    print(f"[act3] active camera: {sc.camera.name if sc.camera else '(none)'}")

    make_clay_material()
    set_clay_override()
    port_sun_action()
    hide_windows()
    configure_render()

    os.makedirs(DST_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
    sz = os.path.getsize(DST) / 1024 / 1024
    print(f"[act3] SAVED {DST}  ({sz:.1f} MB)")
    print("[act3] DONE")


main()
