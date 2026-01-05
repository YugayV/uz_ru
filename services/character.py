


"""Character reaction utilities.

This module provides helper functions to load a character manifest and
select an appropriate reaction (emotion, phrase, media, rewards) for
in-app events such as 'correct', 'incorrect', 'start', 'win', 'lose'.
"""

import json
from pathlib import Path
from random import choice

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "content" / "characters" / "capybara" / "manifest.json"


def load_manifest():
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_reaction(character: str, event: str, streak: int = 0):
    """Return a reaction dict: {emotion, image, audio, phrase, reward}

    event: 'correct' | 'incorrect' | 'start' | 'win' | 'lose'
    """
    manifest = load_manifest()
    if not manifest:
        return None

    if event == "correct":
        emotion = "happy"
        reward = {"xp": 5, "coins": 2}
    elif event == "win":
        emotion = "happy"
        reward = {"xp": 15, "coins": 10}
    elif event == "incorrect":
        emotion = "encourage"
        reward = {"xp": 1, "coins": 0}
    else:
        emotion = "encourage"
        reward = {"xp": 0, "coins": 0}

    emo = manifest["emotions"].get(emotion, {})
    phrase = choice(emo.get("phrases", [emotion]))

    return {
        "character": manifest["id"],
        "emotion": emotion,
        "image": emo.get("image"),
        "audio": emo.get("audio"),
        "phrase": phrase,
        "reward": reward
    }
