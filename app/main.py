from fastapi import FastAPI 
from database import Base, engine 
from routes import (
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
    stripe_webhook,
    telegram,
    webapp,
    character,
    stt_game,
    admin,
    reward,
    health
)

# WARNING: This will drop all tables and recreate them on startup.
# This is useful for development but should be removed in production.
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI( 
    title='AI Language Learning Platform', 
    version='0.3.0'
)

# Attach simple rate-limiting middleware (placeholder for Redis-based limiter)
from app.middleware import SimpleRateLimitMiddleware
app.add_middleware(SimpleRateLimitMiddleware)


# Serve `content/` as static files under `/static`
from fastapi.staticfiles import StaticFiles
from pathlib import Path
CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
app.mount("/static", StaticFiles(directory=str(CONTENT_DIR)), name="static")

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
app.include_router(telegram.router)
app.include_router(webapp.router)
app.include_router(character.router)
app.include_router(stt_game.router)
app.include_router(admin.router)
app.include_router(reward.router)
app.include_router(public_lessons.router)
app.include_router(adaptive.router)
app.include_router(health.router)


@app.get('/')
def root(): 
    return { 
        "status": 'ok', 
        'message': "AI Language Platform backend is running"
    }


