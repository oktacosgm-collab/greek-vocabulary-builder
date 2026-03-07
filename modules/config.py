"""modules/config.py — shared paths and constants"""
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data"
AUDIO_DIR  = BASE_DIR / "audio"
CACHE_PATH = DATA_DIR / "enriched_cache.json"
SRS_PATH   = DATA_DIR / "srs_progress.json"

AUDIO_DIR.mkdir(exist_ok=True)

ARTICLE = {"masculine": "ο", "feminine": "η", "neuter": "το"}
