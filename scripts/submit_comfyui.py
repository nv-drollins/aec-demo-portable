"""
AEC Demo Portable — ComfyUI Submit
Renders all passes and submits to ComfyUI using the bundled workflow.

Run from Blender Python console:
  exec(open(r"C:/AEC_Demo_Portable/scripts/submit_comfyui.py").read())
  submit()              # render + submit
  submit(render=False)  # submit only (reuse last renders)

FIRST-TIME SETUP:
  Before using submit(), you must run the workflow once in the
  ComfyUI browser (http://127.0.0.1:8188) to create a history entry.
  See QUICK_START_GUIDE.md Step 2.
"""
import bpy, os, sys, json, requests, uuid, random, time
from pathlib import Path

# ── Locate AEC_Demo_Portable root ─────────────────────────────
# Checks env var first, then relative to blend file, then common location
_ENV_ROOT = os.environ.get("AEC_DEMO_ROOT", "")
if _ENV_ROOT:
    AEC_ROOT = Path(_ENV_ROOT)
elif bpy.data.filepath:
    # blend file lives in sample_project/blender_assets/
    AEC_ROOT = Path(bpy.data.filepath).parent.parent.parent
else:
    AEC_ROOT = Path("C:/AEC_Demo_Portable")

# Load config via yaml or fall back to defaults
try:
    import yaml
    _cfg_path = AEC_ROOT / "config" / "user_config.yaml"
    with open(_cfg_path) as f:
        _cfg = yaml.safe_load(f)
    COMFY_URL   = _cfg["comfyui"]["url"]
    COMFY_INPUT = Path(_cfg["comfyui"]["install_path"]) / "ComfyUI" / "input"
    BEAUTY_SAMPLES = _cfg["render"]["beauty_samples"]
except Exception as e:
    print(f"[AEC] Config load warning: {e} — using defaults")
    COMFY_URL   = "http://127.0.0.1:8188"
    COMFY_INPUT = Path("D:/tools/comfy_for_blender/ComfyUI_ForDemo/ComfyUI/input")
    BEAUTY_SAMPLES = 32

# Portable Spark runtime overrides take precedence over the local desktop YAML.
_portable_comfy_root = os.environ.get("AEC_PORTABLE_COMFY_ROOT", "")
_portable_comfy_url = os.environ.get("AEC_PORTABLE_COMFY_URL", "")
if _portable_comfy_root:
    COMFY_INPUT = Path(_portable_comfy_root) / "input"
if _portable_comfy_url:
    COMFY_URL = _portable_comfy_url
RGB_FILE = "beauty_input.png"
SEG_FILE = "seg_input.png"

# ──────────────────────────────────────────────────────────────────────────
# Render + Flux output dimensions.
#
# 1024x1024 = native Flux 2 Klein training resolution. Square, safe, slowest.
# 1280x 720 = 16:9 720p experiment. Both dims are multiples of 16 (clean for
#             Flux's VAE) and ~88% of 1024² area so ~12% faster per pass.
#             Slight quality drop vs native 1024² but generally fine for
#             arch-viz previews; upscale later with ESRGAN/etc.
#
# Render resolution is now read DYNAMICALLY from
# bpy.context.scene.render.resolution_x / resolution_y, so the Alt+6 aspect
# toggle in the embedded runtime drives both Blender and ComfyUI from the
# same source of truth. The previous hardcoded 1280x720 is kept here only as
# the documented default; nothing in this module reads these constants.
RENDER_WIDTH  = 1280   # legacy default, NOT read at submit time
RENDER_HEIGHT = 720    # legacy default, NOT read at submit time


def _render_size():
    """Single source of truth for render resolution at submit time."""
    sc = bpy.context.scene
    return sc.render.resolution_x, sc.render.resolution_y

# Maps a mesh's `material` custom-prop to a seg-pass color.
# Colors correspond to the workflow's four MaskFromColor+ nodes:
#   (200,109,103) red  -> Walls chain    (wood/stone inpaint)
#   (197,168,114) tan  -> Foundations chain
#   (136,188,194) cyan -> Windows chain  (glass inpaint)
#   ( 95,114,199) blue -> Roof chain     (roof material inpaint)
#
# Important: ALL glass-like surfaces go to the Windows chain so balcony
# railings/pool water/etc. render as proper transparent glass instead of
# being darkened by the Roof chain prompt.
SEG_COLORS = {
    # walls + opaque architectural surfaces -> Walls chain (red)
    "wall":             (0.784, 0.427, 0.404, 1.0),  # v002-style coarse tag
    "travertine_white": (0.784, 0.427, 0.404, 1.0),
    "travertine_light": (0.784, 0.427, 0.404, 1.0),
    "concrete_board":   (0.784, 0.427, 0.404, 1.0),
    "concrete_light":   (0.784, 0.427, 0.404, 1.0),
    "concrete_dark":    (0.784, 0.427, 0.404, 1.0),
    # wood/foundation -> Foundations chain (tan)
    "wood_walnut":      (0.773, 0.659, 0.447, 1.0),
    # ALL glass + metal framing + water -> Windows chain (cyan)
    "window":           (0.533, 0.737, 0.761, 1.0),  # v002-style coarse tag
    "aluminum_dark":    (0.533, 0.737, 0.761, 1.0),
    "glass_clear":      (0.533, 0.737, 0.761, 1.0),
    "glass_tinted":     (0.533, 0.737, 0.761, 1.0),
    "glass_railing":    (0.533, 0.737, 0.761, 1.0),
    "water_blue":       (0.533, 0.737, 0.761, 1.0),
    # roof -> Roof chain (blue)
    "roof":             (0.373, 0.447, 0.780, 1.0),
    # terrain is intentionally absent — let the model infer ground from
    # context rather than route it through one of the building inpaint
    # chains. Tag terrain meshes with material='terrain' for organization.
}


