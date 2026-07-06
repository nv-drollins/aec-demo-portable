"""
Apply UUID node fixes to the bundled workflow JSON.
Run once: python fix_workflow_for_archive.py
"""
import json, sys
from pathlib import Path

WF = Path(__file__).parent.parent / "comfyui" / "workflows" / "AEC_Transform_Pipeline.json"

with open(WF, encoding="utf-8") as f:
    wf = json.load(f)

UUID_MAP = {
    "39800dc2-0f50-4d87-9149-35c0ca73e9f0": "InpaintModelConditioning",
    "c538f273-9d8b-4327-b0c2-1bae3c7e4d8e": "InpaintModelConditioning",
    "9b2de3f5-8832-4d77-bd1e-2586d01b9eea": "InpaintModelConditioning",
    "e34d6b3d-4b44-4def-af32-d1c313e71e35": "StringConcatenate",
}
INPAINT_INPUT_MAP = {"conditioning": "positive", "conditioning_1": "negative"}

fixed = 0
for node in wf["nodes"]:
    uuid = node.get("type", "")
    if uuid in UUID_MAP:
        new_type = UUID_MAP[uuid]
        node["type"] = new_type
        if new_type == "InpaintModelConditioning":
            for inp in node.get("inputs", []):
                if inp["name"] in INPAINT_INPUT_MAP:
                    inp["name"] = INPAINT_INPUT_MAP[inp["name"]]
        if new_type == "StringConcatenate":
            std = ["string_a", "string_b", "delimiter"]
            for i, inp in enumerate(node.get("inputs", [])[:3]):
                inp["name"] = std[i]
        fixed += 1

# Fix VAE path
for node in wf["nodes"]:
    if node.get("type") == "VAELoader":
        wv = node.get("widgets_values", [])
        for i, v in enumerate(wv):
            if isinstance(v, str) and "flux" in v.lower() and "\\" in v:
                wv[i] = v.replace("flux\\", "")

with open(WF, "w", encoding="utf-8") as f:
    json.dump(wf, f, indent=2)

print(f"Fixed {fixed} UUID nodes in {WF.name}")
remaining = sum(1 for n in wf["nodes"] if "-" in n.get("type","") and len(n["type"]) == 36)
print(f"Remaining UUID-type nodes: {remaining}")
