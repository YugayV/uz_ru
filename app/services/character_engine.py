import random
from app.core.character import Mood

RESPONSES = {
    Mood.HAPPY: [
        "🎉 Ура!",
        "🦫 Отлично!",
        "👏 Молодец!"
    ],
    Mood.ENCOURAGING: [
        "😊 Почти получилось",
        "🦫 Давай ещё раз",
        "👍 Я верю в тебя"
    ],
    Mood.PROUD: [
        "🌟 Я горжусь тобой!",
        "🏆 Ты супер!"
    ],
    Mood.THINKING: [
        "🤔 Хорошая попытка",
        "Хмм, давай подумаем"
    ],
    Mood.SAD: [
        "Мне немного грустно, но всё получится",
        "Не переживай, попробуй снова"
    ]
}


def get_reaction(success: bool, streak: int = 0):
    """Return (mood, message, reward)

    reward: int XP (simple scheme)
    """
    if success and streak >= 3:
        mood = Mood.PROUD
        reward = 15
    elif success:
        mood = Mood.HAPPY
        reward = 10
    else:
        mood = Mood.ENCOURAGING
        reward = 0

    message = random.choice(RESPONSES.get(mood, [mood.value]))

    return mood.value, message, reward
