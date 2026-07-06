"""List workspaces + screen layouts in v17.blend so we know which to copy."""
import bpy

print(f"workspaces in v17: {len(bpy.data.workspaces)}")
for ws in bpy.data.workspaces:
    print(f"  ws '{ws.name}'  screens={len(ws.screens)}")
    for sc in ws.screens:
        n_areas = len(sc.areas)
        types = [a.type for a in sc.areas]
        print(f"    screen '{sc.name}'  areas={n_areas}  types={types}")

# Note the active one if any (only meaningful in interactive Blender)
print()
print(f"window manager open windows (background mode has 0): {len(bpy.context.window_manager.windows)}")
