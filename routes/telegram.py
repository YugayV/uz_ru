import os
import requests
from fastapi import APIRouter, Request
from gtts import gTTS
import uuid
from app.services.limits import allowed
from services.subscription import is_premium


router = APIRouter(prefix="/telegram", tags=["Telegram"])

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

BACKEND_AI_URL = "http://localhost:8000/ai/ask"


def send_voice(chat_id, text, lang="ru"):
    filename = f"/tmp/{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)

    with open(filename, "rb") as audio:
        requests.post(
            f"{TG_API}/sendVoice",
            data={"chat_id": chat_id},
            files={"voice": audio}
        )


@router.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # старт — сразу игра
        requests.post(
            f"{TG_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "👋",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {"text": "🐶", "callback_data": "animal_dog"},
                            {"text": "🐱", "callback_data": "animal_cat"},
                            {"text": "🐮", "callback_data": "animal_cow"}
                        ]
                    ]
                }
            }
        )

    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        choice = data["callback_query"]["data"]

        payload = {
            "mode": "child",
            "age": 4,
            "language": "ru",
            "lesson_type": "animals",
            "text": choice
        }

        ai = requests.post(BACKEND_AI_URL, json=payload).json()
        send_voice(chat_id, ai["voice_text"], lang="ru")

    if not allowed(chat_id): 
        send_voice(chat_id, "Давай отдохнём! Поиграем позже 😊")
        
    # if is_premium(user):
    #     # доступ открыт
    #     pass
    # else:
    #     # действуют ограничения
    #     pass
    

    return {"ok": True}


