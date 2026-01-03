from sqlalchemy.orm import Session 
from app.models.lesson import Lesson
from app.models.progress import UserLessonProgress 


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
