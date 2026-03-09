"""modules/i18n.py — translation helper"""
import json
import streamlit as st
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

LANGUAGES = {
    "English": "en",
    "日本語": "ja",
}

@st.cache_data
def load_translations(lang_code: str) -> dict:
    path = TRANSLATIONS_DIR / f"{lang_code}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    # Fallback to English
    fallback = TRANSLATIONS_DIR / "en.json"
    with open(fallback, encoding="utf-8") as f:
        return json.load(f)

def get_lang_code() -> str:
    """Get current language code from session state or URL param."""
    # Session state takes priority
    if "lang" in st.session_state and st.session_state["lang"] in LANGUAGES.values():
        return st.session_state["lang"]
    # Fall back to URL param
    params = st.query_params
    if "lang" in params and params["lang"] in LANGUAGES.values():
        st.session_state["lang"] = params["lang"]
        return params["lang"]
    return "en"

def t(key: str, **kwargs) -> str:
    """Translate a key with optional format arguments."""
    lang_code = get_lang_code()
    translations = load_translations(lang_code)
    text = translations.get(key, key)  # fallback to key if missing
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text

def render_language_selector():
    """Render language dropdown in sidebar."""
    lang_code = get_lang_code()
    current_name = next((k for k, v in LANGUAGES.items() if v == lang_code), "English")
    lang_names = list(LANGUAGES.keys())
    selected = st.selectbox(
        t("language_selector"),
        lang_names,
        index=lang_names.index(current_name),
        key="lang_selector"
    )
    new_code = LANGUAGES[selected]
    if new_code != lang_code:
        st.session_state["lang"] = new_code
        st.query_params["lang"] = new_code
        # Reset quiz state so choices are regenerated in new language
        for key in list(st.session_state.keys()):
            if key.startswith("quiz_choices_") or key.startswith("lt_ans_") or key.startswith("lt_res_"):
                del st.session_state[key]
        st.session_state["quiz_answer"] = None
        st.session_state["quiz_done"] = False
        st.session_state["quiz_index"] = 0
        st.session_state["quiz_score"] = {"correct": 0, "wrong": 0}
        st.session_state["quiz_failed"] = []
        st.session_state["quiz_words"] = []
        st.session_state["lt_submitted"] = False
        st.session_state["lt_index"] = 0
        st.session_state["lt_score"] = {"correct": 0, "wrong": 0}
        st.session_state["lt_failed"] = []
        st.session_state["lt_words"] = []
        st.session_state["lt_done"] = False
        st.rerun()

ALL_CATEGORIES = [
    "everyday_life","food_drink","travel","nature","science","technology",
    "politics","economy","culture_arts","religion","education","health",
    "law","philosophy","emotions","family","work","sports","other"
]

def cat_label(cat_key: str) -> str:
    """Return translated display label for a category key."""
    return t(f"cat_{cat_key}")
