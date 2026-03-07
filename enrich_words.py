"""
enrich_words.py
───────────────
Reads greek_words_to_import.csv, calls Claude API to enrich each word
with translation, definition, example, and conjugation/declension data.

Run ONCE — already-cached words are skipped automatically.
Use --update-conjugation to add conjugation data to already-cached words.

Usage:
    python enrich_words.py
    python enrich_words.py --update-conjugation
    python enrich_words.py --update-conjugation --limit 10
"""

import json
import time
import argparse
import os
import sys
from pathlib import Path

BASE_DIR     = Path(__file__).parent
CSV_PATH     = BASE_DIR / "data" / "greek_words_to_import.csv"
CACHE_PATH   = BASE_DIR / "data" / "enriched_cache.json"
INVALID_PATH  = BASE_DIR / "data" / "invalid_words.json"
LOOKUP_PATH   = BASE_DIR / "data" / "wiktionary_lookup.json"

SYSTEM_PROMPT = """You are a Greek language expert. When given a Modern Greek word,
respond ONLY with a valid JSON object — no markdown, no explanation, no backticks.

JSON format (all fields required):
{
  "word": "the greek word as given",
  "transliteration": "phonetic romanization",
  "part_of_speech": "noun / verb / adjective / adverb / pronoun / preposition / conjunction / particle / phrase",
  "translation": "concise English translation (1-6 words)",
  "definition": "clear English definition in 1-2 sentences",
  "example_greek": "natural example sentence in Modern Greek",
  "example_english": "English translation of the example sentence",
  "difficulty": "A1 / A2 / B1 / B2 / C1 / C2",
  "conjugation": null,
  "declension": null
}

CONJUGATION RULES (only for verbs — otherwise leave null):
{
  "present":       {"sg1": "εγώ ...", "sg2": "εσύ ...", "sg3": "αυτός/ή/ό ...", "pl1": "εμείς ...", "pl2": "εσείς ...", "pl3": "αυτοί/ές/ά ..."},
  "past_simple":   {"sg1": "...", "sg2": "...", "sg3": "...", "pl1": "...", "pl2": "...", "pl3": "..."},
  "future_simple": {"sg1": "θα ...", "sg2": "θα ...", "sg3": "θα ...", "pl1": "θα ...", "pl2": "θα ...", "pl3": "θα ..."},
  "voice": "active / passive / both"
}

DECLENSION RULES (nouns and adjectives only — otherwise leave null):
For nouns:
{
  "gender": "masculine / feminine / neuter",
  "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
  "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
}
For adjectives — MUST include BOTH singular AND plural for ALL three genders:
{
  "masculine": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  },
  "feminine": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  },
  "neuter": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  }
}
IMPORTANT: For adjectives, each gender key MUST contain "singular" and "plural" sub-objects. Never use a flat structure like {"nominative": ...} directly under a gender key."""

CONJUGATION_ONLY_PROMPT = """You are a Greek language expert. Given a Modern Greek word with existing data,
update the conjugation or declension fields. Respond ONLY with the complete updated JSON — no markdown, no backticks.

CONJUGATION (verbs only, else null):
{
  "present":       {"sg1": "εγώ ...", "sg2": "εσύ ...", "sg3": "αυτός/ή/ό ...", "pl1": "εμείς ...", "pl2": "εσείς ...", "pl3": "αυτοί/ές/ά ..."},
  "past_simple":   {"sg1": "...", "sg2": "...", "sg3": "...", "pl1": "...", "pl2": "...", "pl3": "..."},
  "future_simple": {"sg1": "θα ...", "sg2": "θα ...", "sg3": "θα ...", "pl1": "θα ...", "pl2": "θα ...", "pl3": "θα ..."},
  "voice": "active / passive / both"
}

DECLENSION (nouns and adjectives only, else null):
For nouns:
{
  "gender": "masculine / feminine / neuter",
  "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
  "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
}
For adjectives — MUST include BOTH singular AND plural for ALL three genders:
{
  "masculine": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  },
  "feminine": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  },
  "neuter": {
    "singular": {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."},
    "plural":   {"nominative": "...", "genitive": "...", "accusative": "...", "vocative": "..."}
  }
}
IMPORTANT: For adjectives, each gender key MUST contain "singular" and "plural" sub-objects. Never use a flat structure like {"nominative": ...} directly under a gender key."""

