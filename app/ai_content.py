import httpx
import json
import os

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

async def generate_multiple_choice_exercise(language: str, level: str):
    """
    Generates a multiple-choice exercise as a JSON object using the DeepSeek API.
    """
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY is not set. Please check your .env file."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    # A more advanced prompt to request a JSON structure
    prompt = f"""
    Create a simple and fun multiple-choice language exercise for a child learning {language} at a {level} level.
    The target audience is native Uzbek speakers.
    The question should be engaging for a child.
    Provide a simple description for a relevant and cute cartoon-style image (a visual prompt).

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