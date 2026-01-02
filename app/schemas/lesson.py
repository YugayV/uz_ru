from pydantic import BaseModel 

class LessonCreate(BaseModel): 
    level_id: int 
    title: str 
    content: str 
    order: int 

class LessonOut(LessonCreate): 
    id: int 

    class Config: 
        from_attributes = True