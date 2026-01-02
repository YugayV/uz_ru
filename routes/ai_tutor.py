from fastapi import APIRouter, Depends, HTTPException
from app.core.premium_guard import require_premium
from sqlalchemy.orm import Session

from app.core.deps import get_db 
from app.models.user import User 
from app.services.ai_limits import can_use_ai, register_ai_use 
from app.services.ai_prompt import build_prompt

# временно заглушка вместо GPT API
def fake_ai_response(prompt: str):
    return "Great question! Let's learn step by step 😊"

router = APIRouter(prefix="/ai", tags=["AI Tutor"])

@router.post("/chat/{user_id}")
def ai_chat(
    user_id: int,
    message: str,
    level: str = "A1",
    source_lang: str = "RU",
    target_lang: str = "EN",
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not can_use_ai(db, user):
        raise HTTPException(
            status_code=429,
            detail="Daily AI limit reached"
        )

    prompt = build_prompt(level, source_lang, target_lang, message)

    response = fake_ai_response(prompt)

    register_ai_use(db, user)

    return {
        "reply": response,
        "premium": user.is_premium
    }

@router.get("/chat/{user_id}")
def ai_chat(user_id: int, is_premium: bool = Depends(require_premium)):
    if not is_premium:
        raise HTTPException(
            status_code=402,
            detail="Premium required"
        )

    return {"message": "AI Tutor response 🚀"}

