from pydantic import BaseModel
from datetime import datetime

class LessonProgressOut(BaseModel):
    lesson_id: int
    completed: bool
    completed_at: datetime | None 

    class Config:
        from_attributes = True
