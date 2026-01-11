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
from pathlib import Path # NEW: Import Path
import uuid
from gtts import gTTS

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from app.tg_bot.games import get_random_game

def set_telegram_webhook():
    """Sets the Telegram webhook to the production URL."""
    # Use PUBLIC_URL from environment, but default to the one you provided.
    public_url = os.getenv("PUBLIC_URL", "https://uzru-production.up.railway.app")
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
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")
if not BOT_TOKEN:
    # Instead of crashing, log a critical error. The webhook will fail but the app will run.
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set. Telegram bot will NOT work.")
else:
    print("✅ [telegram.py] TELEGRAM_BOT_TOKEN found.")

# Функция для очистки текста (должна быть здесь)
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
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text) # Более агрессивная чистка
    return cleaned_text.strip()

# Set up the template directory.
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Функция для загрузки тем (должна быть здесь)
def load_topics():
    """Loads topics from the JSON file."""
    topics_path = Path(__file__).resolve().parents[2] / "content" / "topics.json"
    try:
        with open(topics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Define a route for the main page (native language selection)
@router.get("/", response_class=HTMLResponse) # Измените путь на "/"
async def get_native_language_selection(request: Request):
    """Serves the initial page for native language selection."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/learn/native/{native_lang_slug}", response_class=HTMLResponse)
async def get_learn_language_selection(request: Request, native_lang_slug: str):
    """
    Serves the page for selecting the language to learn, after native language is chosen.
    """
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }

    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug
    }
    return templates.TemplateResponse("learn_language_selection.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}", response_class=HTMLResponse)
async def get_level_selection(request: Request, native_lang_slug: str, learn_lang_slug: str):
    """
    Serves the level selection page for a given language.
    """
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug
    }
    return templates.TemplateResponse("level.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}/{level}", response_class=HTMLResponse)
async def get_topics_page(request: Request, native_lang_slug: str, learn_lang_slug: str, level: str):
    """Serves the topic selection page."""
    all_topics = load_topics()
    language_topics = all_topics.get(learn_lang_slug, []) # Topics based on language to learn
    
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug,
        "level_slug": level,
        "topics": language_topics
    }
    return templates.TemplateResponse("topics.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}/{level}/{topic}", response_class=HTMLResponse)
async def get_exercise_page(request: Request, native_lang_slug: str, learn_lang_slug: str, level: str, topic: str):
    """
    Serves the main exercise page.
    This is where the AI-generated content will be displayed.
    """
    session_id = request.cookies.get("session_id")
    user, new_session_id = get_or_create_web_user(session_id)
    
    # Get completed exercises for this user
    completed_hashes = get_completed_exercise_hashes(user.id)
    
    # Generate the exercise content, excluding completed ones and based on the topic
    exercise_data = await generate_multiple_choice_exercise(learn_lang_slug, level, topic, list(completed_hashes))
    
    image_url = None
    # If the exercise was generated successfully, try to generate an image for it
    if exercise_data and not exercise_data.get("error"):
        visual_prompt = exercise_data.get("visual_prompt")
        if visual_prompt:
            image_url = await generate_image(visual_prompt)

    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    level_map = {
        "beginner": "Boshlang'ich",
        "intermediate": "O'rta",
        "advanced": "Yuqori"
    }
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug,
        "level_name": level_map.get(level, level.capitalize()),
        "level_slug": level,
        "exercise": exercise_data,
        "image_url": image_url
    }
    
    # Store the hash of the current exercise in the user's session to mark it as completed later
    if exercise_data and not exercise_data.get("error"):
        current_hash = _hash_exercise(exercise_data)
        request.session['current_exercise_hash'] = current_hash

    response = templates.TemplateResponse("exercise.html", context)
    # If a new session was created, set the cookie in the user's browser
    if new_session_id:
        response.set_cookie(key="session_id", value=new_session_id, httponly=True, max_age=365*24*60*60) # Cookie for 1 year
    
    return response

@router.get("/translator", response_class=HTMLResponse)
async def get_translator_page(request: Request):
    """Serves the translator page."""
    return templates.TemplateResponse("translator.html", {"request": request, "translation_result": ""})

@router.post("/mark_completed")
async def mark_completed(request: Request):
    """Marks the current exercise as completed for the user."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"status": "error", "message": "No session found"}

    user, _ = get_or_create_web_user(session_id)
    
    # We retrieve the hash from the server-side session for security
    current_hash = request.session.get('current_exercise_hash')

    if user and current_hash:
        # This is a simplified way to pass the data to be marked.
        # A more robust way would be to re-hash the data sent from the client.
        mark_exercise_as_completed(user.id, {"question": current_hash}) # We pass a dummy dict with the hash's source
        
        # Clear the hash from the session
        request.session.pop('current_exercise_hash', None)
        
        return {"status": "ok"}
    
    return {"status": "error", "message": "User or exercise hash not found"}


@router.post("/translator", response_class=HTMLResponse)
async def handle_translation(request: Request):
    """Handles the translation request."""
    form_data = await request.form()
    text_to_translate = form_data.get("text_to_translate")
    target_language = form_data.get("target_language")

    translation = ""
    if text_to_translate and target_language:
        translation = await translate_text(text_to_translate, target_language)

    context = {
        "request": request,
        "translation_result": translation,
        "original_text": text_to_translate,
        "target_lang": target_language
    }
    
    return templates.TemplateResponse("translator.html", context)

@router.get("/tts")
async def text_to_speech(text: str, lang: str = 'en'):
    """
    Generates an audio file from text and returns it as a streaming response.
    Supports 'en', 'ru', 'ko', and 'uz'.
    """
    lang_to_use = lang if lang in ['en', 'ru', 'ko'] else 'en'
    
    # Clean the text before generating audio
    cleaned_text = clean_text_for_tts(text)

    if not cleaned_text:
        print("Warning: No text to speak after cleaning.")
        return

    try:
        tts = gTTS(text=cleaned_text, lang=lang_to_use, slow=True)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return StreamingResponse(mp3_fp, media_type="audio/mpeg")
    except Exception as e:
        print(f"Failed to generate TTS audio: {e}")
        return

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
                
                # --- NEW: Visual Menu ---
                state = get_state(chat_id)
                lang = (state or {}).get("language", "RU").lower()
                
                # Define texts based on language
                texts = {
                    "ru": {"caption": "Чем займёмся?", "games": "Игры 🎲", "lessons": "Уроки 📚", "practice": "Практика 🗣️"},
                    "uz": {"caption": "Nima qilamiz?", "games": "O'yinlar 🎲", "lessons": "Darslar 📚", "practice": "Amaliyot 🗣️"},
                    "en": {"caption": "What should we do?", "games": "Games 🎲", "lessons": "Lessons 📚", "practice": "Practice 🗣️"}
                }
                menu_texts = texts.get(lang, texts["ru"])

                # Send a photo with a caption and inline keyboard
                photo_url = "https://i.imgur.com/your_image_placeholder.jpg" # Placeholder image
                keyboard = {"inline_keyboard": [[
                    {"text": menu_texts["games"], "callback_data": "activity:games"},
                    {"text": menu_texts["lessons"], "callback_data": "activity:lessons"},
                    {"text": menu_texts["practice"], "callback_data": "activity:practice"},
                ]]}
                
                payload = {
                    "chat_id": chat_id,
                    "photo": photo_url,
                    "caption": menu_texts["caption"],
                    "reply_markup": keyboard
                }
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json=payload)

            elif cb_data.startswith("activity:"):
                activity = cb_data.split(":", 1)[1]
                if activity == "games":
                    # Logic to start a game (from previous version)
                    state = get_state(chat_id)
                    lang = (state or {}).get("language", "ru")
                    game = get_random_game(is_kid=True, lang=lang)
                    set_state(chat_id, current_game=game)

                    question = game.get("question", "Давай играть!")
                    send_voice(chat_id, question, lang=lang.lower()) # Audio for exercise

                    if game.get("options"):
                        keyboard = {"inline_keyboard": [[{"text": opt, "callback_data": f"game_answer:{i}"} for i, opt in enumerate(game["options"])]]}
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Выбери правильный ответ:", "reply_markup": keyboard})
                    set_expected_answer(chat_id, str(game.get("answer")))
                # Placeholder for other activities
                elif activity == "lessons":
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Раздел 'Уроки' в разработке."})
                elif activity == "practice":
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Раздел 'Практика' в разработке."})


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