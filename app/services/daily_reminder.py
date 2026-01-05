import os
import requests
from datetime import date
from app.services.character_engine import get_reaction

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_character_message(chat_id: int, mood: str, phrase: str = None):
    # find audio/image from capy manifest
    try:
        # manifest path relative to content
        import json
        from pathlib import Path
        manifest_path = Path(__file__).resolve().parents[1] / "content" / "characters" / "capybara" / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        emo = manifest["emotions"].get(mood, {})
        audio = emo.get("audio")
        image = emo.get("image")
        text = phrase or (emo.get("phrases") or [None])[0]

        # send image
        if image:
            local_img = Path(__file__).resolve().parents[1] / image
            if local_img.exists():
                with open(local_img, "rb") as photo:
                    requests.post(f"{TG_API}/sendPhoto", data={"chat_id": chat_id}, files={"photo": photo})

        # send audio if exists
        if audio:
            local_audio = Path(__file__).resolve().parents[1] / audio
            if local_audio.exists():
                with open(local_audio, "rb") as a:
                    requests.post(f"{TG_API}/sendVoice", data={"chat_id": chat_id}, files={"voice": a})
                return

        # fallback to TTS via sendMessage (short phrase)
        if text:
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception:
        # best-effort: plain message
        if phrase:
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": phrase})


def send_daily_reminder_for_user(user, force=False):
    """Send daily reminder to a user if they have not been active today.

    Returns True if a message was sent.
    """
    today = date.today()
    if user.last_activity_date == today and not force:
        return False

    # choose mood
    mood = "proud" if (getattr(user, "streak", 0) or 0) >= 5 else "encourage"
    # get reaction
    reaction = get_reaction("capybara", "encourage" if mood == "encourage" else "win")
    phrase = reaction.get("phrase") if reaction else None

    send_character_message(user.telegram_id, mood if mood != "encourage" else "encourage", phrase)
    return True
