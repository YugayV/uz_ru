import logging
import os
import tempfile
import json # Added for load_topics_for_telegram
from fastapi import APIRouter, Request
# from app.services.stt import speech_to_text # Uncomment if needed and implemented
# from app.services.lives import LIVES # Uncomment if needed and implemented
from pydub import AudioSegment # Keep if actually used for audio manipulation, otherwise can remove
from datetime import datetime, timedelta
from app.models.user import User # Keep if user data is directly accessed here
import requests
import re
import uuid
from gtts import gTTS
from pathlib import Path # Import Path for load_topics_for_telegram

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
# from app.tg_bot.games import get_random_game # Uncomment if needed and implemented
from app.services.speech_utils import is_close_answer # NEW: For fuzzy matching answers
from app.ai_content import generate_multiple_choice_exercise # NEW: For exercise generation

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set. Telegram bot will NOT work.")
else:
    logger.info("✅ [telegram.py] TELEGRAM_BOT_TOKEN found.")

def set_telegram_webhook():
    """Sets the Telegram webhook to the production URL."""
    public_url = os.getenv("PUBLIC_URL", "https://uzru-production.up.railway.app") # Use your Railway URL here
    webhook_url = f"{public_url}/telegram/webhook"
    
    if not BOT_TOKEN:
        logger.error("Cannot set webhook: TELEGRAM_BOT_TOKEN is not configured.")
        return

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    logger.info(f"Setting Telegram webhook to: {webhook_url}")
    
    try:
        response = requests.get(api_url, params={'url': webhook_url})
        response.raise_for_status()
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook set successfully: {result.get('description')}")
        else:
            logger.error(f"Failed to set webhook: {result}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while setting webhook: {e}")


router = APIRouter(prefix="/telegram", tags=["Telegram"])

# NOTE: load_topics is defined in webapp.py. For the Telegram bot, we need a separate way to load them
# or ensure `webapp` is imported. For now, a minimal re-implementation.
def load_topics_for_telegram():
    topics_path = Path(__file__).resolve().parents[2] / "content" / "topics.json"
    try:
        with open(topics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Topics file not found at {topics_path}")
        return {}


def clean_text_for_tts(text: str) -> str:
    """Removes emojis and other non-verbal characters for cleaner TTS output."""
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "]+",
        flags=re.UNICODE,
    )
    cleaned_text = emoji_pattern.sub(r'', text)
    cleaned_text = re.sub(r'[^\\w\\s]', '', cleaned_text) # More aggressive cleaning
    return cleaned_text.strip()

