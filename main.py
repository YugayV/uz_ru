from fastapi import FastAPI 
from app.database import Base, engine 
from app.routes import users, levels, lessons, lives
from app.routes import ai
from app.routes import progress
from app.routes import leaderboard
from app.routes import premium
from app.routes import ai_tutor
from app.routes import payments, stripe_webhook

Base.metadata.create_all(bind=engine)

app = FastAPI( 
    title='AI Language Learning Platform', 
    version='0.3.0'
)

app.include_router(users.router)
app.include_router(levels.router)
app.include_router(lessons.router)
app.include_router(lives.router)
app.include_router(ai.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)
app.include_router(premium.router)
app.include_router(ai_tutor.router)
app.include_router(payments.router)
app.include_router(stripe_webhook.router)

@app.get('/')
def root(): 
    return { 
        "status": 'ok', 
        'message': "AI Language Platform backend is running"
    }

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}


