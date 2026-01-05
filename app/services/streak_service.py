from datetime import date, timedelta


def update_user_streak(user):
    """Update user's streak and total_days based on last_activity_date.

    Modifies and returns the updated streak (int).
    """
    today = date.today()
    last = getattr(user, "last_activity_date", None)

    if last == today:
        return user.streak or 0

    if last == today - timedelta(days=1):
        user.streak = (user.streak or 0) + 1
    else:
        user.streak = 1

    user.last_activity_date = today
    user.total_days = (user.total_days or 0) + 1

    return user.streak
