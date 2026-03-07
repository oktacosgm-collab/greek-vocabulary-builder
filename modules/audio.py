"""modules/audio.py – audio file helpers and playback"""
import re
import streamlit as st
from pathlib import Path
from .config import AUDIO_DIR

def safe_fn(word: str) -> str:
    return re.sub(r'[^\w]', '_', word)

def r2_url(filename: str) -> str:
    base = st.secrets.get("R2_BASE_URL", "")
    return f"{base}/{filename}" if base else ""

def read_audio(path) -> bytes | None:
    p = Path(path)
    if p.exists() and p.stat().st_size > 100:
        return p.read_bytes()
    return None

def play_sequence(data: dict, word: str):
    safe  = safe_fn(word)
    defn  = data.get("definition", data.get("translation", ""))
    ex    = data.get("example_greek", "")
    ex_en = data.get("example_english", "")

    st.markdown("##### 🇬🇷 Greek word")
    audio = read_audio(AUDIO_DIR / f"{safe}_word.mp3")
    if audio: st.audio(audio, format="audio/mp3")
    else:
        url = r2_url(f"{safe}_word.mp3")
        if url: st.audio(url, format="audio/mp3")
        else: st.warning("Audio not available")

    st.markdown("##### 📊 English definition")
    st.markdown(f"> {defn}")
    audio = read_audio(AUDIO_DIR / f"{safe}_definition.mp3")
    if audio: st.audio(audio, format="audio/mp3")
    else:
        url = r2_url(f"{safe}_definition.mp3")
        if url: st.audio(url, format="audio/mp3")
        else: st.warning("Audio not available")

    if ex:
        st.markdown("##### 🇬🇷 Example sentence")
        st.markdown(f"*{ex}*")
        st.caption(ex_en)
        audio = read_audio(AUDIO_DIR / f"{safe}_example.mp3")
        if audio: st.audio(audio, format="audio/mp3")
        else:
            url = r2_url(f"{safe}_example.mp3")
            if url: st.audio(url, format="audio/mp3")
            else: st.warning("Audio not available")