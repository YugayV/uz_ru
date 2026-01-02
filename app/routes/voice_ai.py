from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.user import User
from app.services.ai_limits import can_use_ai, register_ai_use
from app.services.ai_prompt import build_prompt
from app.services.speech_to_text import speech_to_text
from app.services.text_to_speech import text_to_speech

router = APIRouter(prefix="/voice-ai", tags=["Voice AI"])

@router.post("/talk/{user_id}")
async def voice_talk(
    user_id: int,
    audio: UploadFile = File(...),
    level: str = "A1",
    source_lang: str = "RU",
    target_lang: str = "EN",
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not can_use_ai(db, user):
        raise HTTPException(status_code=429, detail="AI limit reached")

    # 1️⃣ Speech → Text
    text = speech_to_text(audio.file)

    # 2️⃣ Prompt
    prompt = build_prompt(level, source_lang, target_lang, text)

    # 3️⃣ AI (заглушка, позже GPT)
    ai_reply = "Nice job! Let me help you 😊"

    # 4️⃣ Text → Speech
    voice_response = text_to_speech(ai_reply)

    register_ai_use(db, user)

    return {
        "recognized_text": text,
        "reply_text": ai_reply,
        "voice": "audio_stream_here"
    }