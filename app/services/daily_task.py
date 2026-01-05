import random

DAILY_TASKS = [
    {"type": "listen_repeat", "duration": 2},
    {"type": "say_word", "duration": 1},
    {"type": "guess_sound", "duration": 2},
]


def get_daily_task():
    return random.choice(DAILY_TASKS)
