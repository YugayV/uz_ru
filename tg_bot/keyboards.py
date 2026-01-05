from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    [
        ["👶 Детский режим", "📱 Открыть приложение"],
        ["📘 Учёба", "🎮 Игра"],
        ["🎥 Посмотреть рекламу"],
        ["⭐ Premium"]
    ],
    resize_keyboard=True
)

payment_menu = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("💳 Visa/Mastercard (Stripe)", callback_data="pay_stripe"),
        InlineKeyboardButton("🅿️ PayPal", callback_data="pay_paypal")
    ]
])
