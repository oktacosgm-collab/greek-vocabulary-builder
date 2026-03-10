"""
modules/i18n.py  — Internationalisation helper
Supports: English (en), Japanese (ja), Greek (el)

Usage:
    from modules.i18n import t, loc, cat_label, render_language_selector, ALL_CATEGORIES

    t("tab_flashcard")          → UI string in current language
    loc(word_data, "translation") → word field, language-aware (_ja / _el suffix)
    cat_label("food_drink")     → translated category label
"""

import streamlit as st
import json
import os

# ── Supported languages ───────────────────────────────────────────────────────
LANGUAGES = {
    "en": {"label": "English",    "flag": "🇬🇧"},
    "ja": {"label": "日本語",      "flag": "🇯🇵"},
    "el": {"label": "Ελληνικά",   "flag": "🇬🇷"},
}

# Language → word-data field suffix  (English has no suffix)
LANG_SUFFIX = {
    "en": "",
    "ja": "_ja",
    "el": "_el",
}

# ── Translation cache ─────────────────────────────────────────────────────────
_cache: dict[str, dict] = {}

def _load(lang: str) -> dict:
    if lang not in _cache:
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "translations", f"{lang}.json"
        )
        try:
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except FileNotFoundError:
            _cache[lang] = {}
    return _cache[lang]


def _current_lang() -> str:
    return st.session_state.get("ui_language", "en")

def get_lang_code() -> str:
    """Public alias — returns active language code: 'en', 'ja', or 'el'."""
    return _current_lang()


# ── Public API ────────────────────────────────────────────────────────────────

def t(key: str, **kwargs) -> str:
    """Return UI string for key in the current language.
    Falls back to English if key is missing from the active language file.
    Supports .format()-style substitutions: t("srs_streak", n=5)
    """
    lang = _current_lang()
    strings = _load(lang)
    en_strings = _load("en")

    raw = strings.get(key) or en_strings.get(key) or key
    try:
        return raw.format(**kwargs) if kwargs else raw
    except KeyError:
        return raw


def loc(data: dict, field: str) -> str:
    """Return the language-aware value for a word-data field.

    Priority:
      1. field + lang_suffix  (e.g. "translation_el")
      2. field                (English fallback)
      3. ""

    Args:
        data:  word dict from enriched_cache.json
        field: base field name, e.g. "translation", "definition", "example_sentence"
    """
    lang   = _current_lang()
    suffix = LANG_SUFFIX.get(lang, "")

    if suffix:
        value = data.get(f"{field}{suffix}", "")
        if value:
            return value

    return data.get(field, "")


def cat_label(category_key: str) -> str:
    """Return the translated label for a category key.
    e.g. cat_label("food_drink") → "Φαγητό & Ποτό"  (when lang=el)
    Falls back to the raw key if no translation exists.
    """
    return t(f"cat_{category_key}", ) or category_key.replace("_", " ").title()


def render_language_selector() -> None:
    """Render the language selector widget in the sidebar.
    Writes selected language to st.session_state["ui_language"].
    Triggers a quiz reset on language switch.
    """
    current = _current_lang()

    options = list(LANGUAGES.keys())
    labels  = [f"{LANGUAGES[l]['flag']} {LANGUAGES[l]['label']}" for l in options]

    current_idx = options.index(current) if current in options else 0

    selected_label = st.sidebar.selectbox(
        t("sidebar_language"),
        labels,
        index=current_idx,
        key="lang_selector_widget",
    )

    selected_lang = options[labels.index(selected_label)]

    if selected_lang != current:
        st.session_state["ui_language"] = selected_lang
        # Reset quiz state on language change
        for key in ["quiz_words", "quiz_index", "quiz_score",
                    "listen_words", "listen_index", "listen_score"]:
            st.session_state.pop(key, None)
        st.rerun()
    else:
        st.session_state["ui_language"] = selected_lang


# ── Category list ─────────────────────────────────────────────────────────────
# Raw keys — use cat_label() for display
ALL_CATEGORIES = [
    "food_drink",
    "travel",
    "family",
    "body",
    "home",
    "work",
    "nature",
    "time",
    "numbers",
    "colors",
    "emotions",
    "health",
    "education",
    "transport",
    "shopping",
    "weather",
    "sports",
    "arts",
    "technology",
]
