from fastapi import FastAPI
from app.database import Base, engine
import asyncio 
import threading

from tg_bot.bot import start_bot
from routes import ai

from app.routes import (
    users,
    levels,
    lessons,
    lives,
    ai,
    progress,
    leaderboard,
    premium,
    ai_tutor,
    payments,
    stripe_webhook
)

import uvicorn

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Language Learning Platform",
    version="0.7.0"
)

# === ROUTERS ===
app.include_router(users.router)
app.include_router(levels.router)
app.include_router(lessons.router)
app.include_router(lives.router)
app.include_router(ai.router)
app.include_router(ai_tutor.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)
app.include_router(premium.router)
app.include_router(payments.router)
app.include_router(stripe_webhook.router)

@app.on_event("startup")
def startup(): 
    loop = asyncio.new_event_loop()
    threading.Thread( 
        target=loop.run_until_complete, 
        args=(start_bot(),), 
        daemon=True
    ).start()

# === SYSTEM ===
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Language Platform backend is running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
