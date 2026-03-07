"""
fix_empty_audio_edge.py
───────────────────────
Finds all empty/corrupt audio files (under 100 bytes) and
regenerates them using Microsoft edge-tts (no rate limits).

Install:
    pip install edge-tts

Usage:
    python fix_empty_audio_edge.py
"""

import json
import re
import asyncio
import time
from pathlib import Path

BASE_DIR   = Path(__file__).parent
CACHE_PATH = BASE_DIR / "data" / "enriched_cache.json"
AUDIO_DIR  = BASE_DIR / "audio"

VOICE_EL = "el-GR-AthinaNeural"   # Greek female
VOICE_EN = "en-US-JennyNeural"    # English female

MIN_SIZE = 100  # bytes — anything smaller is considered empty/corrupt

def safe_fn(word): return re.sub(r'[^\w]', '_', word)

async def make_mp3(text: str, voice: str, path: Path) -> bool:
    """Generate MP3 using edge-tts, overwriting if empty."""
    if not text or not text.strip():
        return True
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(path))
        # Verify file was actually written
        if path.exists() and path.stat().st_size >= MIN_SIZE:
            return True
        else:
            print(f"    ⚠️  File too small after generation: {path.name}")
            return False
    except Exception as e:
        print(f"    ❌  Error: {e}")
        return False

async def main():
    try:
        import edge_tts
    except ImportError:
        print("❌  edge-tts not installed. Run: pip install edge-tts")
        return

    if not CACHE_PATH.exists():
        print("❌  enriched_cache.json not found.")
        return

    cache = json.load(open(CACHE_PATH, encoding="utf-8"))

    # Find all empty/missing/corrupt files
    todo = []
    for word, data in cache.items():
        safe = safe_fn(word)
        entries = [
            (AUDIO_DIR / f"{safe}_word.mp3",       word,                                      VOICE_EL),
            (AUDIO_DIR / f"{safe}_definition.mp3", data.get("definition", data.get("translation", "")), VOICE_EN),
            (AUDIO_DIR / f"{safe}_example.mp3",    data.get("example_greek", ""),             VOICE_EL),
        ]
        for path, text, voice in entries:
            is_empty = not path.exists() or path.stat().st_size < MIN_SIZE
            if is_empty and text and text.strip():
                todo.append((path, text, voice, word))

    print(f"🔧  Found {len(todo)} empty/missing audio files to fix")
    print(f"🎙️  Using edge-tts (no rate limits)\n")

    if not todo:
        print("✅  Nothing to fix!")
        return

    ok = fail = 0
    for i, (path, text, voice, word) in enumerate(todo, 1):
        lang = "GR" if "el-GR" in voice else "EN"
        suffix = path.stem.split("_")[-1]
        print(f"[{i:4}/{len(todo)}] {word:<35} {suffix:<12}", end="", flush=True)

        success = await make_mp3(text, voice, path)
        if success:
            ok += 1
            print("✓")
        else:
            fail += 1
            print("✗")

        # Small delay to be polite
        await asyncio.sleep(0.2)

        # Progress checkpoint every 100 files
        if i % 100 == 0:
            print(f"\n   ✅ Checkpoint: {ok} fixed, {fail} failed so far\n")

    print(f"\n{'='*50}")
    print(f"✅  Fixed : {ok}")
    print(f"❌  Failed: {fail}")
    print(f"📁  Audio : {AUDIO_DIR}")

    if fail > 0:
        print(f"\n⚠️  {fail} files still failed. Re-run the script to retry.")

if __name__ == "__main__":
    asyncio.run(main())
