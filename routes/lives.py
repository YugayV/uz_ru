from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 

from app.core.deps import get_db 
from app.models.user import User 
from app.services.lives import restore_lives_if_needed, lose_life 

router = APIRouter(prefix='/lives', tags=['Lives'])

@router.post("/check/{user_id}")
def check_lives(user_id: int, db: Session = Depends(get_db)): 
    user = db.query(User).get(user_id)

    if not user: 
        raise HTTPException(status_code=404, detail="User not found")

    restore_lives_if_needed(user)
    db.commit()

    return { 
        "lives": user.lives, 
        "is_premium": user.is_premium
    }

@router.post("/lose/{user_id}")
def lose_user_life(user_id: int, db: Session = Depends(get_db)): 
    user = db.query(User).get(user_id)

    if not user: 
        raise HTTPException(status_code=404, detail="User not found")

    restore_lives_if_needed(user)

    if user.lives <=0 and not user.is_premium: 
        raise HTTPException(status_code=403, detail="No lives left")

    lose_life(user)
    db.commit()

    return {"lives": user.lives}
    