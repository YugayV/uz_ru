from datetime import datetime, timedelta

REVIEW = {}

def add_to_review(chat_id, word):
    REVIEW.setdefault(chat_id, []).append({
        "word": word,
        "next_time": datetime.now() + timedelta(minutes=10)
    })

def get_review_word(chat_id):
    now = datetime.now()
    queue = REVIEW.get(chat_id, [])

    for item in queue:
        if item["next_time"] <= now:
            queue.remove(item)
            return item["word"]

    return None
