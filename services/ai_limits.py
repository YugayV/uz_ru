from datetime import date
from sqlalchemy.orm import Session
from app.models.ai_usage import AIUsage

FREE_LIMIT = 5  # запросов в день

def can_use_ai(db: Session, user):
    if user.is_premium:
        return True

    today = date.today()
    usage = (
        db.query(AIUsage)
        .filter_by(user_id=user.id, date=today)
        .first()
    )

    if not usage:
        usage = AIUsage(user_id=user.id, date=today, requests=0)
        db.add(usage)
        db.commit()

    return usage.requests < FREE_LIMIT


def register_ai_use(db: Session, user):
    today = date.today()
    usage = (
        db.query(AIUsage)
        .filter_by(user_id=user.id, date=today)
        .first()
    )

    if not usage:
        usage = AIUsage(user_id=user.id, date=today, requests=0)
        db.add(usage)

    usage.requests += 1
    db.commit()
