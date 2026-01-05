from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_db 
from app.models.user import User 
from app.services.ai_tutor import ask_ai, tutor_reply 
from services.user_progress import get_progress

router = APIRouter(prefix="/ai", tags=["AI Tutor"])

FREE_LIMIT = 5 

class AIRequest(BaseModel):
    # backward-compatible fields
    prompt: Optional[str] = None
    text: Optional[str] = None
    mode: str = "adult"  # adult | child
    age: Optional[int] = None
    language: str = "ru"
    lesson_type: Optional[str] = None

    # tutor-specific fields (per step 44 spec)
    age_group: Optional[str] = None  # kid | adult
    language_pair: Optional[str] = None  # e.g., uz-ru
    level: Optional[int] = None
    lesson_title: Optional[str] = None
    user_input: Optional[str] = None  # text or None
    correct_answer: Optional[str] = None

    # optional user id (for game state)
    user_id: Optional[int] = None

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

    # If tutor-style fields are present, use tutor_reply
    if request.language_pair or request.lesson_title or request.age_group:
        # fill defaults
        age_group = request.age_group or ("kid" if (request.age and request.age < 12) else "adult")
        language_pair = request.language_pair or (f"{request.language}-en")
        level = request.level or 1
        lesson_title = request.lesson_title or "Lesson"
        user_input = request.user_input

        # Game state: check lives/xp/level
        progress = get_progress(user_id)
        if not progress.can_answer():
            return {"answer": "❤️ No lives left. Wait or watch ad.", "lives": progress.lives}

        try:
            # Kid mode + no input -> instruct child to listen & repeat (no penalty)
            if age_group == "kid" and not user_input:
                prompt_text = f"Listen 👂 {request.correct_answer or lesson_title}. Now you say!"
                return {"answer": prompt_text, "result": "no_input", "lives": progress.lives, "xp": progress.xp, "level": progress.level}

            reply = tutor_reply(
                age_group=age_group,
                language_pair=language_pair,
                level=progress.level,
                lesson_title=lesson_title,
                user_input=user_input
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"AI service currently unavailable: {str(e)}")

        # Evaluate the user's answer only if a correct_answer was provided and user input is present
        result = None
        correct_answer = request.correct_answer
        if correct_answer and (user_input is not None):
            try:
                from services.evaluator import evaluate
                result = evaluate(user_input, correct_answer, age_group)
            except Exception as e:
                print(f"Evaluation error: {e}")
                result = "almost"

            if result == "correct":
                progress.gain_xp()
            elif result == "wrong":
                progress.lose_life()
            # 'almost' -> no penalty

        # Add reward/sound on success
        extra = {}
        if result == "correct":
            extra = {"reward": "star", "sound": "/static/characters/capybara/audio/encourage.mp3"}

        if not user.is_premium:
            user.ai_requests_today += 1
            db.commit()

        resp = {"answer": reply, "lives": progress.lives, "xp": progress.xp, "level": progress.level, "is_premium": user.is_premium, "remaining_requests": ('unlimited' if user.is_premium else FREE_LIMIT - user.ai_requests_today)}
        if result is not None:
            resp["result"] = result
        resp.update(extra)
        return resp

    # fallback to conversational ask_ai
    question = request.text or request.prompt or ""
    
    try:
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

@router.post("/ask")
async def ask(request: AIRequest):
    """
    General AI ask endpoint without user_id tracking (or for public use)

    If tutor fields are provided (language_pair/lesson_title/age_group), this will act as the tutor endpoint and return {"reply": "..."}
    """
    # Tutor-style request
    if request.language_pair or request.lesson_title or request.age_group:
        age_group = request.age_group or ("kid" if (request.age and request.age < 12) else "adult")
        language_pair = request.language_pair or (f"{request.language}-en")
        level = request.level or 1
        lesson_title = request.lesson_title or "Lesson"
        user_input = request.user_input
        correct_answer = request.correct_answer
        user_id = request.user_id

        # If user_id provided, update and check progress
        if user_id:
            progress = get_progress(user_id)
            if not progress.can_answer():
                return {"reply": "❤️ No lives left. Wait or watch ad.", "lives": progress.lives}

        # Kid mode + no input -> instruct child to listen & repeat (no penalty)
        if age_group == "kid" and not user_input:
            prompt_text = f"Listen 👂 {correct_answer or lesson_title}. Now you say!"
            return {"reply": prompt_text, "result": "no_input", "lives": progress.lives} if user_id else {"reply": prompt_text, "result": "no_input"}

        try:
            reply = tutor_reply(
                age_group=age_group,
                language_pair=language_pair,
                level=level,
                lesson_title=lesson_title,
                user_input=user_input
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

        result = None
        if correct_answer and (user_input is not None):
            try:
                from services.evaluator import evaluate
                result = evaluate(user_input, correct_answer, age_group)
            except Exception as e:
                print(f"Evaluation error: {e}")
                result = "almost"

            if user_id:
                if result == "correct":
                    progress.gain_xp()
                elif result == "wrong":
                    progress.lose_life()

        # attach reward for correct
        out = {"reply": reply}
        if result is not None:
            out["result"] = result
        if user_id:
            out.update({"lives": progress.lives, "xp": progress.xp, "level": progress.level, "is_premium": progress.is_premium})
            if result == "correct":
                out.update({"reward": "star", "sound": "/static/characters/capybara/audio/encourage.mp3"})
        else:
            if result == "correct":
                out.update({"reward": "star", "sound": "/static/characters/capybara/audio/encourage.mp3"})
        return out

    # fallback conversational
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