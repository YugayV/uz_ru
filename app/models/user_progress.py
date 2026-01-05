from datetime import date

class UserProgress:
    def __init__(self, last_active: date | None = None, streak: int = 0, total_days: int = 0):
        self.last_active: date | None = last_active
        self.streak: int = streak
        self.total_days: int = total_days
