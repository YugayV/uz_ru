import json
import os
import sys
# ensure project root is on sys.path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.deepseek_client import ask_deepseek

PAIRS = [
    ("uz", "ru"),
    ("ru", "en"),
    ("uz", "en"),
    ("uz", "ko"),
]

LEVELS = {
    1: "A0",
    2: "A1",
    3: "A2",
    4: "B1",
    5: "B2",
    6: "C1",
}

PROMPT_TEMPLATE = '''
You are an expert curriculum writer. Produce a short JSON array of {count} lessons for language pair {pair} at level {level}.
Each lesson must have:
- id (string)
- language (e.g. "uz-ru")
- level (int)
- title (short)
- audio_only (bool)
- tasks: an array of tasks where each task is a dict with keys 'type' and simple fields like 'text' or 'expected'
Make the lessons child-friendly (no text in tasks when possible) and concise. Respond with JSON only.
'''

LESSONS_PER_LEVEL = 10


def generate_pair(pair):
    native, foreign = pair
    pair_key = f"{native}_{foreign}"

    out_dir = os.path.join("data", "lessons", pair_key)
    os.makedirs(out_dir, exist_ok=True)

    for level_num, level_name in LEVELS.items():
        prompt = PROMPT_TEMPLATE.format(count=LESSONS_PER_LEVEL, pair=pair_key, level=level_name)
        try:
            text = ask_deepseek(prompt)
            lessons = json.loads(text)
        except Exception as e:
            print("DeepSeek error, falling back to template:", e)
            lessons = []
            for i in range(1, LESSONS_PER_LEVEL + 1):
                lessons.append({
                    "id": f"{pair_key}_{level_num}_{i}",
                    "language": pair_key,
                    "level": level_num,
                    "title": f"Lesson {i}",
                    "audio_only": True,
                    "tasks": [
                        {"type": "listen", "text": "Hello"},
                        {"type": "repeat", "expected": "Hello"}
                    ]
                })

        with open(os.path.join(out_dir, f"level_{level_num}.json"), "w", encoding="utf-8") as f:
            json.dump(lessons, f, ensure_ascii=False, indent=2)
        print(f"Saved {out_dir}/level_{level_num}.json ({len(lessons)} lessons)")


if __name__ == "__main__":
    for pair in PAIRS:
        generate_pair(pair)
