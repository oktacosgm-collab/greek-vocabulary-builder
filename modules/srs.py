"""
modules/srs.py — Spaced Repetition System (SM-2 algorithm)
────────────────────────────────────────────────────────────
Each word has a card record:
  {
    "interval":    1,          # days until next review
    "ease":        2.5,        # ease factor (≥1.3)
    "repetitions": 0,          # consecutive correct answers
    "due":         "2024-01-01", # ISO date string of next review
    "last_score":  null        # 0-5 last quality score
  }

Quality scores (passed in from UI):
  5 — perfect, immediate recall
  4 — correct, slight hesitation
  3 — correct with difficulty
  2 — wrong but answer felt familiar
  1 — wrong, answer was hard
  0 — complete blackout
"""
import json
from datetime import date, timedelta
from .config import SRS_PATH


# ── Persistence ───────────────────────────────────────────────────────────────

def load_srs() -> dict:
    if SRS_PATH.exists():
        with open(SRS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_srs(data: dict):
    with open(SRS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── SM-2 core ─────────────────────────────────────────────────────────────────

def _default_card() -> dict:
    return {
        "interval":    1,
        "ease":        2.5,
        "repetitions": 0,
        "due":         date.today().isoformat(),
        "last_score":  None,
    }


def review(card: dict, quality: int) -> dict:
    """
    Apply one SM-2 review step.
    quality: 0–5 (5 = perfect, 0 = blackout)
    Returns updated card dict.
    """
    card = card.copy()
    q = max(0, min(5, quality))

    if q >= 3:
        # Correct answer
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card["ease"])
        card["repetitions"] += 1
    else:
        # Wrong answer — reset
        card["repetitions"] = 0
        card["interval"]    = 1

    # Update ease factor
    card["ease"] = max(1.3, card["ease"] + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    card["due"]  = (date.today() + timedelta(days=card["interval"])).isoformat()
    card["last_score"] = q
    return card


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_card(srs_data: dict, word: str) -> dict:
    """Return card for word, creating default if new."""
    return srs_data.get(word, _default_card())


def is_due(card: dict) -> bool:
    """True if card is due for review today or overdue."""
    return card.get("due", date.today().isoformat()) <= date.today().isoformat()


def get_due_words(srs_data: dict, word_list: list) -> list:
    """Return words that are due for review today, sorted by due date."""
    due = []
    for w in word_list:
        card = get_card(srs_data, w)
        if is_due(card):
            due.append((card.get("due", date.today().isoformat()), w))
    due.sort()
    return [w for _, w in due]


def get_new_words(srs_data: dict, word_list: list) -> list:
    """Words never reviewed yet, in random order."""
    import random
    words = [w for w in word_list if w not in srs_data]
    random.shuffle(words)
    return words


def get_stats(srs_data: dict, word_list: list) -> dict:
    """Summary statistics for the SRS deck."""
    today = date.today().isoformat()
    new      = [w for w in word_list if w not in srs_data]
    due      = [w for w in word_list if w in srs_data and srs_data[w].get("due","") <= today]
    learning = [w for w in word_list if w in srs_data and srs_data[w].get("repetitions",0) < 3]
    mature   = [w for w in word_list if w in srs_data and srs_data[w].get("repetitions",0) >= 3]
    return {
        "new":      len(new),
        "due":      len(due),
        "learning": len(learning),
        "mature":   len(mature),
        "total":    len(word_list),
    }


# ── Quality label helpers ─────────────────────────────────────────────────────

QUALITY_BUTTONS = [
    (5, "😄 Easy",       "Remembered perfectly"),
    (4, "🙂 Good",       "Correct with slight hesitation"),
    (3, "😐 Hard",       "Correct but difficult"),
    (1, "😟 Wrong",      "Incorrect — will repeat soon"),
]
