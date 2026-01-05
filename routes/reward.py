from fastapi import APIRouter, HTTPException
from typing import Optional
from services.user_progress import get_progress

router = APIRouter(prefix="/reward", tags=["Reward"])

@router.post("/ad")
def watch_ad(user_id: Optional[int] = None):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    progress = get_progress(user_id)
    if getattr(progress, 'is_premium', False):
        return {"message": "Premium user", "lives": progress.lives}
    progress.add_lives(1)
    return {"lives": progress.lives}
