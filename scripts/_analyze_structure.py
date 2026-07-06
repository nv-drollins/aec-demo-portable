import json
from collections import Counter

p = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\user_prompt\AEC_Transform_Pipeline.json"
wf = json.load(open(p, encoding="utf-8"))
nodes = {n["id"]: n for n in wf.get("nodes", [])}
links = {l[0]: l for l in wf.get("links", [])}  # id -> [id, from_node, from_slot, to_node, to_slot, type]

def src_of(node, input_name):
    """Return (type, id) of the node feeding `input_name` of `node`, or None."""
    for inp in node.get("inputs", []) or []:
        if inp.get("name") == input_name and inp.get("link") is not None:
            l = links.get(inp["link"])
            if l:
                fn = nodes.get(l[1])
                return (fn["type"] if fn else "?", l[1])
    return None

types = Counter(n.get("type", "?") for n in wf["nodes"])
print("=== FULL node-type histogram ===")
for t, c in types.most_common():
    print(f"  {c:3d}  {t}")

KEYS = ("ControlNet", "controlnet", "Depth", "depth", "Canny", "canny", "Line", "line",
        "MiDaS", "Zoe", "Union", "ReferenceLatent", "FluxGuidance", "InpaintModelConditioning")
print("\n=== structural / reference nodes present ===")
for n in wf["nodes"]:
    t = n.get("type", "")
    if any(k in t for k in KEYS):
        print(f"  id {n['id']:>5}  {t}")

def consumers(node_id):
    out = []
    for l in wf.get("links", []):
        if l[1] == node_id:
            tn = nodes.get(l[3])
            # find input name on target for slot l[4]
            nm = "?"
            if tn:
                ins = tn.get("inputs", []) or []
                if l[4] < len(ins):
                    nm = ins[l[4]].get("name", "?")
            out.append((tn["type"] if tn else "?", l[3], nm))
    return out

print("\n=== where do Depth (1165) and LineArt (1184) outputs go? ===")
for nid in (1165, 1184):
    print(f"  node {nid} -> {consumers(nid)}")

print("\n=== ReferenceLatent feeds (what image/latent each references) ===")
for n in wf["nodes"]:
    if n.get("type") != "ReferenceLatent":
        continue
    lat = src_of(n, "latent")
    cond = src_of(n, "conditioning")
    # trace latent -> if VAEEncode, what image?
    img = None
    if lat and lat[0] == "VAEEncode":
        img = src_of(nodes[lat[1]], "pixels")
    print(f"  refLatent {n['id']}: latent<-{lat} (img<-{img})")

print("\n=== how each Flux sampler gets structure ===")
for n in wf["nodes"]:
    if n.get("type") != "SamplerCustomAdvanced":
        continue
    lat = src_of(n, "latent_image")
    guider = src_of(n, "guider")
    print(f"  sampler {n['id']}: latent_image<-{lat}  guider<-{guider}")
    # follow guider -> its 'conditioning'/'positive' inputs one level
    if guider:
        gnode = nodes.get(guider[1])
        if gnode:
            for inp in gnode.get("inputs", []) or []:
                s = src_of(gnode, inp["name"])
                print(f"        guider.{inp['name']} <- {s}")
