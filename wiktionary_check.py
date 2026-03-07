"""
wiktionary_check.py
────────────────────
Checks ALL flagged words in invalid_words.json against English and Greek
Wiktionary. If found, prompts user to restore. Close matches prompt to replace.

Results:
  found       -> word is legitimate, prompt to restore (remove from invalid log)
  close_match -> not found but close match exists, prompt to replace in CSV
  not_found   -> keep as invalid

Usage:
    python wiktionary_check.py              # check all invalid words
    python wiktionary_check.py --word WORD  # check a single word
    python wiktionary_check.py --recheck    # re-check already-checked words
    python wiktionary_check.py --group typo # check only one issue group
"""

import json, time, re, argparse, urllib.request, urllib.parse
from pathlib import Path
from collections import defaultdict

BASE_DIR     = Path(__file__).parent
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"
CSV_PATH     = BASE_DIR / "data" / "greek_words_to_import.csv"
WIKT_PATH    = BASE_DIR / "data" / "wiktionary_results.json"

# ── Issue classification (mirrors analyze_invalid.py) ────────────────────────

ISSUE_PATTERNS = [
    ("double_accent",   ["double accent", "two accent", "multiple accent"]),
    ("missing_accent",  ["missing accent", "no accent", "without accent"]),
    ("wrong_accent",    ["wrong accent", "incorrect accent", "misplaced accent", "accent should", "tonos"]),
    ("typo",            ["typo", "misspelling", "misspelled", "spelling error", "garbled"]),
    ("not_real_word",   ["not a real", "not a word", "does not exist", "nonexistent", "invented", "no such word"]),
    ("archaic",         ["archaic", "ancient", "katharevousa", "obsolete", "old form"]),
    ("mixed_script",    ["latin", "mixed script", "non-greek", "english character"]),
    ("phrase_not_word", ["phrase", "two words", "multiple words", "expression"]),
    ("other",           []),
]

def classify(reason):
    r = reason.lower()
    for category, keywords in ISSUE_PATTERNS:
        if any(k in r for k in keywords):
            return category
    return "other"

# ── Wiktionary API ────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "GreekVocabChecker/1.0 (educational tool)"}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def check_wiktionary(word, lang="en"):
    params = urllib.parse.urlencode({"action":"query","titles":word,"format":"json","redirects":1})
    url = f"https://{lang}.wiktionary.org/w/api.php?{params}"
    try:
        data  = api_get(url)
        pages = data["query"]["pages"]
        page  = next(iter(pages.values()))
        exists = "missing" not in page
        title  = page.get("title", word)
        return exists, title
    except Exception as e:
        return False, f"error: {e}"

def search_wiktionary(word, lang="en", limit=5):
    params = urllib.parse.urlencode({"action":"opensearch","search":word,"limit":limit,"namespace":0,"format":"json"})
    url = f"https://{lang}.wiktionary.org/w/api.php?{params}"
    try:
        return api_get(url)[1]
    except Exception:
        return []

def strip_accents(w):
    table = str.maketrans(
        "\u03ac\u03ad\u03ae\u03af\u03cc\u03cd\u03ce"
        "\u0386\u0388\u0389\u038a\u038c\u038e\u038f",
        "\u03b1\u03b5\u03b7\u03b9\u03bf\u03c5\u03c9"
        "\u0391\u0395\u0397\u0399\u039f\u03a5\u03a9"
    )
    return w.translate(table)

def is_greek(s):
    return bool(re.search(r'[\u03b1-\u03c9\u03ac-\u03ce\u0391-\u03a9\u0386-\u038f]', s))

