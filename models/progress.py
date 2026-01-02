from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))

    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, default=None)
