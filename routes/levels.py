from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session 

from app.schemas.level import LevelCreate, LevelOut 
from app.models.level import Level 
from app.core.deps import get_db 

router = APIRouter(prefix="/levels", tags=["levels"])

@router.post("/", response_model=LevelOut) 
def create_level(level: LevelCreate, db: Session = Depends(get_db)): 
    db_level = Level(**level.model_dump())
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level 

@router.get("/", response_model=list[LevelOut])
def get_levels(db: Session = Depends(get_db)): 
    return db.query(Level).all()