STARS = {}

def add_star(chat_id):
    STARS[chat_id] = STARS.get(chat_id, 0) + 1


def check_rewards(user):
    rewards = []

    if getattr(user, "streak", 0) == 3:
        rewards.append("streak_3")

    xp = getattr(user, "xp", 0)
    if xp and xp % 100 == 0:
        rewards.append("level_up")

    return rewards


def level_from_xp(xp: int) -> int:
    return xp // 100
