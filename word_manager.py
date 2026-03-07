"""
word_manager.py
───────────────
Utility to manage individual words in the Greek flashcard app.

Usage:
    python word_manager.py --delete  "συνοδεύομαι"
    python word_manager.py --recreate "συνοδεύομαι"
    python word_manager.py --inspect  "συνοδεύομαι"
    python word_manager.py --list-broken
"""

import json
import re
import asyncio
import argparse
from pathlib import Path

BASE_DIR   = Path(__file__).parent
CACHE_PATH = BASE_DIR / "data" / "enriched_cache.json"
AUDIO_DIR  = BASE_DIR / "audio"
MIN_SIZE   = 100

VOICE_EL = "el-GR-AthinaNeural"
VOICE_EN = "en-US-JennyNeural"

def safe_fn(word): return re.sub(r'[^\w]', '_', word)

def audio_paths(word):
    safe = safe_fn(word)
    return {
        "word":       AUDIO_DIR / f"{safe}_word.mp3",
        "definition": AUDIO_DIR / f"{safe}_definition.mp3",
        "example":    AUDIO_DIR / f"{safe}_example.mp3",
    }

def load_cache():
    if CACHE_PATH.exists():
        return json.load(open(CACHE_PATH, encoding="utf-8"))
    return {}

def save_cache(cache):
    json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

# ── Actions ───────────────────────────────────────────────────────────────────

def delete_word(word):
    cache = load_cache()

    # Remove audio files
    paths = audio_paths(word)
    for label, path in paths.items():
        if path.exists():
            path.unlink()
            print(f"  🗑️  Deleted: {path.name}")
        else:
            print(f"  ⚠️  Not found: {path.name}")

    # Remove from cache
    if word in cache:
        del cache[word]
        save_cache(cache)
        print(f"  🗑️  Removed from cache: {word}")
    else:
        print(f"  ⚠️  '{word}' not in cache")

    print(f"\n✅  Done. '{word}' fully deleted.")

async def recreate_word(word):
    try:
        import edge_tts
    except ImportError:
        print("❌  edge-tts not installed. Run: pip install edge-tts")
        return

    cache = load_cache()
    if word not in cache:
        print(f"❌  '{word}' not in cache — can't recreate audio without data.")
        print(f"   Run enrich_words.py first, or add it manually to the cache.")
        return

    data  = cache[word]
    paths = audio_paths(word)

    tasks = [
        (paths["word"],       word,                                        VOICE_EL),
        (paths["definition"], data.get("definition", data.get("translation", "")), VOICE_EN),
        (paths["example"],    data.get("example_greek", ""),               VOICE_EL),
    ]

    print(f"🎙️  Recreating audio for: {word}")
    for path, text, voice in tasks:
        if not text.strip():
            print(f"  ⚠️  Skipping {path.name} — no text")
            continue
        try:
            await edge_tts.Communicate(text, voice).save(str(path))
            size = path.stat().st_size
            print(f"  ✓  {path.name}  ({size:,} bytes)")
        except Exception as e:
            print(f"  ✗  {path.name}  Error: {e}")

    print(f"\n✅  Done.")

def inspect_word(word):
    cache = load_cache()
    paths = audio_paths(word)

    print(f"\n📋  Word: {word}")
    print("─" * 50)

    if word in cache:
        data = cache[word]
        print(f"  Translation  : {data.get('translation','—')}")
        print(f"  Transliteral : {data.get('transliteration','—')}")
        print(f"  Part of speech: {data.get('part_of_speech','—')}")
        print(f"  Difficulty   : {data.get('difficulty','—')}")
        print(f"  Definition   : {data.get('definition','—')}")
        print(f"  Example (GR) : {data.get('example_greek','—')}")
        print(f"  Example (EN) : {data.get('example_english','—')}")
    else:
        print("  ⚠️  Not in cache")

    print("\n  Audio files:")
    for label, path in paths.items():
        exists = path.exists()
        size   = path.stat().st_size if exists else 0
        status = f"✓  {size:,} bytes" if exists and size >= MIN_SIZE else \
                 f"⚠️  empty ({size} bytes)" if exists else "✗  missing"
        print(f"    {label:<12}: {status}")

def list_broken():
    cache = load_cache()
    broken = []
    for word in cache:
        paths = audio_paths(word)
        for label, path in paths.items():
            is_bad = not path.exists() or path.stat().st_size < MIN_SIZE
            if is_bad:
                broken.append((word, label))

    if not broken:
        print("✅  No broken audio files found!")
        return

    print(f"⚠️  Found {len(broken)} broken audio files:\n")
    for word, label in broken:
        print(f"  {word:<40} {label}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Greek Flashcard Word Manager")
    parser.add_argument("--delete",      metavar="WORD", help="Delete word and all its audio")
    parser.add_argument("--recreate",    metavar="WORD", help="Recreate audio files for a word")
    parser.add_argument("--inspect",     metavar="WORD", help="Show all info and audio status for a word")
    parser.add_argument("--list-broken", action="store_true", help="List all words with broken audio")
    args = parser.parse_args()

    if args.delete:
        confirm = input(f"⚠️  Delete '{args.delete}' and all its audio? (y/n): ")
        if confirm.lower() == "y":
            delete_word(args.delete)
        else:
            print("Cancelled.")

    elif args.recreate:
        asyncio.run(recreate_word(args.recreate))

    elif args.inspect:
        inspect_word(args.inspect)

    elif args.list_broken:
        list_broken()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()