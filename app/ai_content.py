import os
import httpx
import json
from dotenv import load_dotenv
import base64
DEEPSEEK_API_URL = "https://api.deepseek.ai/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

async def generate_exercise(language: str, level: str):
    """
    Generates a language exercise as a JSON object using the DeepSeek API.
    """
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY is not set. Please check your .env file."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    prompt = f"""
    Create a {level} level language exercise for a child learning {language}.
    The target audience is native Uzbek speakers.
    Make the question engaging for a child.
    Provide a simple description for a relevant image.

    Example: {{ "question": "What is 'apple' in {language}?", "options": ["Olma", "Banan", "Uzum", "Anor"], "correct_answer": "Olma", "image_description": "A red apple." }}

    Respond with a JSON object containing "question", "options", "correct_answer", and "image_description".
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an assistant that creates language exercises for children."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']

    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

async def translate_text(text: str, target_language: str):
    """
    Translates text using the DeepSeek API.
    """
    if not DEEPSEEK_API_KEY:
        return "Error: DEEPSEEK_API_KEY is not set. Please check your .env file."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    # A specific prompt for translation
    prompt = f"Translate the following text to {target_language}. Provide only the translated text, without any additional explanations or context.\\n\\nText to translate: \"{text}\""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a powerful and accurate translator."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2, # Lower temperature for more precise, less creative translations
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            translation = data['choices'][0]['message']['content']
            return translation

    except httpx.HTTPStatusError as e:
        return f"Error communicating with DeepSeek API: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

async def generate_multiple_choice_exercise(language: str, level: str, topic: str, exclude_hashes: list[str] = None):
    """
    Generates a multiple-choice exercise for a specific topic as a JSON object.
    """
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY is not set. Please check your .env file."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    # A more advanced prompt to request a JSON structure based on a topic
    prompt = f"""
    Create a simple and fun multiple-choice language exercise for a child learning {language} at a {level} level.
    The exercise must be about the topic: "{topic}".
    Use simple, common, and basic words suitable for a young child.
    The target audience is native Uzbek speakers.
    The question should be engaging for a child.
    All text in the "question" and "options" fields should be short, clear, and easy to pronounce for text-to-speech generation.

    To ensure variety, please try to make this exercise different from ones that might have these themes or questions (represented by hashes): {", ".join(exclude_hashes or [])}

    Please return your response as a single JSON object with the following keys:
    - "question": A string containing the question.
    - "options": A list of 4 strings representing the possible answers.
    - "correct_answer_index": An integer (from 0 to 3) indicating the index of the correct answer in the "options" list.
    - "visual_prompt": A string describing a simple, friendly image related to the question.

    Example: {{ "question": "What is 'apple' in {language}?", "options": ["Olma", "Banan", "Uzum", "Anor"], "correct_answer_index": 0, "visual_prompt": "A friendly red apple smiling." }}

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
            # The JSON content is what we want
            exercise_data = json.loads(data['choices'][0]['message']['content'])
            return exercise_data

    except httpx.HTTPStatusError as e:
        return {"error": f"API Error: {e.response.status_code}", "details": e.response.text}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON from the API response."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# --- Image and Audio Generation ---

# --- Image and Audio Generation ---

# Using a more reliable public Hugging Face model
IMAGE_GENERATION_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_TOKEN = os.getenv("HF_TOKEN") 

async def generate_image(prompt: str) -> str | None:
    """
    Generates an image from a text prompt using a Hugging Face model.
    Returns the URL of the generated image or None if it fails.
    """
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}" if HF_TOKEN else "",
        "Content-Type": "application/json"
    }
    # A very simple and direct prompt for reliability
    payload = {"inputs": f"cute cartoon drawing of a {prompt}, simple, for kids, white background"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(IMAGE_GENERATION_API_URL, json=payload, headers=headers, timeout=120.0)
            
            if response.headers.get("content-type", "").startswith("image/"):
                image_data = base64.b64encode(response.content).decode("utf-8")
                return f"data:image/jpeg;base64,{image_data}"
            else:
                print(f"Image generation API Error: {response.text}")
                return None
    except Exception as e:
        print(f"An unexpected error during image generation: {str(e)}")
        return None