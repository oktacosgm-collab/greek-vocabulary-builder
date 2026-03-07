"""modules/audio.py — audio file helpers and playback"""
import re
import streamlit as st
from pathlib import Path
from .config import AUDIO_DIR


def safe_fn(word: str) -> str:
    return re.sub(r'[^\w]', '_', word)


def gen_gtts(text: str, lang: str, path) -> bool:
    if Path(path).exists():
        return True
    try:
        from gtts import gTTS
        gTTS(text, lang=lang).save(str(path))
        return True
    except:
        return False


def read_audio(path) -> bytes | None:
    p = Path(path)
    if p.exists() and p.stat().st_size > 100:
        return p.read_bytes()
    return None


def play_sequence(data: dict, word: str):
    safe  = safe_fn(word)
    w_p   = AUDIO_DIR / f"{safe}_word.mp3"
    d_p   = AUDIO_DIR / f"{safe}_definition.mp3"
    e_p   = AUDIO_DIR / f"{safe}_example.mp3"
    defn  = data.get("definition", data.get("translation", ""))
    ex    = data.get("example_greek", "")
    ex_en = data.get("example_english", "")

    with st.spinner("Preparing audio…"):
        if not w_p.exists(): gen_gtts(word, "el", w_p)
        if not d_p.exists(): gen_gtts(defn, "en", d_p)
        if ex and not e_p.exists(): gen_gtts(ex, "el", e_p)

    st.markdown("##### 🇬🇷 Greek word")
    audio = read_audio(w_p)
    if audio: st.audio(audio, format="audio/mp3")
    else: st.warning("Audio not available")

    st.markdown("##### 🔊 English definition")
    st.markdown(f"> {defn}")
    audio = read_audio(d_p)
    if audio: st.audio(audio, format="audio/mp3")
    else: st.warning("Audio not available")

    if ex:
        st.markdown("##### 🇬🇷 Example sentence")
        st.markdown(f"*{ex}*")
        st.caption(ex_en)
        audio = read_audio(e_p)
        if audio: st.audio(audio, format="audio/mp3")
        else: st.warning("Audio not available")
