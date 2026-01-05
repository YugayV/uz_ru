from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.character import get_reaction, load_manifest

router = APIRouter(prefix="/character", tags=["Character"])

@router.get("/{name}")
def get_character(name: str):
    manifest = load_manifest()
    if not manifest or manifest.get("id") != name:
        raise HTTPException(status_code=404, detail="Character not found")
    return manifest

class ReactIn(BaseModel):
    character: str
    event: str
    streak: int = 0

@router.post("/react")
def react(in_data: ReactIn):
    r = get_reaction(in_data.character, in_data.event, in_data.streak)
    if not r:
        raise HTTPException(status_code=500, detail="Character not available")
    return r