# Which variations to actually save. Set the value to True to keep, False to
# skip. Skipped SaveImage nodes are removed from the prompt before submission.
#
# IMPORTANT: skipping a SaveImage does NOT skip its sampler when downstream
# stages need it. The workflow cascades: Make_Real -> Walls -> Windows -> Roof
# -> Environment -> Time_Of_Day. Each later stage requires all earlier
# samplers to run. So skipping Walls/Windows/Roof SaveImages just hides their
# intermediate outputs while the material-change passes still execute and
# feed Environment + Time_Of_Day.
#
# The user wants only 3 saved outputs: the final material-cascade result
# (renamed "Make_Real"), Environment, and Time_Of_Day.
SAVE_VARIATIONS = {
    "Make_Real":          False,  # original 1108 - only photoreal, no materials yet
    "Change_Walls":       False,  # intermediate cascade stage
    "CHange_Windows":     False,  # intermediate cascade stage
    "Change_Roof":        True,   # LAST material pass - RENAMED to "Make_Real" below
    "Change_Environment": True,   # SoCal coastal cliff
    "Time_Of_Day":        True,   # same cliff at dusk
}

# At submit time, rename the filename_prefix of certain SaveImage nodes so
# the output files end up with a more intuitive label in the output folder.
# Source name -> new label.
RENAME_VARIATIONS = {
    "Change_Roof": "Make_Real",  # the final material-cascade output IS "make real"
}

# Structural reference for the Make_Real pass: DepthAnything depth map (True,
# constrains 3D VOLUME - good for exterior, stops invented masses/terrain) vs
# lineart (False, edges only). Set PER MODE: depth helped the exterior, but the
# good interior render was made on lineart, so the interior stays on lineart.
USE_DEPTH_STRUCTURE_EXTERIOR = True
USE_DEPTH_STRUCTURE_INTERIOR = False

