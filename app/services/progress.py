from sqlalchemy.orm import Session 
from app.models.lesson import Lesson
from app.models.progress import UserLessonProgress, CompletedExercise
from app.database import SessionLocal
import hashlib

def can_access_lesson(db: Session, user_id: int, lesson: Lesson) -> bool:
    if lesson.order == 1:
        return True

    prev_lesson = (
        db.query(Lesson)
        .filter(
            Lesson.level_id == lesson.level_id,
            Lesson.order == lesson.order - 1
        )
        .first()
    )

    if not prev_lesson:
        return True

    progress = (
        db.query(UserLessonProgress)
        .filter_by(user_id=user_id, lesson_id=prev_lesson.id, completed=True)
        .first()

    )

    return progress is not None

# user_id -> bool
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

def _hash_exercise(exercise_data: dict) -> str:
    """Creates a simple, repeatable hash for an exercise dictionary."""
    # We use the question as the primary source of uniqueness
    question = exercise_data.get("question", "")
    return hashlib.md5(question.encode('utf-8')).hexdigest()

def get_completed_exercise_hashes(user_id: int) -> set[str]:
    """Retrieves a set of all completed exercise hashes for a user."""
    db = SessionLocal()
    try:
        completed = db.query(CompletedExercise.exercise_hash).filter(CompletedExercise.user_id == user_id).all()
        # The query returns a list of tuples, so we unpack them into a set
        return {item[0] for item in completed}
    finally:
        db.close()

def mark_exercise_as_completed(user_id: int, exercise_data: dict):
    """Saves a new completed exercise to the database."""
    db = SessionLocal()
    try:
        exercise_hash = _hash_exercise(exercise_data)
        
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
    finally:
        db.close()
