import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def ask_deepseek(prompt: str):
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
    return response.json()["choices"][0]["message"]["content"]
