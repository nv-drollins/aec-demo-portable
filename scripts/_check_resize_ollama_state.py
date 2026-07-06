"""Check the v2 JSON for any node states that submit_comfyui.py would have to
patch. Tells us whether the coworker even needs those fixes baked in."""
import json
PATH = r"C:\Users\NVIDIA\Downloads\AEC_Transform_Pipeline_API_v2.json"
with open(PATH, "r", encoding="utf-8") as f:
    g = json.load(f)

problems = []
ok_resize = 0
for nid, node in g.items():
    ct = node["class_type"]
    inputs = node["inputs"]
    if ct == "ResizeImageMaskNode":
        rt = inputs.get("resize_type")
        if rt is None:
            problems.append(f"{nid} ResizeImageMaskNode: resize_type MISSING")
        elif isinstance(rt, list):
            problems.append(f"{nid} ResizeImageMaskNode: resize_type is a wire {rt} (should be string enum)")
        elif rt not in ("match size", "scale dimensions", "scale by factor"):
            problems.append(f"{nid} ResizeImageMaskNode: resize_type='{rt}' (unknown enum value)")
        else:
            ok_resize += 1
            # also sanity check the sidecar
            if rt == "match size" and not isinstance(inputs.get("resize_type.match"), list):
                problems.append(f"{nid} ResizeImageMaskNode: 'match size' but resize_type.match missing or not a wire")
    if ct in ("OllamaConnectivityV2", "OllamaGenerateV2"):
        problems.append(f"{nid} {ct}: present (model='{inputs.get('model')}')")

print(f"ResizeImageMaskNode: {ok_resize} OK")
if problems:
    print(f"PROBLEMS ({len(problems)}):")
    for p in problems: print(f"  - {p}")
else:
    print("No Ollama nodes, no broken resize_type widgets. Nothing to patch.")
