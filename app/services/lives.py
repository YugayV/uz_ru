from datetime import datetime, timedelta

# In-memory storage for simple usage (e.g. Telegram bot without DB)
LIVES = {}
FAILS = {}

MAX_LIVES = 6

def init_user(chat_id):
    LIVES.setdefault(chat_id, MAX_LIVES)
    FAILS.setdefault(chat_id, 0)

def mistake(chat_id):
    chat_id = str(chat_id)
    FAILS[chat_id] = FAILS.get(chat_id, 0) + 1
    if FAILS[chat_id] >= 3:
        current_lives = LIVES.get(chat_id, MAX_LIVES)
        LIVES[chat_id] = max(0, current_lives - 1)
        FAILS[chat_id] = 0

def success(chat_id):
    chat_id = str(chat_id)
    FAILS[chat_id] = 0

def can_play(chat_id):
    chat_id = str(chat_id)
    return LIVES.get(chat_id, MAX_LIVES) > 0

# For FastAPI routes using the User database model

def restore_lives_if_needed(user):
    """
    Restores lives based on time passed.
    Logic: 1 life every 2 hours, up to MAX_LIVES.
    If user is premium, they always have MAX_LIVES.
    """
    if user.is_premium:
        user.lives = MAX_LIVES
        return

    if user.lives >= MAX_LIVES:
        user.last_life_restore = datetime.utcnow()
        return

    now = datetime.utcnow()
    if not user.last_life_restore:
        user.last_life_restore = now
        return

    diff = now - user.last_life_restore
    lives_to_restore = int(diff.total_seconds() // 7200) # 2 hours = 7200 seconds

    if lives_to_restore > 0:
        old_lives = user.lives
        user.lives = min(MAX_LIVES, user.lives + lives_to_restore)
        
        # Only advance the last_life_restore by the amount of time consumed for restored lives
        actual_restored = user.lives - old_lives
        if actual_restored > 0:
            user.last_life_restore = user.last_life_restore + timedelta(hours=actual_restored * 2)

def lose_life(user):
    """
    Decrements user lives if not premium.
    """
    if user.is_premium:
        return
    
    if user.lives > 0:
        user.lives -= 1
        # If we were at max lives before, start the timer for restoration
        if user.lives == MAX_LIVES - 1:
            user.last_life_restore = datetime.utcnow()

# For bot.py compatibility (legacy or simple mode)
def get_lives(user_id):
    user_id = str(user_id)
    return LIVES.get(user_id, MAX_LIVES)

def use_life(user_id):
    user_id = str(user_id)
    current = LIVES.get(user_id, MAX_LIVES)
    if current > 0:
        LIVES[user_id] = current - 1
        return True
    return False
