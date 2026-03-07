# 🇬🇷 Greek Word Flashcards

A Streamlit app for learning Greek vocabulary with flashcards, audio pronunciation, and live news word extraction.

---

## 📦 Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 🚀 Features

| Feature | Description |
|---|---|
| **Flashcard Mode** | Flip cards to reveal translation + example sentence |
| **🔊 Audio** | Listen to Greek pronunciation via Google TTS |
| **📊 Score tracking** | Mark words as Known or for Review |
| **Browse All** | Search/browse the full word list |
| **📰 News Words** | Fetch live Greek news and extract words to study |
| **Shuffle** | Randomise card order each session |

---

## 📂 Project Structure

```
greek_app/
│
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── README.md
│
├── data/
│   ├── words_basic.json     # 15 basic words
│   ├── words_politics.json  # 15 politics words
│   ├── words_economy.json   # 15 economy words
│   └── words_culture.json   # 10 culture words
│
└── audio/                   # Auto-generated MP3 cache (gTTS)
```

---

## ➕ Adding Your Own Words

Edit any JSON file in `data/` or create a new one. Each word entry follows this format:

```json
{
  "word": "δημοκρατία",
  "transliteration": "dimokratía",
  "translation": "democracy",
  "example": "Η δημοκρατία είναι θεμέλιο.",
  "example_translation": "Democracy is the foundation.",
  "part_of_speech": "noun"
}
```

To add a new category, add the file to `data/` and register it in `app.py`:

```python
CATEGORY_FILES = {
    "🔤 Basic":    "words_basic.json",
    "🏛️ Politics": "words_politics.json",
    ...
    "⚕️ Health":   "words_health.json",   # ← your new category
}
```

---

## 📱 Mobile Port (Future)

When ready to go mobile:
- **Quick option:** Deploy to Streamlit Cloud → access via mobile browser
- **Native app:** Build Flutter frontend + FastAPI backend (Python logic stays the same)

---

## 🔧 Requirements

- Python 3.9+
- Internet connection (for gTTS audio generation on first use — cached afterwards)
- Internet connection (for News Words feature)
