"""
build_wiktionary_lookup.py
──────────────────────────
Downloads Greek word dumps from kaikki.org (en + el Wiktionary) and builds
a unified local lookup saved to data/wiktionary_lookup.json.

The lookup is used by enrich_words.py as a fallback when Haiku's validation
gate rejects a word — if the word exists in Wiktionary, it can be enriched
from the dump instead of being skipped.

Usage:
    python build_wiktionary_lookup.py           # download + build
    python build_wiktionary_lookup.py --check   # check existing lookup stats
    python build_wiktionary_lookup.py --word αετός  # look up single word

Dump sources:
    EN: https://kaikki.org/dictionary/Greek/kaikki.org-dictionary-Greek.jsonl
    EL: not available on kaikki.org — uses live Wiktionary API (see wiktionary_check.py)
"""

import json
import sys
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
LOOKUP_PATH  = DATA_DIR / "wiktionary_lookup.json"

EN_DUMP_URL  = "https://kaikki.org/dictionary/Greek/kaikki.org-dictionary-Greek.jsonl"
EL_DUMP_URL  = ""  # Not available on kaikki.org — EN dump covers most Modern Greek words

HEADERS = {"User-Agent": "GreekVocabLookup/1.0 (educational tool)"}

# ── POS normalisation ─────────────────────────────────────────────────────────

POS_MAP = {
    "noun": "noun", "verb": "verb", "adj": "adjective", "adjective": "adjective",
    "adv": "adverb", "adverb": "adverb", "prep": "preposition", "preposition": "preposition",
    "conj": "conjunction", "conjunction": "conjunction", "pron": "pronoun", "pronoun": "pronoun",
    "particle": "particle", "phrase": "phrase", "intj": "particle", "det": "particle",
    "num": "particle", "article": "particle",
}

def norm_pos(pos: str) -> str:
    return POS_MAP.get(pos.lower().strip(), pos.lower().strip())

# ── Download ──────────────────────────────────────────────────────────────────

def download_jsonl(url: str, label: str) -> list:
    """Stream-download a JSONL file and return parsed entries."""
    print(f"\n📥  Downloading {label}...")
    print(f"    {url}")

    req = urllib.request.Request(url, headers=HEADERS)
    entries = []
    bytes_read = 0

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line_bytes in resp:
                bytes_read += len(line_bytes)
                line = line_bytes.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                    if len(entries) % 10000 == 0:
                        mb = bytes_read / (1024 * 1024)
                        print(f"    {len(entries):,} entries  ({mb:.1f} MB)", end="\r")
                except json.JSONDecodeError:
                    continue
    except urllib.error.HTTPError as e:
        print(f"\n  ❌  HTTP {e.code} — {e.reason}")
        return []
    except Exception as e:
        print(f"\n  ❌  Error: {e}")
        return []

    mb = bytes_read / (1024 * 1024)
    print(f"    ✅  {len(entries):,} entries downloaded  ({mb:.1f} MB)")
    return entries

# ── Parse EN entry ────────────────────────────────────────────────────────────

def parse_en_entry(entry: dict) -> dict:
    """Extract useful fields from an en.wiktionary entry."""
    word = entry.get("word", "")
    pos  = norm_pos(entry.get("pos", ""))

    # Definitions / glosses
    definitions = []
    for sense in entry.get("senses", []):
        for gloss in sense.get("glosses", []):
            if gloss and gloss not in definitions:
                definitions.append(gloss)

    # Translation — first English gloss is the best short translation
    translation = definitions[0] if definitions else ""
    # Trim long translations to ~60 chars
    if len(translation) > 60:
        translation = translation[:57] + "..."

    # IPA pronunciation
    ipa = ""
    for sound in entry.get("sounds", []):
        if "ipa" in sound:
            ipa = sound["ipa"]
            break

    # Forms (conjugation / declension tags)
    forms = []
    for f in entry.get("forms", []):
        form_word = f.get("form", "")
        tags = f.get("tags", [])
        if form_word and tags:
            forms.append({"form": form_word, "tags": tags})

    # Synonyms
    synonyms = []
    for sense in entry.get("senses", []):
        for syn in sense.get("synonyms", []):
            w = syn.get("word", "")
            if w and w not in synonyms:
                synonyms.append(w)

    return {
        "word":        word,
        "pos":         pos,
        "translation": translation,
        "definition":  " | ".join(definitions[:3]),
        "ipa":         ipa,
        "forms":       forms[:20],
        "synonyms":    synonyms[:5],
        "source":      "en",
    }

