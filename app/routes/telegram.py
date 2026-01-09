import logging
import os
from fastapi import APIRouter, Request
from pydub import AudioSegment
from datetime import datetime, timedelta
from app.models.user import User

router = APIRouter(prefix="/telegram", tags=["Telegram"])
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")

@router.post("/webhook")
async def telegram_webhook(req: Request):
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
        return {"ok": False, "error": "chat_id not found"}

    # ...existing code for handling the webhook...