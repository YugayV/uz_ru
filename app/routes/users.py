from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session 

from app.schemas.user import UserCreate, UserOut 
from app.models.user import User 
from app.core.deps import get_db 

router = APIRouter(prefix="/users", tags=["Users"])

@router.post('/register', response_model=UserOut)
def register_user( user: UserCreate, db: Session = Depends(get_db)):
    db_user_check = db.query(User).filter(User.email == user.email).first()
    if db_user_check:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User( 
        email=user.email, 
        password=user.password, 
        base_language=user.base_language
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user