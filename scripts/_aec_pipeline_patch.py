"""Apply two surgical fixes to AEC_Transform_Pipeline_API.json:

  Fix 1 - rewire 12 hardcoded 1600x992 inputs to GetImageSize(node 26) outputs
          so the sampler resolution always tracks the input image.
  Fix 2 - swap filename_prefix between 1112 (Windows save) and 1114 (Roof save)
          so each saved file matches the prompt that actually generated it.

Reads:  C:\\Users\\NVIDIA\\Downloads\\AEC_Transform_Pipeline_API.json
Writes: C:\\Users\\NVIDIA\\Downloads\\AEC_Transform_Pipeline_API_v2.json
"""
import json
import os
import shutil

SRC = r"C:\Users\NVIDIA\Downloads\AEC_Transform_Pipeline_API.json"
DST = r"C:\Users\NVIDIA\Downloads\AEC_Transform_Pipeline_API_v2.json"

# 6 EmptyFlux2LatentImage + 6 Flux2Scheduler nodes that hardcode 1600x992.
RES_NODES = ["943", "946", "966", "968", "1007", "1009",
             "1036", "1043", "1061", "1068", "1097", "1098"]

# GetImageSize node 26 is already in the graph, taking image from node 1 (Beauty).
# Its outputs are: 0 = width (INT), 1 = height (INT).
WIDTH_LINK  = ["26", 0]
HEIGHT_LINK = ["26", 1]

with open(SRC, "r", encoding="utf-8") as f:
    g = json.load(f)

assert "26" in g and g["26"]["class_type"] == "GetImageSize", \
    "node 26 must exist and be GetImageSize"

patched_res = []
for nid in RES_NODES:
    if nid not in g:
        print(f"  WARN: node {nid} not in graph - skipping")
        continue
    inp = g[nid]["inputs"]
    old_w, old_h = inp.get("width"), inp.get("height")
    inp["width"]  = list(WIDTH_LINK)
    inp["height"] = list(HEIGHT_LINK)
    patched_res.append((nid, g[nid]["class_type"], old_w, old_h))
    print(f"  rewired {nid} ({g[nid]['class_type']:<22}): width {old_w}->[26,0]  height {old_h}->[26,1]")

p1112 = g["1112"]["inputs"]["filename_prefix"]
p1114 = g["1114"]["inputs"]["filename_prefix"]
g["1112"]["inputs"]["filename_prefix"] = p1114
g["1114"]["inputs"]["filename_prefix"] = p1112
print(f"  swapped save prefixes: 1112 '{p1112}' <-> 1114 '{p1114}'")

backup = SRC + ".bak"
if not os.path.exists(backup):
    shutil.copy2(SRC, backup)
    print(f"  backup written: {backup}")

with open(DST, "w", encoding="utf-8") as f:
    json.dump(g, f, indent=2, ensure_ascii=False)
print(f"\n  DONE: wrote {DST}  ({os.path.getsize(DST) // 1024} KB)")
print(f"  Total fixes: {len(patched_res)} resolution rewires + 1 prefix swap.")
