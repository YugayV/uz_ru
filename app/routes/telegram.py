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
        logger.info("--- TELEGRAM WEBHOOK ENDPOINT WAS HIT ---")
        # Log the token to see if it's loaded correctly
        if not BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is not set!")
            return {"ok": False, "error": "Bot token not configured"}
        
        logger.info(f"Received update, bot token configured partially: {BOT_TOKEN[:4]}...{BOT_TOKEN[-4:]}")
        data = await req.json()
        logger.info(f"Full Telegram payload: {data}")

        # Safely extract chat_id from the incoming data
        chat_id = None
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
        elif "callback_query" in data:
            chat_id = data["callback_query"]["message"]["chat"]["id"]
        elif "my_chat_member" in data:
            chat_id = data["my_chat_member"]["chat"]["id"]
            logger.info(f"Bot was added to a chat or status changed. Chat ID: {chat_id}")
            # Optionally, you can handle this event (e.g., send a welcome message)
            # For now, we'll just acknowledge it to prevent errors.
            return {"ok": True}

        if not chat_id:
            logger.warning(f"Could not extract chat_id from payload: {data}")
            return {"ok": True} # Return OK to prevent Telegram from resending

        logger.info(f"Successfully extracted chat_id: {chat_id}")

        # --- Message type routing ---
        if "message" in data:
            logger.info("Processing a 'message' update.")
            message = data["message"]
            
            # Handle /start command or simple text
            if "text" in message:
                text = message["text"]
                logger.info(f"Message text: {text}")
                if text == "/start":
                    logger.info("Sending language selection keyboard for /start command.")
                    # ... (keyboard sending logic)
            
            elif "voice" in message:
                logger.info("Voice message detected, processing now.")
                # ... (voice processing logic)

        elif "callback_query" in data:
            logger.info("Processing a 'callback_query' update.")
            # ... (callback query logic)
        
        return {"ok": True}

    except Exception as e:
        logger.exception(f"An unexpected error occurred in telegram_webhook: {e}")
        return {"ok": True, "error": "An internal error occurred"} # Return OK to prevent resend