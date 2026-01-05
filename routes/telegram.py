import os
import requests
from fastapi import APIRouter, Request
from gtts import gTTS
import uuid
from app.services.limits import allowed
from services.subscription import is_premium
from services.premium import activate_premium
from app.models.user import User
from core.deps import get_db
from sqlalchemy.orm import Session
from fastapi import Depends


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
async def telegram_webhook(req: Request, db: Session = Depends(get_db)):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user = db.query(User).filter(User.telegram_id == chat_id).first()
        if not user:
            # This is a new user, create a user record and give premium
            user = User(telegram_id=chat_id)
            db.add(user)
            db.commit()
            activate_premium(user)
            db.commit()

        # If user sent a voice message, save it and ask for expected phrase to verify
        if "voice" in data["message"]:
            file_id = data["message"]["voice"]["file_id"]
            # get file path
            file_info = requests.get(f"{TG_API}/getFile?file_id={file_id}").json()
            file_path = file_info.get("result", {}).get("file_path")
            if file_path:
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                filename = f"/tmp/{file_id}.oga"
                r = requests.get(file_url)
                with open(filename, "wb") as fh:
                    fh.write(r.content)

                requests.post(f"{TG_API}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Я получил твой голос! Отправь сейчас фразу, которую нужно проверить, в текстовом виде (или отправь голос и подпиши текст в следующем сообщении)."
                })
            return {"ok": True}

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

        # Character reaction (capybara)
        try:
            from services.character import get_reaction
            react = get_reaction("capybara", "correct", streak=0)
            if react:
                # send reaction audio if available as local file
                audio_path = react.get("audio")
                if audio_path and audio_path.startswith("characters/"):
                    local = os.path.join(os.path.dirname(__file__), "..", audio_path)
                    local = os.path.normpath(local)
                    if os.path.exists(local):
                        with open(local, "rb") as audio:
                            requests.post(
                                f"{TG_API}/sendVoice",
                                data={"chat_id": chat_id},
                                files={"voice": audio}
                            )
                    else:
                        # fallback to TTS phrase
                        send_voice(chat_id, react.get("phrase", "Отлично!"), lang="ru")
                else:
                    send_voice(chat_id, react.get("phrase", "Отлично!"), lang="ru")

                # send image if available
                img = react.get("image")
                if img:
                    local_img = os.path.join(os.path.dirname(__file__), "..", img)
                    local_img = os.path.normpath(local_img)
                    if os.path.exists(local_img):
                        with open(local_img, "rb") as photo:
                            requests.post(
                                f"{TG_API}/sendPhoto",
                                data={"chat_id": chat_id},
                                files={"photo": photo}
                            )
        except Exception:
            pass

    if not allowed(chat_id): 
        send_voice(chat_id, "Давай отдохнём! Поиграем позже 😊")
        return {"ok": True}

    # if is_premium(user):
    #     # доступ открыт
    #     pass
    # else:
    #     # действуют ограничения
    #     pass
    

    return {"ok": True}


