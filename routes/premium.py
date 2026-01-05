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

@router.post("/buy")
def buy_premium_simple(user_id: int):
    # Simple in-memory premium activation for non-DB users (stub for $5)
    try:
        from services.user_progress import get_progress, grant_free_premium_for_progress
        progress = get_progress(user_id)
        grant_free_premium_for_progress(progress)
        return {"is_premium": progress.is_premium, "premium_until": progress.premium_until}
    except Exception:
        # Fall back to a simple acknowledgement
        return {"is_premium": True, "premium_until": "30 days from now (mock)"}

@router.post("/telegram/webhook")
def telegram_webhook(update: dict):
    text = update["message"]["text"]
    answer = ask_ai(text)
    return {"ok": True}
