from openai import OpenAI
from app.core.config import DEEPSEEK_API_KEY
import os
from services import child_prompt

# Initialize DeepSeek client
# DeepSeek is compatible with OpenAI SDK
client = OpenAI(
    api_key=DEEPSEEK_API_KEY, 
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT_RU = """
Ты AI-репетитор по изучению языков.
Объясняй максимально просто, как для новичка.
Без сложных терминов.
"""

SYSTEM_PROMPT_UZ = """
Sen til o‘rganish bo‘yicha AI-repetitorsan.
Juda oddiy va tushunarli qilib tushuntir.
Murakkab so‘zlarsiz.
"""

def get_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def ask_ai(question: str, mode: str='study', base_language: str='RU'): 
    if mode == "child":
        system_prompt = child_prompt.SYSTEM_PROMPT_CHILD_RU if base_language == "RU" else child_prompt.SYSTEM_PROMPT_CHILD_UZ
    else:
        system_prompt = SYSTEM_PROMPT_RU if base_language == "RU" else SYSTEM_PROMPT_UZ

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[ 
                {"role": "system", "content": system_prompt}, 
                {"role":"user", "content": question}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek Error: {e}")
        # Fallback or re-raise
        return "⚠️ Ошибка при подключении к DeepSeek. Проверьте баланс или API ключ."

