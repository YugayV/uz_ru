from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.daily_reminder import send_daily_reminder_for_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reminders/send")
def send_reminders(db: Session = Depends(get_db)):
    users = db.query(User).all()
    sent = 0
    for u in users:
        if send_daily_reminder_for_user(u):
            sent += 1
    return {"sent": sent}
