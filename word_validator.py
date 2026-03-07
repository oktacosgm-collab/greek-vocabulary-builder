import json
import re
from pathlib import Path

# Use absolute path relative to this script
BASE_DIR = Path(r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder")
cache_path = BASE_DIR / "data" / "enriched_cache.json"

cache = json.load(open(cache_path, encoding="utf-8"))

vowels = set("αεηιουωάέήίόύώ")

for word, d in cache.items():
    if not any(c in vowels for c in word.lower()):
        print(f"NO VOWELS:    {word}")
    if len(word) <= 2:
        print(f"TOO SHORT:    {word}")
    if re.search(r'[a-zA-Z]', word):
        print(f"MIXED SCRIPT: {word}")