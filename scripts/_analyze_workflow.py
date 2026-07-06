import json
from collections import Counter

p = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\user_prompt\AEC_Transform_Pipeline.json"
wf = json.load(open(p, encoding="utf-8"))
nodes = wf.get("nodes", [])
print("total nodes:", len(nodes))

MODE = {0: "active", 1: "active", 2: "MUTED", 4: "BYPASS", None: "active"}
types = Counter()
samplers = []
schedulers = []
latents = []
saves = []
for n in nodes:
    t = n.get("type", "?")
    types[t] += 1
    mode = n.get("mode", 0)
    if t == "SamplerCustomAdvanced":
        samplers.append((n.get("id"), MODE.get(mode, mode), n.get("title", "")))
    if t == "Flux2Scheduler":
        wv = n.get("widgets_values", [])
        schedulers.append((n.get("id"), MODE.get(mode, mode), wv[0] if wv else "?"))
    if t == "EmptyFlux2LatentImage":
        wv = n.get("widgets_values", [])
        latents.append((n.get("id"), MODE.get(mode, mode), wv[:2] if wv else "?"))
    if t == "SaveImage":
        wv = n.get("widgets_values", [])
        saves.append((n.get("id"), MODE.get(mode, mode), wv[0] if wv else "?"))

print("\n--- node type histogram (top) ---")
for t, c in types.most_common(20):
    print(f"  {c:3d}  {t}")

print("\n--- SamplerCustomAdvanced (Flux passes) ---")
act = sum(1 for s in samplers if s[1] == "active")
print(f"  {act} ACTIVE of {len(samplers)} total")
for sid, m, title in samplers:
    print(f"    id {sid:>5}  {m:7}  {title}")

print("\n--- Flux2Scheduler steps ---")
for sid, m, st in schedulers:
    print(f"    id {sid:>5}  {m:7}  steps={st}")

print("\n--- EmptyFlux2LatentImage resolution ---")
for sid, m, res in latents:
    print(f"    id {sid:>5}  {m:7}  res={res}")

print("\n--- SaveImage ---")
for sid, m, pre in saves:
    print(f"    id {sid:>5}  {m:7}  prefix={pre}")
