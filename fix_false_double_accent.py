import json
from pathlib import Path

BASE_DIR     = Path(__file__).parent
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"

ACCENT_CHARS = set("άέήίόύώΆΈΉΊΌΎΏ")

def count_accents(w):
    return sum(1 for c in w if c in ACCENT_CHARS)

invalid = json.load(open(INVALID_PATH, encoding="utf-8"))

false = {w: r for w, r in invalid.items()
         if "double accent" in r.lower() and count_accents(w) <= 1}
cleaned = {w: r for w, r in invalid.items() if w not in false}

print(f"Removing {len(false)} false double-accent entries:")
for w, r in false.items():
    print(f"  {w}")

json.dump(cleaned, open(INVALID_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nDone. {len(cleaned)} entries remain.")