PROMPTS = {
    # 1124 - Initial photoreal pass. Just photorealism + lock camera; the
    # material specifics happen in 1125/1126/1127 stages where the seg mask
    # tells the inpainter which surfaces are walls vs windows vs roof.
    "1124": (
        "Transform the image into a photoreal architectural photograph of a "
        "modern house. Sharp detail, high resolution. "
        "Keep the materials exactly as shown in the input - do not change surface "
        "materials and do not invent extra structures, decks, fences, or decorations. "
        "Outdoor decks, patios, and the ground around the pool are smooth pale "
        "concrete or stone paving, never wood - do not extend the wood wall "
        "cladding onto the deck or ground. "
        "Preserve the structure exactly: keep every wall, floor slab, railing and "
        "deck edge as in the input; do not move, remove, open, or invent walls. "
        "Same camera angle and framing as input."
    ),
    # 1125 - Walls. Vertical wood paneling, warm modern cabin architecture.
    # Matches the reference image style: clear wood plank texture, warm but
    # natural tones (not too dark walnut, not too light blonde).
    # 1125 -> CLIPTextEncode 997 -> Walls sampler 1000 (correctly wired).
    "1125": "Vertical wood paneling. Warm modern wood cabin architecture.",
    # IMPORTANT: the workflow has its window/roof wires CROSSED. Text Multiline
    # 1126 (labeled "WIndows" in Blender) actually feeds the ROOF cascade
    # sampler (1056), and 1127 ("Roof") feeds the WINDOWS cascade sampler
    # (1031). So we put roof text in 1126 and windows text in 1127 to
    # compensate. The OUTPUT file kept and renamed to "Make_Real" is the
    # cascade result AFTER walls -> windows -> roof.
    # 1126 -> CLIPTextEncode 1069 -> Roof sampler 1056 (despite the label).
    # User wants subtle, not flashy.
    "1126": "Flat dark slate roof, matte finish",
    # 1127 -> CLIPTextEncode 1044 -> Windows sampler 1031 (despite the label).
    # Tinted glass that still reads as glass (subtle reflections OK),
    # not pure-opaque-black which makes windows look like solid panels.
    "1127": "Dark tinted glass windows - smoky charcoal-gray tint, clearly darkened glass, subtle reflections, NOT clear or transparent",
    # 1128 - Environment. Composition anchor + STRONG isolation + explicit
    # preservation of the building's outdoor structures so the cliff doesn't
    # eat the deck and pool. ALSO establishes interior furniture/character;
    # Time_Of_Day downstream just preserves whatever this pass produces.
    "1128": (
        "The building is the only structure in the scene. "
        "Remote uninhabited Southern California coastal cliff in the Santa Barbara area. "
        "No other buildings, no houses, no roads, no streets, no human construction anywhere. "
        "The building stays in the exact same position, scale, and framing as input. "
        "Keep any deck, terrace, pool, or patio that is visible in the input exactly as rendered; "
        "do NOT add or invent a pool, deck, terrace, or patio that is not already visible in the frame. "
        "Any deck, patio, or pool surround is smooth pale concrete or stone paving, never wood. "
        "Do not invent extra structures, railings, fences, or decorative details. "
        "The building's structure is FIXED and takes priority over everything else: keep every "
        "wall, floor slab, railing and the deck's exact edges as in the input - do not move, "
        "remove, open up, or add walls. Do not extend the building or deck with extra terrain, "
        "rock, or planting; the deck's outer edges stay exactly as in the input and the cliff "
        "drops away beyond them. The deck and pool surround stay pale concrete or stone even "
        "though the walls are wood - never extend wood cladding onto the deck or ground. "
        "The floor-to-ceiling windows are dark tinted glass - smoky charcoal, clearly darkened, "
        "NOT clear - with soft reflections of the sky and cliffs; only faint hints of simple "
        "furniture show through. Any interior furniture stays WITHIN the existing rooms - never "
        "alter a wall to make room for it. No people. "
        "Replace only the sky, the cliff face, the ocean, and the ground beyond the building's footprint. "
        "The pool is an infinity pool whose open overflow (infinity) edge faces the view, parallel "
        "to the pool's long side; the house sits on a cliff above a rugged coastline. "
        "Beyond the pool, show a dramatic Southern California cliff COASTLINE - sandstone cliffs, "
        "headlands and coves curving away into the distance with the sea between them. Show MORE "
        "rugged coast and cliffs than open flat ocean; the horizon sits high so the coastline fills "
        "the background. Native coastal shrubs on the cliffs. "
        "Blue sky, daytime, photoreal architectural photography."
    ),
    # 1129 - Time of Day. Strict preservation of the environment image - same
    # composition, same building, same interior furniture, same deck/pool/cliff/ocean.
    # The ONLY thing that changes is the lighting and sky to indicate dusk.
    "1129": (
        "Identical scene to the previous environment image. "
        "Same building, same interior furniture seen through the windows, "
        "same cliffs, the same rugged coastline and sea beyond the pool, "
        "same camera angle, same framing, and whatever deck/terrace/pool was "
        "visible stays exactly the same. "
        "Keep every wall, deck edge and the whole structure exactly as the previous image. "
        "Do not move or remove anything; do not add new objects, and do not invent a pool or deck. "
        "The ONLY change is the time of day: shift to early dusk - a calm deep-blue evening sky "
        "with a few early stars and soft fading light on the coastline and sea. No bright sunset, "
        "no orange glow. "
        "Warm interior lights now visible through the glass walls, with gentle architectural exterior "
        "lighting only on the deck or terrace areas that are already visible in the frame. "
        "Photoreal architectural photography."
    ),
}

# When True, submit() uses PROMPTS_INTERIOR instead of PROMPTS and labels the
# outputs "Interior_...". The interior operator sets this before calling submit.
INTERIOR_MODE = False

# Interior shot: camera is INSIDE the house looking OUT through the glass at the
# cliff. Same node IDs / cascade as PROMPTS, but framed for an interior view.
# Node wiring reminder (same crossed window/roof as exterior):
#   1124 initial photoreal | 1125 walls | 1126 -> roof sampler | 1127 -> windows
#   1128 environment (what's seen THROUGH the glass) | 1129 time of day
PROMPTS_INTERIOR = {
    "1124": (
        "Photoreal modern open-plan interior, warm wood and white with soft-gray accent "
        "walls, soft natural daylight. Keep the architecture and camera exactly as input. "
        "Same camera angle and framing as input."
    ),
    "1125": "Warm wood-slat feature walls and smooth white and soft-gray plaster.",
    # 1126 feeds the ceiling sampler (crossed wiring): keep it a clean ceiling.
    "1126": "Smooth white ceiling, soft recessed lighting.",
    # 1127 feeds the windows sampler: clear glass with plain soft daylight (NOT a cliff).
    "1127": "Clear glass with soft bright daylight outside.",
    # 1128 = furnish the room to MATCH the reference: kitchen at the back, dining
    # table centered with rug under it, sideboard with art+vase on the side wall,
    # pendant cluster over the table + one over the kitchen. Keep the building's
    # stairs/walls/windows from the input; only ADD furniture. No outdoor scenery.
    "1128": (
        "Photoreal warm minimalist open-plan interior. Keep the architecture exactly as in "
        "the input - same floating wood staircase, wood-slat walls, windows, ceiling and "
        "camera angle - and ONLY add furniture to match this layout: a kitchen along the "
        "back wall with light wood cabinets and a white stone island; a long light-oak "
        "dining table centered in the room with light wood dining chairs around it; a soft "
        "neutral striped rug under the dining table; a low wood sideboard against the side "
        "wall holding a framed artwork and a vase with a few green stems; a cluster of "
        "pendant lamps over the dining table and one pendant over the kitchen island. "
        "Light oak floor, calm and uncluttered, no people. All furniture stays indoors; "
        "nothing beyond the glass but soft daylight. Same camera angle and framing as input."
    ),
    # 1129 = same furnished room, only the light changes. Still no outdoor scenery.
    "1129": (
        "Identical furnished interior to the previous image - same kitchen, dining table, "
        "rug, sideboard, staircase, walls, windows and pendant lights, same camera and "
        "framing. Only the light shifts to a soft warm glow. Add nothing new; nothing "
        "beyond the glass but soft daylight."
    ),
}


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


