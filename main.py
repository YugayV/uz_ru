from fastapi import FastAPI
import asyncio 
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables before importing routes
load_dotenv()

from app.database import Base, engine

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

# Initialize database
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the server starts
    print("🚀 AI Language Platform API is starting...")
    # You can start other background tasks here if needed
    yield
    # This runs when the server stops
    print("🛑 AI Language Platform API is shutting down...")

app = FastAPI(
    title="AI Language Learning Platform",
    version="1.1.0",
    lifespan=lifespan
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
