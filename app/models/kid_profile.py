from sqlalchemy import Column, Integer, Date, ForeignKey, String
from app.database import Base

class KidProfile(Base):
    __tablename__ = "kid_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer)
    language_from = Column(String)
    language_to = Column(String)
    level = Column(Integer, default=1)
    stars = Column(Integer, default=0)