def render_seg():
    scene = bpy.context.scene
    # Capture EVERY setting we touch BEFORE changing anything, so the finally
    # block can always restore them even if the render raises. Otherwise a
    # failed render leaves the building wearing the flat seg materials and the
    # view transform stuck on 'Raw' - which corrupts the user's viewport.
    orig_engine     = scene.render.engine
    orig_vt         = scene.view_settings.view_transform
    orig_look       = scene.view_settings.look
    orig_pct        = scene.render.resolution_percentage
    orig_exposure   = scene.view_settings.exposure
    orig_gamma      = scene.view_settings.gamma
    orig_use_nodes  = scene.use_nodes
    orig_film       = scene.render.film_transparent
    originals = {}
    try:
        for obj in bpy.data.objects:
            if obj.type != 'MESH': continue
            tag = obj.get("material", "")
            if tag not in SEG_COLORS: continue
            if not obj.data.materials: obj.data.materials.append(None)
            originals[obj.name] = obj.data.materials[0]
            obj.data.materials[0] = _make_seg_mat(tag, SEG_COLORS[tag])

        render_w, render_h = _render_size()
        scene.render.engine = "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        # Seg colors must land on the EXACT MaskFromColor hex. 'Raw' writes
        # scene-linear values straight to 8-bit (no sRGB curve), so exposure/
        # gamma must be neutral - a +1 stop (x2 gain) was pushing walls
        # 200->255 and roof 199->255, breaking the color->mask match.
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        scene.use_nodes = False
        scene.render.resolution_percentage = 100
        scene.render.filepath = str(COMFY_INPUT / SEG_FILE)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode  = "RGBA"
        scene.render.film_transparent = True
        bpy.ops.render.render(write_still=True)
        kb = os.path.getsize(COMFY_INPUT / SEG_FILE) // 1024
        print(f"[AEC] Seg saved ({render_w}x{render_h}, {kb} KB)")
    finally:
        # ALWAYS restore - even if the render raised - so the viewport is never
        # left showing the flat seg materials or the Raw view transform.
        for obj in bpy.data.objects:
            if obj.name in originals and obj.data.materials:
                obj.data.materials[0] = originals[obj.name]
        scene.render.engine = orig_engine
        scene.view_settings.view_transform = orig_vt
        scene.view_settings.look = orig_look
        scene.view_settings.exposure = orig_exposure
        scene.view_settings.gamma = orig_gamma
        scene.render.resolution_percentage = orig_pct
        scene.use_nodes = orig_use_nodes
        scene.render.film_transparent = orig_film


def render_beauty():
    scene = bpy.context.scene
    orig_samples = scene.cycles.samples
    orig_pct = scene.render.resolution_percentage
    render_w, render_h = _render_size()
    # Defensive: always restore view transform to AgX/Standard before Beauty.
    # If a previous Seg render crashed before restoring, view_transform could
    # be stuck on 'Raw' which blows the HDRI sky out to pure white and gives
    # the model nothing to extrapolate from -> "building floating in space".
    try:
        scene.view_settings.view_transform = 'AgX'
        try: scene.view_settings.look = 'AgX - Base Contrast'
        except Exception: scene.view_settings.look = 'None'
    except Exception:
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = BEAUTY_SAMPLES
    scene.cycles.use_denoising = True
    scene.use_nodes = False
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(COMFY_INPUT / RGB_FILE)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode  = "RGB"
    scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)
    scene.cycles.samples = orig_samples
    scene.render.resolution_percentage = orig_pct
    kb = os.path.getsize(COMFY_INPUT / RGB_FILE) // 1024
    print(f"[AEC] Beauty saved ({render_w}x{render_h}, {kb} KB)")


def _serialize_local_tree():
    """Serialize the AEC workflow directly from the loaded .blend's
    CFNodeTree. This is the most reliable source: it's always our workflow,
    independent of whatever the user has open in their ComfyUI browser tab.
    Returns the prompt dict in the same {node_id: {class_type, inputs}} shape
    that /history would return.
    """
    try:
        tree = bpy.data.node_groups.get("ComfyUI Node")
    except Exception:
        return None
    if not tree or tree.bl_idname != "CFNodeTree" or len(tree.nodes) == 0:
        return None
    try:
        raw = tree.serialize()
    except Exception as e:
        print(f"[AEC] local tree.serialize() failed: {e}")
        return None
    if not raw:
        return None

    # The addon's serialize() returns each item as either a dict OR a tuple
    # whose first element is the node dict (the tuple carries extra metadata
    # the addon uses internally). ComfyUI's /prompt endpoint and our downstream
    # code expect the {node_id: {class_type, inputs}} dict shape, so unwrap.
    prompt = {}
    for nid, ndata in raw.items():
        if isinstance(ndata, tuple):
            prompt[str(nid)] = ndata[0]
        else:
            prompt[str(nid)] = ndata

    tree_node_ids = set(prompt.keys())
    missing = [pid for pid in PROMPTS.keys() if pid not in tree_node_ids]
    if missing:
        print(f"[AEC] WARN: local tree is missing AEC prompt nodes {missing}")
        print("       (tree may be partially loaded; prompts for those IDs will be no-ops)")
    return prompt


