import requests

r = requests.get("http://127.0.0.1:8188/history?max_items=50", timeout=5)
h = r.json()
aec_keys = {"1124", "1125", "1126", "1127", "1128", "1129"}
found = []
for pid, data in h.items():
    p = data.get("prompt", [])
    if len(p) >= 3 and isinstance(p[2], dict):
        if aec_keys.issubset(p[2].keys()):
            found.append((pid[:8], data.get("status", {}).get("status_str")))
print("total history entries:", len(h))
print("AEC-matching entries:", len(found))
for f in found[:5]:
    print("  ", f)
