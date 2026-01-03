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

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: 
        return

    text = update.message.text 

    await update.message.reply_text(" Thinking...")

    try: 
        answer = ask_ai(text, "RU")
    except Exception as e: 
        answer = " Error. Try again later!"

    await update.message.reply_text(answer)

async def start_bot(): 
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep the bot running
    await asyncio.Event().wait()