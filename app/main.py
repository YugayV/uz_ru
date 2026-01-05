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
    webapp
)

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
app.include_router(telegram.router)
app.include_router(webapp.router)


@app.get('/')
def root(): 
    return { 
        "status": 'ok', 
        'message': "AI Language Platform backend is running"
    }


