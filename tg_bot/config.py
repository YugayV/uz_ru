import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Backend tutor endpoint - can be local or deployed
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/ai/ask")

# Default language mapping for TTS (gTTS language codes)
LANGUAGE_MAP = {
    "ru": "ru",
    "uz": "uz",
    "en": "en",
    "ko": "ko"
}
