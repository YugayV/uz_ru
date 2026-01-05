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


from fastapi import HTTPException
from pathlib import Path

@router.get("/lesson/kid/{lesson_id}")
def get_kid_lesson(lesson_id: str):
    """Return kid-friendly lesson payload (audio, image, game).

    lesson_id can be:
    - a direct path relative to `content/` (e.g. `en/a0/lesson_1`)
    - the lesson `id` field from the JSON (e.g. `en_a0_01`)
    - the filename without extension (e.g. `lesson_1`)
    """
    content_dir = Path(__file__).resolve().parents[1] / "content"

    # try direct path first
    candidate = content_dir / f"{lesson_id}.json"
    if candidate.exists():
        try:
            lesson = json.loads(candidate.read_text())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # search all JSON files for matching id or filename
        lesson = None
        for p in content_dir.rglob("*.json"):
            try:
                data = json.loads(p.read_text())
            except Exception:
                continue

            if data.get("id") == lesson_id or p.stem == lesson_id or lesson_id in p.stem:
                lesson = data
                break

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

    # Normalize audio/image paths to static URLs
    def to_static(path_or_obj):
        if not path_or_obj:
            return None
        if isinstance(path_or_obj, dict):
            out = {}
            for k, v in path_or_obj.items():
                out[k] = f"/static/{v.lstrip('/')}" if isinstance(v, str) else v
            return out
        if isinstance(path_or_obj, str):
            return f"/static/{path_or_obj.lstrip('/')}"
        return path_or_obj

    audio = to_static(lesson.get("audio"))
    image = to_static(lesson.get("image"))
    game = lesson.get("practice") or lesson.get("game")

    return {"audio": audio, "image": image, "game": game}