# ── Parse EL entry ────────────────────────────────────────────────────────────

def parse_el_entry(entry: dict) -> dict:
    """Extract useful fields from an el.wiktionary entry (definitions in Greek)."""
    word = entry.get("word", "")
    pos  = norm_pos(entry.get("pos", ""))

    # Greek definitions
    definitions_el = []
    for sense in entry.get("senses", []):
        for gloss in sense.get("glosses", []):
            if gloss and gloss not in definitions_el:
                definitions_el.append(gloss)

    # Forms
    forms = []
    for f in entry.get("forms", []):
        form_word = f.get("form", "")
        tags = f.get("tags", [])
        if form_word and tags:
            forms.append({"form": form_word, "tags": tags})

    return {
        "word":           word,
        "pos":            pos,
        "definition_el":  " | ".join(definitions_el[:3]),
        "forms":          forms[:20],
        "source":         "el",
    }

# ── Build unified lookup ──────────────────────────────────────────────────────

def build_lookup(en_entries: list, el_entries: list) -> dict:
    """
    Merge EN and EL entries into a unified lookup dict keyed by word.
    Structure: { word: { "en": {...}, "el": {...} } }
    """
    print("\n⚙️   Building unified lookup...")
    lookup = defaultdict(dict)

    for entry in en_entries:
        parsed = parse_en_entry(entry)
        word = parsed["word"]
        if word:
            # Keep entry with most definitions if duplicate
            existing = lookup[word].get("en")
            if not existing or len(parsed["definition"]) > len(existing.get("definition", "")):
                lookup[word]["en"] = parsed

    print(f"    EN entries indexed: {sum(1 for v in lookup.values() if 'en' in v):,}")

    for entry in el_entries:
        parsed = parse_el_entry(entry)
        word = parsed["word"]
        if word:
            existing = lookup[word].get("el")
            if not existing or len(parsed["definition_el"]) > len(existing.get("definition_el", "")):
                lookup[word]["el"] = parsed

    print(f"    EL entries indexed: {sum(1 for v in lookup.values() if 'el' in v):,}")
    print(f"    Total unique words : {len(lookup):,}")
    en_and_el = sum(1 for v in lookup.values() if "en" in v and "el" in v)
    print(f"    Words in both      : {en_and_el:,}")

    return dict(lookup)

# ── Save / load ───────────────────────────────────────────────────────────────

