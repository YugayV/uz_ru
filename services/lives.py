from datetime import datetime, time, timedelta 
import time
from services.progress import is_premium

MAX_LIVES = 6
RESET_SECONDS = 24 * 60 * 60  # 24 часа

# user_id -> { lives: int, last_reset: timestamp }
_lives = {}

def _reset_if_needed(user_id: int):
    now = time.time()
    data = _lives.get(user_id)

    if not data:
        _lives[user_id] = {
            "lives": MAX_LIVES,
            "last_reset": now
        }
        return

    if now - data["last_reset"] >= RESET_SECONDS:
        data["lives"] = MAX_LIVES
        data["last_reset"] = now

def get_lives(user_id: int) -> int:
    if is_premium(user_id):
        return MAX_LIVES
    _reset_if_needed(user_id)
    return _lives[user_id]["lives"]

def use_life(user_id: int) -> bool:
    if is_premium(user_id):
        return True
    _reset_if_needed(user_id)

    if _lives[user_id]["lives"] <= 0:
        return False

    _lives[user_id]["lives"] -= 1
    return True

def add_lives(user_id: int, amount: int):
    _reset_if_needed(user_id)
    _lives[user_id]["lives"] += amount
    if _lives[user_id]["lives"] > MAX_LIVES:
        _lives[user_id]["lives"] = MAX_LIVES

        