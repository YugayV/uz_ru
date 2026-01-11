import logging
import os
import tempfile
import json
from fastapi import APIRouter, Request
import requests
import re
import uuid
from gtts import gTTS
from pathlib import Path

# Corrected imports to point inside `app`
from app.services.session import get_state, set_state, clear_state, set_expected_answer, pop_expected_answer
from app.services.speech_utils import is_close_answer
from app.ai_content import generate_multiple_choice_exercise

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set. Telegram bot will NOT work.")
else:
    logger.info("✅ [telegram.py] TELEGRAM_BOT_TOKEN found.")

def set_telegram_webhook():
    """Sets the Telegram webhook to the production URL."""
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

def load_topics_for_telegram():
    """Loads topics from the JSON file."""
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
        "\\U0001F600-\\U0001F64F"  # emoticons
        "\\U0001F300-\\U0001F5FF"  # symbols & pictographs
        "\\U0001F680-\\U0001F6FF"  # transport & map symbols
        "\\U0001F700-\\U0001F77F"  # alchemical symbols
        "]+",
        flags=re.UNICODE,
    )
    cleaned_text = emoji_pattern.sub(r'', text)
    cleaned_text = re.sub(r'[^\\w\\s]', '', cleaned_text) 
    return cleaned_text.strip()

def send_voice(chat_id, text, lang="ru"):
    """Generates a voice message from text and sends it to the user."""
    try:
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            logger.warning(f"Skipping TTS for empty or non-string text: {text}")
            return

        filename = f"/tmp/{uuid.uuid4()}.mp3"
        
        # Map language codes for gTTS
        # For Uzbek (both latin and cyrillic), use Russian voice as gTTS doesn't support Uzbek
        lang_map = {
            'russian': 'ru',
            'english': 'en', 
            'korean': 'ko',
            'uzbek': 'ru',  # Use Russian voice for Uzbek Cyrillic text
            'uz': 'ru',
            'ru': 'ru',
            'en': 'en',
            'ko': 'ko'
        }
        lang_to_use = lang_map.get(lang, 'en')
        logger.debug(f"Generating voice for text: '{clean_text}' in language: '{lang_to_use}' (original: '{lang}')")
        
        tts = gTTS(text=clean_text, lang=lang_to_use, slow=True)
        tts.save(filename)

        with open(filename, "rb") as audio:
            payload = {"chat_id": chat_id}
            files = {"voice": audio}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice", data=payload, files=files)
        os.remove(filename) 
    except Exception as e:
        logger.error(f"Failed to send voice message: {e}", exc_info=True)

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup) # Ensure reply_markup is JSON string
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}", exc_info=True)

# --- Keyboard Helper Functions ---
def get_language_keyboard(langs: list, current_mode: str) -> dict:
    keyboard_buttons = []
    for lang in langs:
        display_name = {
            "russian": "Рус тили 🇷🇺", "english": "Инглиз тили 🇬🇧",
            "korean": "Корейс тили 🇰🇷", "uzbek": "Ўзбек тили 🇺🇿"
        }.get(lang, lang.capitalize())
        keyboard_buttons.append([{"text": display_name}])
    
    # Add a back button if not in native language selection
    if current_mode == "choose_learn_language":
         keyboard_buttons.append([{"text": "/start"}]) # Go back to native lang selection
    
    return {"keyboard": keyboard_buttons, "resize_keyboard": True, "one_time_keyboard": True}

def get_level_keyboard() -> dict:
    keyboard_buttons = [
        [{"text": "Beginner"}, {"text": "Intermediate"}],
        [{"text": "Advanced"}],
        [{"text": "/start"}] # Back to learn language selection
    ]
    return {"keyboard": keyboard_buttons, "resize_keyboard": True, "one_time_keyboard": True}

