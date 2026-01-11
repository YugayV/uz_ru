import os
import httpx
import json
from dotenv import load_dotenv
import base64
import logging

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def extract_json_from_markdown(text: str) -> str:
    """
    Extracts JSON from markdown code blocks if present.
    DeepSeek sometimes returns JSON wrapped in ```json ... ```
    
    Args:
        text: Response text that may contain markdown code blocks
        
    Returns:
        Clean JSON string
    """
    import re
    
    # Try to find JSON in markdown code block
    markdown_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(markdown_pattern, text, re.DOTALL)
    
    if match:
        return match.group(1)
    
    # If no markdown block found, return original text
    return text.strip()


async def translate_text(text: str, target_language: str):
    """
    Translates text using the DeepSeek API.
    """
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY is not set. Please check your .env file.")
        return "Error: DeepSeek API key not configured."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    prompt = f"Translate the following text to {target_language}. Provide only the translated text, without any additional explanations or context.\\n\\nText to translate: \\\"{text}\\\"\""

    payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are an assistant that creates language exercises for children and responds in pure JSON format."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.8,
    "max_tokens": 500,
}

    logger.debug(f"DeepSeek API Request URL: {DEEPSEEK_API_URL}") # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    logger.debug(f"DeepSeek API Request Headers: {headers}") # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    logger.debug(f"DeepSeek API Request Payload: {payload}") # <-- ДОБАВЬТЕ ЭТУ СТРОКУ

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            translation = data['choices'][0]['message']['content']
            return translation

    except httpx.HTTPStatusError as e:
        logger.error(f"API Error during translation: {e.response.status_code} - {e.response.text}", exc_info=True)
        return f"Error communicating with DeepSeek API: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.error(f"An unexpected error occurred during translation: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"


async def generate_multiple_choice_exercise(learn_language: str, native_language: str, level: str, topic: str, exclude_hashes: list[str] = None):
    """
    Generates a multiple-choice exercise for a specific topic as a JSON object.
    The question will be in the native_language, and the answer options will be in the learn_language.
    
    Args:
        learn_language: The language the user is learning (for answer options)
        native_language: The user's native language (for the question)
        level: Difficulty level (beginner, intermediate, advanced)
        topic: The topic of the exercise
        exclude_hashes: List of hashes to avoid duplicate exercises
    """
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY is not set. Please check your .env file.")
        return {"error": "DeepSeek API key not configured."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    # Map language names to readable formats for the prompt
    lang_display = {
        "russian": "Russian (Русский)",
        "english": "English",
        "korean": "Korean (한국어)",
        "uzbek": "Uzbek Cyrillic (Ўзбек кирилл)"
    }
    
    learn_lang_display = lang_display.get(learn_language, learn_language.capitalize())
    native_lang_display = lang_display.get(native_language, native_language.capitalize())

    prompt = f"""
    Create a simple and fun multiple-choice language exercise for a child learning {learn_lang_display} at a {level} level.
    The exercise must be about the topic: "{topic}".
    Use simple, common, and basic words suitable for a young child.
    
    CRITICAL LANGUAGE REQUIREMENTS:
    1. The QUESTION must be written in {native_lang_display} (the user's native language)
    2. The ANSWER OPTIONS must be written in {learn_lang_display} (the language being learned)
    3. This helps the child understand what is being asked in their native language, while learning vocabulary in the target language.
    
    SCRIPT REQUIREMENTS:
    - If the language is "uzbek" or contains "uzbek", use UZBEK CYRILLIC (Ўзбек кирилл) script, NOT Latin script.
    - Use Cyrillic letters: Ў, Қ, Ғ, Ҳ instead of Latin O', Q, G', H
    - For Russian, use Russian Cyrillic
    - For English and Korean, use their respective scripts
    
    The question should be engaging for a child and easy to pronounce for text-to-speech generation.

    To ensure variety, avoid exercises similar to these (represented by hashes): {", ".join(exclude_hashes or [])}

    Please return your response as a single JSON object with the following keys:
    - "question": A string containing the question in {native_lang_display}
    - "options": A list of 4 strings in {learn_lang_display} representing the possible answers
    - "correct_answer_index": An integer (from 0 to 3) indicating the index of the correct answer
    - "visual_prompt": A string describing a simple, friendly image related to the question
    
    Example (if native=Uzbek Cyrillic, learning=Russian):
    {{ "question": "Бу нима?", "options": ["Яблоко", "Банан", "Виноград", "Гранат"], "correct_answer_index": 0, "visual_prompt": "A friendly red apple smiling." }}
    
    Example (if native=Russian, learning=English):
    {{ "question": "Что это?", "options": ["Apple", "Banana", "Grape", "Pomegranate"], "correct_answer_index": 0, "visual_prompt": "A friendly red apple smiling." }}

    Do not include any text or explanations outside of the JSON object.
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an assistant that creates language exercises for children and responds in pure JSON format."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 500,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            exercise_content = data['choices'][0]['message']['content']
            
            # Clean JSON from markdown blocks if present
            clean_json = extract_json_from_markdown(exercise_content)
            
            # Attempt to parse JSON
            try:
                exercise_data = json.loads(clean_json)
                return exercise_data
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from DeepSeek API. Raw response: {exercise_content}")
                return {"error": "Failed to decode JSON from the API response.", "raw_response": exercise_content}

    except httpx.HTTPStatusError as e:
        logger.error(f"API Error during exercise generation: {e.response.status_code} - {e.response.text}", exc_info=True)
        return {"error": f"DeepSeek API Error: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        logger.error(f"An unexpected error occurred during exercise generation: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}


# --- Image Generation ---

# Using a more reliable public Hugging Face model
IMAGE_GENERATION_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_TOKEN = os.getenv("HF_TOKEN") 

async def generate_image(prompt: str) -> str | None:
    """
    Generates an image from a text prompt using a Hugging Face model.
    Returns the URL of the generated image or None if it fails.
    """
    logger.debug(f"Attempting to generate image for prompt: {prompt}")
    logger.debug(f"HF_TOKEN available: {'Yes' if HF_TOKEN else 'No'}")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}" if HF_TOKEN else "",
        "Content-Type": "application/json"
    }
    payload = {"inputs": f"cute cartoon drawing of a {prompt}, simple, for kids, white background"}
    
    logger.debug(f"Sending request to {IMAGE_GENERATION_API_URL} with payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(IMAGE_GENERATION_API_URL, json=payload, headers=headers, timeout=120.0)
            
            logger.debug(f"Image API response status: {response.status_code}")
            logger.debug(f"Image API response headers: {response.headers}")

            if response.status_code == 200 and response.headers.get("content-type", "").startswith("image/"):
                image_data = base64.b64encode(response.content).decode("utf-8")
                logger.debug(f"Image generated successfully. Data URL length: {len(image_data)} bytes.")
                return f"data:image/jpeg;base64,{image_data}"
            else:
                logger.error(f"Image generation API returned non-image data or error status. Status: {response.status_code}, Response: {response.text}")
                return None
    except httpx.TimeoutException:
        logger.error("Image generation timed out after 120 seconds.")
        return None
    except Exception as e:
        logger.error(f"An unexpected error during image generation: {e}", exc_info=True)
        return None