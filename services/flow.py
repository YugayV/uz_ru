from services.state import get_state
from services.review import get_review_word
from app.services.lesson_loader import get_lessons

def next_step(chat_id, native, foreign):
    state = get_state(chat_id)

    # 1. Проверяем review
    review_word = get_review_word(chat_id)
    if review_word:
        return {
            "type": "review",
            "word": review_word
        }

    # 2. Новый урок
    lessons = get_lessons(native, foreign)
    lesson = lessons[state["lesson_index"]]
    word = lesson["words"][state["word_index"]]

    return {
        "type": "lesson",
        "word": word,
        "lesson_id": lesson["id"]
    }
