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
from app.translations import get_text

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
    # Removed aggressive cleaning that was stripping non-Latin characters
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

def get_exercise_result_keyboard(native_lang: str) -> dict:
    return {"keyboard": [
        [{"text": get_text(native_lang, "try_again_button")}, {"text": get_text(native_lang, "next_exercise_button")}],
        [{"text": get_text(native_lang, "restart_button")}]
    ], "resize_keyboard": True, "one_time_keyboard": True}


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
        # Get native language properly, defaulting to 'uzbek' if not set
        native_lang = user_state.get("native_language", "uzbek")
        
        user_message_text = message["text"] if message and "text" in message else ""
        
        # --- Handle commands ---
        if user_message_text.startswith('/'):
            command = user_message_text.split()[0]
            if command == "/start":
                send_message(
                    chat_id,
                    get_text(native_lang, "welcome"),
                    reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_native_language")
                )
                set_state(chat_id, current_mode="choose_native_language")
            elif command == "/help":
                send_message(chat_id, get_text(native_lang, "help"))
            elif command == "/voice_test":
                send_message(chat_id, "Бу овоз тести. Ассалому алайкум!")
                send_voice(chat_id, "Бу овоз тести. Ассалому алайкум!", lang="uzbek")
            elif command == "/topics":
                if "learn_language" in user_state and "level" in user_state:
                    learn_lang = user_state.get("learn_language")
                    topics = load_topics_for_telegram().get(learn_lang, [])
                    send_message(chat_id, get_text(native_lang, "topics_list"), reply_markup=get_topics_keyboard(topics))
                    set_state(chat_id, current_mode="choose_topic")
                else:
                    send_message(chat_id, get_text(native_lang, "need_lang_level"))
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
                    send_message(chat_id, get_text(native_lang, "game_type_select"), reply_markup=game_keyboard)
                    set_state(chat_id, current_mode="choose_game_type")
                else:
                    send_message(chat_id, get_text(native_lang, "need_lang_level"))
            else:
                send_message(chat_id, get_text(native_lang, "unknown_command"))
            return {"ok": True}

        # --- State-based interaction logic ---
        if current_mode == "choose_native_language":
            selected_native_lang_display = user_message_text.strip().replace(" 🇷🇺", "").replace(" 🇬🇧", "").replace(" 🇰🇷", "").replace(" 🇺🇿", "")
            # Mapping for various inputs
            valid_langs_map = {
                "русский": "russian", "рус тили": "russian", "rus tili": "russian", "russian": "russian",
                "инглиз тили": "english", "english": "english", "ingliz tili": "english",
                "корейс тили": "korean", "한국어": "korean", "koreys tili": "korean", "korean": "korean",
                "ўзбек тили": "uzbek", "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            # Simplified mapping check
            native_lang_slug = None
            for key, val in valid_langs_map.items():
                if key in selected_native_lang_display.lower():
                    native_lang_slug = val
                    break
            
            if native_lang_slug:
                set_state(chat_id, native_language=native_lang_slug, current_mode="choose_learn_language")
                
                # Update native_lang usage immediately
                native_lang = native_lang_slug
                
                send_message(
                    chat_id, 
                    get_text(native_lang, "native_selected", lang=selected_native_lang_display),
                    reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_learn_language")
                )
                # Send voice in the new native language
                voice_text = get_text(native_lang, "native_selected", lang=selected_native_lang_display)
                send_voice(chat_id, voice_text, lang=native_lang)
            else:
                send_message(chat_id, get_text(native_lang, "please_select_native"),
                             reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_native_language"))

        elif current_mode == "choose_learn_language":
            selected_learn_lang_display = user_message_text.strip().replace(" 🇷🇺", "").replace(" 🇬🇧", "").replace(" 🇰🇷", "").replace(" 🇺🇿", "")
            # Ensure native_lang is set
            native_lang = user_state.get("native_language", "uzbek")
            
            valid_langs_map = {
                "русский": "russian", "рус тили": "russian", "rus tili": "russian", "russian": "russian",
                "инглиз тили": "english", "english": "english", "ingliz tili": "english",
                "корейс тили": "korean", "한국어": "korean", "koreys tili": "korean", "korean": "korean",
                "ўзбек тили": "uzbek", "o'zbek tili": "uzbek", "uzbek": "uzbek",
            }
            learn_lang_slug = None
            for key, val in valid_langs_map.items():
                if key in selected_learn_lang_display.lower():
                    learn_lang_slug = val
                    break

            if learn_lang_slug:
                set_state(chat_id, learn_language=learn_lang_slug, current_mode="choose_level")
                
                send_message(
                    chat_id, 
                    get_text(native_lang, "learn_selected", lang=selected_learn_lang_display),
                    reply_markup=get_level_keyboard()
                )
                voice_text = get_text(native_lang, "learn_selected", lang=selected_learn_lang_display)
                send_voice(chat_id, voice_text, lang=native_lang)
            else:
                send_message(chat_id, get_text(native_lang, "please_select_learn"),
                             reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_learn_language"))
        
        elif current_mode == "choose_level":
            selected_level = user_message_text.lower().strip()
            learn_lang = user_state.get("learn_language")
            native_lang = user_state.get("native_language", "uzbek")
            
            valid_levels = ["beginner", "intermediate", "advanced"]
            level_map = {
                "бошланғич": "beginner", "boshlang'ich": "beginner", "beginner": "beginner",
                "ўрта": "intermediate", "o'rta": "intermediate", "middle": "intermediate", "intermediate": "intermediate",
                "юқори": "advanced", "yuqori": "advanced", "advanced": "advanced",
            }
            
            # Try to match key in selected level text
            level_slug = None
            for key, val in level_map.items():
                if key in selected_level:
                    level_slug = val
                    break

            if level_slug:
                set_state(chat_id, level=level_slug, current_mode="choose_topic")
                topics = load_topics_for_telegram().get(learn_lang, [])
                
                send_message(
                    chat_id, 
                    get_text(native_lang, "level_selected", level=level_slug.capitalize()),
                    reply_markup=get_topics_keyboard(topics)
                )
                voice_text = get_text(native_lang, "level_selected", level=level_slug.capitalize())
                send_voice(chat_id, voice_text, lang=native_lang)
            else:
                send_message(chat_id, get_text(native_lang, "please_select_level"),
                             reply_markup=get_level_keyboard())

        elif current_mode == "choose_topic":
            selected_topic = user_message_text.strip()
            learn_lang = user_state.get("learn_language")
            level = user_state.get("level")
            native_lang = user_state.get("native_language", "uzbek")
            all_topics = load_topics_for_telegram().get(learn_lang, [])

            if selected_topic in all_topics:
                set_state(chat_id, topic=selected_topic, current_mode="in_exercise")
                
                msg_text = get_text(native_lang, "topic_selected", topic=selected_topic)
                send_message(chat_id, msg_text)
                send_voice(chat_id, msg_text, lang=native_lang)
                
                # Get native language for question generation (using variable we already have)
                exercise_data = await generate_multiple_choice_exercise(
                    learn_language=learn_lang,
                    native_language=native_lang,
                    level=level, 
                    topic=selected_topic,
                    exclude_hashes=[] 
                )
                if exercise_data and not exercise_data.get("error"):
                    question_label = get_text(native_lang, "question_label")
                    question_text = f"{question_label}: {exercise_data['question']}"
                    options_text_list = [f"{idx+1}. {opt}" for idx, opt in enumerate(exercise_data['options'])]
                    options_text_combined = "\n".join(options_text_list)
                    
                    send_message(chat_id, question_text)
                    # Question is now in native language, so use native_lang for TTS
                    send_voice(chat_id, exercise_data['question'], lang=native_lang)
                    
                    send_message(chat_id, options_text_combined, reply_markup=get_exercise_options_keyboard(exercise_data['options']))

                    set_expected_answer(chat_id, str(exercise_data['correct_answer_index'] + 1)) 
                    set_state(chat_id, current_explanation=exercise_data.get("explanation", ""))
                else:
                    error_msg = exercise_data.get('error', 'Unknown error')
                    send_message(chat_id, get_text(native_lang, "error_generating", error=error_msg))
            else:
                topics_text = "\n".join([f"- {t}" for t in all_topics]) if all_topics else ""
                send_message(chat_id, get_text(native_lang, "please_select_topic") + f"\n{topics_text}",
                             reply_markup=get_topics_keyboard(all_topics))
        
        elif current_mode == "in_exercise":
            user_answer = user_message_text.strip()
            # Ensure native_lang is set
            native_lang = user_state.get("native_language", "uzbek")
            
            # Check for navigation buttons first
            try_again_txt = get_text(native_lang, "try_again_button")
            next_ex_txt = get_text(native_lang, "next_exercise_button")
            restart_txt = get_text(native_lang, "restart_button")
            
            if user_answer == try_again_txt:
                 # Logic to re-ask could go here, but for now we'll just treat it as next exercise for simplicity or restart topic
                 # Since we don't store previous question state easily, let's treat "Try Again" as "New Question" or just ignore if not possible.
                 # Actually, better to treating it as "Next Exercise" effectively if we can't repeat.
                 # Or better: "Try Again" is not offering much value if we showed the answer.
                 # Let's map "Try Again" to "Next Exercise" for now to avoid complexity, or just re-generate.
                 # Better yet: Let's assume "Try Again" means "Generate another one".
                 set_state(chat_id, current_mode="choose_topic")
                 # Trigger topic selection logic again (Need to refactor to avoid code duplication? Or just simulate /topics)
                 # Simulating /topics selection with current topic:
                 current_topic = user_state.get("topic")
                 # We can trick the bot by calling the logic for choose_topic again? 
                 # No, let's just send a message to pick topic or auto-pick.
                 # Easiest: clear state slightly and pretend topic was selected.
                 # Actually, simpler:
                 send_message(chat_id, get_text(native_lang, "topic_selected", topic=user_state.get("topic", "")))
                 # Call separate function or just tell user to wait. 
                 # To keep it simple in this monolithic function, let's Redirect to "choose_topic" handler by recursively calling or just guiding user?
                 # We can just change current_mode to "choose_topic" and assume the user sends the topic name? No.
                 # Best: Send "Please type topic again" or just Auto-generate.
                 # Auto-generation requires async call here.
                 
                 # Let's just handle "Next Exercise" and "Home" for now given constraints.
                 # Use "topic" from state to generate new exercise.
                 pass

            if user_answer == next_ex_txt or user_answer == try_again_txt: # treating try again as next for now
                current_topic = user_state.get("topic")
                if current_topic:
                     # Re-run generation logic.
                     # Since we can't easily jump back to 'choose_topic' block without user input,
                     # We will just instruct user or call logic if I refactor.
                     # Refactoring is risky. Let's just unset expected answer and set mode to 'choose_topic' 
                     # and Simulate user sending the topic name?
                     # No, user didn't send topic name.
                     # Let's use a trick: Set mode to "choose_topic" and call the webhook logic? No.
                     
                     # Simple solution: prompt user to click "Next" which sends a command?
                     # No, the button sends text.
                     
                     # Let's just generate the game right here!
                     # Copy-paste generation logic? No.
                     # Let's clean up state and ask to select topic again or use /topics.
                     pass
            
            # --- Simplified Logic within constraints ---
            # If user sends navigation text, handle it.
            if user_answer == next_ex_txt or user_answer == try_again_txt:
                 # Use the existing topic to generate a new Q
                 # Pass control to 'choose_topic' logic by setting mode and simulating input?
                 # We can't simulate input easily. 
                 # We will just ask user to confirm topic or just say "Loading..." and call generate.
                 
                 # REFACTOR: We should extract generation to a function.
                 # But for now:
                 topic = user_state.get("topic")
                 if topic:
                     # Simulate topic selection:
                     # We can just set state 'choose_topic' and tell user "Send topic name" 
                     # but that's bad UX if they clicked "Next".
                     
                     # Let's just generate it here.
                     msg_text = get_text(native_lang, "topic_selected", topic=topic)
                     send_message(chat_id, msg_text)
                     
                     learn_lang = user_state.get("learn_language")
                     level = user_state.get("level")
                     
                     exercise_data = await generate_multiple_choice_exercise(
                        learn_language=learn_lang,
                        native_language=native_lang,
                        level=level, 
                        topic=topic,
                        exclude_hashes=[] 
                     )
                     
                     if exercise_data and not exercise_data.get("error"):
                        question_label = get_text(native_lang, "question_label")
                        question_text = f"{question_label}: {exercise_data['question']}"
                        options_text_list = [f"{idx+1}. {opt}" for idx, opt in enumerate(exercise_data['options'])]
                        options_text_combined = "\n".join(options_text_list)
                        
                        send_message(chat_id, question_text)
                        send_voice(chat_id, exercise_data['question'], lang=native_lang)
                        send_message(chat_id, options_text_combined, reply_markup=get_exercise_options_keyboard(exercise_data['options']))
                        
                        set_expected_answer(chat_id, str(exercise_data['correct_answer_index'] + 1)) 
                        set_state(chat_id, current_explanation=exercise_data.get("explanation", ""))
                     else:
                        send_message(chat_id, get_text(native_lang, "error_generating", error=exercise_data.get('error')))
                     return {"ok": True}

            if user_answer == restart_txt:
                send_message(chat_id, get_text(native_lang, "welcome"), reply_markup=get_language_keyboard(["russian", "english", "korean", "uzbek"], "choose_native_language"))
                set_state(chat_id, current_mode="choose_native_language")
                return {"ok": True}

            expected_answer_index_str = pop_expected_answer(chat_id)

            if expected_answer_index_str and user_answer.isdigit():
                expected_answer_index = int(expected_answer_index_str)
                if int(user_answer) == expected_answer_index:
                    msg_text = get_text(native_lang, "correct") # fixed key from correct_answer
                    send_message(chat_id, msg_text)
                    send_voice(chat_id, msg_text, lang=native_lang) 
                    
                    # Show result buttons
                    send_message(chat_id, get_text(native_lang, "next_exercise"), reply_markup=get_exercise_result_keyboard(native_lang))
                else:
                    explanation = user_state.get("current_explanation", "")
                    msg_text = get_text(native_lang, "incorrect_with_explanation", explanation=explanation)
                    send_message(chat_id, msg_text)
                    send_voice(chat_id, get_text(native_lang, "incorrect"), lang=native_lang) # Just say incorrect for voice
                    
                    # Show result buttons
                    send_message(chat_id, get_text(native_lang, "next_exercise"), reply_markup=get_exercise_result_keyboard(native_lang))
            else:
                # If we popped answer but it wasn't valid digit, and not nav button -> 
                # We lost the expected answer! We must restore it or just fail gracefully.
                # Since pop_expected_answer removes it, we are in trouble if user sends garbage.
                # BUT: pop_expected_answer implementation (redis) typically removes.
                # We should probably peek or restore.
                # Let's assume we can't easily restore without keeping it in variable.
                # Re-set it if valid?
                if expected_answer_index_str:
                    set_expected_answer(chat_id, expected_answer_index_str)
                    
                send_message(chat_id, get_text(native_lang, "enter_number"),
                             reply_markup=get_exercise_options_keyboard(["1","2","3","4"])) 


        elif current_mode == "choose_game_type":
            # Map game type selection
            native_lang = user_state.get("native_language", "uzbek")
            
            game_type_map = {
                "🎯 мослаштириш ўйини": "matching", "matching": "matching",
                "🧠 хотира ўйини": "memory", "memory": "memory",
                "🎨 судраб ташлаш": "drag_drop", "drag_drop": "drag_drop",
                "❓ викторина": "quiz", "quiz": "quiz"
            }
            
            selected_game_type = None
            for key, val in game_type_map.items():
                if key in user_message_text.lower():
                    selected_game_type = val
                    break
            
            if selected_game_type:
                set_state(chat_id, game_type=selected_game_type, current_mode="choose_game_topic")
                
                # Show topics for game
                learn_lang = user_state.get("learn_language")
                topics = load_topics_for_telegram().get(learn_lang, [])
                send_message(chat_id, get_text(native_lang, "choose_game_topic"), reply_markup=get_topics_keyboard(topics))
            else:
                send_message(chat_id, get_text(native_lang, "please_select_game_type"))
                
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
                    
                    # Send link to full game
                    web_app_url = os.getenv("WEBAPP_URL", "https://uzru-production.up.railway.app")
                    
                    play_button_text = get_text(native_lang, "play_on_web")
                    keyboard = {
                        "inline_keyboard": [[{"text": play_button_text, "web_app": {"url": web_app_url}}]]
                    }
                    send_message(chat_id, get_text(native_lang, "click_to_play"), reply_markup=keyboard)
                    
                    set_state(chat_id, current_mode="start")
                else:
                    error_msg = game_data.get('error', 'Unknown error')
                    send_message(chat_id, get_text(native_lang, "error_generating", error=error_msg))
            else:
                send_message(chat_id, get_text(native_lang, "please_select_topic"),
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