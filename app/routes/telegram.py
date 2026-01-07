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
    # Log the token to see if it's loaded correctly
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        return {"ok": False, "error": "Bot token not configured"}
    
    logger.info(f"Received update, bot token configured partially: {BOT_TOKEN[:4]}...{BOT_TOKEN[-4:]}")
    data = await req.json()

    # Safely extract chat_id from the incoming data
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    if not chat_id:
        logger.warning("No chat_id found in the incoming data")
        return {"ok": False, "error": "chat_id not found"}

    # ...existing code for handling the webhook...