from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timedelta
from app.database import Base
from sqlalchemy import Date, Boolean







class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    lives = Column(Integer, default=6)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(Date, nullable=True)

    base_language = Column(String, default="RU")

    last_life_restore = Column(DateTime, default=datetime.utcnow)

    ai_requests_today = Column(Integer, default=0)

    streak = Column(Integer, default=0)
    points = Column(Integer, default=0)
    last_activity_date = Column(Date, default=None)

    # Mapped columns
    telegram_id = Column(Integer, nullable=True, index=True)
    role = Column(String, default="child")  # child | parent
    parent_id = Column(Integer, nullable=True)  # optional parent user id

   
   