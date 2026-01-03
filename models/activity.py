from datetime import datetime
from app.database import Base

class Activity(Base):
    user_id: int
    action: str
    timestamp: datetime