def get_best_prompt():
    """
    Pick the AEC workflow to submit. Order of preference (REVERSED in v17+
    after we discovered the Blender addon's load_json_ex consistently drops
    ~12 links from the 236-link AEC workflow, including critical
    SimpleInpaintStitch composite connections that route inpainted wall/
    window/roof results back into the cascade chain):

      1. The most recent successful AEC-matching prompt in ComfyUI history
         (236 links, all inpaint stitching intact — what v003 used).
      2. The local CFNodeTree as fallback (works for environment+time of day
         but the wall/window/roof material cascades fail silently because
         their stitch links are missing).

    To use option 1: queue AEC_Transform_Pipeline.json from the ComfyUI
    browser ONCE — the resulting history entry has the full workflow with
    all links. Subsequent Render+Submit clicks reuse it.
    """
    try:
        r = requests.get(f"{COMFY_URL}/history?max_items=50", timeout=5)
        entries = []
        for pid, data in r.json().items():
            if data.get("status", {}).get("status_str") != "success": continue
            p = data.get("prompt", [])
            if len(p) < 3: continue
            entries.append((int(p[0]) if isinstance(p[0], int) else 0, p[2], data))
        entries.sort(key=lambda x: x[0], reverse=True)

        aec_keys = set(PROMPTS.keys())
        for prompt_idx, prompt_dict, data in entries:
            if aec_keys.issubset(prompt_dict.keys()):
                img_count = sum(len(v.get("images", [])) for v in data.get("outputs", {}).values())
                print(f"[AEC] Using AEC prompt #{prompt_idx} from ComfyUI history (full 236-link workflow, {img_count} prior outputs)")
                return prompt_dict
    except Exception as e:
        print(f"[AEC] Cannot reach ComfyUI history at {COMFY_URL}: {e}")

    # Fallback A: the last workflow we successfully submitted (dumped to disk on
    # every submit). It carries the full link set, just like a history entry,
    # and survives ComfyUI history rotation / restarts - so submitting no longer
    # breaks just because other workflows (HuliJing, etc.) ran in between.
    #
    # Lives under AEC_ROOT (not a hardcoded per-user path) so this package stays
    # portable across machines/usernames. A verified copy ships with the package
    # so the fallback works even before anyone has run submit() on a new machine.
    try:
        _dump = str(AEC_ROOT / "comfyui" / "workflows" / "AEC_last_submitted_workflow.json")
        if os.path.exists(_dump):
            with open(_dump, "r", encoding="utf-8") as _f:
                _d = json.load(_f)
            if isinstance(_d, dict) and set(PROMPTS.keys()).issubset(_d.keys()):
                print(f"[AEC] No AEC entry in ComfyUI history; using last-submitted "
                      f"workflow dump ({len(_d)} nodes, full links).")
                return _d
    except Exception as e:
        print(f"[AEC] last-submitted dump fallback failed: {e}")

    # Fallback B: local tree (may have missing links)
    local = _serialize_local_tree()
    if local:
        print(f"[AEC] WARN: no AEC entry in ComfyUI history; falling back to local CFNodeTree ({len(local)} nodes).")
        print(f"       This may miss ~12 stitching links — wall/window/roof cascades may not work.")
        print(f"       To fix: open http://127.0.0.1:8188 in your browser, load AEC_Transform_Pipeline,")
        print(f"       click Queue once to create a proper history entry, then try again.")
        return local

    print("[AEC] No workflow source available. Cannot submit.")
    return None


