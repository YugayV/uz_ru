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

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from app.tg_bot.games import get_random_game

router = APIRouter(prefix="/telegram", tags=["Telegram"])
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")

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
        user_id = None
        message = None
        callback_query = None

        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
        elif "callback_query" in data:
            callback_query = data["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            user_id = callback_query["from"]["id"]
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
                keyboard = {"inline_keyboard": [[{"text": "Детский режим", "callback_data": "mode:child"}, {"text": "Взрослый режим", "callback_data": "mode:adult"}]]}
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Выберите режим", "reply_markup": keyboard})

            elif cb_data.startswith("mode:"):
                mode = cb_data.split(":", 1)[1]
                set_state(chat_id, mode=mode)
                if mode == "child":
                    state = get_state(chat_id)
                    lang = (state or {}).get("language", "ru")
                    game = get_random_game(is_kid=True, lang=lang)
                    set_state(chat_id, current_game=game)
                    # ... (TTS and game logic from previous versions)
                else:
                    # ... (Adult mode logic)
                    pass

            elif cb_data.startswith("game_answer:"):
                # ... (Game answer logic)
                pass

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
                logger.info("Processing voice message.")
                # ... (Full voice processing logic from previous versions)
                pass
        
        return {"ok": True}

    except Exception as e:
        logger.exception(f"An unexpected error occurred in telegram_webhook: {e}")
        return {"ok": True}