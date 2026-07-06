import json
p = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\user_prompt\AEC_Transform_Pipeline.json"
wf = json.load(open(p, encoding="utf-8"))
nodes = {n["id"]: n for n in wf["nodes"]}
links = {l[0]: l for l in wf["links"]}

def src(node, name):
    for inp in node.get("inputs", []) or []:
        if inp.get("name") == name and inp.get("link") is not None:
            l = links.get(inp["link"])
            if l: return (nodes[l[1]]["type"], l[1])
    return None

def consumers(nid):
    out = []
    for l in wf["links"]:
        if l[1] == nid:
            tn = nodes.get(l[3]); nm = "?"
            if tn:
                ins = tn.get("inputs", []) or []
                if l[4] < len(ins): nm = ins[l[4]].get("name", "?")
            out.append((tn["type"] if tn else "?", l[3], nm))
    return out

print("=== ConditioningAverage nodes ===")
for n in wf["nodes"]:
    if n.get("type") == "ConditioningAverage":
        print(f"  id {n['id']}  widgets_values={n.get('widgets_values')}")
        for inp in n.get("inputs", []) or []:
            print(f"     in '{inp.get('name')}' <- {src(n, inp.get('name'))}")
        print(f"     -> consumers {consumers(n['id'])}")

print("\n=== Ollama nodes ===")
for n in wf["nodes"]:
    if "Ollama" in n.get("type", ""):
        print(f"  id {n['id']}  type={n['type']}  mode={n.get('mode')}")
        for inp in n.get("inputs", []) or []:
            print(f"     in '{inp.get('name')}' <- {src(n, inp.get('name'))}")
        print(f"     -> consumers {consumers(n['id'])}")
