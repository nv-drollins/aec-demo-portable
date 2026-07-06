
import json, re
wf_raw = open(r"C:\Users\swags\Documents\AEC_Demo_Portable\comfyui\workflows\AEC_Transform_Pipeline.json").read()
hits = re.findall(r'.{0,40}39800dc2.{0,40}', wf_raw)
for h in hits[:5]:
    print(h.strip())
