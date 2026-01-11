import os
import httpx
import json
from dotenv import load_dotenv
import base64
import logging

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


async def generate_interactive_game(learn_language: str, native_language: str, level: str, topic: str, game_type: str = "matching"):
    """
    Generates an interactive game for children with images and sound.
    
    Args:
        learn_language: The language the user is learning
        native_language: The user's native language (for instructions)
        level: Difficulty level (beginner, intermediate, advanced)
        topic: The topic of the game
        game_type: Type of game - "matching", "memory", "drag_drop", "quiz"
    
    Returns:
        dict: Game data with instructions, items, and visual prompts
    """
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY is not set. Please check your .env file.")
        return {"error": "DeepSeek API key not configured."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    # Map language names to readable formats
    lang_display = {
        "russian": "Russian (Русский)",
        "english": "English",
        "korean": "Korean (한국어)",
        "uzbek": "Uzbek Cyrillic (Ўзбек кирилл)"
    }
    
    learn_lang_display = lang_display.get(learn_language, learn_language.capitalize())
    native_lang_display = lang_display.get(native_language, native_language.capitalize())

    # Game-specific prompts
    game_prompts = {
        "matching": f"""
Create a fun MATCHING GAME for a child learning {learn_lang_display} at {level} level.
Topic: "{topic}"

The game should have 6 items to match. Each item has:
- A word in {learn_lang_display} (the language being learned)
- A translation or description in {native_lang_display} (for understanding)
- A visual description for generating an image

CRITICAL REQUIREMENTS:
1. Instructions must be in {native_lang_display} (native language)
2. Words to learn must be in {learn_lang_display} (target language)
3. Use simple, child-friendly vocabulary
4. Visual descriptions should be colorful and appealing to children

SCRIPT REQUIREMENTS:
- For Uzbek: use CYRILLIC (Ўзбек кирилл), NOT Latin
- For Russian: use Russian Cyrillic
- For English and Korean: use their respective scripts

Return JSON with this structure:
{{
  "game_type": "matching",
  "title": "Game title in {native_lang_display}",
  "instructions": "Clear instructions in {native_lang_display}",
  "items": [
    {{
      "id": 1,
      "word": "Word in {learn_lang_display}",
      "translation": "Translation in {native_lang_display}",
      "visual_prompt": "Description for image generation",
      "sound_text": "Text for audio (same as word)"
    }}
  ]
}}

Example for native=Uzbek Cyrillic, learning=Russian:
{{
  "game_type": "matching",
  "title": "Мевалар билан танишамиз",
  "instructions": "Расмларни тўғри сўзлар билан мослаштиринг",
  "items": [
    {{"id": 1, "word": "Яблоко", "translation": "Олма", "visual_prompt": "red apple, cartoon style", "sound_text": "Яблоко"}},
    {{"id": 2, "word": "Банан", "translation": "Банан", "visual_prompt": "yellow banana, cartoon style", "sound_text": "Банан"}}
  ]
}}
""",
        
        "memory": f"""
Create a fun MEMORY CARD GAME for a child learning {learn_lang_display} at {level} level.
Topic: "{topic}"

The game should have 8 pairs (16 cards total). Each pair consists of:
- A word in {learn_lang_display}
- A matching image

CRITICAL REQUIREMENTS:
1. Instructions must be in {native_lang_display}
2. Cards show words in {learn_lang_display}
3. Simple vocabulary suitable for children
4. Engaging visual descriptions

Return JSON with this structure:
{{
  "game_type": "memory",
  "title": "Game title in {native_lang_display}",
  "instructions": "Instructions in {native_lang_display}",
  "pairs": [
    {{
      "id": 1,
      "word": "Word in {learn_lang_display}",
      "translation": "Translation in {native_lang_display}",
      "visual_prompt": "Image description",
      "sound_text": "Word for audio"
    }}
  ]
}}
""",
        
        "drag_drop": f"""
Create a fun DRAG & DROP GAME for a child learning {learn_lang_display} at {level} level.
Topic: "{topic}"

The game should have 6 items where children drag words to matching images.

CRITICAL REQUIREMENTS:
1. Instructions in {native_lang_display}
2. Draggable words in {learn_lang_display}
3. Child-friendly vocabulary
4. Colorful visual descriptions

Return JSON with this structure:
{{
  "game_type": "drag_drop",
  "title": "Game title in {native_lang_display}",
  "instructions": "Instructions in {native_lang_display}",
  "items": [
    {{
      "id": 1,
      "word": "Word in {learn_lang_display}",
      "translation": "Translation in {native_lang_display}",
      "visual_prompt": "Image description",
      "sound_text": "Word for audio"
    }}
  ]
}}
""",
        
        "quiz": f"""
Create a fun INTERACTIVE QUIZ GAME for a child learning {learn_lang_display} at {level} level.
Topic: "{topic}"

The game should have 5 questions. Each question shows an image and asks the child to identify it.

CRITICAL REQUIREMENTS:
1. Questions in {native_lang_display}
2. Answer options in {learn_lang_display}
3. Simple, engaging questions
4. Fun visual descriptions

Return JSON with this structure:
{{
  "game_type": "quiz",
  "title": "Game title in {native_lang_display}",
  "instructions": "Instructions in {native_lang_display}",
  "questions": [
    {{
      "id": 1,
      "question": "Question in {native_lang_display}",
      "visual_prompt": "Image description",
      "options": ["Option1 in {learn_lang_display}", "Option2", "Option3", "Option4"],
      "correct_index": 0,
      "sound_text": "Correct answer for audio"
    }}
  ]
}}
"""
    }

    prompt = game_prompts.get(game_type, game_prompts["matching"])
    prompt += "\n\nDo not include any text or explanations outside of the JSON object."

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a creative game designer for children's language learning apps. You respond in pure JSON format."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 1500,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            game_content = data['choices'][0]['message']['content']
            
            # Import and use extract_json_from_markdown
            from app.ai_content import extract_json_from_markdown
            clean_json = extract_json_from_markdown(game_content)
            
            try:
                game_data = json.loads(clean_json)
                return game_data
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from DeepSeek API. Raw response: {game_content}")
                return {"error": "Failed to decode JSON from the API response.", "raw_response": game_content}

    except httpx.HTTPStatusError as e:
        logger.error(f"API Error during game generation: {e.response.status_code} - {e.response.text}", exc_info=True)
        return {"error": f"DeepSeek API Error: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        logger.error(f"An unexpected error occurred during game generation: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}


async def generate_game_images(game_data: dict) -> dict:
    """
    Generates images for all items in a game.
    
    Args:
        game_data: Game data with visual_prompt fields
        
    Returns:
        dict: Game data with added image_url fields
    """
    from app.ai_content import generate_image
    
    game_type = game_data.get("game_type")
    
    if game_type == "matching" or game_type == "drag_drop":
        items = game_data.get("items", [])
        for item in items:
            visual_prompt = item.get("visual_prompt")
            if visual_prompt:
                image_url = await generate_image(visual_prompt)
                item["image_url"] = image_url
                
    elif game_type == "memory":
        pairs = game_data.get("pairs", [])
        for pair in pairs:
            visual_prompt = pair.get("visual_prompt")
            if visual_prompt:
                image_url = await generate_image(visual_prompt)
                pair["image_url"] = image_url
                
    elif game_type == "quiz":
        questions = game_data.get("questions", [])
        for question in questions:
            visual_prompt = question.get("visual_prompt")
            if visual_prompt:
                image_url = await generate_image(visual_prompt)
                question["image_url"] = image_url
    
    return game_data
