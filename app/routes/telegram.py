import logging
import os
import tempfile
from fastapi import APIRouter, Request
from app.services.stt import speech_to_text
from app.services.lives import LIVES
from pydub import AudioSegment
from datetime import datetime, timedelta
from app.models.user import User

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from app.tg_bot.games import get_random_game

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

    if "callback_query" in data:
        cb = data["callback_query"]["data"]
        logger.info(f"Callback query received: {cb}")

        # Handle game answer callbacks
        if cb.startswith("game_answer:"):
            idx = int(cb.split(":")[1])
            logger.info(f"Game answer index: {idx}")

            # Retrieve the game associated with the callback
            game = get_state(chat_id).get("game")
            logger.info(f"Retrieved game from state: {game}")

            # Determine if the answer is correct
            expected = pop_expected_answer(chat_id)
            from app.services.speech_utils import is_close_answer # Corrected import
            if game and expected is not None and is_close_answer(game.get("options")[idx], expected):
                # success reaction
                from app.services.character import get_reaction # Corrected import
                react = get_reaction("capybara", "correct", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Молодец!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Правильно!"})
            else:
                from app.services.character import get_reaction # Corrected import
                react = get_reaction("capybara", "incorrect", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Попробуй ещё!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Неправильно — попробуй ещё."})
            clear_state(chat_id)
            return {"ok": True}

    if "voice" in data["message"]:
        file_id = data["message"]["voice"]["file_id"]
        logger.info(f"Voice message received. File ID: {file_id}")

        # Download the voice file
        file_path = f"downloads/{file_id}.oga"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_id}"
            f.write(requests.get(file_url).content)

        # Convert OGA to WAV
        wav_path = file_path.replace(".oga", ".wav")
        AudioSegment.from_oga(file_path).export(wav_path, format="wav")

        # STT processing
        text = speech_to_text(wav_path)
        logger.info(f"Converted speech to text: {text}")

        # If a game expected a voice response, check it first
        expected = pop_expected_answer(chat_id)
        if expected is not None:
            from app.services.speech_utils import is_close_answer # Corrected import
            if is_close_answer(text, expected):
                from app.services.character import get_reaction # Corrected import
                react = get_reaction("capybara", "correct", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Молодец!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Правильно!"})
            else:
                from app.services.character import get_reaction # Corrected import
                react = get_reaction("capybara", "incorrect", streak=0)
                if react:
                    send_voice(chat_id, react.get("phrase", "Попробуй ещё!"), lang="ru")
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Не совсем — попробуй ещё."})
            return

        # Regular voice message processing
        logger.info(f"Processing regular voice message for chat_id {chat_id}")

        # Here you can add code to handle regular voice messages
        # For example, save the voice message, transcribe it, etc.

    return {"ok": True}