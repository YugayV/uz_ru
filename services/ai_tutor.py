from openai import OpenAI
from app.core.config import DEEPSEEK_API_KEY
from app.lessons.ru_en import LESSONS
import os

# Initialize client safely to prevent startup crashes
def get_deepseek_client():
    key = DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY") or "EMPTY"
    return OpenAI(
        api_key=key,
        base_url="https://api.deepseek.com"
    )

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

def ask_ai(question: str, mode: str = "study", base_language: str = "RU", age: int | None = None, lesson_type: str | None = None) -> str:
    if mode == "child":
        system_prompt = SYSTEM_PROMPT_CHILD_RU if base_language == "RU" else SYSTEM_PROMPT_CHILD_UZ
    else:
        system_prompt = SYSTEM_PROMPT_RU if base_language == "RU" else SYSTEM_PROMPT_UZ
    
    # Custom adjustments based on age or lesson_type
    if age:
        system_prompt += f"\nNote: The user is {age} years old. Adjust your tone accordingly."
    if lesson_type:
        system_prompt += f"\nContext: This is a '{lesson_type}' lesson."

    try:
        if client.api_key == "EMPTY":
            return "❌ API ключ DeepSeek не настроен в Railway (DEEPSEEK_API_KEY)."
            
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

def get_lesson(topic):
    for lesson in LESSONS:
        if lesson["topic"] == topic:
            return lesson