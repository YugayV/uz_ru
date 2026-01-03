import time
from .subscription import get_plan

MAX_ADS_PER_DAY = 3
REWARD_LIVES = 2
RESET_SECONDS = 24 * 60 * 60

# user_id -> { views: int, last_reset: ts }
_ads = {}

def _reset_if_needed(user_id: int):
    now = time.time()
    data = _ads.get(user_id)

    if not data:
        _ads[user_id] = {
            "views": 0,
            "last_reset": now
        }
        return

    if now - data["last_reset"] >= RESET_SECONDS:
        data["views"] = 0
        data["last_reset"] = now

def can_watch_ad(user_id: int) -> bool:
    _reset_if_needed(user_id)
    return _ads[user_id]["views"] < MAX_ADS_PER_DAY

def register_ad_view(user_id: int):
    _reset_if_needed(user_id)
    _ads[user_id]["views"] += 1

def show_ad(chat_id):
    if get_plan(chat_id) == "free":
        return "📺 Посмотри короткое видео, чтобы продолжить!"

def restore_life(chat_id):
    if get_plan(chat_id) == "free":
        return "❤️ +1 жизнь за просмотр рекламы"

