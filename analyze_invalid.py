"""
analyze_invalid.py
──────────────────
Groups invalid_words.json by issue type and attempts to auto-correct
words flagged for accent placement errors.

Usage:
    python analyze_invalid.py              # show grouped summary
    python analyze_invalid.py --fix-accents # apply accent corrections to CSV
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

BASE_DIR     = Path(__file__).parent
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"
CSV_PATH     = BASE_DIR / "data" / "greek_words_to_import.csv"
CACHE_PATH   = BASE_DIR / "data" / "enriched_cache.json"

# ── Accent utilities ──────────────────────────────────────────────────────────

# Map accented → unaccented for comparison
ACCENT_MAP = str.maketrans(
    "άέήίόύώΆΈΉΊΌΎΏ",
    "αεηιουωΑΕΗΙΟΥΩ"
)

def strip_accents(w: str) -> str:
    return w.translate(ACCENT_MAP)

def count_accents(w: str) -> int:
    return sum(1 for c in w if c in "άέήίόύώΆΈΉΊΌΎΩ")

# ── Issue classification ──────────────────────────────────────────────────────

ISSUE_PATTERNS = [
    ("double_accent",   ["double accent", "two accent", "multiple accent", "δύο τόνοι", "διπλό τόνο"]),
    ("missing_accent",  ["missing accent", "no accent", "without accent", "χωρίς τόνο"]),
    ("wrong_accent",    ["wrong accent", "incorrect accent", "misplaced accent", "accent should", "τόνος"]),
    ("typo",            ["typo", "misspelling", "misspelled", "spelling error", "garbled"]),
    ("not_real_word",   ["not a real", "not a word", "does not exist", "nonexistent", "invented", "no such word"]),
    ("archaic",         ["archaic", "ancient", "katharevousa", "obsolete", "old form"]),
    ("mixed_script",    ["latin", "mixed script", "non-greek", "english character"]),
    ("phrase_not_word", ["phrase", "two words", "multiple words", "expression"]),
    ("other",           []),  # catch-all
]

def is_acronym(w: str) -> bool:
    """True if word is all uppercase Greek letters (2-6 chars) — e.g. ΑΠΕ, ΝΑΤΟ, ΕΛΑ."""
    import unicodedata
    if not (2 <= len(w) <= 6):
        return False
    return all(unicodedata.category(c) == "Lu" or c in "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ" for c in w)

def classify(reason: str) -> str:
    r = reason.lower()
    for category, keywords in ISSUE_PATTERNS:
        if any(k in r for k in keywords):
            return category
    return "other"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix-accents", action="store_true",
                        help="Apply corrected forms to CSV and remove from invalid log")
    args = parser.parse_args()

    if not INVALID_PATH.exists():
        print("No invalid_words.json found.")
        return

    invalid = json.load(open(INVALID_PATH, encoding="utf-8"))
    acronyms = [w for w in invalid if is_acronym(w)]
    print(f"Total flagged words : {len(invalid)}")
    print(f"Acronyms excluded   : {len(acronyms)} ({', '.join(sorted(acronyms)[:10])}{'...' if len(acronyms)>10 else ''})")
    print()

    # ── Group by issue type ───────────────────────────────────────────────────
    groups = defaultdict(list)
    for word, reason in invalid.items():
        if is_acronym(word):
            continue  # skip acronyms
        cat = classify(reason)
        groups[cat].append((word, reason))

    print("=" * 60)
    print("SUMMARY BY ISSUE TYPE")
    print("=" * 60)
    for cat, items in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"\n{'─'*50}")
        print(f"  {cat.upper().replace('_',' ')}  ({len(items)} words)")
        print(f"{'─'*50}")
        for word, reason in sorted(items):
            print(f"  {word:<25} {reason}")

    # ── Accent analysis ───────────────────────────────────────────────────────
    accent_issues = [
        (w, r) for w, r in (
            groups.get("double_accent", []) +
            groups.get("wrong_accent",  []) +
            groups.get("missing_accent",[])
        ) if not is_acronym(w)
    ]

    print(f"\n{'='*60}")
    print(f"ACCENT ISSUES — {len(accent_issues)} words")
    print(f"{'='*60}")

    # For double-accent words, try to find the correct form from cache reason
    # (Haiku often says "typo of X" or "should be X")
    cache = json.load(open(CACHE_PATH, encoding="utf-8")) if CACHE_PATH.exists() else {}

    salvageable = {}  # word → suggested_correction
    for word, reason in accent_issues:
        # Check if Haiku suggested a correct form in the reason text
        # Patterns: "should be X", "correct form is X", "typo of X", "standard form: X"
        suggestion = None
        for pattern in [
            r'should be[:\s]+([^\s,\.]+)',
            r'correct form[:\s]+([^\s,\.]+)',
            r'typo of[:\s]+([^\s,\.]+)',
            r'standard form[:\s]+([^\s,\.]+)',
            r'probably[:\s]+([^\s,\.]+)',
            r'perhaps[:\s]+([^\s,\.]+)',
        ]:
            m = re.search(pattern, reason, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip("\"'()[]")
                # Only accept if it looks Greek
                if re.search(r'[α-ωά-ώΑ-ΩΆ-Ώ]', candidate):
                    suggestion = candidate
                    break

        # Fallback: double-accent word — count accents
        if not suggestion and count_accents(word) > 1:
            suggestion = "MANUAL — double accent, needs review"

        salvageable[word] = (reason, suggestion)
        marker = "✅ suggestion" if suggestion and "MANUAL" not in suggestion else "⚠️  manual"
        print(f"  {word:<25} → {suggestion or '—'}   [{marker}]")

    auto_fixable = [(w, s) for w, (r, s) in salvageable.items()
                    if s and "MANUAL" not in s]
    print(f"\n  Auto-fixable: {len(auto_fixable)}")
    print(f"  Need manual:  {len(accent_issues) - len(auto_fixable)}")

    # ── Apply fixes ───────────────────────────────────────────────────────────
    if args.fix_accents and auto_fixable:
        print(f"\n{'='*60}")
        print("APPLYING ACCENT FIXES")
        print(f"{'='*60}")

        # Load CSV
        with open(CSV_PATH, encoding="utf-8-sig") as f:
            csv_words = [line.strip() for line in f if line.strip()]

        invalid_updated = dict(invalid)
        csv_updated = list(csv_words)
        fixed = 0

        for bad_word, correct_word in auto_fixable:
            if bad_word in csv_updated:
                idx = csv_updated.index(bad_word)
                if correct_word not in csv_updated:
                    csv_updated[idx] = correct_word
                    invalid_updated.pop(bad_word, None)
                    print(f"  ✓  {bad_word}  →  {correct_word}")
                    fixed += 1
                else:
                    # Correct form already in CSV — just remove the bad one
                    csv_updated.remove(bad_word)
                    invalid_updated.pop(bad_word, None)
                    print(f"  🗑  {bad_word}  (correct form {correct_word} already in list)")
                    fixed += 1

        # Save CSV
        with open(CSV_PATH, "w", encoding="utf-8-sig") as f:
            for w in csv_updated:
                f.write(w + "\n")

        # Save updated invalid log
        with open(INVALID_PATH, "w", encoding="utf-8") as f:
            json.dump(invalid_updated, f, ensure_ascii=False, indent=2)

        print(f"\n✅  Fixed {fixed} words in CSV.")
        print(f"    Re-run enrich_words.py to enrich the corrected forms.")
    elif args.fix_accents:
        print("\nNo auto-fixable accent errors found.")


if __name__ == "__main__":
    main()