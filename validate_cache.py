"""
validate_cache.py
─────────────────
Checks words in enriched_cache.json against Haiku validation.
Flags suspicious entries but does NOT delete automatically — review first.

Usage:
    python validate_cache.py --word εμόψει        # test single word
    python validate_cache.py --limit 50            # test first 50 cached words
    python validate_cache.py                       # test all cached words
    python validate_cache.py --remove              # delete flagged words from cache
"""

import json
import time
import argparse
import os
import urllib.request
from pathlib import Path

BASE_DIR = Path(r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder")
CACHE_PATH   = BASE_DIR / "data" / "enriched_cache.json"
INVALID_PATH = BASE_DIR / "data" / "invalid_words.json"

VALIDATE_SYSTEM = (
    "You are a strict Modern Greek dictionary validator. "
    "A word is valid ONLY if it appears in standard Modern Greek dictionaries such as Babiniotis or Triantafyllidis. "
    "Be SKEPTICAL by default. Mark as invalid: typos, garbled text, archaic forms not in modern use, "
    "words with incorrect accentuation, non-Greek characters mixed in, or anything you are not highly confident about. "
    "When in doubt, mark invalid. "
    "Respond ONLY with JSON — no markdown, no backticks: "
    '{"valid": true, "standard_form": "the correct dictionary form"} '
    'or {"valid": false, "reason": "specific reason e.g. typo of X, not a real word, double accent"}'
)


def validate_word(word: str, api_key: str) -> tuple:
    """Ask Haiku if word is real Modern Greek. Returns (is_valid, note)."""
    payload = json.dumps({
        "model":      "claude-haiku-4-5",
        "max_tokens": 100,
        "system":     VALIDATE_SYSTEM,
        "messages":   [{"role": "user", "content": f"Word: {word}"}]
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            text = data["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
            result = json.loads(text)
            if result.get("valid"):
                return True, result.get("standard_form", word)
            return False, result.get("reason", "unknown")
    except Exception as e:
        return True, f"validation_error: {e}"  # fail open


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    parser.add_argument("--remove",  action="store_true", help="Remove invalid words from cache")
    parser.add_argument("--limit",   type=int, default=0, help="Only check N words (0 = all)")
    parser.add_argument("--word",    default="",          help="Test a single specific word")
    args = parser.parse_args()

    if not args.api_key:
        print("❌  No API key. Set ANTHROPIC_API_KEY or use --api-key sk-ant-...")
        return

    # ── Single word test mode ─────────────────────────────────────────────────
    if args.word:
        print(f"🔍  Testing: {args.word}\n")
        is_valid, note = validate_word(args.word, args.api_key)
        if is_valid:
            print(f"  ✓  Valid — standard form: {note}")
        else:
            print(f"  ⚠️  INVALID — {note}")
        return

    # ── Full / limited scan ───────────────────────────────────────────────────
    cache   = json.load(open(CACHE_PATH, encoding="utf-8"))
    invalid = json.load(open(INVALID_PATH, encoding="utf-8")) if INVALID_PATH.exists() else {}

    # Skip words already flagged in previous runs
    words = [w for w in cache if w not in invalid]
    if args.limit:
        words = words[:args.limit]

    print(f"🔍  Validating {len(words)} words ({len(invalid)} already flagged, skipped)…\n")

    flagged = {}
    for i, word in enumerate(words, 1):
        print(f"[{i:4}/{len(words)}] {word:<30}", end="", flush=True)
        is_valid, note = validate_word(word, args.api_key)
        if is_valid:
            print("  ✓")
        else:
            flagged[word] = note
            invalid[word] = note
            print(f"  ⚠️  INVALID — {note}")
        time.sleep(0.4)

    # Save updated invalid log
    with open(INVALID_PATH, "w", encoding="utf-8") as f:
        json.dump(invalid, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*50}")
    if flagged:
        print(f"Found {len(flagged)} invalid words:")
        for w, reason in flagged.items():
            print(f"  ❌  {w}  —  {reason}")
        if args.remove:
            for w in flagged:
                cache.pop(w, None)
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f"\n🗑️   Removed {len(flagged)} words from cache.")
        else:
            print(f"\nRe-run with --remove to delete them from cache.")
    else:
        print("Found 0 invalid words in this run.")


if __name__ == "__main__":
    main()