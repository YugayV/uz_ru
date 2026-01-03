STATE = {}

def get_state(chat_id):
    return STATE.setdefault(chat_id, {
        "lesson_index": 0,
        "word_index": 0,
        "review_queue": []
    })
