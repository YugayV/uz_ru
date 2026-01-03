from datetime import date, timedelta 

LESSON_POINTS = 10 

def update_streak_and_points(user): 
    today = date.today()

    if user.last_activity_date is None: 
        user.streak = 1
    else: 
        delta = (today - user.last_activity_date).days

        if delta == 1: 
            user.streak += 1
        elif delta > 1: 
            user.streak = 1 #Restart

    user.last_activity_date = today 
    user.points += LESSON_POINTS

STREAK = {}

def update_streak(chat_id):
    today = date.today()
    last = STREAK.get(chat_id)

    if last == today:
        return

    if last == today.fromordinal(today.toordinal() - 1):
        STREAK[chat_id] = today
    else:
        STREAK[chat_id] = today