from sqlalchemy import Column, Integer, String, ForeignKey, Text 
from app.database import Base 

class Lesson(Base): 
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"))

    title = Column(String)
    content = Column(Text)

    order = Column(Integer)  # Lesson Number