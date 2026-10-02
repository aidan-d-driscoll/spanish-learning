"""Load quiz data and persist favorites without touching source JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
VOCAB_PATH = DATA_DIR / "spanish_vocabulary.json"
CONJ_PATH = DATA_DIR / "spanish-conjugations.json"
FAVORITES_PATH = ROOT / "user_favorites.json"

VOCAB_LABELS = {
    "noun": "Nouns",
    "infinitive": "Infinitives",
    "adjective": "Adjectives",
    "adverb": "Adverbs",
    "phrase": "Phrases",
    "pronoun": "Pronouns",
    "determiner": "Determiners",
    "preposition": "Prepositions",
    "conjunction": "Conjunctions",
    "interjection": "Interjections",
}

MOOD_TENSES = {
    "indicative": ["present", "preterite", "imperfect", "conditional", "future"],
    "subjunctive": ["present", "imperfect", "future"],
    "imperative": ["affirmative", "negative"],
}

PERSONS = ["yo", "tú", "él/ella/Ud.", "nosotros", "ellos/ellas/Uds."]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_vocabulary() -> dict[str, dict[str, str]]:
    data = load_json(VOCAB_PATH)
    return {category: dict(terms) for category, terms in data.items() if isinstance(terms, dict)}


def load_conjugations() -> dict[str, dict]:
    return load_json(CONJ_PATH)


def default_favorites() -> dict:
    return {"vocab": [], "verbs": []}


def load_favorites() -> dict:
    if not FAVORITES_PATH.exists():
        return default_favorites()
    try:
        data = load_json(FAVORITES_PATH)
    except (OSError, json.JSONDecodeError):
        return default_favorites()
    vocab = data.get("vocab") if isinstance(data, dict) else None
    verbs = data.get("verbs") if isinstance(data, dict) else None
    return {
        "vocab": [item for item in vocab] if isinstance(vocab, list) else [],
        "verbs": [item for item in verbs] if isinstance(verbs, list) else [],
    }


def save_favorites(favorites: dict) -> None:
    payload = {
        "vocab": sorted(set(favorites.get("vocab", []))),
        "verbs": sorted(set(favorites.get("verbs", []))),
    }
    FAVORITES_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def vocab_id(category: str, spanish: str) -> str:
    return f"{category}::{spanish}"


def parse_vocab_id(item_id: str) -> tuple[str, str]:
    category, spanish = item_id.split("::", 1)
    return category, spanish
