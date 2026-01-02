from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.user import User

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/")
def get_leaderboard(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .order_by(User.points.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "user_id": u.id,
            "points": u.points,
            "streak": u.streak
        }
        for u in users
    ]
