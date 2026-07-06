"""Quick verification that the patched JSON has both fixes applied."""
import json

PATH = r"C:\Users\NVIDIA\Downloads\AEC_Transform_Pipeline_API_v2.json"
with open(PATH, "r", encoding="utf-8") as f:
    g = json.load(f)


def t(n): return g[n]["_meta"].get("title", "")
def ct(n): return g[n]["class_type"]


print("== Fix 1: resolution-dependent nodes now dynamic? ==")
res_ids = ["943","946","966","968","1007","1009","1036","1043","1061","1068","1097","1098"]
all_dyn = True
for nid in res_ids:
    w = g[nid]["inputs"].get("width"); h = g[nid]["inputs"].get("height")
    ok = isinstance(w, list) and isinstance(h, list) and w[0] == "26" and h[0] == "26"
    all_dyn = all_dyn and ok
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {nid}  width={w}  height={h}")

print()
print("== Fix 2: SaveImage filename matches prompt feeding it? ==")
expectations = {
    "Make_Real":          "Initial Prompt",
    "Change_Walls":       "Walls & Foundation",
    "Change_Windows":     "WIndows",
    "Change_Roof":        "Roof",
    "CHange_Windows":     "WIndows",
    "Change_Environment": "Environment",
    "Time_Of_Day":        "Time of Day",
}


def trace_back(start, target, max_depth=12):
    """Walk upstream toward the generating sampler. For SimpleInpaintStitch,
    follow processed_crop (the inpaint result) instead of original_image (canvas).
    """
    visited = set(); q = [(start, 0)]
    while q:
        n, d = q.pop(0)
        if n in visited or d > max_depth or n not in g: continue
        visited.add(n)
        if ct(n) == target: return n
        inputs = g[n]["inputs"]
        if ct(n) == "SimpleInpaintStitch":
            v = inputs.get("processed_crop")
            if isinstance(v, list) and len(v) == 2 and v[0] in g:
                q.append((v[0], d + 1))
            continue
        for v in inputs.values():
            if isinstance(v, list) and len(v) == 2 and v[0] in g:
                q.append((v[0], d + 1))
    return None


all_match = True
for nid, node in g.items():
    if ct(nid) != "SaveImage": continue
    prefix = node["inputs"]["filename_prefix"]
    sampler = trace_back(nid, "SamplerCustomAdvanced")
    if not sampler: continue
    gk = g[sampler]["inputs"]["guider"][0]
    pos = g[gk]["inputs"]["positive"][0]
    cur = pos; text_node = "?"; text_title = "?"
    for _ in range(12):
        if ct(cur) == "CLIPTextEncode":
            text_node = g[cur]["inputs"]["text"][0]
            text_title = t(text_node)
            break
        cnd = g[cur]["inputs"].get("conditioning", [None])
        if isinstance(cnd, list) and len(cnd) == 2:
            cur = cnd[0]
        else:
            break
    expected = expectations.get(prefix, "?")
    ok = text_title == expected
    all_match = all_match and ok
    flag = "OK" if ok else "MISMATCH"
    print(f"  [{flag}] '{prefix}'  -> text node {text_node} '{text_title}'  (expected '{expected}')")

print()
print(f"OVERALL: resolution_dynamic={all_dyn}  prompt_alignment={all_match}")
