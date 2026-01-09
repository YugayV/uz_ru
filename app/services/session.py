# Simple in-memory chat session store for Telegram flows
# Note: ephemeral — resets on process restart. Use persistent storage for production.

SESSIONS: dict[int, dict] = {}


def get_state(chat_id: int) -> dict | None:
    return SESSIONS.get(chat_id)


def set_state(chat_id: int, **kwargs):
    state = SESSIONS.setdefault(chat_id, {})
    state.update(kwargs)
    return state


def clear_state(chat_id: int):
    if chat_id in SESSIONS:
        del SESSIONS[chat_id]


def set_expected_answer(chat_id: int, answer: str):
    state = SESSIONS.setdefault(chat_id, {})
    state["expected_answer"] = answer


def pop_expected_answer(chat_id: int) -> str | None:
    state = SESSIONS.get(chat_id)
    if not state:
        return None
    return state.pop("expected_answer", None)
