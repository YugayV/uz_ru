from .state import get_state


def on_success(chat_id):
    state = get_state(chat_id)
    state["word_index"] += 1

    if state["word_index"] >= 5:
        state["word_index"] = 0
        state["lesson_index"] += 1


def on_fail(chat_id, word):
    from .review import add_to_review
    add_to_review(chat_id, word)
