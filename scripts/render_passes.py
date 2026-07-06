"""
AEC Demo Portable — Render Passes
Renders beauty, depth, and segmentation from the active Blender camera.

Run from Blender's Python console:
  exec(open(r"PATH_TO/scripts/render_passes.py").read())
  render_passes()           # renders next auto-numbered set
  render_passes("0005")     # renders a specific number
"""
import bpy, os, re, sys
from pathlib import Path

# ── Locate project root from environment or fallback ──────────
_ENV_ROOT = os.environ.get("AEC_DEMO_ROOT", "")
if _ENV_ROOT:
    PROJECT_ROOT = Path(_ENV_ROOT)
else:
    # Fallback: look relative to the blend file
    blend_path = bpy.data.filepath
    if blend_path:
        PROJECT_ROOT = Path(blend_path).parent.parent
    else:
        raise RuntimeError(
            "Set AEC_DEMO_ROOT environment variable or save the .blend file first"
        )

RENDERS_DIR = PROJECT_ROOT / "renders"
HDRI_PATH   = PROJECT_ROOT.parent / "assets" / "hdri" / "qwantani_puresky_2k.hdr"

SEG_COLORS = {
    "travertine_white": (0.784, 0.427, 0.404, 1.0),
    "travertine_light": (0.784, 0.427, 0.404, 1.0),
    "concrete_board":   (0.784, 0.427, 0.404, 1.0),
    "concrete_light":   (0.784, 0.427, 0.404, 1.0),
    "concrete_dark":    (0.784, 0.427, 0.404, 1.0),
    "glass_clear":      (0.373, 0.447, 0.780, 1.0),
    "glass_tinted":     (0.373, 0.447, 0.780, 1.0),
    "glass_railing":    (0.373, 0.447, 0.780, 1.0),
    "water_blue":       (0.373, 0.447, 0.780, 1.0),
    "aluminum_dark":    (0.533, 0.737, 0.761, 1.0),
    "wood_walnut":      (0.773, 0.659, 0.447, 1.0),
}

def _next_num():
    highest = 0
    for folder in ("beauty", "depth", "seg"):
        d = RENDERS_DIR / folder
        if not d.exists(): continue
        for f in os.listdir(d):
            m = re.search(r'(\d{4})', f)
            if m: highest = max(highest, int(m.group(1)))
    return f"{highest + 1:04d}"

def _make_seg_mat(name, color):
    n = f"__seg_{name}"
    if n in bpy.data.materials: return bpy.data.materials[n]
    m = bpy.data.materials.new(n); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

def _make_depth_mat(clip_start, clip_end):
    n = "__depth_mat__"
    if n in bpy.data.materials: return bpy.data.materials[n]
    m = bpy.data.materials.new(n); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    cd = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = clip_start
    mr.inputs["From Max"].default_value = clip_end
    mr.inputs["To Min"].default_value   = 0.0
    mr.inputs["To Max"].default_value   = 1.0
    mr.clamp = True
    em  = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"],        em.inputs["Color"])
    nt.links.new(em.outputs["Emission"],      out.inputs["Surface"])
    return m

def render_passes(num=None):
    scene = bpy.context.scene
    cam   = scene.camera

    if num is None:
        num = _next_num()

    for sub in ("beauty", "depth", "seg"):
        (RENDERS_DIR / sub).mkdir(parents=True, exist_ok=True)

    # Save render state
    orig_engine  = scene.render.engine
    orig_samples = scene.cycles.samples
    orig_denoise = scene.cycles.use_denoising
    orig_vt      = scene.view_settings.view_transform
    orig_look    = scene.view_settings.look
    orig_fmt     = scene.render.image_settings.file_format
    orig_cmode   = scene.render.image_settings.color_mode
    orig_transp  = scene.render.film_transparent

    def render_to(path, samples, denoise, color_mode, engine, transparent=False):
        scene.render.engine           = engine
        scene.render.film_transparent = transparent
        if engine == "CYCLES":
            scene.cycles.device = "GPU"
            scene.cycles.samples = samples
            scene.cycles.use_denoising = denoise
        scene.use_nodes = False
        scene.render.filepath = str(path)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode  = color_mode
        bpy.ops.render.render(write_still=True)
        sz = os.path.getsize(path) // 1024
        print(f"  {path.name}  ({sz} KB)")

    # 1. Beauty
    print(f"[1/3] Beauty → beauty_{num}.png")
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "None"
    render_to(RENDERS_DIR / "beauty" / f"beauty_{num}.png", 128, True, "RGB", "CYCLES")

    # 2. Depth
    print(f"[2/3] Depth → depth_{num}.png")
    scene.view_settings.view_transform = "Raw"
    scene.view_settings.look = "None"
    originals = {}
    depth_mat = _make_depth_mat(cam.data.clip_start, cam.data.clip_end)
    for obj in bpy.data.objects:
        if obj.type != 'MESH': continue
        if not obj.data.materials: obj.data.materials.append(None)
        originals[obj.name] = obj.data.materials[0]
        obj.data.materials[0] = depth_mat
    render_to(RENDERS_DIR / "depth" / f"depth_{num}.png", 4, False, "BW", "CYCLES")
    for obj in bpy.data.objects:
        if obj.name in originals: obj.data.materials[0] = originals[obj.name]

    # 3. Segmentation (transparent background, RGBA)
    print(f"[3/3] Seg → seg_{num}.png  (RGBA transparent background)")
    originals = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH': continue
        tag = obj.get("material", "")
        if tag not in SEG_COLORS: continue
        if not obj.data.materials: obj.data.materials.append(None)
        originals[obj.name] = obj.data.materials[0]
        obj.data.materials[0] = _make_seg_mat(tag, SEG_COLORS[tag])
    render_to(RENDERS_DIR / "seg" / f"seg_{num}.png", 1, False, "RGBA", "BLENDER_EEVEE", True)
    for obj in bpy.data.objects:
        if obj.name in originals: obj.data.materials[0] = originals[obj.name]

    # Restore
    scene.render.engine            = orig_engine
    scene.cycles.samples           = orig_samples
    scene.cycles.use_denoising     = orig_denoise
    scene.view_settings.view_transform = orig_vt
    scene.view_settings.look       = orig_look
    scene.render.image_settings.file_format = orig_fmt
    scene.render.image_settings.color_mode  = orig_cmode
    scene.render.film_transparent  = orig_transp

    print(f"\nSet {num} complete in {RENDERS_DIR}")
    return num
