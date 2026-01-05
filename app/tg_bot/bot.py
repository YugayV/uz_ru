import os 
import asyncio 
from telegram import Update 
from telegram.ext import ( 
    ApplicationBuilder, 
    MessageHandler, 
    CommandHandler,
    ContextTypes, 
    filters, 
)
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from services.ai_tutor import ask_ai 
from app.tg_bot.keyboards import main_menu 
from app.tg_bot.states import user_state, MODE_CHILD, MODE_STUDY
from app.tg_bot.games import math_game
from app.services.lives import get_lives, use_life

# Voice/STT/TTS support
import requests
from tg_bot.config import BACKEND_URL, LANGUAGE_MAP
from tg_bot.voice import voice_to_text
from gtts import gTTS
import uuid
import tempfile
import os

# Simple in-memory user state for this bot
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


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN is not set in environment or .env file")
    # Don't raise immediately, let's see if we can log it first
    # raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    user_id = update.message.from_user.id
    # Grant monthly free premium to new user in both premium set and in-memory progress
    try:
        from services.premium import enable_premium
        from services.user_progress import get_progress, grant_free_premium_for_progress
        enable_premium(user_id)
        progress = get_progress(user_id)
        grant_free_premium_for_progress(progress)
    except Exception:
        pass

    user_state[user_id] = MODE_STUDY
    print(f"User {user_id} started the bot")
    await update.message.reply_text(
        "👋 Welcome to AI Tutor!\nChoose a mode:",
        reply_markup=main_menu
    )

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text
    print(f"Received message from {user_id}: {text}")

    if text == "👶 Детский режим":
        user_state[user_id] = MODE_CHILD
        await update.message.reply_text(
            "🧸 Детский режим включён!\nЗадай вопрос 👇"
        )
        return

    if text == "📘 Учёба":
        user_state[user_id] = MODE_STUDY
        await update.message.reply_text("📘 Режим учёбы активен.")
        return

    if text == "🎮 Игра":
        game = math_game()
        await update.message.reply_text(f"🎲 Игра началась!\n{game['question']}")
        user_state[user_id] = ("game", str(game["answer"]))
        return

    mode = user_state.get(user_id, MODE_STUDY)

    if isinstance(user_state.get(user_id), tuple):
        state_type, correct = user_state[user_id]
        if state_type == "game":
            if text.strip() == correct:
                await update.message.reply_text("🎉 Correct! You are smart 🦫")
            else:
                await update.message.reply_text(f"❌ Try again! (Answer was {correct})")
            user_state[user_id] = MODE_CHILD # Reset to a default mode after game
            return

    try:
        # Prefer backend tutor
        payload = {**get_user(user_id), "user_input": text, "user_id": user_id}
        try:
            resp = requests.post(BACKEND_URL, json=payload, timeout=8)
            data = resp.json()
            answer = data.get("reply") or data.get("answer") or ""
            if not answer:
                answer = "Sorry, I couldn't generate a response."
            lives = data.get('lives')
            xp = data.get('xp')
            level = data.get('level')
            # Determine premium badge (use backend flag if present, otherwise check local progress)
            from services.user_progress import get_progress
            try:
                is_premium = data.get('is_premium') if 'data' in locals() and isinstance(data, dict) else get_progress(user_id).is_premium
            except Exception:
                is_premium = get_progress(user_id).is_premium
            badge = "💎 PREMIUM" if is_premium else "FREE"

            if lives is not None or xp is not None or level is not None:
                stats = []
                if lives is not None:
                    stats.append(f"❤️ {lives}")
                if xp is not None:
                    stats.append(f"⭐ {xp}")
                if level is not None:
                    stats.append(f"Lv {level}")
                answer = f"{badge}\n{answer}\n\n{' '.join(stats)}"
            else:
                answer = f"{badge}\n{answer}"
        except Exception as e:
            print(f"Backend tutor call failed, falling back to local ask_ai: {e}")
            answer = ask_ai(text, mode=mode, base_language='RU') or "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"Error calling AI: {e}")
        answer = "⚠️ Error: AI Tutor is currently unavailable."

    await update.message.reply_text(answer)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = voice_to_text(ogg_path, language_code=sr_lang)
        # Kid mode: if child is silent, request audio prompt from backend (voice-first)
        if not text:
            # Determine child mode based on user_state
            mode = user_state.get(user_id, MODE_STUDY)
            is_kid = (mode == MODE_CHILD)
            if is_kid:
                payload = {**get_user(user_id), 'user_id': user_id}
                try:
                    resp = requests.post(BACKEND_URL, json=payload, timeout=6)
                    data = resp.json()
                    prompt = data.get('answer') or data.get('reply')
                except Exception as e:
                    print(f"Backend prompt error: {e}")
                    prompt = "Listen 👂 Now you say!"

                # slow TTS for kids
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
            print(f"Tutor backend call failed: {e}")

        if not reply:
            try:
                reply = ask_ai(text, mode=user.get('mode','adult'), base_language='RU')
            except Exception:
                reply = "Извините, AI временно недоступен."

        try:
            tts = gTTS(reply, lang=gtts_lang)
            tts.save(mp3_path)
            with open(mp3_path, 'rb') as f:
                await update.message.reply_voice(voice=f)
            if stats_text:
                from services.user_progress import get_progress
                is_premium = get_progress(user_id).is_premium
                badge = "💎 PREMIUM" if is_premium else "FREE"
                await update.message.reply_text(f"{badge}\n{stats_text}")
        except Exception as e:
            print(f"TTS failed: {e}")
            await update.message.reply_text(reply)

    finally:
        for p in [ogg_path, mp3_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

def start_bot(): 
    if not BOT_TOKEN:
        print("❌ Cannot start bot: TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    masked_token = f"{BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}" if len(BOT_TOKEN) > 10 else "***"
    print(f"Bot is starting with token: {masked_token}")
    print("🚀 Bot is polling... Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_bot()