def submit(render=True):
    if render:
        print("[AEC] Rendering seg pass...")
        render_seg()
        print("[AEC] Rendering beauty pass...")
        render_beauty()

    prompt = get_best_prompt()
    if not prompt:
        return False

    # Override resolution-dependent widgets so the cascade samples at our
    # RENDER_WIDTH x RENDER_HEIGHT (instead of the hardcoded 1024x1024 the
    # workflow ships with). Two node types carry resolution widgets:
    #   - EmptyFlux2LatentImage : [width, height, batch_size]
    #   - Flux2Scheduler        : [steps, width, height]
    render_w, render_h = _render_size()
    res_patched = {"empty_latent": 0, "scheduler": 0}
    for nid, node in prompt.items():
        ct = node.get("class_type", "")
        inputs = node.setdefault("inputs", {})
        if ct == "EmptyFlux2LatentImage":
            # Only override if the value is currently a widget (scalar).
            # Connected inputs (lists) are computed from GetImageSize -> leave alone.
            if not isinstance(inputs.get("width"),  list): inputs["width"]  = render_w
            if not isinstance(inputs.get("height"), list): inputs["height"] = render_h
            inputs.setdefault("batch_size", 1)
            res_patched["empty_latent"] += 1
        elif ct == "Flux2Scheduler":
            if not isinstance(inputs.get("width"),  list): inputs["width"]  = render_w
            if not isinstance(inputs.get("height"), list): inputs["height"] = render_h
            # steps widget stays untouched - cascade depends on it being 4 / 8
            res_patched["scheduler"] += 1
    print(f"[AEC] Resolution patched: {res_patched['empty_latent']} EmptyFlux2Latent + "
          f"{res_patched['scheduler']} Flux2Scheduler -> {render_w}x{render_h}")

    # Per-node-type fixups. These exact same patches live in auto_comfy.py's
    # push_task hook, but that hook only fires for the addon's Execute button.
    # The AEC Render+Submit button posts directly to /prompt and bypasses the
    # addon, so without these patches ComfyUI rejects the workflow with
    # validation errors on OllamaConnectivityV2 / ResizeImageMaskNode.
    patched = {"resize": 0, "removed_ollama": 0, "removed_debug": 0, "cond": 0, "paths": 0, "crop": 0}

    # Remove the Ollama auto-caption branch entirely. It is bypassed in the
    # graph and only feeds a PreviewAny, so it does nothing for our pipeline -
    # and the user does not want it. Strip the Ollama nodes plus anything
    # downstream of them so no dangling input references remain.
    ollama_ids = {nid for nid, nd in prompt.items()
                  if "Ollama" in nd.get("class_type", "")}
    dead = set(ollama_ids)
    for _ in range(6):
        for nid, nd in prompt.items():
            for v in nd.get("inputs", {}).values():
                if isinstance(v, list) and len(v) == 2 and str(v[0]) in dead:
                    dead.add(nid)
    for nid in list(dead):
        if prompt.pop(nid, None) is not None:
            patched["removed_ollama"] += 1

    # Browser-only preview/comparison outputs create extra validation roots.
    # Production submission keeps only SaveImage outputs.
    for nid in list(prompt):
        if prompt[nid].get("class_type") in {"PreviewImage", "Image Comparer (rgthree)"}:
            del prompt[nid]
            patched["removed_debug"] += 1

    for nid, node in prompt.items():
        ct = node.get("class_type", "")
        inputs = node.setdefault("inputs", {})
        for key in ("unet_name", "clip_name", "vae_name", "ckpt_name"):
            value = inputs.get(key)
            if isinstance(value, str) and "\\" in value:
                inputs[key] = value.replace("\\", "/")
                patched["paths"] += 1
        if ct == "SimpleInpaintCrop":
            inputs.setdefault("blur", False)
            patched["crop"] += 1
        if ct == "ConditioningAverage":
            # Weight the lineart structure reference much harder so the output
            # sticks to the building's geometry. Was 0.10 (10% structure, 90%
            # text) which let walls drift; 0.75 = 75% lineart structure.
            inputs["conditioning_to_strength"] = 0.75
            patched["cond"] += 1
        elif ct == "ResizeImageMaskNode":
            # The widget format is the dropdown selection PLUS sidecar keys
            # (resize_type.match, resize_type.width, resize_type.height,
            # resize_type.crop). When the addon serializes a wired connection
            # for resize_type, it leaves the dropdown value as a [node_id,
            # slot] list, which ComfyUI then can't interpret -> the node's
            # tensor-shape check fails with "too many indices for tensor of
            # dimension 4".
            rt = inputs.get("resize_type")
            if isinstance(rt, list):
                inputs["resize_type.match"] = rt
                inputs["resize_type"] = "match size"
                inputs.setdefault("resize_type.crop", "center")
                patched["resize"] += 1
            elif rt is None:
                inputs["resize_type"] = "scale dimensions"
                inputs["resize_type.width"] = 512
                inputs["resize_type.height"] = 512
                inputs.setdefault("resize_type.crop", "center")
                patched["resize"] += 1
    if any(patched.values()):
        print(f"[AEC] Patched: removed Ollama={patched['removed_ollama']}, "
              f"removed debug={patched['removed_debug']}, model paths={patched['paths']}, "
              f"SimpleInpaintCrop={patched['crop']}, ResizeImageMask={patched['resize']}, "
              f"ConditioningAverage->0.75={patched['cond']}")

    for node in prompt.values():
        if (
            node.get("class_type") == "SaveImage"
            and node.get("inputs", {}).get("images") == ["1113", 0]
        ):
            node["inputs"]["filename_prefix"] = "Change_Roof"

    has_make_real = any(
        node.get("class_type") == "SaveImage"
        and any(tag in str(node.get("inputs", {}).get("filename_prefix", ""))
                for tag in ("Change_Roof", "Make_Real"))
        for node in prompt.values()
    )
    if SAVE_VARIATIONS.get("Change_Roof") and "1113" in prompt and not has_make_real:
        prompt["1210"] = {"class_type": "SaveImage", "inputs": {"images": ["1113", 0], "filename_prefix": "Change_Roof"}}
        print("[AEC] Restored missing Make Real SaveImage from final material cascade")

    # Drop SaveImage nodes for variations the user disabled in SAVE_VARIATIONS.
    # Also apply RENAME_VARIATIONS so the kept SaveImage gets a friendlier
    # filename_prefix. The prefix may be a string widget OR a wired connection
    # from an upstream String/Text node -- in the wired case we walk upstream
    # and modify the source node's string.
    dropped = []
    kept_saves = []
    for nid in list(prompt.keys()):
        node = prompt[nid]
        if node.get("class_type") != "SaveImage":
            continue
        inputs = node.get("inputs", {})
        fp = inputs.get("filename_prefix", "")
        fp_str = fp if isinstance(fp, str) else ""
        src_for_rename = None
        if not fp_str and isinstance(fp, list) and len(fp) == 2:
            src_for_rename = prompt.get(str(fp[0]))
            if src_for_rename:
                sinp = src_for_rename.get("inputs", {})
                fp_str = sinp.get("string", sinp.get("text", "")) or ""

        # Match against the configured variation tags
        matched_tag = None
        kept = True
        for tag, enabled in SAVE_VARIATIONS.items():
            if tag and tag in fp_str:
                matched_tag = tag
                kept = enabled
                break

        if not kept:
            dropped.append(f"{matched_tag or fp_str}({nid})")
            del prompt[nid]
            continue

        # Kept -- apply rename if configured
        if matched_tag and matched_tag in RENAME_VARIATIONS:
            new_label = RENAME_VARIATIONS[matched_tag]
            new_fp = fp_str.replace(matched_tag, new_label) if matched_tag in fp_str else new_label
            if isinstance(fp, str):
                inputs["filename_prefix"] = new_fp
            elif src_for_rename:
                sinp = src_for_rename.get("inputs", {})
                if "string" in sinp: sinp["string"] = new_fp
                elif "text" in sinp: sinp["text"] = new_fp
            kept_saves.append(f"{matched_tag}->{new_label}({nid})")
        else:
            kept_saves.append(f"{matched_tag or fp_str}({nid})")

    if dropped:
        print(f"[AEC] Dropped SaveImages: {', '.join(dropped)}")
    if kept_saves:
        print(f"[AEC] Keeping SaveImages: {', '.join(kept_saves)}")

    # Swap image files. STRUCTURAL identification — find which LoadImage
    # feeds the MaskFromColor nodes (transitively, through reroutes / image
    # processors). That LoadImage gets the seg file; everything else gets
    # the beauty file.
    #
    # Previous filename-matching heuristic ("seg" in img.lower()) failed
    # because the addon's serialize() sometimes returns a Blender datablock
    # name instead of the file name, so the SAM LoadImage's image field
    # didn't contain "seg" at submit time -> all three LoadImages ended up
    # set to beauty_input.png -> MaskFromColor extracted from beauty image
    # -> empty masks -> walls/windows/roof cascades did nothing.
    def _trace_image_source(start_id, max_depth=10):
        """BFS backwards from a node id, following any list-valued inputs,
        until we hit a LoadImage. Returns its node id, or None."""
        visited = set()
        queue = [str(start_id)]
        while queue and len(visited) < 50:
            nid = queue.pop(0)
            if nid in visited: continue
            visited.add(nid)
            node = prompt.get(nid)
            if not node: continue
            if node.get("class_type") == "LoadImage":
                return nid
            for inp_val in node.get("inputs", {}).values():
                if isinstance(inp_val, list) and len(inp_val) == 2:
                    queue.append(str(inp_val[0]))
        return None

    seg_loadimage_ids = set()
    for nid, node in prompt.items():
        if "MaskFromColor" not in node.get("class_type", ""):
            continue
        img_inp = node.get("inputs", {}).get("image")
        if isinstance(img_inp, list) and len(img_inp) == 2:
            src = _trace_image_source(img_inp[0])
            if src:
                seg_loadimage_ids.add(src)
        elif isinstance(img_inp, str):
            # Some workflows might have MaskFromColor.image as a widget
            pass

    swapped_seg = swapped_rgb = 0
    for nid, node in prompt.items():
        if node.get("class_type") != "LoadImage":
            continue
        if nid in seg_loadimage_ids:
            node["inputs"]["image"] = SEG_FILE
            swapped_seg += 1
        else:
            node["inputs"]["image"] = RGB_FILE
            swapped_rgb += 1
    print(f"[AEC] LoadImage swap: {swapped_seg} -> {SEG_FILE}, {swapped_rgb} -> {RGB_FILE}")
    if swapped_seg == 0:
        print(f"[AEC] WARN: no LoadImage was identified as the seg-mask source!")
        print(f"       The MaskFromColor nodes won't receive the seg image,")
        print(f"       so walls/windows/roof cascades will get empty masks and do nothing.")

    # Optionally route the STRUCTURAL reference through DepthAnything (1165)
    # instead of lineart (1184). Lineart only constrains edges, so flat areas
    # (decks, ground, sky) let the model invent extra masses; depth constrains
    # the overall 3D volume and holds the building's form much better. The depth
    # node is normally disconnected, so feed it the same beauty image the
    # lineart used, then point the resize/reference node (1206) at depth.
    use_depth = USE_DEPTH_STRUCTURE_INTERIOR if INTERIOR_MODE else USE_DEPTH_STRUCTURE_EXTERIOR
    if "1206" in prompt:
        if use_depth and "1165" in prompt:
            li_src = prompt.get("1184", {}).get("inputs", {}).get("image")
            if li_src is not None:
                prompt["1165"].setdefault("inputs", {})["image"] = li_src
            prompt["1206"]["inputs"]["input"] = ["1165", 0]
            print("[AEC] Structural reference: DEPTH (DepthAnything)")
        else:
            # Explicitly route the reference back to lineart (1184) so a base
            # workflow wired to depth (e.g. a reused history/dump made in depth
            # mode) does not stay stuck on depth.
            prompt["1206"]["inputs"]["input"] = ["1184", 0]
            print("[AEC] Structural reference: lineart")

    # Update text prompts by node ID (interior set when INTERIOR_MODE is on)
    active_prompts = PROMPTS_INTERIOR if INTERIOR_MODE else PROMPTS
    print(f"[AEC] prompt set: {'INTERIOR' if INTERIOR_MODE else 'EXTERIOR'}")
    for nid, text in active_prompts.items():
        if nid in prompt:
            inp = prompt[nid].get("inputs", {})
            if "string" in inp: inp["string"] = text
            elif "text"  in inp: inp["text"]   = text
            print(f"[AEC] Updated prompt node {nid}")

    # Randomize seeds (force fresh outputs even if inputs/prompts cached) and
    # tag every SaveImage with a Comfy_<timestamp>_ batch prefix so all files
    # from one submission cluster together when sorted in the output folder.
    batch_id = time.strftime("%Y%m%d_%H%M%S")
    mode_tag = "Interior_" if INTERIOR_MODE else ""
    seed_count = 0; si_count = 0; si_via_upstream = 0; si_skipped_wired = 0
    for nid, node in prompt.items():
        inputs = node.get("inputs", {})
        if "noise_seed" in inputs:
            inputs["noise_seed"] = random.randint(0, 2**31 - 1); seed_count += 1
        elif "seed" in inputs:
            inputs["seed"] = random.randint(0, 2**31 - 1); seed_count += 1
        if node.get("class_type") == "SaveImage" and "filename_prefix" in inputs:
            fp = inputs["filename_prefix"]
            if isinstance(fp, str):
                original = fp.split("/")[-1]
                parts = original.split("_", 3)
                if len(parts) == 4 and parts[0] == "Comfy": original = parts[3]
                # Strip accumulated mode tags so "Interior_" doesn't pile up on
                # every submit (it was overflowing the 260-char Windows path
                # limit, which silently broke the Blender image-editor load).
                while original.startswith("Interior_"): original = original[9:]
                while original.startswith("Exterior_"): original = original[9:]
                inputs["filename_prefix"] = f"Comfy_{batch_id}_{mode_tag}{original}"
                si_count += 1
            elif isinstance(fp, list) and len(fp) == 2:
                src = prompt.get(str(fp[0]))
                if src:
                    sinp = src.get("inputs", {})
                    wk = next((k for k in ("string","text","value","Text","String")
                               if k in sinp and isinstance(sinp[k], str)), None)
                    if wk:
                        original = sinp[wk].split("/")[-1]
                        parts = original.split("_", 3)
                        if len(parts) == 4 and parts[0] == "Comfy": original = parts[3]
                        while original.startswith("Interior_"): original = original[9:]
                        while original.startswith("Exterior_"): original = original[9:]
                        sinp[wk] = f"Comfy_{batch_id}_{mode_tag}{original}"
                        si_via_upstream += 1
                    else: si_skipped_wired += 1
                else: si_skipped_wired += 1
    summary = f"[AEC] Randomized {seed_count} seeds; prefixed {si_count} SaveImage outputs with Comfy_{batch_id}_"
    if si_via_upstream:  summary += f"; updated {si_via_upstream} upstream String nodes"
    if si_skipped_wired: summary += f"; SKIPPED {si_skipped_wired} wired SaveImages"
    print(summary)

    payload = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    # Dump the EXACT workflow being submitted - AFTER all Python patches
    # (injected PROMPTS, pruned SaveImages per SAVE_VARIATIONS, patched
    # resolution, swapped LoadImage inputs). This is the real graph ComfyUI
    # runs, in API/prompt format, so it can be inspected or loaded.
    try:
        _dump = str(AEC_ROOT / "comfyui" / "workflows" / "AEC_last_submitted_workflow.json")
        with open(_dump, "w", encoding="utf-8") as _f:
            json.dump(prompt, _f, indent=2)
        print(f"[AEC] Dumped submitted workflow -> {_dump}")
    except Exception as _e:
        print(f"[AEC] workflow dump failed: {_e}")
    resp = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=10)
    print(f"[AEC] POST -> {resp.status_code}")
    if resp.status_code == 200:
        pid = resp.json().get("prompt_id", "?")
        print(f"[AEC] Queued: {pid}")
        print(f"[AEC] Watch output at: {COMFY_URL}")
        return True
    print(f"[AEC] Error: {resp.text[:300]}")
    return False

print("[AEC] submit_comfyui.py loaded. Call submit() to render and queue.")
print(f"[AEC] ComfyUI: {COMFY_URL}  |  Input: {COMFY_INPUT}")
