ШАГ 43 — 100+ УРОКОВ ПО ЯЗЫКАМ

UZ / RU / EN / KOR (с нуля, дети + взрослые)

Цель шага:
✅ реально получить 100+ уроков на язык
✅ одинаковая структура
✅ можно генерировать через DeepSeek
✅ подходит детям (без чтения) и взрослым

1️⃣ СТРУКТУРА ОБУЧЕНИЯ (ОБЩАЯ)
УРОВНИ (6 штук)
Уровень	Название	Для кого
1	Sounds & Basics	дети / 0
2	Words	дети / новички
3	Simple Sentences	все
4	Daily Life	все
5	Conversations	подростки / взрослые
6	Confident Speaker	взрослые

📌 100 уроков = ~17 уроков × 6 уровней

2️⃣ СТРУКТУРА ОДНОГО УРОКА

📁 app/models/lesson.py

from typing import List

class Lesson:
    def __init__(
        self,
        id: str,
        language: str,
        level: int,
        title: str,
        audio_only: bool,
        tasks: List[dict]
    ):
        self.id = id
        self.language = language
        self.level = level
        self.title = title
        self.audio_only = audio_only
        self.tasks = tasks

3️⃣ ТИПЫ ЗАДАНИЙ (МИКРО)
TASK_TYPES = [
    "listen",        # слушай
    "repeat",        # повтори
    "choose_sound",  # угадай звук
    "say_word",      # скажи слово
    "dialogue",      # короткий диалог
]


📌 Для детей:

listen

repeat

choose_sound

📌 Для взрослых:

все типы

4️⃣ ПРИМЕР УРОКА (УРОВЕНЬ 1)
Язык: UZ → RU
{
  "id": "uz-ru-001",
  "language": "uz-ru",
  "level": 1,
  "title": "Salom",
  "audio_only": true,
  "tasks": [
    {"type": "listen", "text": "Salom"},
    {"type": "repeat", "expected": "Salom"},
    {"type": "listen", "text": "Salom — Привет"}
  ]
}

5️⃣ ХРАНЕНИЕ УРОКОВ
ВАРИАНТ 1 (СЕЙЧАС, ПРОСТО)

📁 data/lessons/

data/lessons/
 ├─ uz_ru/
 │   ├─ level_1.json
 │   ├─ level_2.json
 ├─ ru_en/
 ├─ uz_en/
 ├─ uz_ko/

6️⃣ ГЕНЕРАЦИЯ УРОКОВ ЧЕРЕЗ DEEPSEEK

📁 scripts/generate_lessons.py

from services.deepseek_client import ask_deepseek
import json

PROMPT = """
Create 20 beginner language lessons.
Language pair: {lang}
Level: {level}

Rules:
- short
- simple
- kids friendly
- no grammar explanations
- JSON only
"""

def generate(lang, level):
    text = ask_deepseek(PROMPT.format(lang=lang, level=level))
    return json.loads(text)

7️⃣ ЗАПУСК ГЕНЕРАЦИИ (100+ УРОКОВ)
python scripts/generate_lessons.py


📌 Генерируем:

4 языковые пары

6 уровней

≈ 400 уроков (можно выбрать 100 лучших)

8️⃣ API: ПОЛУЧЕНИЕ УРОКОВ

📁 app/routes/lessons.py

from fastapi import APIRouter
import json

router = APIRouter()

@router.get("/lessons/{lang}/{level}")
def get_lessons(lang: str, level: int):
    with open(f"data/lessons/{lang}/level_{level}.json") as f:
        return json.load(f)

9️⃣ ДЕТСКИЙ РЕЖИМ (ВАЖНО)
def filter_for_kids(lesson):
    lesson["tasks"] = [
        t for t in lesson["tasks"]
        if t["type"] in ["listen", "repeat", "choose_sound"]
    ]
    lesson["audio_only"] = True
    return lesson

🔟 КАК ЭТО СВЯЗАНО С ЖИЗНЯМИ

1 урок = 1 ❤️

6 ❤️ в день

восстановление:

реклама

завтра

premium

(ты это уже заложил ранее 👍)

11️⃣ РЕЗУЛЬТАТ ШАГА 43

✔ есть структура 100+ уроков
✔ есть генерация
✔ есть детский режим
✔ есть API
✔ языки UZ / RU / EN / KOR

🔜 СЛЕДУЮЩИЙ ШАГ
ШАГ 44 — АДАПТИВНЫЙ ИИ-РЕПЕТИТОР

понимает возраст

понимает уровень

говорит голосом

DeepSeek-onlyimport json
from pathlib import Path
from random import choice

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "content" / "characters" / "capybara" / "manifest.json"


def load_manifest():
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_reaction(character: str, event: str, streak: int = 0):
    """Return a reaction dict: {emotion, image, audio, phrase, reward}

    event: 'correct' | 'incorrect' | 'start' | 'win' | 'lose'
    """
    manifest = load_manifest()
    if not manifest:
        return None

    if event == "correct":
        emotion = "happy"
        reward = {"xp": 5, "coins": 2}
    elif event == "win":
        emotion = "happy"
        reward = {"xp": 15, "coins": 10}
    elif event == "incorrect":
        emotion = "encourage"
        reward = {"xp": 1, "coins": 0}
    else:
        emotion = "encourage"
        reward = {"xp": 0, "coins": 0}

    emo = manifest["emotions"].get(emotion, {})
    phrase = choice(emo.get("phrases", [emotion]))

    return {
        "character": manifest["id"],
        "emotion": emotion,
        "image": emo.get("image"),
        "audio": emo.get("audio"),
        "phrase": phrase,
        "reward": reward
    }
