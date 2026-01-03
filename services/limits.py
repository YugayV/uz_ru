from datetime import datetime, timedelta

USAGE = {}

def allowed(chat_id, max_minutes=20):
    now = datetime.now()
    if chat_id not in USAGE:
        USAGE[chat_id] = now
        return True

    return (now - USAGE[chat_id]) < timedelta(minutes=max_minutes)
