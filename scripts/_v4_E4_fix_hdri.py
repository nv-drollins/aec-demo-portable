"""E4: rebuild ArchWorld with a real HDRI env texture, load + pack it.
Keep Studio_Gray as the active (default) world; ArchWorld is the Alt+7 target."""
import bpy, os

V4 = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\sample_project\blender_assets\cliff_house_act2_textured_v4.blend"
HDRI = r"C:\Users\NVIDIA\Downloads\BlenderScene_with_Texture\Textures\citrus_orchard_road_puresky_4k.exr"
HDRI_FALLBACK = r"C:\Users\NVIDIA\Downloads\AEC_Demo_Portable\AEC_Demo_Portable\assets\hdri\kloppenheim_06_2k.hdr"

bpy.ops.wm.open_mainfile(filepath=V4)

path = HDRI if os.path.exists(HDRI) else HDRI_FALLBACK
img = bpy.data.images.load(path, check_existing=True)

w = bpy.data.worlds.get("ArchWorld")
if w is None:
    w = bpy.data.worlds.new("ArchWorld")
w.use_fake_user = True
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (600, 0)
bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (300, 0)
bg.inputs["Strength"].default_value = 1.0
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.location = (0, 0)
env.image = img
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-400, 0)
mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-200, 0)
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# Keep Studio_Gray active (default look); ArchWorld available via Alt+7.
studio = bpy.data.worlds.get("Studio_Gray")
if studio:
    bpy.context.scene.world = studio

# pack everything (orphan mp4 warning is harmless)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print(f"[E4] pack warn: {e}")

# verify
hdri_name = None
for n in w.node_tree.nodes:
    if n.type == "TEX_ENVIRONMENT" and n.image:
        hdri_name = n.image.name
packed = sum(1 for i in bpy.data.images if i.packed_file)
print(f"[E4] ArchWorld hdri = {hdri_name}  (packed images: {packed})")
print(f"[E4] active world = {bpy.context.scene.world.name}")

bpy.ops.wm.save_as_mainfile(filepath=V4, compress=True)
print(f"[E4] SAVED ({os.path.getsize(V4)/1024/1024:.1f} MB)")
print("[E4] DONE")
