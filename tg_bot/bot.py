import os 
import asyncio 
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ( 
    ApplicationBuilder, 
    MessageHandler, 
    CommandHandler,
    ContextTypes, 
    filters,
    CallbackQueryHandler,
)
import logging
from dotenv import load_dotenv
from services.premium import is_premium, enable_premium
from services.ai_tutor import ask_ai 
from services.ads import can_watch_ad, register_ad_view
from services.lives import add_lives, get_lives
from app.tg_bot.games import get_random_game
from services.analytics import track_event

# HTTP backend for tutor (we call /ai/ask)
import requests
from tg_bot.config import BACKEND_URL, LANGUAGE_MAP
from tg_bot.voice import voice_to_text
from gtts import gTTS
import uuid
import tempfile
import os

# Simple in-memory user state for demo purposes
USER_STATE: dict = {}

def get_user(user_id: int) -> dict:
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {
            "age_group": "kid",
            "language_pair": "uz-ru",
            "level": 1,
            "lesson_title": "Salom"
        }
    return USER_STATE[user_id]

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()
from .keyboards import main_menu
from app.tg_bot.states import user_state, MODE_CHILD, MODE_STUDY
from app.tg_bot.games import get_random_game
from services.lives import get_lives, use_life
from services.stripe_service import create_checkout
from services.paypal_service import create_paypal_order


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is not set in environment or .env file")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    user_id = update.message.from_user.id
    # Activate premium in the lightweight premium set
    enable_premium(user_id)
    # Also update in-memory progress premium expiry
    try:
        from services.user_progress import get_progress, grant_free_premium_for_progress
        progress = get_progress(user_id)
        grant_free_premium_for_progress(progress)
    except Exception:
        pass

    user_state[user_id] = MODE_STUDY
    logger.info(f"User {user_id} started the bot")
    await update.message.reply_text(
        "👋 Welcome to AI Tutor!\nChoose a mode:",
        reply_markup=main_menu
    )

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user or not update.message.text:
        return

    user_id = update.message.from_user.id
    
    if not is_premium(user_id):
        lives = get_lives(user_id)
        if lives <= 0:
            await update.message.reply_text(
                "❤️ У тебя закончились жизни.\n"
                "⏳ Попробуй завтра или включи ⭐ Premium."
            )
            return

        if not use_life(user_id):
            await update.message.reply_text(
                "❤️ Жизни закончились.\n"
                "⏳ Попробуй позже."
            )
            return
    
    text = update.message.text
    logger.info(f"Received message from {user_id}: {text}")

    if text == "👶 Детский режим":
        user_state[user_id] = MODE_CHILD
        await update.message.reply_text(
            f"🧸 Детский режим включён!\nЗадай вопрос 👇\n\n🦫 У тебя осталось {lives} сердечек ❤️"
        )
        return
        await update.message.reply_text(
        f"🦫 Молодец!\n"
        f"Ты получил 2 сердечка ❤️❤️"
)
        return

    if text == "📱 Открыть приложение":
        await update.message.reply_text(
            "Нажмите на кнопку ниже, чтобы открыть приложение",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Открыть", web_app={"url": f"{os.getenv('WEBAPP_URL')}/webapp/"})
            ]])
        )
        return

    if text == "📘 Учёба":
        user_state[user_id] = MODE_STUDY
        await update.message.reply_text("📘 Режим учёбы активен.")
        return

    if text == "⭐ Premium":
        if is_premium(user_id):
            await update.message.reply_text(
                "⭐ У тебя уже активен Premium!\n"
                "Наслаждайся обучением 🚀"
            )
        else:
            await update.message.reply_text(
                "🌟 **Premium Доступ**\n\n"
                "• Безлимитные жизни ❤️\n"
                "• Приоритетный AI (GPT-4o)\n"
                "• Доступ ко всем играм\n\n"
                "Выберите способ оплаты (или напишите ACTIVATE для теста):",
                reply_markup=payment_menu,
                parse_mode="Markdown"
            )
        return

    if text == "ACTIVATE":
        enable_premium(user_id)
        await update.message.reply_text(
            "🎉 Premium активирован!\n"
            "Жизни теперь бесконечны ❤️♾"
        )
        return

    if text == "🎮 Игра":
        mode = user_state.get(user_id, MODE_STUDY)
        is_kid = mode == MODE_CHILD
        game = get_random_game(is_kid=is_kid)
        
        track_event(str(user_id), "game_started", {"game_name": game['question'], "is_kid": is_kid})

        await update.message.reply_text(f"🎲 Игра началась!\n{game['question']}")
        user_state[user_id] = ("game", str(game["answer"]))
        return

    mode = user_state.get(user_id, MODE_STUDY)

    if isinstance(user_state.get(user_id), tuple):
        state_type, correct = user_state[user_id]
        if state_type == "game":
            is_correct = text.strip().lower() == correct.lower()
            
            track_event(str(user_id), "game_answered", {"correct_answer": correct, "user_answer": text, "is_correct": is_correct})

            if is_correct:
                await update.message.reply_text("🎉 Correct! You are smart 🦫")
            else:
                await update.message.reply_text(f"❌ Try again! (Answer was {correct})")
            user_state[user_id] = MODE_CHILD # Reset to a default mode after game
            return

    try:
        # Prefer tutor backend (DeepSeek) via HTTP POST so we can use tutor payloads
        payload = {**get_user(user_id), "user_input": text, "user_id": user_id}
        try:
            resp = requests.post(BACKEND_URL, json=payload, timeout=8)
            data = resp.json()
            # 'reply' for tutor mode, fallback to 'answer'
            answer = data.get("reply") or data.get("answer") or ""
            if not answer:
                answer = "Sorry, I couldn't generate a response."
            # append game stats when present
            lives = data.get('lives')
            xp = data.get('xp')
            level = data.get('level')
            if lives is not None or xp is not None or level is not None:
                stats = []
                if lives is not None:
                    stats.append(f"❤️ {lives}")
                if xp is not None:
                    stats.append(f"⭐ {xp}")
                if level is not None:
                    stats.append(f"Lv {level}")
                answer = f"{answer}\n\n{' '.join(stats)}"
    except Exception as e:
        logger.error(f"Error calling AI: {e}")
        answer = "⚠️ Error: AI Tutor is currently unavailable."

    await update.message.reply_text(answer)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages: download, transcribe, send to tutor backend and respond with voice."""
    if not update.message or not update.message.from_user or not update.message.voice:
        return

    user_id = update.message.from_user.id
    user = get_user(user_id)

    voice = update.message.voice
    file = await voice.get_file()

    temp_dir = tempfile.gettempdir()
    ogg_path = os.path.join(temp_dir, f"{uuid.uuid4()}.ogg")
    mp3_path = ogg_path.replace('.ogg', '.mp3')

    try:
        await file.download_to_drive(ogg_path)

        # guess languages
        def guess_lang_codes(language_pair: str):
            parts = language_pair.split('-')
            if len(parts) >= 2:
                lang_short = parts[1]
            else:
                lang_short = parts[0]
            sr_map = {'ru': 'ru-RU', 'uz': 'uz-UZ', 'en': 'en-US', 'ko': 'ko-KR'}
            gtts_lang = LANGUAGE_MAP.get(lang_short, 'en')
            sr_lang = sr_map.get(lang_short, 'en-US')
            return sr_lang, gtts_lang

        sr_lang, gtts_lang = guess_lang_codes(user.get('language_pair', 'uz-ru'))

        # Transcribe
        text = voice_to_text(ogg_path, language_code=sr_lang)
        # Kid mode: if child is silent, request audio prompt from backend (voice-first)
        if not text:
            if user.get('age_group') == 'kid':
                # Call backend with no user_input to get the 'listen & repeat' prompt
                payload = {**user, 'user_id': user_id}
                try:
                    resp = requests.post(BACKEND_URL, json=payload, timeout=6)
                    data = resp.json()
                    prompt = data.get('answer') or data.get('reply')
                except Exception as e:
                    print(f"Backend prompt error: {e}")
                    prompt = "Listen 👂 Now you say!"

                # TTS slow for kids
                try:
                    tts = gTTS(prompt, lang=gtts_lang, slow=True)
                    tts.save(mp3_path)
                    with open(mp3_path, 'rb') as f:
                        await update.message.reply_voice(voice=f)
                except Exception as e:
                    print(f"TTS failed: {e}")
                    await update.message.reply_text(prompt)
                finally:
                    try:
                        if os.path.exists(mp3_path):
                            os.remove(mp3_path)
                    except Exception:
                        pass
                return
            else:
                await update.message.reply_text("Извините, я не расслышал. Попробуйте ещё раз.")
                return

        # send to backend tutor
        payload = {**user, 'user_input': text, 'user_id': user_id}
        reply = None
        stats_text = None
        try:
            resp = requests.post(BACKEND_URL, json=payload, timeout=10)
            data = resp.json()
            reply = data.get('reply') or data.get('answer')
            lives = data.get('lives')
            xp = data.get('xp')
            level = data.get('level')
            if lives is not None or xp is not None or level is not None:
                parts = []
                if lives is not None:
                    parts.append(f"❤️ {lives}")
                if xp is not None:
                    parts.append(f"⭐ {xp}")
                if level is not None:
                    parts.append(f"Lv {level}")
                stats_text = " ".join(parts)
        except Exception as e:
            logger.warning(f"Tutor backend call failed: {e}")

        if not reply:
            # fallback to local AI
            try:
                reply = ask_ai(text, mode=user.get('mode','adult'), base_language='RU')
            except Exception:
                reply = "Извините, AI временно недоступен."

        # TTS
        try:
            # slow TTS for kids
            slow_tts = True if user.get('age_group') == 'kid' else False
            tts = gTTS(reply, lang=gtts_lang, slow=slow_tts)
            tts.save(mp3_path)
            with open(mp3_path, 'rb') as f:
                await update.message.reply_voice(voice=f)
            if stats_text:
                await update.message.reply_text(stats_text)
            # handle reward sound if present
            if data.get('reward') and data.get('sound'):
                # convert static path -> local file
                sound_path = data.get('sound')
                if sound_path.startswith('/static/'):
                    from pathlib import Path
                    project_root = Path(__file__).resolve().parents[1]
                    local_sound = project_root / sound_path.lstrip('/static/')
                    if local_sound.exists():
                        with open(local_sound, 'rb') as sf:
                            await update.message.reply_audio(audio=sf)
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            await update.message.reply_text(reply)
    finally:
        for p in [ogg_path, mp3_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "pay_stripe":
        url = create_checkout(user_id)
        await query.edit_message_text(
            f"💳 **Оплата Картой (Visa/Mastercard)**\n\nНажмите кнопку ниже для перехода к оплате:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Оплатить $5", url=url)]]),
            parse_mode="Markdown"
        )
    elif query.data == "pay_paypal":
        url = create_paypal_order(user_id)
        await query.edit_message_text(
            f"🅿️ **Оплата через PayPal**\n\nНажмите кнопку ниже для перехода к оплате:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Оплатить $5", url=url)]]),
            parse_mode="Markdown"
        )

def start_bot(): 
    if not BOT_TOKEN:
        logger.error("❌ Cannot start bot: TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    masked_token = f"{BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}" if len(BOT_TOKEN) > 10 else "***"
    logger.info(f"Bot is starting with token: {masked_token}")
    logger.info("🚀 Bot is polling... Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_bot()