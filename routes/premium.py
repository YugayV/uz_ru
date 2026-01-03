from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.user import User
from app.services.premium import activate_premium
from app.services.ai_tutor import ask_ai

router = APIRouter(prefix="/premium", tags=["Premium"])

@router.post("/buy/{user_id}")
def buy_premium(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ⚠️ Здесь позже будет реальная оплата (Stripe / KakaoPay)
    activate_premium(user)
    db.commit()

    return {
        "status": "premium_activated",
        "premium_until": user.premium_until
    }

@router.post("/telegram/webhook")
def telegram_webhook(update: dict):
    text = update["message"]["text"]
    answer = ask_ai(text)
    return {"ok": True}
