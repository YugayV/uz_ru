from openai import OpenAI, responses 
from app.core.config import OPENAI_API_KEY 

client = OpenAI(api_key=OPENAI_API_KEY)

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

def ask_ai(question: str, mode: str = "study", base_language: str = "RU") -> str: 
    if mode == "child":
        system_prompt = SYSTEM_PROMPT_CHILD_RU if base_language == "RU" else SYSTEM_PROMPT_CHILD_UZ
    else:
        system_prompt = SYSTEM_PROMPT_RU if base_language == "RU" else SYSTEM_PROMPT_UZ 

    response = client.chat.completions.create( 
        model="gpt-4o-mini", 
        messages=[ 
            {"role": "system", "content": system_prompt}, 
            {"role":"user", "content": question}
        ], 
        temperature=0.4
    )

    return response.choices[0].message.content or ""
