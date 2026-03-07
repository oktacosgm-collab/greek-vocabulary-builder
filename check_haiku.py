import json
cache = json.load(open(r"data\enriched_cache.json", encoding="utf-8"))
a2 = [w for w,d in cache.items() if d.get("difficulty") == "A2"]
print(len(a2))