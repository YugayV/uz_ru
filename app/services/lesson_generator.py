from app.services.deepseek_client import ask_deepseek
import json

def generate_game_topics(level: int, source_lang: str, target_lang: str):
    """
    Generate a list of game topics for a given level and language pair using DeepSeek.
    """
    prompt = f"""
    Create a JSON list of 5 simple and fun game topics for kids learning {target_lang} (from {source_lang}) at level {level}.
    The topics should be relatable for children.
    Example topics: "Animals", "Colors", "Family", "Food", "Toys".
    Return ONLY a JSON list of strings. For example: ["topic1", "topic2", "topic3", "topic4", "topic5"]
    """
    
    try:
        response_text = ask_deepseek(prompt)
        # Assuming the response is a JSON string list, parse it
        topics = json.loads(response_text)
        return topics
    except Exception as e:
        # Fallback in case of API or parsing error
        print(f"Error generating topics: {e}")
        return ["Animals", "Colors", "Family", "Food", "Toys"]

def generate_lesson(level, topic, source_lang, target_lang):
    return {
        "title": topic,
        "level": level,
        "lesson_type": "mixed",
        "content": {
            "explain": f"Let's learn about {topic} in {target_lang}!",
            "examples": [
                f"Example 1 about {topic}",
                f"Example 2 about {topic}"
            ],
            "exercise": [
                {
                    "question": f"How to say a word related to {topic} in {source_lang}?",
                    "answer": "Answer"
                }
            ]
        }
    }


