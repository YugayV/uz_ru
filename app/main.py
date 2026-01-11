import os
import json
import logging
from fastapi import FastAPI 
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware # Import the session middleware

from app.database import Base, engine 
from app.routes import webapp, telegram
# from app.routes import progress # Temporarily commented out to fix import error

from app.routes.telegram import set_telegram_webhook

# Import all models to ensure they are registered with Base before table creation
# Ensure all your models are imported here, including any new ones
from app.models import user, lesson, level, ai_usage, kid_profile
from app.models.progress import UserLessonProgress, CompletedExercise 

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager. Runs on startup and shutdown.
    """
    logger.info("✅ [main.py] LIFESPAN: Startup sequence initiated.")
    
    # Set the Telegram webhook on startup
    set_telegram_webhook()

    logger.info("🚀 AI Language Platform API is starting...")
    logger.info("--- DEVELOPMENT: Resetting database ---")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables dropped.")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables recreated successfully.")
    except Exception as e:
        logger.critical(f"!!! DB RESET FAILED: {e}", exc_info=True)
    
    logger.info("✅ [main.py] LIFESPAN: Startup sequence finished. App is running.")
    yield
    
    logger.info("🛑 AI Language Platform API is shutting down...")


app = FastAPI( 
    title='AI Language Platform', 
    version='0.3.0',
    lifespan=lifespan
)
logger.info("✅ [main.py] FastAPI app instance created.")

# Add session middleware. A strong, secret key is required for production.
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "a-temporary-secret-key-for-dev"))

# Attach simple rate-limiting middleware (placeholder for Redis-based limiter)
# from app.middleware import SimpleRateLimitMiddleware
# app.add_middleware(SimpleRateLimitMiddleware)


# Serve `content/` as static files under `/static`
from fastapi.staticfiles import StaticFiles
from pathlib import Path
CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
app.mount("/static", StaticFiles(directory=str(CONTENT_DIR)), name="static")

# Include all the routers for the application
# app.include_router(users.router) # Uncomment when these files exist and are correct
# app.include_router(levels.router)
# app.include_router(lessons.router)
# app.include_router(lives.router)
# app.include_router(ai.router)
# app.include_router(progress.router) # Temporarily commented out
# app.include_router(leaderboard.router)
# app.include_router(premium.router)
# app.include_router(ai_tutor.router)
# app.include_router(payments.router)
# app.include_router(stripe_webhook.router)
app.include_router(telegram.router)
# app.include_router(stt_game.router)
# app.include_router(admin.router)
# app.include_router(health.router)
# app.include_router(public_lessons.router)
# app.include_router(adaptive.router)
# app.include_router(translator.router)
app.include_router(webapp.router)


logger.info("✅ [main.py] END: All routers included. App is configured.")


@app.get('/')
def root(): 
    return { 
        "status": 'ok', 
        'message': "AI Language Platform backend is running. Use /learn to start the web app, or interact with the Telegram bot."
    }