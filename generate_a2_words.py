"""
generate_a2_words.py
────────────────────
Asks Claude Haiku to generate A2-level Modern Greek vocabulary in batches.
Deduplicates against existing cache and CSV before saving.

Usage:
    python generate_a2_words.py
"""

import json
import time
import urllib.request
from pathlib import Path
import os

api_key = os.environ.get("ANTHROPIC_API_KEY")
BASE_DIR   = Path(__file__).parent
CACHE_PATH = BASE_DIR / "data" / "enriched_cache.json"
CSV_PATH   = BASE_DIR / "data" / "greek_words_to_import.csv"
OUT_PATH   = BASE_DIR / "data" / "a2_new_words.csv"

BATCH      = 80   # words per API call
MAX_ROUNDS = 20   # max calls (~1,600 words before repeats)


def load_existing() -> set:
    """Load all words already in cache and CSV to avoid duplicates."""
    existing = set()

    # From enriched cache
    if CACHE_PATH.exists():
        cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        existing.update(cache.keys())
        print(f"  📂 Cache:  {len(cache):,} words")

    # From CSV
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8-sig") as f:
            for line in f:
                w = line.strip()
                if w and w.lower() != "word":
                    existing.add(w)
        print(f"  📂 CSV:    {len(existing):,} words total (cache + csv)")

    return existing


def ask_batch(already_have: list, round_num: int) -> list:
    # Pass last 300 collected to avoid repeats within this session
    exclude_sample = already_have[-300:] if len(already_have) > 300 else already_have
    exclude = ", ".join(exclude_sample) if exclude_sample else "none yet"

    prompt = f"""List {BATCH} Modern Greek vocabulary words at CEFR A2 level.

A2 words are simple everyday words covering:
numbers, family members, food & drink, daily routines, basic verbs,
common adjectives, time expressions, weather, body parts, shopping,
transport, colours, clothing, home & furniture, emotions, directions.

Rules:
- Return ONLY a JSON array of Greek words — no explanation, no markdown, no backticks
- All words must be genuine A2 level (not A1 basics, not B1 complexity)
- Use dictionary form: nominative singular for nouns, first person singular present for verbs
- Mix word types: nouns, verbs, adjectives, adverbs
- Do NOT repeat any of these words: {exclude}

Return format example: ["αγαπώ", "βιβλίο", "καλός", "γρήγορα", "τραπέζι"]"""

    payload = json.dumps({
        "model":      "claude-haiku-4-5",
        "max_tokens": 800,
        "messages":   [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key":         API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        text = data["content"][0]["text"].strip()
        text = text.replace("```json","").replace("```","").strip()

        # Repair truncated JSON array — find last complete quoted word
        try:
            words = json.loads(text)
        except json.JSONDecodeError:
            # Find last complete "word" before truncation
            last_quote = text.rfind('",')
            if last_quote == -1:
                last_quote = text.rfind('"')
            if last_quote > 0:
                repaired = text[:last_quote+1] + "]"
                # Strip any leading [ if missing
                if not repaired.startswith("["):
                    repaired = "[" + repaired
                try:
                    words = json.loads(repaired)
                    print(f"  ⚠️  repaired truncated JSON ({len(words)} words)", end="", flush=True)
                except:
                    print(f"  ⚠️  could not repair JSON, skipping round", end="", flush=True)
                    return []
            else:
                return []

        return [w.strip() for w in words if isinstance(w, str) and w.strip()]

def main():
    print("🔍  Loading existing words…")
    existing = load_existing()
    print()

    new_words  = set()   # words found this session, not in existing
    all_seen   = set()   # everything seen this session (for dedup within session)

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"Round {round_num:2}/{MAX_ROUNDS}  —  new words so far: {len(new_words)}", end="", flush=True)

        try:
            batch = ask_batch(list(all_seen), round_num)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            time.sleep(5)
            continue

        added = 0
        for w in batch:
            all_seen.add(w)
            if w not in existing and w not in new_words:
                new_words.add(w)
                added += 1

        print(f"  → +{added} new unique  (total new: {len(new_words)})")

        # Stop early if Haiku is running out of ideas
        if added < 8:
            print("  ⚠️  Few new words returned — stopping early.")
            break

        time.sleep(1.0)

    # ── Save new words only ───────────────────────────────────────────────────
    if new_words:
        sorted_words = sorted(new_words)
        with open(OUT_PATH, "w", encoding="utf-8-sig") as f:
            for w in sorted_words:
                f.write(w + "\n")
        print(f"\n✅  Saved {len(new_words)} new A2 words to: {OUT_PATH}")
        print(f"    (All {len(existing)} existing words were excluded)")
        print(f"\nNext steps:")
        print(f"  1. Review {OUT_PATH} and remove any unwanted words")
        print(f"  2. Append to your main CSV:")
        print(f"     cat data/a2_new_words.csv >> data/greek_words_to_import.csv")
        print(f"  3. Run: python enrich_words.py")
        print(f"  4. Run: python fix_empty_audio_edge.py")
    else:
        print("\n⚠️  No new words found — all generated words already exist in your list!")


if __name__ == "__main__":
    main()