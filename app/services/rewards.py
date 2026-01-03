STARS = {}

def add_star(chat_id):
    STARS[chat_id] = STARS.get(chat_id, 0) + 1
