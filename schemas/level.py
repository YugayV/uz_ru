from pydantic import BaseModel 

class LevelCreate(BaseModel): 
    code: str # A0, A1...
    title: str 
    language: str #ru/ en/ ko

class LevelOut(LevelCreate): 
    id: int

    class Config: 
        from_attributes = True