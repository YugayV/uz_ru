import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def ask_deepseek(prompt: str) -> str:
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    )

    data = response.json()

    # 🔴 если ошибка
    if "error" in data:
        raise RuntimeError(f"DeepSeek error: {data['error']}")

    # ✅ формат как OpenAI
    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    # ✅ альтернативный формат
    if "output_text" in data:
        return data["output_text"]

    if "data" in data and "content" in data["data"]:
        return data["data"]["content"]

    # ❌ если формат неизвестен
    raise RuntimeError(f"Unknown DeepSeek response format: {data}")
