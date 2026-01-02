from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from datetime import datetime
from app.models.user import User

from app.core.deps import get_db 
from app.models.lesson import Lesson 
from app.models.progress import UserLessonProgress 
from app.services.progress import can_access_lesson 
from app.services.streak import update_streak_and_points

router = APIRouter(prefix='/progress', tags=["Progress"])

@router.get("/lesson/{user_id}/{lesson_id}")
def open_lesson(user_id: int, lesson_id: int, db: Session =Depends(get_db)): 
    lesson = db.query(Lesson).get(lesson_id)
    if not lesson: 
        raise HTTPException(status_code=404, detail='Lesson not found')

    if not can_access_lesson(db, user_id, lesson): 
        raise HTTPException(status_code=403, detail='Lesson is locked')

    return {'lesson_id': lesson.id, 'title': lesson.title, 'content': lesson.content}


@router.post("/complete/{user_id}/{lesson_id}")
def complete_lesson(user_id: int, lesson_id: int, db: Session = Depends(get_db)):
    progress = (
        db.query(UserLessonProgress)
        .filter_by(user_id=user_id, lesson_id=lesson_id)
        .first()
    )

    if not progress:
        progress = UserLessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(progress)
    else:
        progress.completed = True
        progress.completed_at = datetime.utcnow()

    db.commit()
    return {"status": "completed"}
    

@router.get("/level/{user_id}/{level_id}")
def level_progress(user_id: int, level_id: int, db: Session = Depends(get_db)): 
    total = db.query(Lesson).filter(Lesson.level_id == level_id).count()
    completed = ( 
        db.query(UserLessonProgress)
        .join(Lesson, Lesson.id == UserLessonProgress.lesson_id)
        .filter( 
            UserLessonProgress.user_id == user_id, 
            UserLessonProgress.completed == True, 
            Lesson.level_id == level_id
        )
        .count()
    )

    percent = (completed / total * 100) if total > 0 else 0

    return { 
        "total_lessons": total,
        "completed": completed, 
        "progress_percent": round(percent, 1)
    }

    user = db.query(User).get(user_id)
    update_streak_and_points(user)
    db.commit()

    