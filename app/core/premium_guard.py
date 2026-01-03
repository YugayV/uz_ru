from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.premium import check_premium
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

def require_premium(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user or not check_premium(user):
        return False
    return True

def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()
client = get_openai_client()

class AIRequest(BaseModel):
    lang_from: str
    question: str

@router.post("/ask")
async def ask_ai(req: AIRequest):
    if not client:
        return {"answer": "⚠️ OpenAI API key is missing. Please add OPENAI_API_KEY to your .env or ini file."}
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Explain simply in {req.lang_from}"},
                {"role": "user", "content": req.question}
            ]
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": f"⚠️ Error calling OpenAI: {str(e)}"}
