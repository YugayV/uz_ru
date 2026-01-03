from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_db 
from app.models.user import User 
from app.services.ai_tutor import ask_ai 

router = APIRouter(prefix="/ai", tags=["AI Tutor"])

FREE_LIMIT = 5 

class AIRequest(BaseModel):
    prompt: Optional[str] = None
    text: Optional[str] = None
    mode: str = "adult"  # adult | child
    age: Optional[int] = None
    language: str = "ru"
    lesson_type: Optional[str] = None

class AIResponse(BaseModel):
    answer: str
    remaining_requests: Optional[int | str] = None

@router.post("/ask/{user_id}", response_model=AIResponse)
def ask_ai_tutor(user_id: int, request: AIRequest, db: Session = Depends(get_db)): 
    user = db.query(User).get(user_id)
    if not user: 
        raise HTTPException(status_code=404, detail='User not found')

    if not user.is_premium and user.ai_requests_today >= FREE_LIMIT: 
        raise HTTPException( 
            status_code=403, 
            detail="AI limit reached. Upgrade to premium."
        )

    # Use 'text' if 'prompt' is missing, fallback to empty string
    question = request.text or request.prompt or ""
    
    try:
        # Map our request fields to ask_ai signature
        # We might need to update ask_ai to support age and lesson_type
        answer = ask_ai(
            question=question, 
            mode=request.mode, 
            base_language=request.language.upper(),
            age=request.age,
            lesson_type=request.lesson_type
        )
    except Exception as e:
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

@router.post("/ask", response_model=AIResponse)
async def ask(request: AIRequest):
    """
    General AI ask endpoint without user_id tracking (or for public use)
    """
    question = request.text or request.prompt or ""
    if not question:
        raise HTTPException(status_code=400, detail="Text or prompt is required")
        
    try:
        response = ask_ai(
            question=question,
            mode=request.mode,
            base_language=request.language.upper(),
            age=request.age,
            lesson_type=request.lesson_type
        )
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))