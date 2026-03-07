"""modules/data_loader.py — cache and word list loading"""
import json
import streamlit as st
from .config import CACHE_PATH, DATA_DIR


@st.cache_data
def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data
def load_raw_words():
    csv_path = DATA_DIR / "greek_words_to_import.csv"
    words = []
    if csv_path.exists():
        with open(csv_path, encoding="utf-8-sig") as f:
            for line in f:
                w = line.strip()
                if w and w.lower() != "word":
                    words.append(w)
    return words


def build_word_map(cache: dict, raw_words: list) -> dict:
    """Merge cache with raw word list, filling defaults for unenriched words."""
    all_words = {}
    for w in raw_words:
        all_words[w] = cache[w] if w in cache else {
            "word": w, "translation": "—",
            "definition": "Not yet enriched.",
            "example_greek": "", "example_english": "",
            "transliteration": "—", "part_of_speech": "—", "difficulty": "?"
        }
    return all_words
