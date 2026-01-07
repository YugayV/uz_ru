from openai import OpenAI
from app.core.config import DEEPSEEK_API_KEY
import os

# Initialize client safely to prevent startup crashes
def get_deepseek_client():
    # Robustly get the key from multiple possible env vars
    key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("DEEPSEEK_KEY")
        or DEEPSEEK_API_KEY
        or "EMPTY"
    )
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


client = get_deepseek_client()

SYSTEM_PROMPT_RU = """
Ты AI-репетитор по изучению языков.
Объясняй максимально просто, как для новичка.
Без сложных терминов.
Ты детский AI.
Никогда:
- не говори про насилие
- не говори про взрослых темы
- не задавай вопросы про семью
- не проси личные данные
Говори коротко.
Хвали ребёнка.

"""

SYSTEM_PROMPT_UZ = """
Sen til o‘rganish bo‘yicha AI-repetitorsan.
Juda oddiy va tushunarli qilib tushuntir.
Murakkab so‘zlarsiz.
"""

SYSTEM_PROMPT_CHILD_RU = """
Ты — веселый и добрый учитель для детей.
Твоя задача — объяснять все очень просто, используя понятные аналогии, игры и простые слова.
Избегай сложных терминов.
Будь дружелюбным и поддерживающим.
"""

SYSTEM_PROMPT_CHILD_UZ = """
Sen bolalar uchun quvnoq va mehribon o‘qituvchisan.
Vazifang — hammasini juda oddiy, tushunarli o‘xshatishlar, o‘yinlar va oddiy so‘zlar yordamida tushuntirish.
Murakkab atamalardan qoch.
Do‘stona va qo‘llab-quvvatlovchi bo‘l.
"""

def ask_ai(question: str, mode: str = "study", native_language: str = "RU", learning_language: str = "UZ", age: int | None = None, lesson_type: str | None = None, base_language: str | None = None) -> str:
    # Use native_language or fallback to base_language for compatibility
    native_lang = native_language or base_language or "RU"
    
    if mode == "child":
        system_prompt = SYSTEM_PROMPT_CHILD_RU if native_lang == "RU" else SYSTEM_PROMPT_CHILD_UZ
        # Add child-specific rules and context
        system_prompt += f"""
Ты детский AI для обучения языкам.
Возраст: {age or 'не указан'}
Родной язык: {native_lang}
Изучаемый язык: {learning_language}

Правила:
- сначала родной язык
- потом иностранное слово
- потом повтор
- коротко
- весело
"""
    else:
        system_prompt = SYSTEM_PROMPT_RU if native_lang == "RU" else SYSTEM_PROMPT_UZ

    
    # Custom adjustments based on age or lesson_type
    if age:
        system_prompt += f"\nNote: The user is {age} years old. Adjust your tone accordingly."
    if lesson_type:
        system_prompt += f"\nContext: This is a '{lesson_type}' lesson."

    try:
        # Re-check the key on every call to be sure it's fresh
        client.api_key = (
            os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("DEEPSEEK_KEY")
            or DEEPSEEK_API_KEY
        )
        if not client.api_key or client.api_key == "EMPTY":
            return "❌ API-ключ DeepSeek не настроен. Проверьте переменную DEEPSEEK_API_KEY в Railway."

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role":"user", "content": question}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"AI error: {e}")
        return "⚠️ Ошибка связи с AI. Попробуйте позже."


# --- Tutor wrapper using DeepSeek and the tutor prompt ---
from app.services.tutor_prompt import build_tutor_prompt
from services.deepseek_client import ask_deepseek


def tutor_reply(
    age_group: str,
    language_pair: str,
    level: int,
    lesson_title: str,
    user_input: str | None = None
) -> str:
    prompt = build_tutor_prompt(
        age_group=age_group,
        language_pair=language_pair,
        level=level,
        lesson_title=lesson_title,
        user_input=user_input
    )

    try:
        return ask_deepseek(prompt)
    except Exception as e:
        print(f"Tutor DeepSeek error: {e}")
        return "⚠️ Ошибка связи с AI. Попробуйте позже."
