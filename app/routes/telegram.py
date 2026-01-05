import os
import requests
from fastapi import APIRouter, Request
from gtts import gTTS
import uuid
import tempfile
from app.services.stt import speech_to_text
from app.services.lives import LIVES
from pydub import AudioSegment
from datetime import datetime, timedelta
from app.models.user import User

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

LAST_REGEN = {}

def regen(chat_id):
    now = datetime.now()
    last = LAST_REGEN.get(chat_id, now)

    if now - last > timedelta(minutes=30):
        LIVES[chat_id] = min(LIVES.get(chat_id, 6) + 1, 6)
        LAST_REGEN[chat_id] = now


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

    if "voice" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        file_id = data["message"]["voice"]["file_id"]

        # 1. скачать файл
        file_info = requests.get(
            f"{TG_API}/getFile",
            params={"file_id": file_id}
        ).json()

        file_path = file_info["result"]["file_path"]
        audio_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        audio_data = requests.get(audio_url).content

        with tempfile.NamedTemporaryFile(suffix=".ogg") as f:
            f.write(audio_data)
            f.flush()

            # 2. STT
            wav_path = f.name.replace(".ogg", ".wav")
            AudioSegment.from_ogg(f.name).export(wav_path, format="wav")

            text = speech_to_text(wav_path)

            if not text:
                send_voice(chat_id, "Ничего страшного! Попробуй ещё 😊")
                return


            # 3. AI
            payload = {
                "mode": "child",
                "age": 4,
                "language": "ru",
                "lesson_type": "free",
                "text": text
            }

            ai = requests.post(BACKEND_AI_URL, json=payload).json()

            # 4. TTS
            send_voice(chat_id, ai["voice_text"], lang="ru")


    return {"ok": True}
