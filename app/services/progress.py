from sqlalchemy.orm import Session 
from app.models.lesson import Lesson
from app.models.progress import UserLessonProgress, CompletedExercise # Ensure CompletedExercise is imported
from app.database import SessionLocal
import hashlib


def _hash_exercise(exercise_data: dict) -> str:
    """Creates a simple, repeatable hash for an exercise dictionary."""
    question = exercise_data.get("question", "")
    # Use topic and options as well for better uniqueness
    topic = exercise_data.get("topic", "") 
    options_str = "".join(sorted(exercise_data.get("options", [])))
    unique_string = f"{question}-{topic}-{options_str}"
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def get_completed_exercise_hashes(user_id: int) -> set[str]:
    """Retrieves a set of all completed exercise hashes for a user."""
    db = SessionLocal()
    try:
        completed = db.query(CompletedExercise.exercise_hash).filter(CompletedExercise.user_id == user_id).all()
        return {item[0] for item in completed}
    finally:
        db.close()

def mark_exercise_as_completed(user_id: int, exercise_data: dict):
    """Saves a new completed exercise to the database."""
    db = SessionLocal()
    try:
        exercise_hash = _hash_exercise(exercise_data) # Hash the full exercise data
        
        # Check if it already exists to avoid duplicates
        exists = db.query(CompletedExercise).filter(
            CompletedExercise.user_id == user_id, 
            CompletedExercise.exercise_hash == exercise_hash
        ).first()
        
        if not exists:
            new_completion = CompletedExercise(
                user_id=user_id,
                exercise_hash=exercise_hash
            )
            db.add(new_completion)
            db.commit()
            db.refresh(new_completion) # Refresh to get ID
    finally:
        db.close()

# --- Existing (potentially unused) Telegram-related progress functions ---
# These functions seem to be for in-memory tracking of words, keep for now if they are used elsewhere.
_premium_users = set()

def is_premium(user_id: int) -> bool:
    """Check if a user has premium access."""
    return user_id in _premium_users

def enable_premium(user_id: int):
    """Enable premium access for a user."""
    _premium_users.add(user_id)

def disable_premium(user_id: int):
    """Disable premium access for a user."""
    _premium_users.discard(user_id)


PROGRESS = {}

def add_word(chat_id, word, language):
    PROGRESS.setdefault(chat_id, {}).setdefault(language, set()).add(word)

def count_words(chat_id, language):
    return len(PROGRESS.get(chat_id, {}).get(language, []))