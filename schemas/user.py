from pydantic import BaseModel

class UserCreate(BaseModel): 
    email: str 
    password: str 
    base_language: str 

class UserOut(BaseModel): 
    id: int 
    email: str 
    lives: int 
    is_premium: bool
    base_language: str

    class Config: 
        from_attributes = True 
        