def check_word(word):
    result = {
        "word": word,
        "en_exists": False, "el_exists": False,
        "en_title": None,   "el_title": None,
        "suggestions_en": [], "suggestions_el": [],
        "status": None, "recommendation": None,
    }

    en_exists, en_title = check_wiktionary(word, "en"); time.sleep(0.3)
    el_exists, el_title = check_wiktionary(word, "el"); time.sleep(0.3)
    result.update({"en_exists":en_exists,"en_title":en_title,
                   "el_exists":el_exists,"el_title":el_title})

    if en_exists or el_exists:
        result["status"] = "found"
        result["recommendation"] = en_title if en_exists else el_title
        return result

    # Not found — search for close matches
    sugg_en = search_wiktionary(word, "en");               time.sleep(0.3)
    sugg_el = search_wiktionary(word, "el");               time.sleep(0.3)
    bare    = search_wiktionary(strip_accents(word), "en"); time.sleep(0.3)

    all_sugg  = list(dict.fromkeys(sugg_en + bare + sugg_el))
    greek_sug = [s for s in all_sugg if is_greek(s)]

    result["suggestions_en"] = sugg_en
    result["suggestions_el"] = sugg_el

    if greek_sug:
        result["status"] = "close_match"
        result["recommendation"] = greek_sug[0]
    else:
        result["status"] = "not_found"
    return result

# ── Display helpers ───────────────────────────────────────────────────────────

def src_label(r):
    if r["en_exists"] and r["el_exists"]: return "en+el"
    return "en" if r["en_exists"] else "el"

def print_result(r):
    if r["status"] == "found":
        print(f"  Found in Wiktionary [{src_label(r)}]  =>  {r['recommendation']}")
    elif r["status"] == "close_match":
        print(f"  Not found directly. Closest match: {r['recommendation']}")
        if r["suggestions_en"]: print(f"    EN: {', '.join(r['suggestions_en'][:3])}")
        if r["suggestions_el"]: print(f"    EL: {', '.join(r['suggestions_el'][:3])}")
    else:
        print(f"  Not found in Wiktionary (en or el)")

def print_inline(r):
    if r["status"] == "found":
        print(f"  OK [{src_label(r)}]")
    elif r["status"] == "close_match":
        print(f"  -> {r['recommendation']}")
    else:
        print(f"  NOT FOUND")

# ── Interactive restore ───────────────────────────────────────────────────────

