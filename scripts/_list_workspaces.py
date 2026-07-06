import bpy
print(f"=== WORKSPACES in {bpy.data.filepath} ===")
for ws in bpy.data.workspaces:
    types = []
    for sc in ws.screens:
        for a in sc.areas:
            types.append(a.type)
    print(f"  '{ws.name}'  areas={sorted(set(types))}")
