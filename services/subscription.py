from datetime import  datetime


SUBSCRIPTIONS = {}

def get_plan(chat_id):
    return SUBSCRIPTIONS.get(chat_id, "free")

def set_plan(chat_id, plan):
    SUBSCRIPTIONS[chat_id] = plan

def is_premium(user: User) -> bool:
    if user.premium_until is None:
        return False
    return user.premium_until > datetime.utcnow()

    if new_user:
        await update.message.reply_text(
        "🎉 У тебя **Premium на 30 дней**! 🎉\n"
        "Всё без ограничений, без рекламы и с полным доступом к AI Tutor."
    )
    # действуют ограничения
