from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session 

from app.schemas.lesson import LessonCreate, LessonOut 
from app.models.lesson import Lesson 
from app.core.deps import get_db 
import json 
import app.database

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.post("/", response_model=LessonOut)
def create_lesson(lesson: LessonCreate, data: dict, db: Session = Depends(get_db)): 
    db_lesson = Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson, {
        "status": "created",
        "lesson": data
    }

@router.get("/by-level/{level_id}", response_model = list[LessonOut])
def get_lessons_by_level(level_id: int, db: Session = Depends(get_db)): 
    return ( 
        db.query(Lesson)
        .filter(Lesson.level_id == level_id)
        .order_by(Lesson.order)
        .all(), 
        {"lessons": []}
    )


    lesson = Lesson(
        title=data["title"],
        level_id=level_id,
        content=json.dumps(data["content"])
    )
    db.add(lesson)
    db.commit()

@router.get("/lesson/{lang}/{level}/{num}")
def get_lesson(lang: str, level: str, num: int):
    with open(f"content/{lang}/{level}/lesson_{num}.json") as f:
        return json.load(f)


