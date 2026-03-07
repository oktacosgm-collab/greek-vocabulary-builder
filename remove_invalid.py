"""
remove_invalid.py
─────────────────
Manually remove specific words from invalid_words.json and optionally
re-add them to the CSV.

Usage:
    python remove_invalid.py αιφνιδιαστικός "εν πολλοίς" νυν
"""

import json
import sys
from pathlib import Path

BASE_DIR     = Path(__file__).parent
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"
CSV_PATH     = BASE_DIR / "data" / "greek_words_to_import.csv"

def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_invalid.py WORD1 WORD2 ...")
        return

    words = sys.argv[1:]

    invalid = json.load(open(INVALID_PATH, encoding="utf-8")) if INVALID_PATH.exists() else {}
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        csv_words = [line.strip() for line in f if line.strip()]

    removed_invalid = []
    not_in_invalid  = []
    added_csv       = []
    already_csv     = []

    for w in words:
        if w in invalid:
            print(f"\n  Word   : {w}")
            print(f"  Reason : {invalid[w]}")
            ans = input("  Remove from invalid list and re-add to CSV? [Y]es / [N]o : ").strip().lower()
            if ans == "y":
                del invalid[w]
                removed_invalid.append(w)
                if w not in csv_words:
                    csv_words.append(w)
                    added_csv.append(w)
                else:
                    already_csv.append(w)
            else:
                print(f"  Skipped: {w}")
        else:
            not_in_invalid.append(w)
            print(f"\n  '{w}' not found in invalid_words.json — already clean.")

    # Save
    if removed_invalid:
        with open(INVALID_PATH, "w", encoding="utf-8") as f:
            json.dump(invalid, f, ensure_ascii=False, indent=2)
        with open(CSV_PATH, "w", encoding="utf-8-sig") as f:
            for w in csv_words:
                f.write(w + "\n")

        print(f"\n{'─'*50}")
        print(f"Removed from invalid : {', '.join(removed_invalid)}")
        if added_csv:
            print(f"Re-added to CSV      : {', '.join(added_csv)}")
        if already_csv:
            print(f"Already in CSV       : {', '.join(already_csv)}")
        print("Run enrich_words.py to enrich any re-added words.")

if __name__ == "__main__":
    main()