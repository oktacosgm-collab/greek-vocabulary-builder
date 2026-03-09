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
    # Check URL query param first
    params = st.query_params
    if "lang" in params and params["lang"] in LANGUAGES.values():
        if st.session_state.get("lang") != params["lang"]:
            st.session_state["lang"] = params["lang"]
    return st.session_state.get("lang", "en")

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
    # Find current language display name
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
        st.rerun()
