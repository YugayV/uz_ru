from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.character_engine import get_reaction
from app.services.rewards import check_rewards

router = APIRouter(prefix="/stt", tags=["STT"])

class STTIn(BaseModel):
    user_id: int
    success: bool

@router.post("/game")
def stt_game(in_data: STTIn, db: Session = Depends(get_db)):
    user = db.query(User).get(in_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update streak and XP
    if in_data.success:
        user.streak = (user.streak or 0) + 1
    else:
        user.streak = 0

    mood, message, reward = get_reaction(in_data.success, getattr(user, "streak", 0))

    # Apply reward
    user.xp = (user.xp or 0) + reward

    # Persist
    db.add(user)
    db.commit()
    db.refresh(user)

    rewards = check_rewards(user)

    return {
        "success": in_data.success,
        "mood": mood,
        "message": message,
        "reward": reward,
        "rewards": rewards,
        "streak": user.streak,
        "xp": user.xp
    }


from pydantic import BaseModel
from difflib import SequenceMatcher

class VerifyIn(BaseModel):
    user_id: int
    transcript: str
    expected: str

@router.post("/verify")
def verify_transcript(in_data: VerifyIn, db: Session = Depends(get_db)):
    user = db.query(User).get(in_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ratio = SequenceMatcher(None, in_data.transcript.lower(), in_data.expected.lower()).ratio()
    success = ratio > 0.6  # adjustable threshold

    # reuse stt_game logic
    class TempIn:
        def __init__(self, user_id, success):
            self.user_id = user_id
            self.success = success

    temp = TempIn(in_data.user_id, success)
    resp = stt_game(temp, db)
    resp.update({"similarity": ratio})
    return resp
