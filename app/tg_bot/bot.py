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


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN is not set in environment or .env file")
    # Don't raise immediately, let's see if we can log it first
    # raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    user_id = update.message.from_user.id
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
        # Note: base_language is hardcoded to RU for now in this handler
        answer = ask_ai(text, mode=mode, base_language='RU')
        if not answer:
            answer = "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"Error calling AI: {e}")
        answer = "⚠️ Error: AI Tutor is currently unavailable."

    await update.message.reply_text(answer)

def start_bot(): 
    if not BOT_TOKEN:
        print("❌ Cannot start bot: TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    
    masked_token = f"{BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}" if len(BOT_TOKEN) > 10 else "***"
    print(f"Bot is starting with token: {masked_token}")
    print("🚀 Bot is polling... Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_bot()