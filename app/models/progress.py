from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, String
from datetime import datetime
from app.database import Base

class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))

    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, default=None)

class CompletedExercise(Base):
    __tablename__ = "completed_exercises"

    id = Column(Integer, primary_key=True, index=True)
    
    # We will use the user's ID from the users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # A unique hash or ID representing the exercise
    exercise_hash = Column(String, index=True, nullable=False)

    def __repr__(self):
        return f"<CompletedExercise user_id='{self.user_id}' hash='{self.exercise_hash}'>"
