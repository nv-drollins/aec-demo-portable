"""Structural audit of an AEC_Transform_Pipeline ComfyUI API JSON.

Reports adherence-relevant issues:
  1. Hardcoded resolution in EmptyFlux2LatentImage / Flux2Scheduler nodes.
  2. SaveImage filename vs. actual prompt-source mismatches.
  3. Orphan or unused nodes.
  4. Sampler initialization (empty latent vs encoded reference).
"""
import json
from collections import defaultdict

PATH = r"C:\Users\NVIDIA\Downloads\AEC_Transform_Pipeline_API.json"

with open(PATH, "r", encoding="utf-8") as f:
    g = json.load(f)


def t(n): return g[n]["_meta"].get("title", "")
def ct(n): return g[n]["class_type"]


print("=" * 78)
print("1) RESOLUTION-DEPENDENT NODES (hardcoded vs dynamic)")
print("=" * 78)
res_nodes = []
for nid, node in g.items():
    if ct(nid) in ("EmptyFlux2LatentImage", "Flux2Scheduler"):
        inp = node["inputs"]
        w = inp.get("width"); h = inp.get("height")
        w_s = f"{w}" if not isinstance(w, list) else f"<dyn:{w[0]}>"
        h_s = f"{h}" if not isinstance(h, list) else f"<dyn:{h[0]}>"
        res_nodes.append((nid, ct(nid), w_s, h_s))
        print(f"  node {nid:>4}  {ct(nid):<22}  width={w_s:<6}  height={h_s:<6}  title='{t(nid)}'")
hard_count = sum(1 for r in res_nodes if not r[2].startswith("<dyn"))
print(f"\n  TOTAL: {len(res_nodes)} resolution nodes, {hard_count} HARDCODED")
print("  IMPACT: if input image size != hardcoded value, reference-latent and")
print("          sample-latent dimensions disagree -> composition drifts.")

print()
print("=" * 78)
print("2) INPUT IMAGES")
print("=" * 78)
for nid, node in g.items():
    if ct(nid) == "LoadImage":
        print(f"  node {nid:>4}  filename='{node['inputs'].get('image')}'  title='{t(nid)}'")

print()
print("=" * 78)
print("3) SAMPLER MAP: empty-latent start + steps + conditioning ids")
print("=" * 78)
for nid, node in g.items():
    if ct(nid) != "SamplerCustomAdvanced": continue
    inp = node["inputs"]
    latent = inp.get("latent_image", [None])[0]
    guider = inp.get("guider", [None])[0]
    sigmas = inp.get("sigmas", [None])[0]
    steps  = g[sigmas]["inputs"].get("steps", "?") if sigmas in g else "?"
    latent_ct = ct(latent) if latent in g else "?"
    pos = g[guider]["inputs"].get("positive", [None])[0] if guider in g else None
    neg = g[guider]["inputs"].get("negative", [None])[0] if guider in g else None
    print(f"  sampler {nid:>4}  steps={steps:<3}  start_latent={latent} ({latent_ct})  pos_cond={pos}  neg_cond={neg}")

print()
print("=" * 78)
print("4) SAVEIMAGE -> upstream prompt trace (verifies filename matches intent)")
print("=" * 78)


def trace_back(start_nid, target_class, max_depth=12):
    visited = set(); queue = [(start_nid, 0)]
    while queue:
        nid, d = queue.pop(0)
        if nid in visited or d > max_depth: continue
        visited.add(nid)
        if nid not in g: continue
        if ct(nid) == target_class: return nid
        for v in g[nid]["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and v[0] in g:
                queue.append((v[0], d + 1))
    return None


for nid, node in g.items():
    if ct(nid) != "SaveImage": continue
    prefix = node["inputs"].get("filename_prefix", "")
    upstream_sampler = trace_back(nid, "SamplerCustomAdvanced")
    upstream_text_id = upstream_text_title = upstream_text_preview = "?"
    if upstream_sampler:
        gk = g[upstream_sampler]["inputs"].get("guider", [None])[0]
        pos = g[gk]["inputs"].get("positive", [None])[0]
        cur = pos; depth = 0
        while cur and depth < 12:
            if ct(cur) == "CLIPTextEncode":
                upstream_text_id = g[cur]["inputs"].get("text", [None])[0]
                upstream_text_title = t(upstream_text_id) if upstream_text_id in g else "?"
                upstream_text_preview = g[upstream_text_id]["inputs"].get("text", "")[:50] if upstream_text_id in g else ""
                break
            if cur in g:
                cnd = g[cur]["inputs"].get("conditioning", [None])
                if isinstance(cnd, list) and len(cnd) == 2:
                    cur = cnd[0]; depth += 1; continue
            break
    print(f"  save '{prefix:<20}'  sampler={upstream_sampler}  text_node={upstream_text_id} ('{upstream_text_title}')")
    print(f"      prompt='{upstream_text_preview}'")

print()
print("=" * 78)
print("5) ORPHAN NODES (built but never consumed downstream)")
print("=" * 78)
referenced = set()
for nid, node in g.items():
    for v in node["inputs"].values():
        if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
            referenced.add(v[0])
output_only = set(g.keys()) - referenced
# SaveImage is a leaf - normal output. Exclude.
output_only = {n for n in output_only if ct(n) != "SaveImage"}
for n in sorted(output_only):
    print(f"  orphan: {n}  ({ct(n)})  title='{t(n)}'")

print()
print("=" * 78)
print("6) DIAGNOSIS")
print("=" * 78)
print(f"  - {hard_count} hardcoded resolution inputs -> rewire to GetImageSize(input) for")
print(f"    automatic adherence to whatever resolution the source image is.")
print("  - Verify each SaveImage filename in section (4) matches the prompt title")
print("    listed alongside it. Mismatches indicate crossed wiring.")
print("  - Orphan nodes (5) are graph leftovers, safe to remove but not blocking.")
