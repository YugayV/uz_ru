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

# Make backend AI endpoint configurable; fallback to localhost
BACKEND_AI_URL = os.getenv("BACKEND_AI_URL", "http://localhost:8000/ai/ask")

from app.routes.ai import AIRequest, ask as _ai_ask_endpoint

from services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from tg_bot.games import get_random_game

import tempfile
from app.services.stt import speech_to_text
from pydub import AudioSegment

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
                audio_data = requests.get(file_url).content

                with tempfile.NamedTemporaryFile(suffix=".ogg") as f:
                    f.write(audio_data)
                    f.flush()
                    wav_path = f.name.replace('.ogg', '.wav')
                    AudioSegment.from_ogg(f.name).export(wav_path, format="wav")
                    text = speech_to_text(wav_path)

                    if not text:
                        send_voice(chat_id, "Ничего страшного! Попробуй ещё 😊")
                        return {"ok": True}

                    expected = pop_expected_answer(chat_id)
                    if expected is not None:
                        got = text.lower().strip()
                        exp = expected.lower().strip()
                        if got == exp or exp in got or got in exp:
                            from services.character import get_reaction
                            react = get_reaction("capybara", "correct", streak=0)
                            if react:
                                send_voice(chat_id, react.get("phrase", "Молодец!"), lang="ru")
                            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Правильно!"})
                        else:
                            from services.character import get_reaction
                            react = get_reaction("capybara", "incorrect", streak=0)
                            if react:
                                send_voice(chat_id, react.get("phrase", "Попробуй ещё!"), lang="ru")
                            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Не совсем — попробуй ещё."})
                        return {"ok": True}

                    # fallback to AI
                    payload = {"mode": "child", "age": 4, "language": "ru", "lesson_type": "free", "text": text}
                    try:
                        resp = requests.post(BACKEND_AI_URL, json=payload, timeout=5)
                        ai = resp.json()
                    except Exception:
                        try:
                            ai = await _ai_ask_endpoint(AIRequest(**payload))
                        except Exception:
                            ai = {}

                    voice_text = ai.get("voice_text") or ai.get("reply") or ai.get("answer") or ""
                    send_voice(chat_id, voice_text, lang="ru")
            return {"ok": True}

        # старт — показать выбор языка
        keyboard = {"inline_keyboard": [[
            {"text": "UZ ", "callback_data": "lang:UZ"},
            {"text": "RU ", "callback_data": "lang:RU"},
            {"text": "EN ", "callback_data": "lang:EN"},
            {"text": "KOR", "callback_data": "lang:KOR"}
        ]]} 
        requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Выберите язык / Tilni tanlang", "reply_markup": keyboard})

    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        cb = data["callback_query"]["data"]

        if cb.startswith("lang:"):
            lang = cb.split(":", 1)[1]
            set_state(chat_id, language=lang)
            keyboard = {"inline_keyboard": [[{"text": str(i), "callback_data": f"level:{i}"} for i in range(1, 7)]]}
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Выберите уровень (1-6)", "reply_markup": keyboard})
            return {"ok": True}

        if cb.startswith("level:"):
            level = int(cb.split(":", 1)[1])
            set_state(chat_id, level=level)
            keyboard = {"inline_keyboard": [[{"text": "Детский режим", "callback_data": "mode:child"}, {"text": "Взрослый режим", "callback_data": "mode:adult"}]]}
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Выберите режим", "reply_markup": keyboard})
            return {"ok": True}

        if cb.startswith("mode:"):
            mode = cb.split(":", 1)[1]
            set_state(chat_id, mode=mode)
            if mode == "child":
                state = get_state(chat_id)
                lang = (state or {}).get("language", "ru")
                game = get_random_game(is_kid=True, lang=lang)
                set_state(chat_id, current_game=game)
                send_voice(chat_id, game.get("question", "Давай играть!"), lang=lang.lower())
                if game.get("options"):
                    keyboard = {"inline_keyboard": [[{"text": opt, "callback_data": f"game_answer:{i}"} for i, opt in enumerate(game.get("options"))]]}
                    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": game.get("question"), "reply_markup": keyboard})
                    set_expected_answer(chat_id, str(game.get("answer")))
                else:
                    set_expected_answer(chat_id, str(game.get("answer")))
                    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Послушай и повтори, пожалуйста. Отправь голосом."})
            else:
                payload = {"mode": "adult", "language": "ru", "text": "start conversation"}
                try:
                    resp = requests.post(BACKEND_AI_URL, json=payload, timeout=5)
                    ai = resp.json()
                except Exception:
                    try:
                        ai = await _ai_ask_endpoint(AIRequest(**payload))
                    except Exception:
                        ai = {}
                voice_text = ai.get("voice_text") or ai.get("reply") or ai.get("answer") or ""
                send_voice(chat_id, voice_text, lang="ru")
            return {"ok": True}

        if cb.startswith("game_answer:"):
            idx = int(cb.split(":", 1)[1])
            state = get_state(chat_id)
            game = (state or {}).get("current_game")
            if not game:
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Нет активной игры."})
                return {"ok": True}
            expected = str(game.get("answer"))
            chosen = None
            try:
                chosen = game.get("options")[idx]
            except Exception:
                chosen = None
            from services.speech_utils import is_close_answer
            if chosen and is_close_answer(chosen, expected):
                from services.character import get_reaction
                react = get_reaction("capybara", "correct", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Молодец!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Правильно!"})
            else:
                from services.character import get_reaction
                react = get_reaction("capybara", "incorrect", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Попробуй ещё!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Неправильно — попробуй ещё."})
            clear_state(chat_id)
            return {"ok": True}

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


