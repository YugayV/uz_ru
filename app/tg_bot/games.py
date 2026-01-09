import random
import os
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "content" / "games"
ASSETS_DIR.mkdir(exist_ok=True)

# Basic templates for games. Each game returns a dict with keys:
# {id, type, question, options, answer, image (optional)}

def _simple_guess_word(idx: int, lang: str = "ru"):
    templates = [
        {"question": "Угадай животное: _ _ a _ _ _ a", "answer": "кабан"},
        {"question": "Угадай фрукт: _ п п _ е", "answer": "яблоко"},
        {"question": "Угадай цвет: _ л у _", "answer": "синий"},
    ]
    t = random.choice(templates)
    return {"id": f"guess_word_{idx}", "type": "guess_word", "question": t["question"], "answer": t["answer"], "image": None}


def _associations(idx: int):
    items = [
        {"question": "Что не подходит: Яблоко, Банан, Морковь, Апельсин", "answer": "Морковь"},
        {"question": "Что не подходит: Бег, Плавание, Сон, Полёт", "answer": "Сон"},
    ]
    t = random.choice(items)
    return {"id": f"assoc_{idx}", "type": "associations", "question": t["question"], "answer": t["answer"], "image": None}


def _memory(idx: int):
    # Simple matching pairs generated on the fly
    pairs = [
        ("cat", "кот"),
        ("dog", "собака"),
        ("sun", "солнце"),
    ]
    return {"id": f"memory_{idx}", "type": "memory", "question": "Найди пару для слова", "pairs": pairs, "answer": None, "image": None}


def _quiz(idx: int):
    q = {"question": "Сколько будет 2+2?", "options": ["3", "4", "5"], "answer": "4"}
    return {"id": f"quiz_{idx}", "type": "quiz", "question": q["question"], "options": q["options"], "answer": q["answer"], "image": None}


def generate_games(count: int = 50, is_kid: bool = True, lang: str = "ru"):
    games = []
    for i in range(count):
        t = random.choices([_simple_guess_word, _associations, _memory, _quiz], weights=[0.4, 0.25, 0.2, 0.15])[0]
        games.append(t(i, lang=lang) if t == _simple_guess_word else t(i))
    return games


import json
from pathlib import Path

GAMES_DIR = Path(__file__).resolve().parents[1] / "content" / "games"


def _load_games_from_disk(limit: int = 100):
    if not GAMES_DIR.exists():
        return None
    games = []
    for p in sorted(GAMES_DIR.glob('*.json')):
        try:
            games.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception:
            continue
    return games[:limit]


def get_random_game(is_kid: bool = True, lang: str = "ru"):
    disk = _load_games_from_disk(limit=200)
    if disk:
        return random.choice(disk)
    return random.choice(generate_games(20, is_kid=is_kid, lang=lang))

