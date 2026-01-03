import os 
import asyncio 
from telegram import Update 
from telegram.ext import ( 
    ApplicationBuilder, 
    MessageHandler, 
    ContextTypes, 
    filters, 
)

from app.services.ai_tutor import ask_ai 
from tg_bot.keyboards import main_menu 
from tg_bot.states import user_state, MODE_CHILD, MODE_STUDY




BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text

    if text == "/start":
        user_state[user_id] = MODE_STUDY
        await update.message.reply_text(
            "👋 Welcome to AI Tutor!\nChoose a mode:",
            reply_markup=main_menu
        )
        return

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
    if mode == MODE_CHILD:
        prompt = f"Explain for a 6 year old with emojis: {text}"

    await update.message.reply_text("🤔 Thinking...")
    try: 
        answer = ask_ai(prompt, "RU")
    except Exception as e: 
        print(f"Error: {e}")
        answer = "Error. Try again later!"

    if not answer:
        answer = "Error: Empty response."

    await update.message.reply_text(answer)

def start_bot(): 
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, on_message))
    app.run_polling()

if __name__ == "__main__":
    start_bot()