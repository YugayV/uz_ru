import logging
import os
import tempfile
from fastapi import APIRouter, Request
from app.services.stt import speech_to_text
from app.services.lives import LIVES
from pydub import AudioSegment
from datetime import datetime, timedelta
from app.models.user import User
import requests
import re
import uuid
from gtts import gTTS

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from app.tg_bot.games import get_random_game

router = APIRouter(prefix="/telegram", tags=["Telegram"])
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")

def clean_text_for_tts(text: str) -> str:
    """Removes emojis and other non-verbal characters for cleaner TTS output."""
    if not isinstance(text, str):
        return ""
    # Regex to remove most emojis and special symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+",
        flags=re.UNICODE,
    )
    cleaned_text = emoji_pattern.sub(r'', text)
    # Also remove common non-verbal characters
    cleaned_text = cleaned_text.replace("🎲", "").replace("📚", "").replace("🗣️", "").replace("🧒", "").replace("🧑", "")
    return cleaned_text.strip()

def send_voice(chat_id, text, lang="ru"):
    """Generates a voice message from text and sends it to the user."""
    try:
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            logger.warning(f"Skipping TTS for empty or non-string text: {text}")
            return

        filename = f"/tmp/{uuid.uuid4()}.mp3"
        tts = gTTS(text=clean_text, lang=lang)
        tts.save(filename)

        with open(filename, "rb") as audio:
            payload = {"chat_id": chat_id}
            files = {"voice": audio}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice", data=payload, files=files)
        os.remove(filename) # Clean up the temp file
    except Exception as e:
        logger.error(f"Failed to send voice message: {e}")

@router.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        if not BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is not set!")
            return {"ok": False, "error": "Bot token not configured"}
        
        data = await req.json()
        logger.info(f"Full Telegram payload: {data}")

        # --- Safely extract chat_id and other relevant data ---
        chat_id = None
        message = None
        callback_query = None

        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
        elif "callback_query" in data:
            callback_query = data["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
        elif "my_chat_member" in data:
            logger.info(f"Bot status changed in chat: {data['my_chat_member']['chat']['id']}")
            return {"ok": True}

        if not chat_id:
            logger.warning(f"Could not extract chat_id from payload: {data}")
            return {"ok": True}

        logger.info(f"Processing update for chat_id: {chat_id}")

        # --- Handle different update types ---

        # 1. Handle callback queries (button presses)
        if callback_query:
            cb_data = callback_query["data"]
            logger.info(f"Processing callback_query: {cb_data}")

            if cb_data.startswith("lang:"):
                lang = cb_data.split(":", 1)[1]
                set_state(chat_id, language=lang)
                keyboard = {"inline_keyboard": [[{"text": str(i), "callback_data": f"level:{i}"} for i in range(1, 7)]]}
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Выберите уровень (1-6)", "reply_markup": keyboard})
            
            elif cb_data.startswith("level:"):
                level = int(cb_data.split(":", 1)[1])
                set_state(chat_id, level=level)
                keyboard = {"inline_keyboard": [[
                    {"text": "Детский режим 🧒", "callback_data": "mode:child"},
                    {"text": "Взрослый режим 🧑", "callback_data": "mode:adult"}
                ]]}
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Выберите режим:", "reply_markup": keyboard})

            elif cb_data.startswith("mode:"):
                mode = cb_data.split(":", 1)[1]
                set_state(chat_id, mode=mode)
                if mode == "child":
                    state = get_state(chat_id)
                    lang = (state or {}).get("language", "ru")
                    game = get_random_game(is_kid=True, lang=lang)
                    set_state(chat_id, current_game=game)

                    question = game.get("question", "Давай играть!")
                    send_voice(chat_id, question, lang=lang.lower())

                    if game.get("options"):
                        keyboard = {"inline_keyboard": [[{"text": opt, "callback_data": f"game_answer:{i}"} for i, opt in enumerate(game["options"])]]}
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Выбери правильный ответ:", "reply_markup": keyboard})
                    set_expected_answer(chat_id, str(game.get("answer")))
                
                else: # Adult mode
                    # This is where premium checks would go
                    from app.services.ai_tutor import ask_ai
                    response = ask_ai("Начнем урок.", mode="adult", base_language="RU")
                    send_voice(chat_id, response, lang="ru")

            elif cb_data.startswith("game_answer:"):
                idx = int(cb_data.split(":", 1)[1])
                state = get_state(chat_id)
                game = (state or {}).get("current_game")
                if not game: return {"ok": True}

                expected = pop_expected_answer(chat_id)
                chosen = game.get("options", [])[idx]

                from app.services.speech_utils import is_close_answer
                if is_close_answer(chosen, expected):
                    send_voice(chat_id, "Правильно, молодец!", lang="ru")
                else:
                    send_voice(chat_id, "Неверно, попробуй ещё раз.", lang="ru")
                clear_state(chat_id) # End of game turn

        # 2. Handle messages (text, voice, etc.)
        elif message:
            if "text" in message and message["text"] == "/start":
                logger.info("Sending language selection keyboard for /start command.")
                keyboard = {"inline_keyboard": [[
                    {"text": "UZ 🇺🇿", "callback_data": "lang:UZ"},
                    {"text": "RU 🇷🇺", "callback_data": "lang:RU"},
                ]]}
                payload = {"chat_id": chat_id, "text": "Tilni tanlang / Выберите язык:", "reply_markup": keyboard}
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
            
            elif "voice" in message:
                file_id = message["voice"]["file_id"]
                file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
                file_path = file_info["result"]["file_path"]
                audio_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                audio_data = requests.get(audio_url).content

                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
                    ogg_file.write(audio_data)
                    ogg_path = ogg_file.name
                
                wav_path = ogg_path.replace(".ogg", ".wav")
                AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")
                
                text = speech_to_text(wav_path)
                os.remove(ogg_path)
                os.remove(wav_path)

                if not text:
                    send_voice(chat_id, "Я не расслышал, повтори, пожалуйста.", lang="ru")
                    return {"ok": True}

                expected = pop_expected_answer(chat_id)
                if expected:
                    from app.services.speech_utils import is_close_answer
                    if is_close_answer(text, expected):
                        send_voice(chat_id, "Отлично, всё верно!", lang="ru")
                    else:
                        send_voice(chat_id, "Не совсем так, давай попробуем ещё раз.", lang="ru")
                    clear_state(chat_id)
                else:
                    # Fallback to AI for general conversation
                    from app.services.ai_tutor import ask_ai
                    response = ask_ai(text, mode="adult", base_language="RU")
                    send_voice(chat_id, response, lang="ru")

        return {"ok": True}

    except Exception as e:
        logger.exception(f"An unexpected error occurred in telegram_webhook: {e}")
        return {"ok": True}