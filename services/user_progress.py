from datetime import datetime, timedelta

MAX_LIVES = 6
LIFE_RESTORE_MINUTES = 15

class UserProgress:
    def __init__(self):
        self.lives = MAX_LIVES
        self.xp = 0
        self.level = 1
        self.last_life_lost_at: datetime | None = None
        self.is_premium = False
        self.premium_until: datetime | None = None

    def can_answer(self):
        # premium users can always answer
        if self.is_premium:
            # expire check
            if self.premium_until and datetime.utcnow() > self.premium_until:
                self.is_premium = False
                self.premium_until = None
            else:
                return True

        self.restore_lives_if_needed()
        return self.lives > 0

    def lose_life(self):
        if self.is_premium:
            return
        self.restore_lives_if_needed()
        if self.lives > 0:
            self.lives -= 1
            self.last_life_lost_at = datetime.utcnow()

    def gain_xp(self, amount=10):
        self.xp += amount
        # Simple leveling: every level requires level*100 xp
        if self.xp >= self.level * 100:
            self.level += 1
            self.xp = 0

    def restore_lives_if_needed(self):
        if self.lives >= MAX_LIVES:
            return

        if not self.last_life_lost_at:
            return

        minutes_passed = (datetime.utcnow() - self.last_life_lost_at).total_seconds() / 60
        restored = int(minutes_passed // LIFE_RESTORE_MINUTES)

        if restored > 0:
            self.lives = min(MAX_LIVES, self.lives + restored)
            # move last_life_lost_at forward by restored*interval to avoid double counting
            self.last_life_lost_at = datetime.utcnow()

    def add_lives(self, amount: int = 1):
        """Add lives (used for watching ads or rewards)."""
        if self.is_premium:
            return
        self.restore_lives_if_needed()
        self.lives = min(MAX_LIVES, self.lives + amount)


# In-memory store
_USER_PROGRESS: dict = {}

def get_progress(user_id: str | int) -> UserProgress:
    if user_id not in _USER_PROGRESS:
        progress = UserProgress()
        # Grant free 30-day premium to every new user by default
        grant_free_premium_for_progress(progress)
        _USER_PROGRESS[user_id] = progress
    return _USER_PROGRESS[user_id]

def grant_free_premium_for_progress(progress: UserProgress, days: int = 30):
    progress.is_premium = True
    progress.premium_until = datetime.utcnow() + timedelta(days=days)
