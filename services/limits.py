from datetime import datetime, timedelta
from .subscription import get_plan
USAGE = {}

def allowed(chat_id, max_minutes=20):
    now = datetime.now()
    if chat_id not in USAGE:
        USAGE[chat_id] = now
        return True

    return (now - USAGE[chat_id]) < timedelta(minutes=max_minutes)

def can_use_ai(chat_id):
    return get_plan(chat_id) != "free"

def lesson_limit(chat_id):
    return 10 if get_plan(chat_id) == "free" else 9999


def lives_limit(chat_id):
    return 6 if get_plan(chat_id) == "free" else 9999
