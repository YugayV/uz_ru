print("✅ [main.py] START: Script execution begins.")

import os
import json
from fastapi import FastAPI 
from contextlib import asynccontextmanager
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
    stripe_webhook,
    telegram,
    webapp,
    stt_game,
    admin,
    health,
    public_lessons,
    adaptive,
    translator,
)
from app.routes.telegram import set_telegram_webhook # Import the new function

# Import all models to ensure they are registered with Base before table creation
from app.models import user, lesson, level, ai_usage, kid_profile
from app.models.progress import UserLessonProgress, CompletedExercise # Make sure our new model is imported

# Legacy routers are now removed, ensure they are migrated to app/routes if needed.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager. Runs on startup and shutdown.
    """
    print("✅ [main.py] LIFESPAN: Startup sequence initiated.")
    
    # Set the Telegram webhook on startup
    set_telegram_webhook()

    print("🚀 AI Language Platform API is starting...")
    print("--- DEVELOPMENT: Resetting database ---")
    try:
        # The engine and Base are already imported
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped.")
        Base.metadata.create_all(bind=engine)
        print("Tables recreated successfully.")
    except Exception as e:
        print(f"!!! DB RESET FAILED: {e}")
    
    print("✅ [main.py] LIFESPAN: Startup sequence finished. App is running.")
    yield
    
    print("🛑 AI Language Platform API is shutting down...")


# Base.metadata.create_all(bind=engine) # This is now handled in lifespan

app = FastAPI( 
    title='AI Language Platform', 
    version='0.3.0',
    lifespan=lifespan
)
print("✅ [main.py] FastAPI app instance created.")

# Attach simple rate-limiting middleware (placeholder for Redis-based limiter)
from app.middleware import SimpleRateLimitMiddleware
app.add_middleware(SimpleRateLimitMiddleware)


# Serve `content/` as static files under `/static`
from fastapi.staticfiles import StaticFiles
from pathlib import Path
CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
app.mount("/static", StaticFiles(directory=str(CONTENT_DIR)), name="static")

# Include all the routers for the application
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
app.include_router(telegram.router) # Re-enable the telegram router
app.include_router(webapp.router)
app.include_router(stt_game.router)
app.include_router(admin.router)
app.include_router(health.router)
app.include_router(public_lessons.router)
app.include_router(adaptive.router)
app.include_router(translator.router)

print("✅ [main.py] END: All routers included. App is configured.")


@app.get('/')
def root(): 
    return { 
        "status": 'ok', 
        'message': "AI Language Platform backend is running"
    }


