from openai import OpenAI, responses 
from app.core.config import OPENAI_API_KEY 
import os
from services import child_prompt

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

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

def ask_ai(question: str, mode: str='study', base_language: str='RU'): 
    if mode == "child":
        system_prompt = child_prompt.SYSTEM_PROMPT_CHILD_RU if base_language == "RU" else child_prompt.SYSTEM_PROMPT_CHILD_UZ
    else:
        system_prompt = SYSTEM_PROMPT_RU if base_language == "RU" else SYSTEM_PROMPT_UZ

    response = client.chat.completions.create(  # type: ignore 
        model="gpt-4o-mini", 
        messages=[ 
            {"role": "system", "content": system_prompt}, 
            {"role":"user", "content": question}
        ],
        temperature=0.4
        
    )

    return response.choices[0].message.content

