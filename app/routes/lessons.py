from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session 

from app.schemas.lesson import LessonCreate, LessonOut 
from app.models.lesson import Lesson 
from app.core.deps import get_db 
import json 
import app.database

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.post("/", response_model=LessonOut)
def create_lesson(lesson: LessonCreate, db: Session = Depends(get_db)): 
    db_lesson = Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@router.get("/by-level/{level_id}", response_model = list[LessonOut])
def get_lessons_by_level(level_id: int, db: Session = Depends(get_db)): 
    return ( 
        db.query(Lesson)
        .filter(Lesson.level_id == level_id)
        .order_by(Lesson.order)
        .all()
    )


    lesson = Lesson(
        title=data["title"],
        level_id=level_id,
        content=json.dumps(data["content"])
    )
    db.add(lesson)
    db.commit()


from fastapi import Query, HTTPException
from pathlib import Path

@router.get("/{pair}/{level}")
def get_lessons_for_pair(pair: str, level: int, topic: str = "Greetings", kids: bool = Query(False)):
    """
    Generate a lesson for a language pair, level, and topic.
    If `kids=true`, it will filter/modify tasks suitable for kids.
    """
    # Placeholder for language mapping
    source_lang, target_lang = pair.split("-")

    # Generate a lesson dynamically instead of loading from a static file
    lesson_content = generate_lesson(level, topic, source_lang, target_lang)

    # The structure of the returned lesson can be adjusted as needed.
    # This is a simplified example.
    return {
        "level": level,
        "pair": pair,
        "topic": topic,
        "kids_mode": kids,
        "lesson": lesson_content,
    }
    path = content_dir / pair_key / f"level_{level}.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Lessons not found")

    with open(path, encoding="utf-8") as f:
        lessons = json.load(f)

    if kids:
        try:
            from app.routes.public_lessons import filter_for_kids
            lessons = [filter_for_kids(l) for l in lessons]
        except Exception:
            # If the filter helper is not available for any reason, do a minimal filter
            filtered = []
            for l in lessons:
                l2 = dict(l)
                l2['tasks'] = [t for t in l.get('tasks', []) if t.get('type') in ['listen', 'repeat', 'choose_sound']]
                filtered.append(l2)
            lessons = filtered

    return lessons
