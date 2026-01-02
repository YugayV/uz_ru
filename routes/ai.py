from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 

from app.core.deps import get_db 
from app.models.user import User 
from app.services.ai_tutor import ask_ai 

router = APIRouter(prefix="/ai", tags=["AI Tutor"])

FREE_LIMIT = 5 

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_tutor import ask_ai

router = APIRouter(prefix="/ai", tags=["AI"])

class AIRequest(BaseModel):
    prompt: str


@router.post("/ask/{user_id}")
def ask_ai_tutor(user_id: int, request: AIRequest, question: str, db: Session = Depends(get_db)): 
    user = db.query(User).get(user_id)
    answer = ask_ai(request.prompt)

    if not user: 
        raise HTTPException(status_code=404, detail='User not found')

    if not user.is_premium and user.ai_requests_today >= FREE_LIMIT: 
        raise HTTPException( 
            status_code=403, 
            detail="AI  limit reached. Upgrade to premium."
        )

    import openai

    try:
        answer = ask_ai(question, user.base_language)
    except openai.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="OpenAI API quota exceeded. Please check your billing details or try again later."
        )
    except openai.APIError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service currently unavailable: {str(e)}"
        )

    if not user.is_premium: 
        user.ai_requests_today += 1
        db.commit()

    return { 
        'answer': answer, 
        "remaining_requests": ( 
            'unlimited' if user.is_premium else FREE_LIMIT - user.ai_requests_today
        )
    }