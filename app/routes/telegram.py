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

# Backend AI endpoint can be overridden in production via env var
BACKEND_AI_URL = os.getenv("BACKEND_AI_URL", "http://localhost:8000/ai/ask")

# Local AI fallback (call internal handler directly) imports
# Use lazy imports inside handlers to avoid import cycles

# Simple session store
from services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from tg_bot.games import get_random_game


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

    # Safely extract chat_id from the incoming data
    chat_id = None
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]

    # If no chat_id could be determined, exit early
    if not chat_id:
        return {"ok": True}

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

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

        # language selection (e.g. lang:RU)
        if cb.startswith("lang:"):
            lang = cb.split(":", 1)[1]
            set_state(chat_id, language=lang)
            # Ask for level
            keyboard = {"inline_keyboard": [[{"text": str(i), "callback_data": f"level:{i}"} for i in range(1, 7)]]}
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Выберите уровень (1-6)", "reply_markup": keyboard})
            return {"ok": True}

        if cb.startswith("level:"):
            level = int(cb.split(":", 1)[1])
            set_state(chat_id, level=level)
            # Ask for mode
            keyboard = {"inline_keyboard": [[{"text": "Детский режим", "callback_data": "mode:child"}, {"text": "Взрослый режим", "callback_data": "mode:adult"}]]}
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Выберите режим", "reply_markup": keyboard})
            return {"ok": True}

        if cb.startswith("mode:"):
            mode = cb.split(":", 1)[1]
            set_state(chat_id, mode=mode)
            if mode == "child":
                # Start a kid-friendly game
                state = get_state(chat_id)
                lang = (state or {}).get("language", "ru")
                game = get_random_game(is_kid=True, lang=lang)
                set_state(chat_id, current_game=game)

                # Play TTS instruction and show options (if any)
                send_voice(chat_id, game.get("question", "Давай играть!"), lang=lang.lower())

                # If the game has options, show them as buttons
                if game.get("options"):
                    keyboard = {"inline_keyboard": [[{"text": opt, "callback_data": f"game_answer:{i}"} for i, opt in enumerate(game.get("options"))]]}
                    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": game.get("question"), "reply_markup": keyboard})
                    # store expected answer as the correct index
                    set_expected_answer(chat_id, str(game.get("answer")))
                else:
                    # Expect voice response
                    set_expected_answer(chat_id, str(game.get("answer")))
                    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Послушай и повтори, пожалуйста. Отправь голосом."})
            else:
                # adult mode: ask conversational question via AI
                payload = {"mode": "adult", "language": "ru", "text": "start conversation"}
                try:
                    resp = requests.post(BACKEND_AI_URL, json=payload, timeout=5)
                    ai = resp.json()
                except Exception:
                    try:
                        from app.core.premium_guard import AIRequest, ask_ai as _ai_ask_endpoint
                        req = AIRequest(lang_from=payload.get("language", "ru"), question=payload.get("text", ""))
                        ai = await _ai_ask_endpoint(req)
                    except Exception:
                        try:
                            from app.services.ai_tutor import ask_ai as _local_ask
                            ans = _local_ask(payload.get("text", ""), mode=payload.get("mode", "study"), base_language=payload.get("language", "RU"), age=payload.get("age"))
                            ai = {"answer": ans, "voice_text": ans}
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
                # success reaction
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

            # If a game expected a voice response, check it first
            expected = pop_expected_answer(chat_id)
            if expected is not None:
                from services.speech_utils import is_close_answer
                if is_close_answer(text, expected):
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
                return

            # 3. AI fallback
            payload = {
                "mode": "child",
                "age": 4,
                "language": "ru",
                "lesson_type": "free",
                "text": text
            }

            try:
                resp = requests.post(BACKEND_AI_URL, json=payload, timeout=5)
                ai = resp.json()
            except Exception:
                try:
                    from app.core.premium_guard import AIRequest, ask_ai as _ai_ask_endpoint
                    req = AIRequest(lang_from=payload.get("language", "ru"), question=payload.get("text", ""))
                    ai = await _ai_ask_endpoint(req)
                except Exception:
                    try:
                        from app.services.ai_tutor import ask_ai as _local_ask
                        ans = _local_ask(payload.get("text", ""), mode=payload.get("mode", "study"), base_language=payload.get("language", "RU"), age=payload.get("age"))
                        ai = {"answer": ans, "voice_text": ans}
                    except Exception:
                        ai = {}
            # 4. TTS
            voice_text = ai.get("voice_text") or ai.get("reply") or ai.get("answer") or ""
            send_voice(chat_id, voice_text, lang="ru")


    return {"ok": True}