def get_topics_keyboard(topics: list) -> dict:
    keyboard_buttons = []
    row = []
    for i, topic in enumerate(topics):
        row.append({"text": topic})
        if (i + 1) % 2 == 0: # 2 topics per row
            keyboard_buttons.append(row)
            row = []
    if row: # Add any remaining topic
        keyboard_buttons.append(row)
    
    keyboard_buttons.append([{"text": "/start"}]) # Back to level selection
    return {"keyboard": keyboard_buttons, "resize_keyboard": True, "one_time_keyboard": False} # One-time keyboard is set to False for topics

def get_exercise_options_keyboard(options: list) -> dict:
    keyboard_buttons = []
    for i, option in enumerate(options):
        keyboard_buttons.append([{"text": str(i + 1)}]) # Send 1, 2, 3, 4
    keyboard_buttons.append([{"text": "/topics"}, {"text": "/start"}]) # Navigation
    return {"keyboard": keyboard_buttons, "resize_keyboard": True, "one_time_keyboard": True}


@router.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        if not BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is not set!")
            return {"ok": False, "error": "Bot token not configured"}
        
        data = await req.json()
        logger.info(f"Full Telegram payload: {data}")

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

        user_state = get_state(chat_id)
        if user_state is None:
            set_state(chat_id, current_mode="start")
            user_state = get_state(chat_id)

        current_mode = user_state.get("current_mode")
        user_message_text = message["text"] if message and "text" in message else ""
        
        # --- Handle commands ---
        if user_message_text.startswith('/'):
            command = user_message_text.split()[0]
            if command == "/start":
                send_message(
                    chat_id,
                    "Ассалому алайкум! AI тил ўрганиш ботига хуш келибсиз. 🎓\n\n"
                    "Аввал ўзингизнинг она тилингизни танланг:\n\n"
                    "💡 Кейинчалик:\n"
                    "📚 /topics - Машқлар учун мавзулар\n"
                    "🎮 /games - Интерактив ўйинлар",
                    reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_native_language")
                )
                set_state(chat_id, current_mode="choose_native_language")
            elif command == "/help":
                send_message(chat_id, "Ҳали ёрдам функцияси мавжуд эмас.")
            elif command == "/voice_test":
                send_message(chat_id, "Бу овоз тести. Ассалому алайкум!")
                send_voice(chat_id, "Бу овоз тести. Ассалому алайкум!", lang="uz")
            elif command == "/topics":
                if "learn_language" in user_state and "level" in user_state:
                    learn_lang = user_state.get("learn_language")
                    topics = load_topics_for_telegram().get(learn_lang, [])
                    send_message(chat_id, "Мавзулар рўйхати:", reply_markup=get_topics_keyboard(topics))
                    set_state(chat_id, current_mode="choose_topic")
                else:
                    send_message(chat_id, "Мавзуларни кўриш учун аввал тил ва даражани танлашингиз керак. Бошлаш учун /start босинг.")
            elif command == "/games":
                if "learn_language" in user_state and "level" in user_state:
                    # Show game type selection
                    game_keyboard = {
                        "keyboard": [
                            [{"text": "🎯 Мослаштириш ўйини"}, {"text": "🧠 Хотира ўйини"}],
                            [{"text": "🎨 Судраб ташлаш"}, {"text": "❓ Викторина"}],
                            [{"text": "/start"}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": True
                    }
                    send_message(chat_id, "Ўйин турини танланг:", reply_markup=game_keyboard)
                    set_state(chat_id, current_mode="choose_game_type")
                else:
                    send_message(chat_id, "Ўйинларни кўриш учун аввал тил ва даражани танлашингиз керак. Бошлаш учун /start босинг.")
            else:
                send_message(chat_id, "Номаълум буйруқ.")
            return {"ok": True}

        # --- State-based interaction logic ---
        if current_mode == "choose_native_language":
            selected_native_lang_display = user_message_text.strip().replace(" 🇷🇺", "").replace(" 🇬🇧", "").replace(" 🇰🇷", "").replace(" 🇺🇿", "")
            valid_langs_map = {
                "рус тили": "russian", "rus tili": "russian", "russian": "russian",
                "инглиз тили": "english", "ingliz tili": "english", "english": "english",
                "корейс тили": "korean", "koreys tili": "korean", "korean": "korean",
                "ўзбек тили": "uzbek", "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            native_lang_slug = valid_langs_map.get(selected_native_lang_display.lower())

            if native_lang_slug:
                set_state(chat_id, native_language=native_lang_slug, current_mode="choose_learn_language")
                send_message(
                    chat_id, 
                    f"Сизнинг она тилингиз: {native_lang_slug.capitalize()}. Энди ўрганиш учун тилни танланг:",
                    reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_learn_language")
                )
                send_voice(chat_id, f"Сизнинг она тилингиз: {native_lang_slug.capitalize()}.", lang=native_lang_slug)
            else:
                send_message(chat_id, "Илтимос, она тилингизни танланг (Рус тили, Инглиз тили, Корейс тили, Ўзбек тили).",
                             reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_native_language"))

        elif current_mode == "choose_learn_language":
            selected_learn_lang_display = user_message_text.strip().replace(" 🇷🇺", "").replace(" 🇬🇧", "").replace(" 🇰🇷", "").replace(" 🇺🇿", "")
            native_lang = user_state.get("native_language")
            valid_langs_map = {
                "рус тили": "russian", "rus tili": "russian", "russian": "russian",
                "инглиз тили": "english", "ingliz tili": "english", "english": "english",
                "корейс тили": "korean", "koreys tili": "korean", "korean": "korean",
                "ўзбек тили": "uzbek", "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            learn_lang_slug = valid_langs_map.get(selected_learn_lang_display.lower())

            if learn_lang_slug:
                set_state(chat_id, learn_language=learn_lang_slug, current_mode="choose_level")
                send_message(
                    chat_id, 
                    f"Ажойиб! Сиз {learn_lang_slug.capitalize()} тилини ўрганишни танладингиз. Энди даражангизни танланг:",
                    reply_markup=get_level_keyboard()
                )
                send_voice(chat_id, f"Ажойиб! Сиз {learn_lang_slug.capitalize()} тилини ўрганишни танладингиз.", lang=learn_lang_slug)
            else:
                send_message(chat_id, "Илтимос, ўрганиш учун тиллардан бирини танланг (Рус тили, Инглиз тили, Корейс тили, Ўзбек тили).",
                             reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_learn_language"))
        
        elif current_mode == "choose_level":
            selected_level = user_message_text.lower().strip()
            learn_lang = user_state.get("learn_language")
            valid_levels = ["beginner", "intermediate", "advanced"]
            level_map = {
                "бошланғич": "beginner", "boshlang'ich": "beginner", "beginner": "beginner",
                "ўрта": "intermediate", "o'rta": "intermediate", "intermediate": "intermediate",
                "юқори": "advanced", "yuqori": "advanced", "advanced": "advanced",
            }
            level_slug = level_map.get(selected_level)

            if level_slug:
                set_state(chat_id, level=level_slug, current_mode="choose_topic")
                topics = load_topics_for_telegram().get(learn_lang, [])
                send_message(
                    chat_id, 
                    f"Даража {level_slug.capitalize()} танланди. Энди мавзуни танланг:",
                    reply_markup=get_topics_keyboard(topics)
                )
                send_voice(chat_id, f"Даража {level_slug.capitalize()} танланди. Энди мавзуни танланг.", lang=learn_lang)
            else:
                send_message(chat_id, "Илтимос, тўғри даражани танланг (Beginner, Intermediate, Advanced).",
                             reply_markup=get_level_keyboard())

        elif current_mode == "choose_topic":
            selected_topic = user_message_text.strip()
            learn_lang = user_state.get("learn_language")
            level = user_state.get("level")
            all_topics = load_topics_for_telegram().get(learn_lang, [])

            if selected_topic in all_topics:
                set_state(chat_id, topic=selected_topic, current_mode="in_exercise")
                send_message(chat_id, f"Мавзу '{selected_topic}' танланди. Машқ юкланмоқда...")
                
                # Get native language for question generation
                native_lang = user_state.get("native_language", "uzbek")
                send_voice(chat_id, f"Мавзу '{selected_topic}' танланди. Машқ юкланмоқда.", lang=native_lang)
                
                exercise_data = await generate_multiple_choice_exercise(
                    learn_language=learn_lang,
                    native_language=native_lang,
                    level=level, 
                    topic=selected_topic,
                    exclude_hashes=[] 
                )
                if exercise_data and not exercise_data.get("error"):
                    question_text = f"Савол: {exercise_data['question']}"
                    options_text_list = [f"{idx+1}. {opt}" for idx, opt in enumerate(exercise_data['options'])]
                    options_text_combined = "\\n".join(options_text_list)
                    
                    send_message(chat_id, question_text)
                    # Question is now in native language, so use native_lang for TTS
                    send_voice(chat_id, exercise_data['question'], lang=native_lang)
                    
                    send_message(chat_id, options_text_combined, reply_markup=get_exercise_options_keyboard(exercise_data['options']))

                    set_expected_answer(chat_id, str(exercise_data['correct_answer_index'] + 1)) 
                else:
                    send_message(chat_id, f"Машқни яратишда хатолик юз берди: {exercise_data.get('error', 'Номаълум хато')}")
            else:
                topics_text = "\n".join([f"- {t}" for t in all_topics]) if all_topics else "(Мавзулар топилмади)"
                send_message(chat_id, f"Илтимос, мавзулар рўйхатидан бирини танланг: \n{topics_text}",
                             reply_markup=get_topics_keyboard(all_topics))
        
        elif current_mode == "in_exercise":
            user_answer = user_message_text.strip()
            expected_answer_index_str = pop_expected_answer(chat_id)

            if expected_answer_index_str and user_answer.isdigit():
                expected_answer_index = int(expected_answer_index_str)
                if int(user_answer) == expected_answer_index:
                    send_message(chat_id, "Тўғри жавоб! Баракалла!")
                    send_voice(chat_id, "Тўғри жавоб! Баракалла!", lang=user_state.get("native_language", "uz")) 
                else:
                    send_message(chat_id, "Нотўғри жавоб. Яна бир бор уриниб кўринг.")
                    send_voice(chat_id, "Нотўғри жавоб. Яна бир бор уриниб кўринг.", lang=user_state.get("native_language", "uz"))
            else:
                send_message(chat_id, "Илтимос, жавоб вариантининг рақамини киритинг.",
                             reply_markup=get_exercise_options_keyboard(["1","2","3","4"])) # Show options again

            send_message(
                chat_id, 
                "Кейинги машқни бошлаш учун /start буйруғини босинг ёки мавзуни ўзгартириш учун /topics ёзинг.",
                reply_markup={"remove_keyboard": True}
            )
            set_state(chat_id, current_mode="start")

        elif current_mode == "choose_game_type":
            # Map game type selection
            game_type_map = {
                "🎯 мослаштириш ўйини": "matching",
                "🧠 хотира ўйини": "memory",
                "🎨 судраб ташлаш": "drag_drop",
                "❓ викторина": "quiz"
            }
            
            selected_game_type = game_type_map.get(user_message_text.lower().strip())
            
            if selected_game_type:
                set_state(chat_id, game_type=selected_game_type, current_mode="choose_game_topic")
                
                # Show topics for game
                learn_lang = user_state.get("learn_language")
                topics = load_topics_for_telegram().get(learn_lang, [])
                send_message(chat_id, "Ўйин учун мавзу танланг:", reply_markup=get_topics_keyboard(topics))
            else:
                send_message(chat_id, "Илтимос, ўйин турини танланг.")
                
        elif current_mode == "choose_game_topic":
            from app.game_generator import generate_interactive_game, generate_game_images
            
            selected_topic = user_message_text.strip()
            learn_lang = user_state.get("learn_language")
            native_lang = user_state.get("native_language", "uzbek")
            level = user_state.get("level")
            game_type = user_state.get("game_type", "matching")
            all_topics = load_topics_for_telegram().get(learn_lang, [])
            
            if selected_topic in all_topics:
                send_message(chat_id, f"Ўйин яратилмоқда... Илтимос кутинг ⏳")
                
                # Generate game
                game_data = await generate_interactive_game(
                    learn_language=learn_lang,
                    native_language=native_lang,
                    level=level,
                    topic=selected_topic,
                    game_type=game_type
                )
                
                if game_data and not game_data.get("error"):
                    # Generate images for the game (this may take time)
                    send_message(chat_id, "Расмлар яратилмоқда... 🎨")
                    game_data_with_images = await generate_game_images(game_data)
                    
                    # Send game information
                    title = game_data_with_images.get("title", "Ўйин")
                    instructions = game_data_with_images.get("instructions", "")
                    
                    send_message(chat_id, f"🎮 {title}\n\n{instructions}")
                    
                    # Send game items with images
                    if game_type in ["matching", "drag_drop"]:
                        items = game_data_with_images.get("items", [])
                        for item in items[:3]:  # Send first 3 items as example
                            word = item.get("word", "")
                            translation = item.get("translation", "")
                            image_url = item.get("image_url")
                            
                            caption = f"{word}\n({translation})"
                            
                            if image_url:
                                send_photo(chat_id, image_url, caption)
                            else:
                                send_message(chat_id, caption)
                            
                            # Send voice for the word
                            if word:
                                send_voice(chat_id, word, lang=learn_lang)
                    
                    elif game_type == "memory":
                        pairs = game_data_with_images.get("pairs", [])
                        for pair in pairs[:3]:  # Send first 3 pairs as example
                            word = pair.get("word", "")
                            translation = pair.get("translation", "")
                            image_url = pair.get("image_url")
                            
                            caption = f"{word}\n({translation})"
                            
                            if image_url:
                                send_photo(chat_id, image_url, caption)
                            else:
                                send_message(chat_id, caption)
                            
                            if word:
                                send_voice(chat_id, word, lang=learn_lang)
                    
                    elif game_type == "quiz":
                        questions = game_data_with_images.get("questions", [])
                        if questions:
                            first_q = questions[0]
                            question_text = first_q.get("question", "")
                            options = first_q.get("options", [])
                            image_url = first_q.get("image_url")
                            
                            send_message(chat_id, f"❓ {question_text}")
                            
                            if image_url:
                                send_photo(chat_id, image_url)
                            
                            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
                            send_message(chat_id, options_text)
                    
                    send_message(chat_id, 
                                "\n✅ Бу ўйиннинг намунаси!\n\n"
                                "Тўлиқ интерактив ўйинни веб-саҳифада ўйнаш мумкин.\n\n"
                                "Яна ўйин яратиш учун /games буйруғини босинг.",
                                reply_markup={"remove_keyboard": True})
                    
                    set_state(chat_id, current_mode="start")
                else:
                    send_message(chat_id, f"Ўйинни яратишда хатолик: {game_data.get('error', 'Номаълум хато')}")
            else:
                send_message(chat_id, "Илтимос, мавзулар рўйхатидан бирини танланг.",
                            reply_markup=get_topics_keyboard(all_topics))

        else:
            send_message(chat_id, "Қандай ёрдам бера оламан? Бошлаш учун /start буйруғини босинг.",
                         reply_markup={"remove_keyboard": True})

    except Exception as e:
        logger.error(f"An unexpected error occurred in telegram_webhook: {e}", exc_info=True)
        send_message(chat_id, "Uzr, kutilmagan xato yuz berdi. Iltimos, keyinroq urinib ko'ring.",
                     reply_markup={"remove_keyboard": True})
    
    return {"ok": True}

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