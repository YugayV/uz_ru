from sqlalchemy import Column, Integer, Date, ForeignKey
from app.database import Base

class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    requests = Column(Integer, default=0)
