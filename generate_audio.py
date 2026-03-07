"""
generate_audio.py
─────────────────
Reads enriched_cache.json and generates 3 MP3 files per word:
  audio/{word}_word.mp3        → Greek word (Greek voice)
  audio/{word}_definition.mp3  → English definition (English voice)
  audio/{word}_example.mp3     → Greek example sentence (Greek voice)

Skips files that already exist (safe to re-run).

Usage:
    python generate_audio.py
    python generate_audio.py --limit 50   # test first 50 words
"""

import json
import re
import argparse
import time
from pathlib import Path

BASE_DIR   = Path(__file__).parent
CACHE_PATH = BASE_DIR / "data" / "enriched_cache.json"
AUDIO_DIR  = BASE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

def safe_filename(word: str) -> str:
    """Convert Greek word to safe ASCII filename."""
    return re.sub(r'[^\w]', '_', word)

def generate_mp3(text: str, lang: str, path: Path, retries: int = 5) -> bool:
    if path.exists():
        return True  # already cached
    from gtts import gTTS
    for attempt in range(1, retries + 1):
        try:
            tts = gTTS(text, lang=lang)
            tts.save(str(path))
            return True
        except Exception as e:
            err = str(e)
            if "429" in err:
                wait = 10 * attempt  # 10s, 20s, 30s, 40s, 50s
                print(f"\n    ⚠️  Rate limited. Waiting {wait}s before retry {attempt}/{retries}…", end="", flush=True)
                time.sleep(wait)
            else:
                print(f"\n    TTS error: {e}")
                return False
    print(f"\n    ❌  Failed after {retries} retries.")
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    if not CACHE_PATH.exists():
        print("❌  enriched_cache.json not found. Run enrich_words.py first.")
        return

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)

    words = list(cache.items())
    if args.limit:
        words = words[:args.limit]

    print(f"🔊  Generating audio for {len(words)} words…")
    ok = skip = fail = 0

    for i, (word, data) in enumerate(words, 1):
        safe   = safe_filename(word)
        w_path = AUDIO_DIR / f"{safe}_word.mp3"
        d_path = AUDIO_DIR / f"{safe}_definition.mp3"
        e_path = AUDIO_DIR / f"{safe}_example.mp3"

        # Check if all 3 already exist
        if w_path.exists() and d_path.exists() and e_path.exists():
            skip += 1
            continue

        print(f"[{i:4}/{len(words)}] {word:<30}", end="", flush=True)

        r1 = generate_mp3(word,                      "el", w_path)
        r2 = generate_mp3(data.get("definition",""), "en", d_path)
        r3 = generate_mp3(data.get("example_greek",""), "el", e_path)

        if r1 and r2 and r3:
            ok += 1
            print("✓")
        else:
            fail += 1
            print("✗ (partial)")

        time.sleep(args.delay)

    print(f"\n✅  Generated: {ok}  |  Skipped (cached): {skip}  |  Failed: {fail}")
    print(f"📁  Audio saved to: {AUDIO_DIR}")

if __name__ == "__main__":
    main()