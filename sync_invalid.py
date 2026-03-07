"""
sync_invalid.py
───────────────
Removes entries from invalid_words.json that no longer exist in the CSV
(i.e. words that have been manually corrected or deleted from source).
"""

from pathlib import Path
import json

BASE_DIR     = Path(__file__).parent
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"
CSV_PATH     = BASE_DIR / "data" / "greek_words_to_import.csv"

# Load
invalid = json.load(open(INVALID_PATH, encoding="utf-8"))
with open(CSV_PATH, encoding="utf-8-sig") as f:
    csv_words = set(line.strip() for line in f if line.strip() and line.strip().lower() != "word")

# Find stale entries
removed = {w: r for w, r in invalid.items() if w not in csv_words}
cleaned = {w: r for w, r in invalid.items() if w in csv_words}

print(f"Invalid entries  : {len(invalid)}")
print(f"Stale (not in CSV): {len(removed)}")
for w, r in removed.items():
    print(f"  removing: {w}  —  {r}")

# Save
json.dump(cleaned, open(INVALID_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nDone. {len(cleaned)} entries remain in invalid_words.json")