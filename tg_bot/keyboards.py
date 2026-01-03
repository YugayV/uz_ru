from telegram import ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    [
        ["👶 Детский режим"],
        ["📘 Учёба", "🎮 Игра"],
        ["⭐ Premium"]
    ],
    resize_keyboard=True
)
