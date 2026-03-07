import json
path = r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_learner\data\enriched_cache.json"
cache = json.load(open(path, encoding="utf-8"))

count = 0
for word, d in cache.items():
    decl = d.get("declension") or {}
    if isinstance(decl, dict):
        for g in ["masculine","feminine","neuter"]:
            if g in decl and isinstance(decl[g], dict) and "singular" not in decl[g]:
                d["declension"] = None
                count += 1
                break

json.dump(cache, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Reset {count} adjectives")