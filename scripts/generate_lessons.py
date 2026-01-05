from scripts.vocab import VOCAB
from scripts.levels import LEVELS
import json
from services.deepseek_client import ask_deepseek
import os

def generate(native, foreign):
    lessons = []
    lesson_id = 1

    for level, topics in LEVELS.items():
        for topic in topics:
            if topic not in VOCAB:
                continue

            words = []
            for i in range(5):
                words.append({
                    "emoji": "🎯",
                    "native": VOCAB[topic][native][i],
                    "foreign": VOCAB[topic][foreign][i]
                })

            lessons.append({
                "id": f"{native}_{foreign}_{lesson_id}",
                "level": level,
                "topic": topic,
                "words": words
            })
            lesson_id += 1

    return lessons


def save(filename, lessons):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("LESSONS = ")
        f.write(str(lessons))


if __name__ == "__main__":
    pairs = [
        ("ru", "en"),
        ("ru", "ko"),
        ("uz", "en"),
        ("uz", "ko")
    ]

    for native, foreign in pairs:
        lessons = generate(native, foreign)
        save(f"./app/lessons/{native}_{foreign}.py", lessons)
        print(f"✔ Generated {native}_{foreign}.py ({len(lessons)} lessons)")


TOPICS = {
    "animals": ["cat", "dog", "cow", "mouse", "chicken"],
    "colors": ["red", "blue", "green", "yellow"],
}


LANGUAGES = ["EN", "KOR"]
LEVELS = {
    "A0": ["Greeting", "Numbers", "Colors", "Family", "Animals", "Food"],
    "A1": ["Daily life", "Emotions", "Time", "School", "Home"],
    "A2": ["Dialogues", "Travel", "Shopping", "Stories"]
}

LESSONS_PER_TOPIC = 5

def load_template():
    with open("content/templates/lesson_prompt.txt") as f:
        return f.read()

template = load_template()

for lang in LANGUAGES:
    for level, topics in LEVELS.items():
        lesson_number = 1
        for topic in topics:
            for _ in range(LESSONS_PER_TOPIC):
                prompt = template \
                    .replace("{{TARGET_LANGUAGE}}", lang) \
                    .replace("{{LEVEL}}", level) \
                    .replace("{{TOPIC}}", topic) \
                    .replace("{{LESSON_NUMBER}}", str(lesson_number)) \
                    .replace("{{LANG}}", lang.lower())

                lesson_text = ask_deepseek(prompt)

                path = f"content/{lang.lower()}/{level.lower()}"
                os.makedirs(path, exist_ok=True)

                with open(f"{path}/lesson_{lesson_number}.json", "w", encoding="utf-8") as f:
                    f.write(lesson_text)

                lesson_number += 1