def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def load_words():
    words = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for line in f:
            word = line.strip().strip("\r\n")
            if word and word.lower() != "word":
                words.append(word)
    return words

VALIDATE_SYSTEM = (
    "You are a Modern Greek language validator. When given a word or string, "
    "determine if it is a real standard Modern Greek word that would appear in a dictionary. "
    "Respond ONLY with valid JSON, no markdown, no backticks, no explanation. "
    'Format: {"valid": true, "standard_form": "correct form"} '
    'or {"valid": false, "reason": "brief reason"}'
)

def load_invalid() -> dict:
    if INVALID_PATH.exists():
        with open(INVALID_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_invalid(data: dict):
    with open(INVALID_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_wiktionary_lookup() -> dict:
    """Load the local Wiktionary lookup, normalizing keys to NFC Unicode."""
    import unicodedata
    if LOOKUP_PATH.exists():
        with open(LOOKUP_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        # Normalize all keys to NFC so CSV words match regardless of encoding source
        return {unicodedata.normalize("NFC", k): v for k, v in raw.items()}
    return {}

FILL_GAPS_PROMPT = """You are a Greek language expert. Given a Modern Greek word and its English translation,
fill in the missing fields. Respond ONLY with a valid JSON object — no markdown, no backticks.

JSON format (all fields required):
{
  "transliteration": "phonetic romanization",
  "example_greek": "natural example sentence in Modern Greek",
  "example_english": "English translation of the example sentence",
  "difficulty": "A1 / A2 / B1 / B2 / C1 / C2"
}"""

def enrich_from_lookup(word: str, lookup_entry: dict, api_key: str) -> dict | None:
    """
    Build a cache entry from local Wiktionary lookup data.
    Calls Haiku only to fill transliteration, example, and difficulty.
    No validation gate — word is already confirmed via lookup.
    """
    # Map POS to our standard values
    pos_map = {
        "noun": "noun", "verb": "verb", "adjective": "adjective",
        "adverb": "adverb", "preposition": "preposition",
        "conjunction": "conjunction", "pronoun": "pronoun",
        "particle": "particle", "phrase": "phrase",
    }
    pos = pos_map.get(lookup_entry.get("pos", "").lower(), lookup_entry.get("pos", ""))
    translation = lookup_entry.get("translation", "")
    definition  = lookup_entry.get("definition", "")

    # Ask Haiku to fill gaps only (no validation, smaller prompt)
    msg = f"Word: {word}\nTranslation: {translation}\nDefinition: {definition}"
    gaps = call_api(FILL_GAPS_PROMPT, msg, api_key, max_tokens=300)

    if not gaps:
        # Fallback: minimal entry without Haiku gaps
        return {
            "word":             word,
            "transliteration":  "",
            "part_of_speech":   pos,
            "translation":      translation,
            "definition":       definition,
            "example_greek":    "",
            "example_english":  "",
            "difficulty":       "?",
            "conjugation":      None,
            "declension":       None,
            "_source":          "wiktionary_lookup",
        }

    return {
        "word":             word,
        "transliteration":  gaps.get("transliteration", ""),
        "part_of_speech":   pos,
        "translation":      translation,
        "definition":       definition,
        "example_greek":    gaps.get("example_greek", ""),
        "example_english":  gaps.get("example_english", ""),
        "difficulty":       gaps.get("difficulty", "?"),
        "conjugation":      None,
        "declension":       None,
        "_source":          "wiktionary_lookup",
    }

def is_acronym(w: str) -> bool:
    """True if word is all uppercase Greek letters (2-6 chars) e.g. ΑΠΕ, ΝΑΤΟ."""
    import unicodedata
    if not (2 <= len(w) <= 6):
        return False
    return all(unicodedata.category(c) == "Lu" for c in w)

def validate_word(word: str, api_key: str) -> tuple:
    """Ask Haiku if word is real Modern Greek. Returns (is_valid, note)."""
    import urllib.request
    payload = json.dumps({
        "model": "claude-haiku-4-5", "max_tokens": 100,
        "system": VALIDATE_SYSTEM,
        "messages": [{"role": "user", "content": f"Word: {word}"}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            text = data["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
            result = json.loads(text)
            if result.get("valid"):
                return True, result.get("standard_form", word)
            return False, result.get("reason", "unknown")
    except Exception as e:
        return True, f"validation_error: {e}"  # fail open

def call_api(system: str, user_msg: str, api_key: str, max_tokens=800, retries=4) -> dict | None:
    import urllib.request
    import urllib.error

    for attempt in range(1, retries + 2):
        payload = json.dumps({
            "model":      "claude-haiku-4-5",
            "max_tokens": max_tokens,
            "system":     system,
            "messages":   [{"role": "user", "content": user_msg}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
        except json.JSONDecodeError:
            if attempt <= retries:
                max_tokens = int(max_tokens * 1.5)
                print(f"  ⚠️  truncated, retry {attempt} with {max_tokens} tokens", end="", flush=True)
                time.sleep(1)
            else:
                print(f"  ✗  still truncated after {retries} retries")
                return None
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 529:
                wait = 30 * attempt
                print(f"  ⚠️  overloaded, waiting {wait}s…", end="", flush=True)
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code}: {body[:200]}")
            return None
        except Exception as e:
            print(f"  Error: {e}")
            return None

def enrich_word(word: str, api_key: str) -> dict | None:
    return call_api(SYSTEM_PROMPT, f"Greek word: {word}", api_key, max_tokens=800)

def update_conjugation(word: str, existing: dict, api_key: str) -> dict | None:
    msg = f"Word: {word}\nExisting data:\n{json.dumps(existing, ensure_ascii=False, indent=2)}"
    return call_api(CONJUGATION_ONLY_PROMPT, msg, api_key, max_tokens=1200)

def needs_update(word: str, cache: dict) -> bool:
    d = cache[word]
    # No conjugation/declension at all
    if d.get("conjugation") is None and d.get("declension") is None:
        return True
    # Adjective with old flat format (missing singular/plural nesting)
    decl = d.get("declension") or {}
    if isinstance(decl, dict):
        for g in ["masculine", "feminine", "neuter"]:
            if g in decl and isinstance(decl[g], dict) and "singular" not in decl[g]:
                return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY", ""))
    parser.add_argument("--limit",   type=int, default=0,
                        help="Only process N words (0 = all). Useful for testing.")
    parser.add_argument("--delay",   type=float, default=0.5,
                        help="Seconds between API calls (default 0.5)")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip word validation gate (faster, less safe)")
    parser.add_argument("--use-lookup", action="store_true",
                        help="Fall back to local Wiktionary lookup for words rejected by validation gate")
    parser.add_argument("--update-conjugation", action="store_true",
                        help="Add/fix conjugation and declension for cached words")
    args = parser.parse_args()

    if not args.api_key:
        print("❌  No API key. Set ANTHROPIC_API_KEY or use --api-key")
        sys.exit(1)

    words = load_words()
    cache = load_cache()

    # ── Mode: update conjugation/declension ───────────────────────────────────
    if args.update_conjugation:
        todo = [w for w in words if w in cache and needs_update(w, cache)]

        if args.limit:
            todo = todo[:args.limit]

        print(f"🔄  Updating conjugation/declension for {len(todo)} words")
        if not todo:
            print("All words already up to date!")
            return

        errors = 0
        for i, word in enumerate(todo, 1):
            pos = cache[word].get("part_of_speech", "")
            print(f"[{i:4}/{len(todo)}] {word:<30} ({pos})", end="", flush=True)

            result = update_conjugation(word, cache[word], args.api_key)
            if result:
                cache[word] = result
                has_conj = result.get("conjugation") is not None
                has_decl = result.get("declension") is not None
                # Check adjective got nested format
                decl = result.get("declension") or {}
                adj_ok = any(
                    isinstance(decl.get(g), dict) and "singular" in decl[g]
                    for g in ["masculine","feminine","neuter"]
                )
                tag = "conj✓" if has_conj else ("decl✓" if adj_ok else "decl(flat)") if has_decl else "—"
                print(f"  [{tag}]")
            else:
                errors += 1
                print("  ✗ failed")

            if i % 25 == 0:
                save_cache(cache)
                print(f"   💾 Checkpoint ({i} updated)")

            time.sleep(args.delay)

        save_cache(cache)
        print(f"\n✅  Done! Updated {len(todo)-errors} words. Errors: {errors}")
        return

    # ── Mode: enrich new words ────────────────────────────────────────────────
    todo = [w for w in words if w not in cache]
    if args.limit:
        todo = todo[:args.limit]

    print(f"📖  Total words    : {len(words)}")
    print(f"✅  Already cached : {len(cache)}")
    print(f"⏳  To enrich      : {len(todo)}")
    if not todo:
        print("Nothing to do — all words already cached!")
        return

    invalid_log  = load_invalid()
    wikt_lookup  = load_wiktionary_lookup() if args.use_lookup else {}
    if args.use_lookup and wikt_lookup:
        print(f"📖  Wiktionary lookup loaded: {len(wikt_lookup):,} words")
    elif args.use_lookup:
        print("⚠️   Wiktionary lookup not found — run build_wiktionary_lookup.py first")
    lookup_count = 0
    skipped = 0
    errors = 0
    for i, word in enumerate(todo, 1):
        print(f"[{i:4}/{len(todo)}] {word:<30}", end="", flush=True)

        # 1. Lookup gate — check local Wiktionary dump first (no API call needed)
        import unicodedata as _ud
        word_nfc = _ud.normalize("NFC", word)
        if args.use_lookup and word_nfc in wikt_lookup:
            print(f"  [wikt]...", end="", flush=True)
            wikt_entry = wikt_lookup[word_nfc].get("en") or wikt_lookup[word_nfc].get("el") or {}
            result = enrich_from_lookup(word, wikt_entry, args.api_key)
            if result:
                cache[word] = result
                lookup_count += 1
                print(f"  ok  {result.get('translation','')}  [wiktionary]")
                time.sleep(args.delay)
                continue

        # 2. Validation gate — ask Haiku only if not in local lookup
        if not args.skip_validation and not is_acronym(word):
            is_valid, note = validate_word(word, args.api_key)
            if not is_valid:
                invalid_log[word] = note
                save_invalid(invalid_log)
                skipped += 1
                print(f"  INVALID -- {note}")
                time.sleep(0.3)
                continue
            time.sleep(0.3)

        result = enrich_word(word, args.api_key)
        if result:
            cache[word] = result
            print(f"\u2713  {result.get('translation','')}")
        else:
            errors += 1
            print("\u2717  failed")

        if i % 25 == 0:
            save_cache(cache)
            print(f"   💾 Checkpoint ({len(cache)} words cached)")

        time.sleep(args.delay)

    save_cache(cache)
    print(f"\n✅  Done! {len(cache)} words in cache. Errors: {errors}")
    if lookup_count:
        print(f"📖  {lookup_count} words enriched from Wiktionary lookup")
    if not args.skip_validation and skipped:
        print(f"⚠️   {skipped} invalid words skipped — see data/invalid_words.json")
    print(f"📁  Cache: {CACHE_PATH}")

if __name__ == "__main__":
    main()
