from vocab import VOCAB
from levels import LEVELS

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
        save(f"../app/lessons/{native}_{foreign}.py", lessons)
        print(f"✔ Generated {native}_{foreign}.py ({len(lessons)} lessons)")


TOPICS = {
    "animals": ["cat", "dog", "cow", "mouse", "chicken"],
    "colors": ["red", "blue", "green", "yellow"],
}
