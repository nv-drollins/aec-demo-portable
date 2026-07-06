import json
p = r"C:\Users\NVIDIA\ComfyUI\ComfyUI_windows_portable\ComfyUI\user_prompt\AEC_Transform_Pipeline.json"
wf = json.load(open(p, encoding="utf-8"))
nodes = {n["id"]: n for n in wf["nodes"]}
links = {l[0]: l for l in wf["links"]}

def show(nid):
    n = nodes.get(nid)
    if not n:
        print(f"  node {nid}: MISSING"); return
    print(f"  node {nid}  type={n['type']}")
    for inp in n.get("inputs", []) or []:
        s = None
        if inp.get("link") is not None:
            l = links.get(inp["link"])
            if l: s = (nodes[l[1]]["type"], l[1], "slot", l[2])
        print(f"     in '{inp.get('name')}' <- {s}")
    # consumers
    cons = []
    for l in wf["links"]:
        if l[1] == nid:
            tn = nodes.get(l[3]); nm = "?"
            if tn:
                ins = tn.get("inputs", []) or []
                if l[4] < len(ins): nm = ins[l[4]].get("name", "?")
            cons.append((tn["type"] if tn else "?", l[3], nm))
    print(f"     -> consumers {cons}")

for nid in (1165, 1184, 1206):
    show(nid)
