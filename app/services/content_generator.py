from app.services.deepseek_client import ask_deepseek
import json

def generate_topics(pair: str, level: int):
    """
    Generate a list of learning topics for a given language pair and level.
    """
    source_lang, target_lang = pair.split("-")
    
    prompt = f"""
    Create a JSON list of 7 fun topics for Uzbek-speaking kids learning {target_lang} at level {level}.
    Topics should be simple, like "Animals", "Fruits", "My Family".
    Return ONLY a JSON list of strings. Example: ["Animals", "Colors", "Toys"]
    """
    
    try:
        response = ask_deepseek(prompt)
        return json.loads(response)
    except Exception as e:
        print(f"Error generating topics: {e}")
        # Return a fallback list if the API fails
        return ["Animals", "Colors", "Family", "Food", "Toys", "Numbers", "Clothes"]

def generate_games_for_topic(pair: str, level: int, topic: str):
    """
    Generate a set of 10-15 exercises/games for a specific topic.
    """
    source_lang, target_lang = pair.split("-")

    prompt = f"""
    You are a creative teacher for Uzbek-speaking children learning {target_lang}.
    The topic is "{topic}" and the level is {level} (where 1 is beginner).
    Create a JSON list of 10 simple, visual, and audio-based exercises.
    Use these game types: "match_word_to_visual", "listen_and_repeat", "what_is_this".

    For each exercise, provide:
    1. "game_type": The type of game.
    2. "instruction_text": A simple instruction in Uzbek.
    3. "audio_text": The word or short phrase to be spoken in {target_lang}.
    4. "visual_prompt": A single, simple English keyword for a picture (e.g., "apple", "dog", "red car").
    5. "options": A list of 4 {target_lang} words for multiple-choice questions.
    6. "correct_answer": The correct {target_lang} word from the options.

    Return ONLY the JSON list.
    """

    try:
        response = ask_deepseek(prompt)
        return json.loads(response)
    except Exception as e:
        print(f"Error generating games: {e}")
        return [{"error": "Could not generate games at the moment."}]

def translate_text(text: str, source_lang: str, target_lang: str):
    """
    Translate text using DeepSeek.
    """
    prompt = f"Translate the following text from {source_lang} to {target_lang}. Return only the translated text:\n\n{text}"
    
    try:
        return ask_deepseek(prompt)
    except Exception as e:
        print(f"Error translating text: {e}")
        return "Translation failed."



