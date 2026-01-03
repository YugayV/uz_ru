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
from services.progress import is_premium, enable_premium
from services.ai_tutor import ask_ai 

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()
from .keyboards import main_menu, payment_menu
from app.tg_bot.states import user_state, MODE_CHILD, MODE_STUDY
from app.tg_bot.games import math_game
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
        logger.error(f"Error calling AI: {e}")
        answer = "⚠️ Error: AI Tutor is currently unavailable."

    await update.message.reply_text(answer)

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
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    masked_token = f"{BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}" if len(BOT_TOKEN) > 10 else "***"
    logger.info(f"Bot is starting with token: {masked_token}")
    logger.info("🚀 Bot is polling... Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_bot()