def interactive_restore(found, close_match, results, invalid, csv_words):
    invalid_updated = dict(invalid)
    csv_updated     = list(csv_words)
    restored = replaced = skipped = 0

    all_candidates = (
        [(w, "found",       results[w]["recommendation"]) for w in found] +
        [(w, "close_match", results[w]["recommendation"]) for w in close_match]
    )

    for w, status, recommendation in all_candidates:
        reason = invalid.get(w, "")
        group  = classify(reason)
        print(f"  Word     : {w}")
        print(f"  Group    : {group}")
        print(f"  Reason   : {reason}")
        if status == "found":
            print(f"  Status   : found in Wiktionary [{src_label(results[w])}]")
            print(f"  Action   : remove from invalid list (keep in CSV as-is)")
        else:
            print(f"  Status   : close match")
            print(f"  Action   : replace in CSV  {w}  =>  {recommendation}")

        answer = input("  Apply? [Y]es / [N]o / [Q]uit / [R]ename : ").strip().lower()
        print()

        if answer == "q":
            print("  Stopped early.")
            break
        elif answer == "r":
            manual = input(f"  Enter correct form for '{w}' : ").strip()
            if not manual:
                skipped += 1
                print(f"  Skipped  : {w}  (empty input)")
            else:
                invalid_updated.pop(w, None)
                if w in csv_updated:
                    idx = csv_updated.index(w)
                    if manual not in csv_updated:
                        csv_updated[idx] = manual
                        print(f"  Replaced : {w}  =>  {manual}")
                    else:
                        csv_updated.remove(w)
                        print(f"  Removed  : {w}  (correct form {manual} already in list)")
                else:
                    csv_updated.append(manual)
                    print(f"  Added    : {manual}  (original {w} was not in CSV)")
                replaced += 1
        elif answer == "y":
            invalid_updated.pop(w, None)
            if status == "found":
                if w not in csv_updated:
                    csv_updated.append(w)
                    print(f"  Restored : {w}  (re-added to CSV)")
                else:
                    print(f"  Restored : {w}  (already in CSV)")
                restored += 1
            else:
                if w in csv_updated:
                    idx = csv_updated.index(w)
                    if recommendation not in csv_updated:
                        csv_updated[idx] = recommendation
                        print(f"  Replaced : {w}  =>  {recommendation}")
                    else:
                        csv_updated.remove(w)
                        print(f"  Removed  : {w}  (correct form already in list)")
                replaced += 1
        else:
            skipped += 1
            print(f"  Skipped  : {w}")
        print()

    # Save
    with open(CSV_PATH, "w", encoding="utf-8-sig") as f:
        for w in csv_updated:
            f.write(w + "\n")
    with open(INVALID_PATH, "w", encoding="utf-8") as f:
        json.dump(invalid_updated, f, ensure_ascii=False, indent=2)

    print(f"Done. {restored} restored, {replaced} replaced, {skipped} skipped.")
    if restored + replaced > 0:
        print("Run enrich_words.py to enrich any new/corrected words.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recheck", action="store_true", help="Re-check already-checked words")
    parser.add_argument("--word",    default="",          help="Check a single word")
    parser.add_argument("--group",   default="",          help="Only check words in this issue group (e.g. typo, archaic, other)")
    args = parser.parse_args()

    invalid = json.load(open(INVALID_PATH, encoding="utf-8")) if INVALID_PATH.exists() else {}
    prior   = json.load(open(WIKT_PATH,    encoding="utf-8")) if WIKT_PATH.exists()    else {}

    # ── Single word mode ──────────────────────────────────────────────────────
    if args.word:
        print(f"Checking: {args.word}\n")
        r = check_word(args.word)
        print_result(r)
        return

    # ── Select words to check ─────────────────────────────────────────────────
    if args.group:
        target = {w: r for w, r in invalid.items() if classify(r) == args.group}
        if not target:
            print(f"No words found in group '{args.group}'")
            print(f"Available groups: {', '.join(set(classify(r) for r in invalid.values()))}")
            return
    else:
        target = dict(invalid)

    to_check = {w: r for w, r in target.items() if args.recheck or w not in prior}

    # Group breakdown for display
    groups = defaultdict(list)
    for w, r in target.items():
        groups[classify(r)].append(w)

    print(f"Total flagged words : {len(invalid)}")
    if args.group:
        print(f"Filtering to group  : {args.group} ({len(target)} words)")
    else:
        print(f"Groups              : " + ", ".join(f"{g}({len(ws)})" for g, ws in sorted(groups.items())))
    print(f"Already checked     : {len(target) - len(to_check)}")
    print(f"To check now        : {len(to_check)}\n")

    if not to_check:
        print("Nothing new to check. Use --recheck to re-scan all.")
        # Still show summary from prior results if available
        checked = {w: prior[w] for w in target if w in prior}
    else:
        results = dict(prior)
        for i, (word, reason) in enumerate(to_check.items(), 1):
            group = classify(reason)
            print(f"[{i:3}/{len(to_check)}] {word:<30} ({group})", end="", flush=True)
            r = check_word(word)
            results[word] = r
            print_inline(r)

        with open(WIKT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        checked = {w: results[w] for w in target if w in results}

    # ── Summary ───────────────────────────────────────────────────────────────
    found       = [w for w, r in checked.items() if r["status"] == "found"]
    close_match = [w for w, r in checked.items() if r["status"] == "close_match"]
    not_found   = [w for w, r in checked.items() if r["status"] == "not_found"]

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")

    print(f"\nFOUND IN WIKTIONARY ({len(found)}) - legitimate:")
    for w in found:
        r = checked[w]
        print(f"  {w:<30} [{src_label(r)}]  —  {classify(invalid.get(w,''))}")

    print(f"\nCLOSE MATCH ({len(close_match)}) - recommend replacing:")
    for w in close_match:
        print(f"  {w:<30} =>  {checked[w]['recommendation']}")

    print(f"\nNOT FOUND ({len(not_found)}) - keep as invalid:")
    for w in not_found:
        print(f"  {w:<30} —  {invalid.get(w,'')[:60]}")

    # ── Interactive restore ───────────────────────────────────────────────────
    if found or close_match:
        print(f"\n{'='*60}")
        answer = input(f"Review {len(found)+len(close_match)} salvageable words one by one? [Y]es / [N]o : ").strip().lower()
        print()
        if answer == "y":
            with open(CSV_PATH, encoding="utf-8-sig") as f:
                csv_words = [line.strip() for line in f if line.strip()]
            interactive_restore(found, close_match, checked, invalid, csv_words)
    else:
        print("\nNo salvageable words found.")

if __name__ == "__main__":
    main()