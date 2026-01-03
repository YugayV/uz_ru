from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.premium import check_premium
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

def require_premium(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user or not check_premium(user):
        return False
    return True

router = APIRouter()
client = OpenAI()

class AIRequest(BaseModel):
    lang_from: str
    question: str

@router.post("/ask")
async def ask_ai(req: AIRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Explain simply in {req.lang_from}"},
            {"role": "user", "content": req.question}
        ]
    )
    return {"answer": response.choices[0].message.content}