def save_lookup(lookup: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(LOOKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = LOOKUP_PATH.stat().st_size / (1024 * 1024)
    print(f"\n💾  Saved to {LOOKUP_PATH}  ({size_mb:.1f} MB)")

def load_lookup() -> dict:
    if not LOOKUP_PATH.exists():
        return {}
    with open(LOOKUP_PATH, encoding="utf-8") as f:
        return json.load(f)

# ── Public lookup API (used by other scripts) ─────────────────────────────────

def lookup_word(word: str, lookup: dict = None) -> dict | None:
    """
    Look up a word in the local Wiktionary dump.
    Returns combined dict or None if not found.

    Result structure:
    {
        "word": str,
        "found_in": ["en"] | ["el"] | ["en","el"],
        "pos": str,
        "translation": str,        # from EN
        "definition": str,         # from EN (English)
        "definition_el": str,      # from EL (Greek)
        "ipa": str,
        "forms": [...],
        "synonyms": [...],
    }
    """
    if lookup is None:
        lookup = load_lookup()

    entry = lookup.get(word)
    if not entry:
        return None

    result = {"word": word, "found_in": list(entry.keys())}

    en = entry.get("en", {})
    el = entry.get("el", {})

    # Prefer EN for English fields
    result["pos"]          = en.get("pos") or el.get("pos", "")
    result["translation"]  = en.get("translation", "")
    result["definition"]   = en.get("definition", "")
    result["definition_el"]= el.get("definition_el", "")
    result["ipa"]          = en.get("ipa", "")
    result["forms"]        = en.get("forms") or el.get("forms", [])
    result["synonyms"]     = en.get("synonyms", [])

    return result

# ── CLI helpers ───────────────────────────────────────────────────────────────

def print_word_result(r: dict):
    print(f"\n  Word       : {r['word']}")
    print(f"  Found in   : {', '.join(r['found_in'])}")
    print(f"  POS        : {r['pos']}")
    print(f"  Translation: {r['translation']}")
    print(f"  Definition : {r['definition']}")
    if r["definition_el"]:
        print(f"  Def (EL)   : {r['definition_el']}")
    if r["ipa"]:
        print(f"  IPA        : {r['ipa']}")
    if r["forms"]:
        sample = [f["form"] for f in r["forms"][:5]]
        print(f"  Forms      : {', '.join(sample)}{'...' if len(r['forms'])>5 else ''}")
    if r["synonyms"]:
        print(f"  Synonyms   : {', '.join(r['synonyms'])}")

def print_stats(lookup: dict):
    total    = len(lookup)
    en_only  = sum(1 for v in lookup.values() if "en" in v and "el" not in v)
    el_only  = sum(1 for v in lookup.values() if "el" in v and "en" not in v)
    both     = sum(1 for v in lookup.values() if "en" in v and "el" in v)

    # POS breakdown
    pos_counts = defaultdict(int)
    for v in lookup.values():
        pos = (v.get("en") or v.get("el") or {}).get("pos", "unknown")
        pos_counts[pos] += 1

    print(f"\n📊  Wiktionary Lookup Stats")
    print(f"{'─'*40}")
    print(f"  Total words    : {total:,}")
    print(f"  EN only        : {en_only:,}")
    print(f"  EL only        : {el_only:,}")
    print(f"  Both EN + EL   : {both:,}")
    print(f"\n  POS breakdown:")
    for pos, count in sorted(pos_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {pos:<20} {count:,}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check",   action="store_true", help="Show stats for existing lookup")
    parser.add_argument("--word",    default="",          help="Look up a single word")
    parser.add_argument("--en-only", action="store_true", help="Download EN dump only")
    parser.add_argument("--el-only", action="store_true", help="Download EL dump only")
    args = parser.parse_args()

    # ── Check mode ────────────────────────────────────────────────────────────
    if args.check:
        if not LOOKUP_PATH.exists():
            print("No lookup file found. Run without --check to build it.")
            return
        lookup = load_lookup()
        print_stats(lookup)
        return

    # ── Single word lookup ────────────────────────────────────────────────────
    if args.word:
        if not LOOKUP_PATH.exists():
            print("No lookup file found. Run without --word to build it first.")
            return
        lookup = load_lookup()
        result = lookup_word(args.word, lookup)
        if result:
            print_word_result(result)
        else:
            print(f"\n  '{args.word}' not found in local Wiktionary lookup.")
        return

    # ── Build mode ────────────────────────────────────────────────────────────
    print("🇬🇷  Building Wiktionary lookup from kaikki.org (EN Wiktionary only)...")
    print("    Downloads ~200 MB and may take a few minutes.\n")
    print("    Note: kaikki.org only provides EN Wiktionary extractions.")
    print("    For EL coverage, use wiktionary_check.py which queries el.wiktionary.org live.\n")

    # Load existing lookup if partial rebuild
    existing = load_lookup() if LOOKUP_PATH.exists() else {}

    en_entries = []
    el_entries = []

    if not args.el_only:
        en_entries = download_jsonl(EN_DUMP_URL, "EN Wiktionary (Greek words)")
    if not args.en_only:
        if EL_DUMP_URL:
            el_entries = download_jsonl(EL_DUMP_URL, "EL Wiktionary (Greek words)")
        else:
            print("\nℹ️   EL Wiktionary dump not available on kaikki.org.")
            print("    EL lookups are handled live via wiktionary_check.py API calls.")

    if not en_entries and not el_entries:
        print("\n❌  No data downloaded. Check your internet connection.")
        sys.exit(1)

    lookup = build_lookup(en_entries, el_entries)
    save_lookup(lookup)
    print_stats(lookup)

    print("\n✅  Done. Use lookup_word() in other scripts to query the lookup.")
    print(f"    Example: python build_wiktionary_lookup.py --word αετός")

if __name__ == "__main__":
    main()
