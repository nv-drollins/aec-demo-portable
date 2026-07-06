"""Dump water/pool material shader settings so we can restore them."""
import bpy

for m in bpy.data.materials:
    if "water" in m.name.lower() or "pool" in m.name.lower():
        print(f"=== {m.name}  use_nodes={m.use_nodes} ===")
        if m.use_nodes and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for k in ("Base Color", "Metallic", "Roughness", "IOR", "Alpha",
                              "Transmission Weight", "Transmission"):
                        if k in n.inputs:
                            v = n.inputs[k].default_value
                            sv = tuple(round(x, 4) for x in v) if hasattr(v, "__len__") else round(v, 4)
                            print(f"  PRINCIPLED.{k} = {sv}")
                elif n.type in ("RGB", "EMISSION", "BSDF_GLASS", "VOLUME_ABSORPTION",
                                "VOLUME_SCATTER", "BSDF_TRANSPARENT", "MIX_SHADER"):
                    print(f"  node {n.type} '{n.name}':")
                    for inp in n.inputs:
                        try:
                            v = inp.default_value
                            sv = tuple(round(x, 4) for x in v) if hasattr(v, "__len__") else round(v, 4)
                            print(f"    {inp.name} = {sv}")
                        except Exception:
                            pass
        else:
            print(f"  diffuse_color = {tuple(round(x,4) for x in m.diffuse_color)}")