def send_voice(chat_id, text, lang="ru"):
    """Generates a voice message from text and sends it to the user."""
    try:
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            logger.warning(f"Skipping TTS for empty or non-string text: {text}")
            return

        filename = f"/tmp/{uuid.uuid4()}.mp3"
        
        # Use fallback for Uzbek ('uz') to 'en', and slow pronunciation for clarity
        lang_to_use = lang if lang in ['en', 'ru', 'ko'] else 'en'
        logger.debug(f"Generating voice for text: '{clean_text}' in language: '{lang_to_use}' (original: '{lang}')")
        
        tts = gTTS(text=clean_text, lang=lang_to_use, slow=True)
        tts.save(filename)

        with open(filename, "rb") as audio:
            payload = {"chat_id": chat_id}
            files = {"voice": audio}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice", data=payload, files=files)
        os.remove(filename) # Clean up the temp file
    except Exception as e:
        logger.error(f"Failed to send voice message: {e}", exc_info=True)

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
            return {"ok": False, "error": "No chat_id found"}

        # --- Get user's current state ---
        user_state = get_state(chat_id)
        if user_state is None: # If no state, set initial state
            set_state(chat_id, current_mode="start")
            user_state = get_state(chat_id)

        current_mode = user_state.get("current_mode")
        user_message_text = message["text"] if message and "text" in message else ""
        
        # Process commands (e.g., /start)
        if user_message_text.startswith('/'):
            command = user_message_text.split()[0]
            if command == "/start":
                send_message(
                    chat_id,
                    "Assalomu alaykum! AI til o'rganish botiga xush kelibsiz. "
                    "Avval o'zingizning ona tilingizni tanlang: Rus tili, Ingliz tili, Koreys tili, O'zbek tili."
                )
                set_state(chat_id, current_mode="choose_native_language")
            elif command == "/help":
                send_message(chat_id, "Hali yordam funksiyasi mavjud emas.")
            elif command == "/voice_test": # Command for voice test
                send_message(chat_id, "Bu ovoz testi. Assalomu alaykum!")
                send_voice(chat_id, "Bu ovoz testi. Assalomu alaykum!", lang="uz") # Test Uzbek voice
            elif command == "/topics": # Command to go back to topic selection
                if "learn_language" in user_state and "level" in user_state:
                    learn_lang = user_state.get("learn_language")
                    level_slug = user_state.get("level")
                    topics = load_topics_for_telegram().get(learn_lang, [])
                    topics_text = "\\n".join([f"- {t}" for t in topics]) if topics else "(Mavzular topilmadi)"
                    send_message(chat_id, f"Mavzular ro'yxati: \\n{topics_text}")
                    set_state(chat_id, current_mode="choose_topic")
                else:
                    send_message(chat_id, "Mavzularni ko'rish uchun avval til va darajani tanlashingiz kerak. Boshlash uchun /start bosing.")
            else:
                send_message(chat_id, "Noma'lum buyruq.")
            return {"ok": True}

        # State-based interaction logic
        if current_mode == "choose_native_language":
            selected_native_lang = user_message_text.lower().strip()
            valid_langs = ["russian", "english", "korean", "uzbek", "rus tili", "ingliz tili", "koreys tili", "o'zbek tili"]
            lang_map = {
                "rus tili": "russian", "russian": "russian",
                "ingliz tili": "english", "english": "english",
                "koreys tili": "korean", "korean": "korean",
                "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            if selected_native_lang in valid_langs:
                native_lang_slug = lang_map.get(selected_native_lang, selected_native_lang)
                set_state(chat_id, native_language=native_lang_slug, current_mode="choose_learn_language")
                send_message(chat_id, f"Sizning ona tilingiz: {native_lang_slug.capitalize()}. Endi o'rganish uchun tilni tanlang: Russian, English, Korean, Uzbek.")
                send_voice(chat_id, f"Sizning ona tilingiz: {native_lang_slug.capitalize()}.", lang=native_lang_slug)
            else:
                send_message(chat_id, "Iltimos, ona tilingizni tanlang (Russian, English, Korean, Uzbek).")

        elif current_mode == "choose_learn_language":
            selected_learn_lang = user_message_text.lower().strip()
            native_lang = user_state.get("native_language") # Keep native_lang in state
            valid_langs = ["russian", "english", "korean", "uzbek", "rus tili", "ingliz tili", "koreys tili", "o'zbek tili"]
            lang_map = {
                "rus tili": "russian", "russian": "russian",
                "ingliz tili": "english", "english": "english",
                "koreys tili": "korean", "korean": "korean",
                "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            if selected_learn_lang in valid_langs:
                learn_lang_slug = lang_map.get(selected_learn_lang, selected_learn_lang)
                set_state(chat_id, learn_language=learn_lang_slug, current_mode="choose_level")
                send_message(chat_id, f"Ajoyib! Siz {learn_lang_slug.capitalize()} tilini o'rganishni tanladingiz. Endi darajangizni tanlang: Beginner, Intermediate, Advanced")
                send_voice(chat_id, f"Ajoyib! Siz {learn_lang_slug.capitalize()} tilini o'rganishni tanladingiz.", lang=learn_lang_slug)
            else:
                send_message(chat_id, "Iltimos, o'rganish uchun tillardan birini tanlang (Russian, English, Korean, Uzbek).")
        
        elif current_mode == "choose_level":
            selected_level = user_message_text.lower().strip()
            learn_lang = user_state.get("learn_language")
            native_lang = user_state.get("native_language") # Keep native_lang in state
            valid_levels = ["beginner", "intermediate", "advanced", "boshlang'ich", "o'rta", "yuqori"]
            level_map = {
                "boshlang'ich": "beginner", "beginner": "beginner",
                "o'rta": "intermediate", "intermediate": "intermediate",
                "yuqori": "advanced", "advanced": "advanced",
            }
            if selected_level in valid_levels:
                level_slug = level_map.get(selected_level, selected_level)
                set_state(chat_id, level=level_slug, current_mode="choose_topic")
                topics = load_topics_for_telegram().get(learn_lang, [])
                topics_text = "\\n".join([f"- {t}" for t in topics]) if topics else "(Mavzular topilmadi)"
                send_message(chat_id, f"Daraja {level_slug.capitalize()} tanlandi. Endi mavzuni tanlang: \\n{topics_text}")
                send_voice(chat_id, f"Daraja {level_slug.capitalize()} tanlandi. Endi mavzuni tanlang.", lang=learn_lang)
            else:
                send_message(chat_id, "Iltimos, to'g'ri darajani tanlang (Beginner, Intermediate, Advanced).")

        elif current_mode == "choose_topic":
            selected_topic = user_message_text.strip()
            learn_lang = user_state.get("learn_language")
            level = user_state.get("level")
            native_lang = user_state.get("native_language") # Keep native_lang in state
            all_topics = load_topics_for_telegram().get(learn_lang, [])

            if selected_topic in all_topics:
                set_state(chat_id, topic=selected_topic, current_mode="in_exercise")
                send_message(chat_id, f"Mavzu '\\{selected_topic}\\' tanlandi. Mashq yuklanmoqda...")
                send_voice(chat_id, f"Mavzu '\\{selected_topic}\\' tanlandi. Mashq yuklanmoqda.", lang=learn_lang)
                
                # Generate and send the first exercise
                exercise_data = await generate_multiple_choice_exercise(
                    language=learn_lang, 
                    level=level, 
                    topic=selected_topic,
                    exclude_hashes=[] # Telegram bot doesn't track hashes this way yet
                )
                if exercise_data and not exercise_data.get("error"):
                    send_message(chat_id, f"Savol: {exercise_data['question']}")
                    send_voice(chat_id, exercise_data['question'], lang=learn_lang)
                    options_text = "\\n".join([f"{idx+1}. {opt}" for idx, opt in enumerate(exercise_data['options'])])
                    send_message(chat_id, options_text)
                    for idx, opt in enumerate(exercise_data['options']):
                        send_voice(chat_id, f"{idx+1}. {opt}", lang=learn_lang)
                    set_expected_answer(chat_id, str(exercise_data['correct_answer_index'] + 1)) # Store 1-indexed answer
                else:
                    send_message(chat_id, f"Mashqni yaratishda xatolik yuz berdi: {exercise_data.get('error', 'Noma\\'lum xato')}")
            else:
                topics_text = "\\n".join([f"- {t}" for t in all_topics]) if all_topics else "(Mavzular topilmadi)"
                send_message(chat_id, f"Iltimos, mavzular ro'yxatidan birini tanlang: \\n{topics_text}")
        
        elif current_mode == "in_exercise":
            user_answer = user_message_text.strip()
            expected_answer_index_str = pop_expected_answer(chat_id)

            if expected_answer_index_str and user_answer.isdigit():
                expected_answer_index = int(expected_answer_index_str)
                if int(user_answer) == expected_answer_index:
                    send_message(chat_id, "To'g'ri javob! Barakalla!")
                    send_voice(chat_id, "To'g'ri javob! Barakalla!", lang=user_state.get("native_language", "uz")) # Speak confirmation in native language
                else:
                    send_message(chat_id, "Noto'g'ri javob. Yana bir bor urinib ko'ring.")
                    send_voice(chat_id, "Noto'g'ri javob. Yana bir bor urinib ko'ring.", lang=user_state.get("native_language", "uz")) # Speak confirmation in native language
            else:
                send_message(chat_id, "Iltimos, javob variantining raqamini kiriting.")

            send_message(chat_id, "\\nKeyingi mashqni boshlash uchun /start buyrug'ini bosing yoki mavzuni o'zgartirish uchun /topics yozing.")
            set_state(chat_id, current_mode="start") # Reset to start for simplicity for now

        else:
            send_message(chat_id, "Qanday yordam bera olaman? /start buyrug'ini bosing.")

    except Exception as e:
        logger.error(f"An unexpected error occurred in telegram_webhook: {e}", exc_info=True)
        send_message(chat_id, "Uzr, kutilmagan xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")
    
    return {"ok": True}

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}", exc_info=True)


def send_photo(chat_id, photo_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram photo: {e}", exc_info=True)


def send_game_options(chat_id, game_data):
    # This function would be expanded to send interactive game elements
    pass