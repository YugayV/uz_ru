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

from app.services.ai_tutor import ask_ai 
from tg_bot.keyboards import main_menu 
from tg_bot.states import user_state, MODE_CHILD, MODE_STUDY
from tg_bot.games import math_game

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

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

    mode = user_state.get(user_id, MODE_STUDY)

    prompt = text
    if mode == MODE_CHILD and text.lower() == "game":
        game = math_game()
        await update.message.reply_text(game["question"])
        user_state[user_id] = ("game", game["answer"])
        return

if isinstance(user_state.get(user_id), tuple):
    _, correct = user_state[user_id]
    if text.strip() == correct:
        await update.message.reply_text("🎉 Correct! You are smart 🦫")
    else:
        await update.message.reply_text("❌ Try again!")
    user_state[user_id] = MODE_CHILD
    return

answer = ask_ai(text, mode=mode)

def start_bot(): 
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    start_bot()