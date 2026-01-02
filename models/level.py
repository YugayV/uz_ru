from sqlalchemy import Column, Integer, String 
from app.database import Base 

class Level(Base): 
    __tablename__ = 'levels' 

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True) 
    title = Column(String) 
    language = Column(String) 

    