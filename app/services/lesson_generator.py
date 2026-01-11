def generate_lesson(level, topic, source_lang, target_lang):
    return {
        "title": topic,
        "level": level,
        "lesson_type": "mixed",
        "content": {
            "explain": f"Simple explanation of {topic}",
            "examples": [
                "Example 1",
                "Example 2"
            ],
            "exercise": [
                {
                    "question": f"Translate from {source_lang}",
                    "answer": "Answer"
                }
            ]
        }
    }


