from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.adaptive_tutor import select_lesson_for_user, handle_submission

router = APIRouter(prefix="/adaptive", tags=["Adaptive"])

class NextIn(BaseModel):
    user_id: int
    pair: str  # e.g. 'uz_ru'

class SubmitIn(BaseModel):
    user_id: int
    lesson_id: str
    transcript: str
    expected: str

@router.post("/next")
def next_lesson(in_data: NextIn, db: Session = Depends(get_db)):
    user = db.query(User).get(in_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    lesson = select_lesson_for_user(user, in_data.pair)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"lesson": lesson}

@router.post("/submit")
def submit(in_data: SubmitIn, db: Session = Depends(get_db)):
    user = db.query(User).get(in_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # minimal: lesson_task not used directly here, we just eval
    res = handle_submission(user, None, in_data.transcript, in_data.expected)
    db.add(user)
    db.commit()
    db.refresh(user)

    # suggest next lesson
    next_lesson = select_lesson_for_user(user, user.base_language.lower() + "_en")

    return {"result": res, "next_lesson": next_lesson}
