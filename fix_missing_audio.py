"""
fix_missing_audio_edge.py
─────────────────────────
Uses Microsoft edge-tts (free, no rate limits) to generate
missing audio files. Much more reliable than gTTS for bulk generation.

Install:
    pip install edge-tts

Usage:
    python fix_missing_audio_edge.py
"""

import json
import re
import time
import asyncio
from pathlib import Path

BASE_DIR   = Path(__file__).parent
CACHE_PATH = BASE_DIR / "data" / "enriched_cache.json"
AUDIO_DIR  = BASE_DIR / "audio"

# Microsoft voices — great quality
VOICE_EL = "el-GR-AthinaNeural"   # Greek female voice
VOICE_EN = "en-US-JennyNeural"    # English female voice

def safe_fn(word): return re.sub(r'[^\w]', '_', word)

async def make_mp3_edge(text: str, voice: str, path: Path) -> bool:
    if path.exists():
        return True
    if not text.strip():
        return True
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(path))
        return True
    except Exception as e:
        print(f"    ❌  Error: {e}")
        return False

async def main():
    try:
        import edge_tts
    except ImportError:
        print("❌  edge-tts not installed. Run: pip install edge-tts")
        return

    cache = json.load(open(CACHE_PATH, encoding="utf-8"))

    # Find all incomplete words
    todo = []
    for word, data in cache.items():
        safe = safe_fn(word)
        w = AUDIO_DIR / f"{safe}_word.mp3"
        d = AUDIO_DIR / f"{safe}_definition.mp3"
        e = AUDIO_DIR / f"{safe}_example.mp3"
        if not (w.exists() and d.exists() and e.exists()):
            todo.append((word, data, w, d, e))

    if not todo:
        print("✅  All audio files already complete!")
        return

    print(f"🔧  Found {len(todo)} words with missing audio")
    print(f"🎙️  Using voices: {VOICE_EL} / {VOICE_EN}\n")

    ok = fail = 0
    for i, (word, data, w_p, d_p, e_p) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {word}")

        defn = data.get("definition", data.get("translation", ""))
        ex   = data.get("example_greek", "")

        r1 = await make_mp3_edge(word, VOICE_EL, w_p)
        r2 = await make_mp3_edge(defn, VOICE_EN, d_p)
        r3 = await make_mp3_edge(ex,   VOICE_EL, e_p)

        status = f"word={'✓' if r1 else '✗'}  def={'✓' if r2 else '✗'}  ex={'✓' if r3 else '✗'}"
        print(f"    {status}")

        if r1 and r2 and r3:
            ok += 1
        else:
            fail += 1

        time.sleep(0.5)  # gentle delay

    print(f"\n✅  Done! Complete: {ok}  Failed: {fail}")

if __name__ == "__main__":
    asyncio.run(main())