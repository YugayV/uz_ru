from pydantic import BaseModel 

class LeaderboardUser(BaseModel): 
    user_id: int 
    points: int 
    streak: int 

    class Config: 
        from_attributes = True 
        