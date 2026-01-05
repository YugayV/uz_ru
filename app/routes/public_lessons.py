from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import json

router = APIRouter(prefix="/public-lessons", tags=["PublicLessons"])

CONTENT_LESSON_DIR = Path(__file__).resolve().parents[1].parents[0] / "data" / "lessons"


def filter_for_kids(lesson: dict) -> dict:
    lesson = dict(lesson)
    tasks = [t for t in lesson.get("tasks", []) if t.get("type") in ["listen", "repeat", "choose_sound"]]
    lesson["tasks"] = tasks
    lesson["audio_only"] = True
    return lesson


@router.get("/{pair}/{level}")
def get_lessons(pair: str, level: int, kids: bool = Query(False)):
    path = CONTENT_LESSON_DIR / pair / f"level_{level}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Lessons not found")

    with open(path, encoding="utf-8") as f:
        lessons = json.load(f)

    if kids:
        lessons = [filter_for_kids(l) for l in lessons]

    return lessons
