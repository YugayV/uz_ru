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

# --- Database-backed User and Session Management ---
import uuid
from app.database import SessionLocal
from app.models.user import User

def get_or_create_web_user(session_id: str | None) -> tuple[User, str]:
    """
    Finds a user by their session ID or creates a new one if not found.
    Returns the User object and a (potentially new) session_id.
    """
    db = SessionLocal()
    try:
        if session_id:
            # A session ID is a string, but our User model uses an email-like field.
            # We'll use a special format for web session IDs.
            session_email = f"session-{session_id}@webapp.guest"
            user = db.query(User).filter(User.email == session_email).first()
            if user:
                return user, session_id

        # If no user found or no session_id provided, create a new one.
        new_session_id = str(uuid.uuid4())
        new_user_email = f"session-{new_session_id}@webapp.guest"
        
        new_user = User(
            email=new_user_email,
            password="", # Not needed for guest users
            role="webapp_guest"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user, new_session_id
    finally:
        db.close()
