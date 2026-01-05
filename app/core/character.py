from enum import Enum

class Mood(str, Enum):
    HAPPY = "happy"
    PROUD = "proud"
    THINKING = "thinking"
    ENCOURAGING = "encouraging"
    SAD = "sad"
